# -*- Encoding: utf-8 -*-

import sys
import os
import os.path
import xml.sax
import codecs
import time
import multiprocessing

import meta

allowed_attributes = ['sem', 'sem2', 'flags', 'source_el', 'lex_el', 'disamb', 'transcr']
all_attributes = ['lex', 'gr'] + allowed_attributes

replace_colon = False
CORPUS_NAME = 'default'
WITHMONTHS = False
METATABLE = None
HEADER = []
TASKS = []
JOBS_NUMBER = 16

good_grams = [
    "S", "A", "NUM", "ANUM", "V", "ADV", "PRAEDIC", "PARENTH",
    "SPRO", "APRO", "PRAEDICPRO", "ADVPRO", "PR", "CONJ", "PART", "INTJ",
    "nom", "voc", "gen", "gen2", "dat", "acc", "acc2", "ins", "loc", "loc2", "adnum",
    "indic", "imper", "imper2", "inf", "partcp", "ger",
    "comp", "comp2",
    "supr", "plen", "brev",
    "praes", "fut", "praet",
    "tran", "intr",
    "sg", "pl",
    "1p", "2p", "3p",
    "famn", "persn", "patrn",
    "m", "f", "n", "mf",
    "act", "pass", "med",
    "anim", "inan",
    "pf", "ipf",
    "norm", "ciph", "anom", "distort", "bastard",
    "INIT", "abbr", "0",
    "dialflex", "dialstem", "dialsfx", "dialform", "dial_gen2", "dial_loc2",
    "lab", "vel", "proth_n", "proth_j", "var",
    "1decl", "2decl", "3decl", "hetrcl", "adjdecl",
    "1conj", "2conj", "hetrcj",
    "dialnum", "dialgend", "dialanim", "dialcase", "dialdecl", "dialcontract",
    "dialplen", "dialcomp", "dialaspect", "dialtense", "dialtrans", "dialrefl", "dialpostf",
    "NONLEX", "obsc"
]

for i in range(len(good_grams)):
    good_grams[i] = good_grams[i].lower()
good_grams = set(good_grams)
filter_gramms = True


def _quotetext(s):
    if not s:
        return ""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _quoteattr(s):
    return _quotetext(s)\
        .replace("'", '&#39;')\
        .replace('"', '&#34;')\
        .replace('\n', '&#xA;')\
        .replace('\r', '&#xD;')\
        .replace('\t', '&#x9;')


def _strattrs(attrs):
    l = [""]
    for (attname, attvalue) in attrs.items():
        l.append("%s=\"%s\"" % (attname, _quoteattr(attvalue)))
    return " ".join(l)


def load_metatable(inpath, utf=False):
    table = {}
    if os.path.exists(inpath):
        reader =\
            meta.UnicodeReader(file(inpath, "rb"),
                               encoding="utf-8" if utf else "windows-1251")
        # header
        global HEADER
        HEADER = reader.next()[1:]
        for row in reader:
            key = os.path.normpath(row[0].lower().replace("\\", "/"))
            if key.endswith(".xml") or key.endswith("xhtml"):
                key = key.rsplit(".", 1)[0]
            table[key] = row[1:]
        return table


class CounterHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self.wordcount = 0
        self.sentcount = 0
    def startElement(self, tag, attrs):
        if tag == u'w':
           self.wordcount += 1
        elif tag == u'se':
           self.sentcount += 1


class WordInfo:
    def __init__(self, attrs):
        self.text = u""
        self.analyses = []
        self.attrs = _strattrs(attrs) if attrs else ''

    def add_analysis(self, attrs):
        flags = attrs.get(u'flags')
        if flags:
            for ana in self.analyses:
                ana[u'flags'] = flags
            return

        lexvalue = attrs.get(u'lex')
        if lexvalue: # doesn't nessecary in clean corpus because there we should have non empty attr lex
            lexvalue = \
                lexvalue\
                    .replace(u'@', u'')\
                    .replace(u'?', u'')\
                    .replace(u'!', u'')\
                    .replace(u'#', u'')\
                    .strip()

        grvalue = attrs.get(u'gr')
        if grvalue:
            grvalue =\
                grvalue\
                    .replace(u'-', u'')\
                    .replace(u',', u' ')\
                    .replace(u'=', u' ')\
                    .replace(u'(', u' ')\
                    .replace(u')', u' ')\
                    .replace(u'/', u' ')\
                    .strip()\
                    .split()
            if filter_gramms:
                grvalue = [g for g in grvalue if g.lower() in good_grams]
            grvalue = u",".join(grvalue)

        new_attrs = {u'lex': lexvalue, u'gr': grvalue}
        for attr_name in allowed_attributes:
          attr_value = attrs.get(attr_name)
          if attr_value:
            new_attrs[attr_name] = attr_value
        self.analyses.append(new_attrs)

    def write(self, out):
        global errwriter
        clean_text = \
            self.text\
                .replace(u'`', u'')\
                .replace(u'\u0300', u'')\
                .replace(u'\u0301', u'')\
                .replace(u'*', u'')\
                .replace(u'?', u'')\
                .replace(u'!', u'')\
                .strip()

        if not clean_text:
            out.write(_quotetext(self.text))
            return  # skip empty words

        out.write(u"<w%s>" % self.attrs)
        has_full_analysis = False

        for ana in self.analyses:
            if ana[u'lex'] and ana[u'gr']:
                has_full_analysis = True
                break

        for ana in self.analyses:
            if not ana[u'lex']:
               if has_full_analysis:
                   continue
               ana[u'lex'] = clean_text
               print >>errwriter, "Fixed empty lemma:", clean_text

            if not ana[u'gr']:
               if has_full_analysis:
                   continue
               ana[u'gr'] = u'NONLEX'
               print >>errwriter, "Fixed empty analysis for lemma", ana[u'lex']
            out.write(u'<ana')

            for attname in all_attributes:
                attvalue = ana.get(attname)
                if attvalue:
                    out.write(u" %s=\"%s\"" % (attname, _quoteattr(attvalue)))
            out.write(u'/>')

        out.write(_quotetext(self.text))
        out.write(u"</w>")


