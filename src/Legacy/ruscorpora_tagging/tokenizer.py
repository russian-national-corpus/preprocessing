# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

import codecs
import os
import xml.sax
import re
import optparse
from modules import fs_walk, element_stack, config, task_list
from modules import common

word_break_tags = [u'sub', u'sup']

para_break_tags = [u'p', u'tr', u'td', u'th', u'table', u'body', u'se', 'speach']

chars = u'A-Za-z\u00C0-\u00D7\u00D8-\u00F6\u00F8-\u04FF\u2DE0-\u2DFF\uA640-\uA69F'
cap_chars = ur'A-Z\u0401\u0410-\u042F'
low_chars = ur'a-z\u0451\u0430-\u044F'
token_separators = u'-'
ext_token_separators = u'-\'\u2019' # for Ukrainian

char_re = re.compile(ur'[%s]' % chars)
cap_char_re = re.compile(ur'[%s]' % cap_chars)
low_char_re = re.compile(ur'[%s]' % low_chars)

word_pattern = ur'([%s]*[%s]+[%s%s]*)+([%s]([%s%s])+)*|[0-9]+([.,-][0-9]+)*'

editor_brackets_re = '|'.join(['\\' + bracket for bracket in common.EDITOR_BRACKETS])
word_re = re.compile(word_pattern % \
                     (editor_brackets_re,
                      chars,
                      chars,
                      editor_brackets_re,
                      token_separators,
                      chars,
                      editor_brackets_re))

ext_word_re = re.compile(word_pattern % \
                         (editor_brackets_re,
                          chars, chars,
                          editor_brackets_re,
                          ext_token_separators,
                          chars,
                          editor_brackets_re))

dot_in_digits_re = re.compile(u'[0-9]+[.][0-9]+')
dot_before_lowercase_re = re.compile(u'[.] *[%s]+' % low_chars)
# sentence_end_re = re.compile(ur'\.\.\.|[.?!]')
sentence_end_re = re.compile(ur'[?!\.]{1,}[\xbb|\"]*')

# string -> list of sentences (lists of words)
def make_sentences(para):
    sentences = []
    startpos = 0
    pos = 2
    while True:
        match = sentence_end_re.search(para, pos)
        if not match:
            sentences.append(make_words(para[startpos:], startpos))
            break
        pos = match.end()
        if para[pos - 1] == '.':
            if cap_char_re.match(para[pos - 2]) \
               and (pos == startpos + 2 or not char_re.match(para[pos - 3])):
                continue
            if dot_in_digits_re.match(para, pos - 2):
                continue
            if dot_before_lowercase_re.match(para, pos - 1):
                continue

        sentences.append(make_words(para[startpos: pos], startpos))
        startpos = pos
        pos = startpos + 2

    return sentences

# string -> list of words;
# each word is a tuple (token_text, token_type {punct/word}, begin position, end_position)
def make_words(sent, begin_position=0):
    words = []
    pos = 0
    while True:
        if not len(sent[pos:]):
            break
        match = ext_word_re.search(sent, pos)
        if not match:
            words.append((sent[pos:], 'punct', begin_position + pos, begin_position + len(sent)))
            break
        if pos != match.start():
            words.append((sent[pos:match.start()],
                          'punct',
                          begin_position + pos,
                          begin_position + match.start()))
        words.append((sent[match.start(): match.end()],
                      'word',
                      begin_position + match.start(),
                      begin_position + match.end()))
        pos = match.end()
    return words


