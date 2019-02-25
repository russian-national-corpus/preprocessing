#coding: utf-8

import sys
import re
import os.path
import xml.sax
import xml.sax.saxutils
import time
import multiprocessing


# to reach 'general' module (TODO: this should be somehow avoided...)
sys.path.insert(0, '..')

import general.utils as my_utils
import filters

__doc__ = "Usage: %(name)s 'inpath' 'outpath'" % {'name': os.path.basename(sys.argv[0])}

marks_re = re.compile(ur"[,-:;/.!?]|&#8213;")

""" интерфейс объкта word
class Word:
    form
    ana
        gr
        sem
        lex
"""

INPUT_DIR = ''
OUTPUT_DIR = ''
FILTERS = []
JOBS_NUMBER = 1


def ClearForm(form):
    return form.replace(u"ё", u"е").replace("`", '').replace("'", '').replace(u'\u0301', '').replace(u'\u0300', '').lower()


class Word:
    def __init__(self):
        self.table = []
        self.__form = ""
        self.__ana = []

    def startElement(self, name, attrs):
        if name == 'ana':
            self.table.append(attrs.get('lex'))
            self.table.extend(attrs.get('gr', "").replace(",", " ").split())
            self.table.extend(attrs.get('sem', "").replace(",", " ").split())
            self.__ana.append(dict(attrs))
        # there can be some meaningless tags like <b> inside of <w> but we will ignore them

    def endElement(self, name):
        return

    def characters(self, content):
        self.__form += content

    def ignorableWhitespace(self, whitespace):
        return

    def prepare(self):
        self.table.append("'%s'" % ClearForm(self.__form))
        self.table = set(self.table)

    def Flush(self, handler):
        for ana in self.__ana:
            handler.startElement("ana", ana)
            handler.endElement("ana")
        handler.characters(self.__form)

    def applyResults(self, results):
        delete = set()
        for add in results:
            delete.update(add.keys())
        for d in delete:
            for i in range(len(self.__ana)):
                self.__ana[i].pop(d, None)
        for add in results:
            self.__ana.append(add)


class PhraseResolver(xml.sax.ContentHandler):
    """ Class for collecting data of a sentence,
    resolve semantics of words in sentence
    and passing resolved sentence to the next handler.
    """
    def __init__(self, filt):
        xml.sax.ContentHandler.__init__(self)
        self.__filters = filt
        self.__buffer = [] # objects buffer
        self.words = [] # references to objects in buffer which are words
        self.word = None # current word, can be None or instance of Word

    def MakeProcessing(self):
        for word in self.words:
            word.prepare()
        for filt in self.__filters:
            for i, res in enumerate(filt.getResults(self.words)):
                if len(res) > 0:
                    self.words[i].applyResults(res)

    def startElement(self, name, attrs):
        if name == 'w':
            assert not self.word, "Enclosed words are not allowed"
            self.__buffer.append(("startElement", name, attrs))
            self.word = Word()
        elif self.word:
            self.word.startElement(name, attrs)
        else:
            self.__buffer.append(('startElement', name, attrs))

    def endElement(self, name):
        if name == 'w':
            assert self.word
            self.__buffer.append(('word', len(self.words)))
            self.words.append(self.word)
            self.word = None
            self.__buffer.append(("endElement", name))
        elif self.word:
            self.word.endElement(name)
        else:
            self.__buffer.append(('endElement', name))

    def ignorableWhitespace(self, whitespace):
        if self.word:
            self.word.ignorableWhitespace(whitespace)
        else:
            self.__buffer.append(('ignorableWhitespace', whitespace))

    def characters(self, content):
        if self.word:
            self.word.characters(content)
        else:
            self.__buffer.append(('characters', content))

    def Flush(self, handler):
        for data in self.__buffer:
            if data[0] == "word":
                self.words[data[1]].Flush(handler)
            else:
                getattr(handler, data[0])(*data[1:])


class Resolver(xml.sax.ContentHandler):
    def __init__(self, filt, handler):
        xml.sax.ContentHandler.__init__(self)
        self.__filters = filt
        self.__handler = handler

        self.startDocument = self.__handler.startDocument
        self.endDocument = self.__handler.endDocument

        self.__currentHandler = self.__handler
        self.__phrase = False

    def startElement(self, name, attrs):
        self.__currentHandler.startElement(name, attrs)
        if name == 'se':
            assert not isinstance(self.__currentHandler, PhraseResolver), "Enclosed sentences are not allowed"
            self.__currentHandler = PhraseResolver(self.__filters)
            self.__phrase = True

    def endElement(self, name):
        if name == 'se':
            assert isinstance(self.__currentHandler, PhraseResolver)
            self.__currentHandler.MakeProcessing()
            self.__currentHandler.Flush(self.__handler)
            self.__currentHandler = self.__handler
            self.__phrase = False

        self.__currentHandler.endElement(name)

    def ignorableWhitespace(self, whitespace):
        self.__currentHandler.ignorableWhitespace(whitespace)

    def characters(self, content):
        if self.__phrase and not self.__currentHandler.word and marks_re.search(content):
            self.__currentHandler.MakeProcessing()
            self.__currentHandler.Flush(self.__handler)
            self.__currentHandler = PhraseResolver(self.__filters)
        self.__currentHandler.characters(content)


def GetFormater(filename):
    dir = os.path.dirname(filename)
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
    except OSError, e:
        # in the parallelized version,
        # some other worker may be trying to makedirs at the same exact time,
        # thus creating a race condition
        if e.errno != 17:
            raise
        pass

    output = open(filename, "wb")
    return xml.sax.saxutils.XMLGenerator(output, "windows-1251")


def process_file(in_path):
    out = GetFormater('%s%s' % (OUTPUT_DIR, in_path[len(INPUT_DIR):]))
    print("%s" % in_path)
    result = 1
    try:
        xml.sax.parse(open(in_path, "r"), Resolver(FILTERS, out))
        print("xml.sax.parse OK")
        result = 0
    except xml.sax.SAXParseException as sax_parse_exception:
        print("xml.sax.parse FAILED while processing file " + in_path)
        print(sax_parse_exception)

    return result


def main():
    if "-h" in sys.argv:
        print __doc__
    else:
        global INPUT_DIR, OUTPUT_DIR, FILTERS
        filtersNames = sys.argv[1].strip().split()

        for el in filtersNames:
            FILTERS.append(filters.Filter(filters.produceRules(el)))
        INPUT_DIR = os.path.abspath(sys.argv[2])
        OUTPUT_DIR = os.path.abspath(sys.argv[3])

        ttime = time.time()
        tasks = my_utils.getAllFiles(INPUT_DIR)
        print("DEBUG. sys.argv is %s" % ' '.join(sys.argv))
        print("DEBUG. INPUT_DIR is %s" % INPUT_DIR)
        print("DEBUG. OUTPUT_DIR is %s" % OUTPUT_DIR)
        pool = multiprocessing.Pool(JOBS_NUMBER)
        result = pool.map(process_file, tasks)

        print my_utils.str_time(time.time() - ttime)

        # for i, el in enumerate(FILTERS):
        #     print "\n", filtersNames[i]
        #     for key in ["phrases", "matches", "empty", "rules", "getRulesTime", "matchTime"]:
        #         print "%s : %s" % (key, el.stat[key])
        # returning errors number
        return sum(result)

if __name__ == '__main__':
    errors_number = main()
    sys.exit(errors_number != 0)
