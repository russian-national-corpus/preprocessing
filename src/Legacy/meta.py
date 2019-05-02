# -*- Encoding: utf-8 -*-
import sys
import codecs
import xml.sax
import re
import os
import time

from csvreader import *

ERRORS_NUMBER = 0

def _quotetext(s):
    if not s:
        return ""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _quoteattr(s):
    return _quotetext(s).replace("'", '&#39;').replace('"', '&#34;').replace('\n', '&#xA;').replace('\r', '&#xD;').replace('\t', '&#x9;')

def normalizePath(path):
    normpath = os.path.normpath(path.lower().replace("\\", "/")) #.replace(" ", "_"))
    if normpath.endswith(".xml") or normpath.endswith(".xhtml"):
        return normpath.rsplit(".", 1)[0]
    else:
        return normpath

dates_columns = ["created", "birthday", "publ_year", "date"]

def parseDate(date):
    y = []
    replace_mapping = [('\s*,\s*', '|'), (u'\u2013', '-'), ('\s*\-\s*', '-')]
    # applying replace actions sequentially
    for pair in replace_mapping:
        date = re.sub(pair[0], pair[1], date)
    for e in date.split('|'):# date.replace(",", "|").replace(u"\u2013","-").split("|"):
        if len(e) > 0:
            q = []
            for qq in e.split("-"):
                year = None
                month = None
                day = None
                question = False
                d = qq.split(".")
                if len(d) == 1:
                    if len(d[0]) == 4:
                        year = d[0]
                    elif len(d[0]) == 6:
                        year = d[0][:4]
                        month = int(d[0][4:])
                        day = 0
                    else:
                        print "parseDate-1:", date
                        raise AssertionError
                elif len(d) == 2:
                    if len(d[0]) == 4 and len(d[1]) == 2:
                        year = d[0]
                        month = d[1]
                    else:
                        print "parseDate-2:", date
                        raise AssertionError
                elif len(d) == 3:
                    if len(d[0]) == 4 and len(d[1]) <= 2 and len(d[2]) <= 2:
                        year = d[0]
                        month = int(d[1])
                        day = int(d[2])
                    elif len(d[0]) <= 2 and len(d[1]) <= 2 and len(d[2]) == 4:
                        year = d[2]
                        month = int(d[1])
                        day = int(d[0])
                    else:
                        print "parseDate-3:", date
                        raise AssertionError
                else:
                    print "parseDate-4:", date
                    raise AssertionError

                if year != None:
                    if year.find("??") > 0:
                        year = int(year.replace("??", "00"))
                        q.append("%s" % year)
                        q.append("%s" % (year + 99))
                    elif month != None and day != None:
                        q.append("%s.%02d.%02d" % (year, month, day))
                    else:
                        q.append("%s" % year)

            q.sort()
            if len(q) > 1:
                y.append([min(q), max(q)])
            elif len(q) > 0:
                y.append([q[0]])
            else:
                print "parseDate-5:", date
                raise AssertionError
    return y

class HeaderHandler(xml.sax.handler.ContentHandler):
    def __init__(self, infile="", outPath=None):
        self.skipp = False
        if outPath != None:
            self.out = codecs.getwriter("windows-1251")(file(outPath, "wb"), 'xmlcharrefreplace')

    def startDocument(self):
        self.out.write("<?xml version=\"1.0\" encoding=\"windows-1251\"?>\n")

    def startElement(self, name, attrs):
        if name == "head":
            self.out.write("<%s>" % name)
            self.skipp = True
        elif not self.skipp:
            self.out.write("<%s" % name)
            for attr in attrs.getQNames():
                self.out.write(' %s="%s"' % (attr, _quoteattr(attrs.getValueByQName(attr))))
            self.out.write(">")

    def endElement(self, name):
        if name == "head":
            self.out.write("</%s>" % name)
            self.skipp = False
        elif not self.skipp:
            self.out.write("</%s>" % (name))

    def characters(self, content):
        if not self.skipp:
            self.out.write(_quotetext(content))

    def ignorableWhitespace(self, whitespace):
        self.out.write(whitespace)

class CheckHandler(xml.sax.handler.ContentHandler):
    def __init__(self, infile="", outfile=None):
        self.err = False
        self.rawpath = infile
        self.path = normalizePath(infile)
        self.latin = re.compile(ur"^[A-Za-z\-\+\._0-9/\\]*$")
        self.out = codecs.getwriter("windows-1251")(sys.stderr, 'xmlcharrefreplace')

    def load(self, inp):
        errors_number = 0
        self.table = {}
        self.header = []
        try:
            f = UnicodeReader(file(inp, "rb"), csv.excel, "utf-8" if utf else "windows-1251")
            header = f.next()
            fields_number = len(header)
            self.header = header[2:]

            i = 0
            for x in f:
                i += 1
                if len(x) > 1:
                    path = normalizePath(x[0])
                    if not self.latin.match(path):
                        print >>self.out, "Bad name:", path.encode("utf-8")
                        errors_number += 1
                        continue
                    title = x[1]
                    if not self.latin.match(path):
                        self.out.write("Nonlatin filename at the table: %s\n" % path)
                    if path in self.table:
                        self.out.write("Duplicate table row: %s\n" % path)
                    self.table[path] = (title, x[2:])
                if len(x) != fields_number:
                    line_fields_number = len(x)
                    line_number = i + 1
                    err = \
                        '[ERR] Variable fields number' \
                        ' (header: %d, line #%d: %d)' %\
                        (fields_number, line_number, line_fields_number)
                    print >>self.out, err
                    errors_number += 1
        except:
            errors_number += 1
            print sys.exc_info()
            self.table = {}
            self.header = []
        global ERRORS_NUMBER
        ERRORS_NUMBER += errors_number
        return errors_number

    def errors(self):
        for path in self.table:
            self.out.write("Bad metatable path: %s\n" % path)

    def startDocument(self):
        if self.path in self.table:
            del self.table[self.path]
        else:
            self.out.write("Not in metatable: %s.\n" % self.rawpath)
            self.err = True
        if not self.latin.match(self.path):
            self.out.write("Nonlatin document name: %s\n" % self.path)
            self.err = True
            raise AssertionError