class TokenizerHandler(xml.sax.handler.ContentHandler):
    NULL_ELEMENT = -1
    def __init__(self, in_destination):
        self.sentences = []
        self.element_stack = element_stack.ElementStack()
        self.inbody = False
        self.inside_noindex = False
        self.noindex_characters = ''
        self.out = in_destination
        self.do_not_tokenize_sentence = False

    def characters(self, content):
        if self.inside_noindex:
            self.noindex_characters += content
            return
        self.element_stack.addChars(content)

    def flush_tag(self, in_tag_name, in_tag_attrs={}):
        characters = '<%s' % in_tag_name
        for (name, value) in in_tag_attrs.items():
            characters += ' %s="%s"' % (name, value)
        characters += '>'
        return characters

    def startDocument(self):
        self.out.write('<?xml version="1.0" encoding="%s"?>\n' % config.CONFIG['out_encoding'])

    def endDocument(self):
        self.collapse_element_stack()
        self.out.write('\n')

    def startElement(self, tag, attrs):
        if self.inside_noindex:
            self.noindex_characters += self.flush_tag(tag, attrs)
        if tag in para_break_tags:
            self.collapse_element_stack()
        if tag == 'noindex':
            self.inside_noindex = True
            return
        if tag == 'w':
            self.do_not_tokenize_sentence = True
        if tag == 'body':
            self.inbody = True
        self.element_stack.startTag(tag, attrs)

    def endElement(self, tag):
        if tag == 'noindex':
            self.element_stack.insertNoindexTag('noindex', self.noindex_characters)
            self.inside_noindex = False
            self.noindex_characters = ''
            return
        if self.inside_noindex:
            self.noindex_characters += self.flush_tag('/' + tag)
        self.element_stack.endTag(tag)
        if tag in para_break_tags: # 'body' is in para_break_tags
            self.collapse_element_stack()
        if tag == 'se':
            self.do_not_tokenize_sentence = False
        if tag == 'body':
            self.inbody = False

    def collapse_element_stack(self):
        if self.inbody and not self.do_not_tokenize_sentence:
            self.tokenize_sentences()
        self.out.write(self.element_stack.collapse())

    def ignorableWhitespace(self, whitespace):
        self.characters(whitespace)

    def tokenize_sentences(self):
        plaintext = ''
        for element in self.element_stack.storage:
            if element[0] == 'content':
                plaintext += element[1]
        tokenizing_one_sentence = False
        if len(self.element_stack.storage):
            last_element = self.element_stack.storage[-1]
            tokenizing_one_sentence = last_element[0] == 'tag_close' and last_element[1] == 'se'
        if tokenizing_one_sentence:
            self.sentences = [make_words(plaintext)]
        else:
            self.sentences = make_sentences(plaintext)
        if not tokenizing_one_sentence:
            self.tag_sentence_boundaries()
        self.tag_word_boundaries()

    def tag_word_boundaries(self):
        for sentence in self.sentences:
            for word in sentence:
                if word[1] == 'word':
                    coordinates = word[2:]
                    begin_element = self.find_region_begin(coordinates, False)
                    word_open_index = \
                        self.element_stack.insert_tag_into_content(begin_element,
                                                                   coordinates[0],
                                                                   ('tag_open', 'w', ''))
                    end_element = self.find_region_end(coordinates, False)
                    word_close_index = \
                        self.element_stack.insert_tag_into_content(end_element,
                                                                   coordinates[1],
                                                                   ('tag_close', 'w', ''))
                    if word_open_index >= word_close_index:
                        raise RuntimeError('Invalid tag positions: <w> - %d, </w> - %d' %
                                           (word_open_index, word_close_index))
                    self.element_stack.fix_intersected_tags(word_open_index, word_close_index)

    def tag_sentence_boundaries(self):
        for sentence in self.sentences:
            if self.sentence_is_punct(sentence):
                continue
            sentence_begin = self.find_region_begin(sentence[0][2:], True)
            tag_open = ('tag_open', 'se', '')
            heading_spaces = re.search('^\s+', sentence[0][0])
            open_position = sentence[0][2]
            if heading_spaces:
                open_position += heading_spaces.end()
            open_index = self.element_stack.insert_tag(sentence_begin, open_position, tag_open)

            sentence_end = self.find_region_end(sentence[-1][2:], True)
            trailing_spaces = re.search('\s+$', sentence[-1][0])
            close_position = sentence[-1][3]
            if trailing_spaces:
                close_position += trailing_spaces.start()
            tag_close = ('tag_close', 'se', '')
            close_index = self.element_stack.insert_tag(sentence_end, close_position, tag_close)
            self.element_stack. fix_intersected_tags(open_index, close_index)

    def sentence_is_punct(self, in_sentence):
        for token in in_sentence:
            if token[1] == 'word':
                return False
        return True

    def position_breaks_content(self, in_position, in_element_index):
        element = self.element_stack.storage[in_element_index]
        return in_position > element[2] and in_position < element[3]

    # greedy enclosing means that we want to enclose
    # all the non-para-breaking tags we encounter
    def find_region_begin(self, in_first_content_token_position, in_greedy_enclosing):
        (content_begin, content_end) = in_first_content_token_position
        element_index = self.find_content_tag_by_coordinate(content_begin)
        keep_tracking = in_greedy_enclosing \
                        and not self.position_breaks_content(content_begin, element_index)
        while keep_tracking:
            previous_index = max(0, element_index - 1)
            if element_index == previous_index:
                keep_tracking = False
                continue
            element = self.element_stack.storage[previous_index]
            # going over all tag elements like <i>, <b>, <line>...
            if element[0] == 'tag_open' and element[1] not in para_break_tags:
                element_index = previous_index
            else:
                keep_tracking = False
        return element_index

    def find_region_end(self, in_last_content_token_position, in_greedy_enclosing):
        (content_begin, content_end) = in_last_content_token_position
        # normally we don't have zero-length regions, so -1 is ok
        element_index = self.find_content_tag_by_coordinate(content_end - 1)
        keep_tracking = in_greedy_enclosing \
                        and not self.position_breaks_content(content_end, element_index)
        while keep_tracking:
            next_index = min(len(self.element_stack.storage) - 1, element_index + 1)
            if element_index == next_index:
                keep_tracking = False
                continue
            element = self.element_stack.storage[next_index]
            # going over all tag elements like <i>, <b>, <line>...
            if element[0] == 'tag_close' and element[1] not in para_break_tags:
                element_index = next_index
            else:
                keep_tracking = False
        return element_index

    def find_content_tag_by_coordinate(self, in_coordinate):
        for index in xrange(len(self.element_stack.storage)):
            element = self.element_stack.storage[index]
            el_type = element[0]
            if el_type == 'content' and element[2] <= in_coordinate and in_coordinate < element[3]:
                return index
        return TokenizerHandler.NULL_ELEMENT

    def flush_sentences(self):
        text_to_flush = ''
        for sentence in self.sentences:
            (first_word_position, last_word_position) = (len(sentence), -1)
            for index in xrange(len(sentence)):
                token = sentence[index]
                if token[1] == 'word':
                    if index < first_word_position:
                        first_word_position = index
                    if last_word_position < index:
                        last_word_position = index
            for index in xrange(len(sentence)):
                (token_text, token_type, begin, end) = sentence[index]
                if index == first_word_position:
                    text_to_flush += '<se>'
                if token_type == 'word':
                    text_to_flush += '<w>%s</w>' % common.quotetext(token_text)
                else:
                    text_to_flush += self.meld_layers_for_token(sentence[index])
                if index == last_word_position:
                    text_to_flush += '</se>'
        return text_to_flush