class CorpusHandler(xml.sax.handler.ContentHandler):
    def __init__(self, in_metatable, infile="", outfile=None, wc=0, sc=0):
        xml.sax.handler.ContentHandler.__init__(self)
        self.path = infile.rsplit(".", 1)[0].lower()
        self.out = None
        self.outfile = outfile
        self.skip = 0
        self.current_word = None
        self.textnode = u""
        self.quotecount = 0
        self.wordcount = wc
        self.sentcount = sc
        self.table = in_metatable

    def writeHeader(self, full):
        if full:
            self.out.write("<head>\n")
            self.out.write("<title>Title</title>\n")

            row = self.table.get(self.path, ("", []))

            for i in range(len(row)):
                if len(row[i]) > 0 and i < len(HEADER):
                    name = HEADER[i]
                    record = row[i]
                    if replace_colon:
                        record = record.replace(" : ", "|")
                    if name == "tagging" and record == "":
                        record = "none"
                    if name == "sphere" and not u"художественная" in record: #
                        record += u"|нехудожественная"
                    doc_attr_names = [
                        "sex",
                        "author",
                        "sphere",
                        "type",
                        "genre_fi",
                        "topic"
                    ]
                    if name in doc_attr_names:
                        self.out.write('<meta name="gr%s" content="%s"/>\n' % (_quoteattr(name), _quoteattr(record).replace("|"," | ").replace("  |  ", " | ")))
                    grcreated = []
                    if name in meta.dates_columns:
                        for date in meta.parseDate(record):
                            if len(date) == 2:
                                for year in range(int(date[0].split(".")[0]), int(date[1].split(".")[0]) + 1):
                                    self.out.write('<meta name="%s" content="%s"/>\n' % (_quoteattr(name), year))
                            else: # len == 1
                                self.out.write('<meta name="%s" content="%s"/>\n' % (_quoteattr(name), date[0]))
                            if name == "created":
                                if WITHMONTHS:
                                    date_atomics = []
                                    # extracting years and months, joining
                                    grcreated.append("-".join(['.'.join(d.split('.')[:2]) for d in date]))
                                else:
                                    # extracting only years, joining
                                    grcreated.append("-".join([d.split(".")[0] for d in date]))
                        if name == "created":
                            self.out.write('<meta name="%s" content="%s"/>\n' % (_quoteattr("grcreated"), " | ".join(grcreated)))
                    else:
                        for value in record.split("|"):
                            self.out.write('<meta name="%s" content="%s"/>\n' % (_quoteattr(name), _quoteattr(value)))

        self.out.write(u"<meta name=\"words\" content=\"%s\"/>\n" % self.wordcount)
        self.out.write(u"<meta name=\"sentences\" content=\"%s\"/>\n" % self.sentcount)

        if full:
            self.out.write("</head>\n")

    def flush_text(self):
        if not self.textnode:
            return

        text = []
        quotecount = self.quotecount
        for i in range(len(self.textnode)):
           c = self.textnode[i]
           if c in u")]}\u00BB\u2019\u201D,?!:;":
               text.append(c)
               text.append(u' ')
           elif c in u"([{\u00AB\u2018\u201C":
               text.append(' ')
               text.append(c)
           elif c == u'\"':
               quotecount += 1
               if quotecount % 2 == 0:
                   text.append(c);
                   text.append(u' ')
               else:
                   text.append(u' ')
                   text.append(c);
           else:
                text.append(c);
        self.textnode = "".join(text)

        text = u""
        quotecount = self.quotecount
        for i in range(len(self.textnode)):
            c = self.textnode[i]
            if c in u")]}\u00BB\u2019\u201D.,?!:;":
                text = text.rstrip()
            elif c == u'\"':
                quotecount += 1
                if quotecount % 2 == 0:
                    text = text.rstrip()
            text += c
        self.textnode = text

        text = u""
        quotecount = self.quotecount
        for i in range(len(self.textnode), 0, -1):
            c = self.textnode[i-1]
            if c in u"([{\u00AB\u2018\u201C":
                text = text.lstrip()
            elif c == u'\"':
                quotecount += 1
                if quotecount % 2 == 1:
                    text = text.lstrip()
            text = c + text
        self.quotecount = quotecount

        tmp = text
        text = ""
        while len(tmp) != len(text):
            text = tmp
            tmp = text.replace("  ", " ")
        text = tmp

        self.out.write(_quotetext(text))
        self.textnode = u""

    def startDocument(self):
        if self.outfile != None:
            self.out = codecs.getwriter("windows-1251")(file(self.outfile, "wb"), 'xmlcharrefreplace')
        self.out.write(u"<?xml version=\"1.0\" encoding=\"windows-1251\"?>\n")

    def endDocument(self):
        self.flush_text()

    def startElement(self, tag, attrs):
        if tag == u"meta":
            pass

        if self.skip > 0:
            self.skip += 1
            return
        if tag == u"head" and self.path in self.table:
            self.skip = 1
            self.writeHeader(True)
            return

        if self.current_word:
            if tag == u'ana':
                self.current_word.add_analysis(attrs)
                return
            else:
                # raise xml.sax.SAXException, "Invalid tag '%s' inside word descriptor" % tag
                return

        self.flush_text()
        if tag == u'w':
            self.current_word = WordInfo(attrs)
            return

        if tag in [u'p', u'body', u'table', u'td', u'th']:
           self.quotecount = 0

        self.out.write(u"<%s" % tag)
        for (attname, attvalue) in attrs.items():
            if attvalue:
                self.out.write(u" %s=\"%s\"" % (attname, _quoteattr(attvalue)))
        self.out.write(u">")

    def endElement(self, tag):
        if self.skip > 0:
            self.skip -= 1
            return

        if self.current_word:
            if tag == u"w":
                self.current_word.write(self.out)
                self.current_word = None
            return

        self.flush_text()
        if tag == u"head":
            self.writeHeader(False)
        self.out.write(u"</%s>" % tag)

    def characters(self, content):
        if self.skip > 0:
            return

        if self.current_word:
            self.current_word.text += content
            return

        if content:
            self.textnode += content

    def ignorableWhitespace(self, whitespace):
        self.characters(whitespace)