def convert_directory(indir, outdir, handler, root = "", indent = ""):
    if indir.endswith("multi"):
      return

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
        convert_directory(inpath, outpath, handler, root, nextindent)

    for f in files:
        inpath = os.path.join(indir, f)
        outpath = os.path.join(outdir, f)
        convert(inpath, outpath, handler, root, nextindent)

    print "%sTime: %.2f s" % (indent, time.time() - starttime)

def convert(inpath, outpath, handler, root = "", indent=""):
    global ERRORS_NUMBER
    print "%s%s" % (indent, os.path.basename(inpath)),
    try:
        handler.__init__(inpath[len(root) + 1:], outpath)
        xml.sax.parse(inpath, handler)
        print " - OK"
    except xml.sax.SAXParseException, e:
        ERRORS_NUMBER += 1
        print " - FAILED"
        codecs.getwriter("windows-1251")(sys.stderr, "xmlcharrefreplace").write("%s - %s\n" % (inpath, e.getMessage()))
    except AssertionError:
        if handler.err:
            ERRORS_NUMBER += 1
            print " - ERROR"
        else:
            print " - OK"

def convert_table(inpath, outpath, reverseAuthor = False):
    global ERRORS_NUMBER
    table = []

    reader = UnicodeReader(file(inpath, "rb"), csv.excel, "utf-8" if utf else "windows-1251")
    writer = UnicodeWriter(file(outpath, "wb"), csv.excel, "utf-8" if utf else "windows-1251")

    header = reader.next()
    header[0] = "path"
    writer.writerow(header)

    dates = []
    for date in dates_columns:
        if date in header:
            dates.append(header.index(date))

    for row in reader:
        if len(row) > 1:
            row[0] = normalizePath(row[0])

            if reverseAuthor:
                rau = []
                for au in row[header.index("author")].split("|"):
                    auu = au.split()
                    if len(auu) > 1:
                        auu = " ".join(auu[1:] + [auu[0]]) # "Pushkin A. S." -> "A. S. Pushkin"
                        rau.append(auu)
                row[header.index("author")] = "|".join(rau)

            for date_index in dates:
                date_list = []
                row[date_index] = row[date_index].replace(" ", "").replace(",", "|").replace("||", "-").replace("(?)", "")
                try:
                    for date in parseDate(row[date_index]):
                        if len(date) in [1, 2]:
                            date_list.append("-".join(date))
                except:
                    ERRORS_NUMBER += 1
                    print "Wrong data: %s" % ((row[0], header[date_index], row[date_index]),)
                row[date_index] = "|".join(date_list)
            try:
                writer.writerow(row)
            except csv.Error as error:
                ERRORS_NUMBER += 1
                print "Error in row %s : %s" % (";".join(row).encode("utf-8"), error)

def delete_intersection(path0, path1):
    filelist0 = os.listdir(path0)
    filelist1 = os.listdir(path1)

    diff = set(filelist0).intersection(set(filelist1))
    diff = list(diff)
    diff.sort()
    for el in diff:
        print "unlink %s" % el
        os.unlink(os.path.join(path1, el))

def delete_rows(to_delete, inpath, outpath):
    delete = set([el.strip().split(";")[0].replace("/", "\\") for el in codecs.getreader("windows-1251")(file(to_delete, "rb"), 'xmlcharrefreplace').readlines()[1:]])
    f = codecs.getreader("windows-1251")(file(inpath, "rb"), 'xmlcharrefreplace')
    ff = codecs.getwriter("windows-1251")(file(outpath, "wb"), 'xmlcharrefreplace')
    for el in f:
        if not el.strip().split(";")[0].replace("/", "\\") in delete:
            ff.write(el)
        else:
            print el.strip().split(";")[0].replace("/", "\\")

def main():
    global utf
    utf = True if "-utf" in sys.argv else False

    if "-header" in sys.argv:
        convert_directory(sys.argv[1], sys.argv[2], HeaderHandler())
    elif "-check" in sys.argv:
        handler = CheckHandler()
        meta_errors_number = handler.load(sys.argv[1])
        if meta_errors_number:
            exit('Metatable check failed: ' + sys.argv[1] + ' contains ' + str(meta_errors_number) + ' errors')
        if sys.argv[2]:
            convert_directory(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[2]), handler, os.path.abspath(sys.argv[2]))
        handler.errors()
    elif "-convert" in sys.argv:
        convert_table(sys.argv[1], sys.argv[2], "-ra" in sys.argv)
    elif "-intersection" in sys.argv:
        delete_intersection(sys.argv[1], sys.argv[2])
    elif "-del_rows" in sys.argv:
        delete_rows(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    csv.field_size_limit(sys.maxsize)
    if len(sys.argv) < 3:
        usage_string = 'Usage:'
        usage_string +='\nchecking metatable and texts correspondence: meta.py <metatable.csv> <texts root> -check [-utf]'
        usage_string += '\nconverting metatable for indexing: meta.py <metatable.csv> <output_table.csv> -convert [-utf]'
        print usage_string
        exit(0)
    main()
    if ERRORS_NUMBER:
        exit('Errors during the work')