def convert_and_log(in_paths):
    retcode = convert(in_paths)
    print '"%s" tokenized - %s' % (in_paths[0], 'OK' if retcode == 0 else 'FAIL')
    return retcode

def convert(in_paths):
    (inpath, outpath) = in_paths
    out = outpath
    if isinstance(outpath, str):
        out = codecs.getwriter(config.CONFIG['out_encoding'])(file(outpath, 'wb'), 'xmlcharrefreplace')
    tokenizer_handler = TokenizerHandler(out)
    retcode = 0
    try:
        parser = xml.sax.make_parser()
        parser.setContentHandler(tokenizer_handler)
        parser.parse(inpath)
    except xml.sax.SAXException:
        retcode = 1
    return retcode

def convert_test(in_paths):
    (inpath, outpath) = in_paths
    open(outpath, 'w').writelines(open(inpath).readlines())
    return 0

def main():
    usage_string = 'Usage: tokenizer.py --input <input path> --output <output path>'
    parser = optparse.OptionParser(usage=usage_string)
    parser.add_option('--input', dest='input', help='input path - directory or file')
    parser.add_option('--output', dest='output', help='output path - directory or file')
    parser.add_option('--output_encoding', dest='out_encoding', help='encoding of the output files', default='cp1251')
    parser.add_option('--jobs', dest='jobs_number', help='concurrent jobs number', default=1, type='int')

    (options, args) = parser.parse_args()
    config.generate_config(options)
    if not options.input or not options.output:
        parser.print_help()
        exit(0)
    inpath = os.path.abspath(options.input)
    outpath = os.path.abspath(options.output)

    if os.path.isdir(inpath):
        print 'Collecting tasks...'
        fs_walk.process_directory(inpath, outpath, task_list.add_task)
    else:
        task_list.TASKS.append(inpath, outpath)    
    jobs_number = config.CONFIG['jobs_number']
    print 'Starting processing...'
    if 1 < jobs_number:
        child_retcodes = task_list.execute_tasks(convert_and_log)
        retcode = sum([1 if code != 0 else 0 for code in child_retcodes])
    else:
        retcode = True
        for paths_pair in task_list.TASKS:
            retcode &= convert_and_log(paths_pair)
    return retcode

if __name__ == '__main__':
    retcode = main()
    print retcode
    exit(retcode)
