# -*- Encoding: utf-8 -*-

# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

import sys
import os
import xml.sax
import codecs
import re
import time
from modules import common

import global_trash

ignored_columns = ["ex", "dc"]

feature_token_re = re.compile("^[a-z0-9_\-]+$")

bracketed_re = re.compile("^(.*)\(.*\)(.*)$")

merge_items = {
    u"r:concr" : u"concr",
    u"r:abstr" : u"abstr",
    u"t:stuff" : u"mat",
    u"pt:aggr" : u"coll",

    u"r:qual" : u"qual",

    u"r:pers" : u"pers",
    u"r:ref" : u"refl",
    u"r:rel" : u"rel",
    u"r:indet" : u"indef",
    u"r:neg" : u"neg",
    u"r:poss" : u"poss",
    u"r:dem" : u"dem",
    u"r:spec" : u"def"
}

merge_classes = {
    u"S" : set([u"concr", u"abstr", u"mat", u"coll"]),
    u"A" : set([u"qual", u"rel", u"poss"]),
    u"SPRO" : set([u"pers", u"refl"]),
    u"*PRO" : set([u"rel", u"indef", u"neg", u"poss", u"dem", u"def"])
}

dictionary = None

class SemanticEntry:
    def __init__ (self, lemma, category):
       self.lemma = lemma
       self.category = category
       self.primary_features = []
       self.secondary_features = []

class SemanticDictionary:
    def __init__ (self, filename):
        self.data = {}
        self.stats = {}

        headers = []
        if filename != None and len(filename) > 0:
            src = codecs.getreader("utf-8")(file(filename, "rb"))
            for line in src:
                tokens = line.strip().split(";")
                if not tokens: continue

                if tokens[0] == "Cat" and tokens[1] == "Lemma":
                   headers = [x.strip().lower() for x in tokens]
                   continue
                elif not headers:
                   raise ValueError, "No header before data line in file '" + filename + "'"

                if len(tokens) < 2:
                    print >>sys.stderr, "Trouble: bad line >", line
                    continue

                category = tokens[0].strip().lower().replace("-", "")
                lemma = tokens[1].strip().lower()
                key = category + ":" + lemma
                entry = self.data.get(key)
                if entry is None:
                    entry = SemanticEntry(lemma, category)
                    self.data[key] = entry

                primary = (len(tokens) > 2 and tokens[2] == "1")
                features = []

                for h, t in zip(headers, tokens)[3:]:
                   if h in ignored_columns:
                       continue

                   while True:
                       match = bracketed_re.match(t)
                       if not match: break
                       t = match.group(1) + match.group(2)

                   for s in t.split('/'):
                       if '$' in s or '?' in s or '*' in s:
                           continue
                       parts = [h]
                       for p in s.strip().lower().replace('@', '').split(':'):
                          if not feature_token_re.match(p): break
                          parts.append(p)

                       if len(parts) < 2: continue

                       s = ":".join(parts)
                       s = s.replace("ev:ev", "ev")
                       features.append(s)
                       # Stats
                       rec = self.stats.setdefault(s, [0, []])
                       rec[0] += 1
                       if len(rec[1]) < 20:
                          rec[1].append((category, lemma))

                if primary:
                    entry.primary_features.append(features)
                else:
                    entry.secondary_features.append(features)

    def get(self, in_entry, default=None):
        return self.data.get(in_entry, default)


def _semantic_filter(features, category, grams):
    result = []
    animated = (u'anim' in grams) # or u'од' in grams)
    qualitative = (u'brev' in grams or # u'кр' in grams or
                   u'comp' in grams or # u'срав' in grams or
                   u'supr' in grams) # or u'прев' in grams)
    for f in features:
        if not doMerge:
            if category == u'S':
                semantic_animated = (u't:hum' in f or
                                     u't:animal' in f or
                                     u't:persn' in f or
                                     u't:patrn' in f or
                                     u't:famn' in f)
                if animated != semantic_animated:
                    continue
            elif category == u'A':
                if qualitative and 'r:qual' not in f:
                    continue
        result.extend(f)
    return list(set(result))

