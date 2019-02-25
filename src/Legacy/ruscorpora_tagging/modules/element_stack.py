# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

import common

TEXT_FORMATTING_TAGS = ['i', 'b', 'u', 'em']

class ElementStack(object):
    def __init__(self):
        self.storage = []
        self.content_caret = 0

    def __len__(self):
        return len(self.storage)

    # text enclosed by this tag will not appear as text node in all processing procedures
    def insertNoindexTag(self, in_tag, in_content):
        self.storage.append(('tag_open_close', in_tag, in_content))

    def startTag(self, tag, attrs):
        tag_attrs = ['%s="%s"' % (name, common.quoteattr(value)) for (name, value) in attrs.items()]
        if self.closeOpenTagSequence(tag, tag_attrs):
            self.storage.pop()
        else:
            self.storage.append(('tag_open', tag, ' '.join(tag_attrs)))

    def endTag(self, tag):
        self.storage.append(('tag_close', tag))

    # identifying </tag><tag> sequences
    def closeOpenTagSequence(self, in_tag, in_tag_attrs):
        DO_NOT_COLLAPSE_TAGS = ['se']

        if not len(in_tag_attrs) \
           and len(self.storage) \
           and in_tag not in DO_NOT_COLLAPSE_TAGS:
            last_element = self.storage[-1]
            return last_element[0] == 'tag_close' and last_element[1] == in_tag

    def addChars(self, content):
        content_begin = self.content_caret
        content_end = content_begin + len(content)
        self.content_caret = content_end

        if len(self.storage):
            last_element = self.storage[-1]
            if last_element[0] == 'content':
                self.storage.pop()
                new_content = last_element[1] + content
                content_begin = last_element[2]
                content_end = content_begin + len(new_content)
                self.storage.append(('content', new_content, content_begin, content_end))
                return
        self.storage.append(('content', content, content_begin, content_end))

    def join_empty_tags(self):
        index = 0
        while index < len(self.storage) - 1:
            (current_tag, next_tag) = self.storage[index: index + 2]
            if current_tag[0] == 'tag_open' \
                and next_tag[0] == 'tag_close' \
                and current_tag[1] == next_tag[1]:
                open_close_tag = ('tag_open_close', current_tag[1], current_tag[2])
                self.storage[index:index + 2] = \
                    [] if current_tag[1] in TEXT_FORMATTING_TAGS else [open_close_tag]
            index += 1

    def collapse(self):
        result = ''
        self.join_empty_tags()
        for element in self.storage:
            if element[0] == 'tag_open':
                result += '<%s%s%s>' % (element[1], ' ' * int(len(element[2]) != 0), element[2])
            elif element[0] == 'tag_open_close':
                if element[1] == 'noindex':
                    result += '<%s>%s</%s>' % (element[1], common.quotetext(element[2]), element[1])
                else:
                    result += '<%s%s%s/>' %\
                        (element[1],' ' * int(len(element[2]) != 0), element[2])
            elif element[0] == 'tag_close':
                result += '</%s>' % element[1]
            elif element[0] == 'content':
                result += common.quotetext(element[1])
        self.storage = []
        self.content_caret = 0
        return result

    def insert_tag(self, in_insert_index, in_content_position, in_tag):
        if self.storage[in_insert_index][0] == 'content':
            # inserting right into the element, with possible breaking it
            return self.insert_tag_into_content(in_insert_index,
                                                in_content_position,
                                                in_tag)
        else:
            # inserting after the element
            self.storage.insert(in_insert_index + 1, in_tag)
            return in_insert_index + 1

    # inserting a tag element into the storage at the place of content element,
    # with possible splitting
    def insert_tag_into_content(self, in_element_index, in_coordinate, in_tag):
        inserted_tag_index = in_element_index
        element = self.storage[in_element_index]
        text = element[1]
        local_tag_coordinate = in_coordinate - element[2]
        prefix = text[:local_tag_coordinate]
        suffix = text[local_tag_coordinate:]
        tags_sequence = []
        if len(prefix):
            inserted_tag_index += 1
            tags_sequence.append(('content', prefix, element[2], in_coordinate))
        tags_sequence.append(in_tag)
        if len(suffix):
            tags_sequence.append(('content', suffix, in_coordinate, element[3]))
        self.storage[in_element_index: in_element_index + 1] = tags_sequence
        return inserted_tag_index

    # finding not open/not closed tags in the segment (in_begin, in_end)
    # and fixing tag structure
    def fix_intersected_tags(self, in_begin, in_end):
        (result_begin_index, result_end_index) = (in_begin, in_end)
        local_tagstack = []
        for index in xrange(in_begin + 1, in_end):
            element = self.storage[index]
            if element[0] == 'tag_open':
                local_tagstack.append(element)
            elif element[0] == 'tag_close':
                if len(local_tagstack) \
                    and local_tagstack[-1][0] == 'tag_open' \
                    and local_tagstack[-1][1] == element[1]:
                    local_tagstack.pop()
                else:
                    local_tagstack.append(element)
        if not len(local_tagstack):
            return (result_begin_index, result_end_index)
        unclosed_open_tags = [tag for tag in local_tagstack if tag[0] == 'tag_open']
        unopened_close_tags = [tag for tag in local_tagstack if tag[0] == 'tag_close']
        open_tags_fix = []
        for tag in reversed(unclosed_open_tags):
            open_tags_fix.append(('tag_close', tag[1]))
        closed_tags_fix = []
        for tag in reversed(unopened_close_tags):
            closed_tags_fix.append(('tag_open', tag[1], ''))
        if len(unclosed_open_tags):
            self.storage[in_end:in_end + 1] += unclosed_open_tags
            self.storage[in_end - 1:in_end] += open_tags_fix
            result_end_index += len(open_tags_fix)
        if len(unopened_close_tags):
            self.storage[in_begin:in_begin + 1] += closed_tags_fix
            result_end_index += len(closed_tags_fix)
            self.storage[in_begin - 1:in_begin] += unopened_close_tags
            result_begin_index += len(unopened_close_tags)
        return (result_begin_index, result_end_index)