def convert_directory(indir, outdir, root = "", indent = ""):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    curdirname = os.path.basename(indir)

    print "%sEntering %s" % (indent, curdirname)
    starttime = time.time()
    nextindent  = indent + "    "

    filelist = os.listdir(indir)
    subdirs = [f for f in filelist if os.path.isdir(os.path.join(indir, f))]
    if ".svn" in subdirs:
        subdirs.remove(".svn")
    files = [f for f in filelist if not os.path.isdir(os.path.join(indir, f))]

    subdircount = 0
    for subdir in subdirs:
        subdircount += 1
        inpath = os.path.join(indir, subdir)
        outpath = os.path.join(outdir, subdir)
        convert_directory(inpath, outpath, root, nextindent)

    global TASKS
    for f in files:
        inpath = os.path.join(indir, f)
        # changing all extensions to xml
        outpath = os.path.join(outdir, f.rsplit(".", 1)[0] + ".xml")
        TASKS.append((inpath, outpath, root, nextindent))
    # print "%sTime: %.2f s" % (indent, time.time() - starttime)


def convert(in_options):
    (inpath, outpath, root, indent) = in_options
    retcode = 0
    global errwriter
    print "%s%s" % (indent, os.path.basename(inpath)),
    counthandler = CounterHandler()
    try:
        xml.sax.parse(inpath, counthandler)
        corpusHandler = CorpusHandler(METATABLE,
                                      inpath[len(root) + 1:],
                                      outpath,
                                      counthandler.wordcount,
                                      counthandler.sentcount)
        if corpusHandler.path in corpusHandler.table:
            xml.sax.parse(inpath, corpusHandler)
            print " - OK"
        else:
            print " - NOT IN TABLE"
    except xml.sax.SAXParseException:
        print " - FAILED"
        retcode = 1
    except AssertionError:
        print >>errwriter, inpath
        retcode = 1
    return retcode


def main():
    global dictionary
    global errwriter
    global filter_gramms

    errwriter = codecs.getwriter('utf-8')(sys.stderr)

    global WITHMONTHS
    WITHMONTHS = '-withmonths' in sys.argv

    filter_gramms = "-f" in sys.argv

    global replace_colon
    replace_colon = "--colon" in sys.argv

    # assuming that if 4th argument doesn't start with '-', it's not some arbitrary option but
    # corpus name
    if len(sys.argv) > 4 and not sys.argv[4].startswith('-'):
        global CORPUS_NAME
        CORPUS_NAME = sys.argv[4]

    global METATABLE
    METATABLE = load_metatable(sys.argv[1], "-utf" in sys.argv)

    convert_directory(os.path.abspath(sys.argv[2]),
                      os.path.abspath(sys.argv[3]),
                      os.path.abspath(sys.argv[2]))
    pool = multiprocessing.Pool(JOBS_NUMBER)
    return_codes = pool.map(convert, TASKS)
    errors_number = sum(return_codes)
    return errors_number


if __name__ == "__main__":
    errors_number = main()
    exit(errors_number != 0)