class CorpusHandler(xml.sax.handler.ContentHandler):
    def __init__(self, outfile):
        xml.sax.handler.ContentHandler.__init__(self)
        self.out = outfile

    def close_pending_tag(self):
        if self.tag_pending:
            self.out.write(">")
            self.tag_pending = False

    def startDocument(self):
        self.out.write(u"<?xml version=\"1.0\" encoding=\"windows-1251\"?>\n")
        self.tag_pending = False

    def endDocument(self):
        self.close_pending_tag()

    def startElement(self, tag, attrs):
        self.close_pending_tag()
        self.out.write("<%s" % tag)

        for (attname, attvalue) in attrs.items():
            if attname != u"gr":
                self.out.write(" %s=\"%s\"" % (attname, common.quoteattr(attvalue)))

        if tag == "ana":
            lemma = attrs.get(u"lex")
            features = attrs.get(u"gr")
            if lemma and features:
                grams = features.replace(',', ' ').replace('=', ' ').replace('(', ' ').replace(')', ' ').replace('/', ' ').strip().split()
                category = grams[0].lower().replace("-", "")
                entry = dictionary.get(category + ":" + lemma.lower())
                if entry:
                    if not doMerge:
                        primary_semantics = _semantic_filter(entry.primary_features, category, grams)
                        if primary_semantics:
                            self.out.write(" sem=\"%s\"" % common.quoteattr(" ".join(
                                primary_semantics)))

                        secondary_semantics = _semantic_filter(entry.secondary_features, category, grams)
                        if secondary_semantics:
                            self.out.write(" sem2=\"%s\"" % common.quoteattr(" ".join(
                                secondary_semantics)))
                    else:
                        features = _semantic_filter(entry.primary_features + entry.secondary_features, category, grams)
                        addition = [merge_items.get(x) for x in features]
                        if category.lower() == u"s":
                            addition = merge_classes[u"S"].intersection(addition)
                        elif category.lower() == u"a":
                            addition = merge_classes[u"A"].intersection(addition)
                            if u"rel" in addition:
                                addition.discard(u"rel")
                                addition.add(u"reladj")
                            elif u"poss" in addition:
                                addition.discard(u"poss")
                                addition.add(u"possadj")
                        elif category.endswith(u"apro") or category.lower() == u"spro":
                            if category.lower() == u"spro":
                                addition = merge_classes[u"SPRO"].intersection(addition)
                            else:
                                addition = merge_classes[u"*PRO"].intersection(addition)
                            if lemma == u"где":
                                addition.discard(u"indef")
                        else:
                            addition = []
                        grams.extend(list(addition))
                self.out.write(" gr=\"%s\"" % common.quoteattr(" ".join(grams)))

        self.tag_pending = True

    def endElement(self, tag):
        if self.tag_pending:
            self.out.write("/>")
        else:
            self.out.write("</%s>" % tag)
        self.tag_pending = False

    def characters(self, content):
        if content:
            self.close_pending_tag()
            self.out.write(common.quotetext(content))

    def ignorableWhitespace(self, whitespace):
        self.characters(whitespace)

def convert_directory(indir, outdir, indent = ""):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    curdirname = os.path.basename(indir)

    print "%sEntering %s" % (indent, curdirname)
    starttime = time.time()
    nextindent  = indent + "    "

    filelist = os.listdir(indir)
    subdirs = [f for f in filelist if os.path.isdir(os.path.join(indir, f))]
    files = [f for f in filelist if not os.path.isdir(os.path.join(indir, f))]

    for subdir in subdirs:
        if subdir == ".svn": continue
        inpath = os.path.join(indir, subdir)
        outpath = os.path.join(outdir, subdir)
        convert_directory(inpath, outpath, nextindent)

    for f in files:
        inpath = os.path.join(indir, f)
        outpath = os.path.join(outdir, f)
        convert(inpath, outpath, nextindent)

    print "%sTime: %.2f s" % (indent, time.time() - starttime)

def convert(inpath, outpath, indent=""):
    print "%s%s" % (indent, os.path.basename(inpath)),
    out = codecs.getwriter("windows-1251")(file(outpath, "wb"), 'xmlcharrefreplace')
    try:
        xml.sax.parse(inpath, CorpusHandler(out))
        print " - OK"
    except xml.sax.SAXParseException:
        print " - FAILED"

doMerge = False

def main():
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option("--input", dest="input", help="input path")
    parser.add_option("--output", dest="output", help="output path")
    parser.add_option("--semdict", dest="dict", help="semantic dictionary path")
    parser.add_option("--merge", action="store_true", dest="merge", default=False, help="use full morphology")
    parser.add_option("--mystem", dest="mystem", help="mystem binary path")

    (options, args) = parser.parse_args()

    global_trash.MYSTEM_PATH = options.mystem

    doMerge = options.merge

    inpath = os.path.abspath(options.input)
    outpath = os.path.abspath(options.output)

    print "Reading the semantic dictionary...",
    global dictionary
    dictionary = SemanticDictionary(options.dict)
    print "done!"

    test = False
    if test:
        writer = codecs.getwriter("windows-1251")(sys.stdout, 'xmlcharrefreplace')
        atoms = dictionary.stats.keys()
        atoms.sort()
        for key in atoms:
            (freq, samples) = dictionary.stats[key]
            print >>writer, str(freq).rjust(6)+"\t"+key+"\t",
            for item in samples:
                print >>writer, ":".join(item),
            if freq > 20:
                print  >>writer, "...",
            print >>writer

        sys.exit(1)
    else:
        dictionary = dictionary.data

    if os.path.isdir(inpath):
        convert_directory(inpath, outpath)
    else:
        convert(inpath, outpath)

if __name__ == "__main__":
    main()
