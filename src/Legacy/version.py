# -*- Encoding: utf-8 -*-
import sys
import os
import os.path
import codecs
import xml.sax
import csv
import re

from csvreader import UnicodeReader, UnicodeWriter

field_modified = "mrevision"
field_created  = "crevision"

copyfrom_paths = dict()

def add_field(table, header, field):
    if field not in header:
        header.append(field)
        for key in table.iterkeys():
            table[key].append("0")

def addrev(revmap, table, rev_index):
    for (path, rev) in revmap.iteritems():
        table_key = os.path.normpath(path.lower().replace("\\", "/").rsplit(".", 1)[0])
        if table_key in table:
            if rev_index < len(table[table_key]):
                prev_rev = table[table_key][rev_index]
                table[table_key][rev_index] = rev if int(rev) > int(prev_rev) else prev_rev
            elif rev_index == len(table[table_key]):
                table[table_key].append(rev)
        else:
            print >>sys.stdout, '<WARN> Not in table: %s' % table_key.encode('utf-8')

def update_table(tablepath, svnlog, outpath, utf = False):
    table = {}
    header = []

    reader = UnicodeReader(file(tablepath, "rb"), csv.excel, "utf-8" if utf else "windows-1251")

    header = reader.next()
    for row in reader:
        key = os.path.normpath(row[0].lower().replace("\\", "/"))
        #if key.endswith(".xml") or key.endswith(".xhtml") or key.endswith(".html"):
        #    key = key.rsplit(".", 1)[0]
        table[key] = row
    add_field(table, header, field_modified)
    add_field(table, header, field_created)

    modified_index = header.index(field_modified)
    created_index = header.index(field_created)

    addrev(svnlog.created, table, created_index)
    addrev(svnlog.modified, table, modified_index)

    for v in table.itervalues():
        if len(v) <= modified_index or len(v) <= created_index:
            print >>sys.stderr, "\t".join(v).encode("utf-8")
            continue
        if int(v[modified_index]) < int(v[created_index]):
            v[modified_index] = v[created_index]

    if not os.path.exists(os.path.dirname(outpath)):
        os.makedirs(os.path.dirname(out))

    writer = UnicodeWriter(file(outpath, "wb"), csv.excel, "utf-8" if utf else "windows-1251")

    writer.writerow(header)
    writer.writerows(table.itervalues())


class XmlToMapHandler(xml.sax.handler.ContentHandler):
    def __init__(self, path=""):
        xml.sax.handler.ContentHandler.__init__(self)
        self.path = path
        self.modified = {}
        self.created = {}
        self.url = ""
        self.action = ""
        self.copy_from = ""
        self.collect = False
        self.revision = ""
        self.actions = []

    def startElement(self, name, attrs):
        if name == "logentry":
            self.revision = attrs.get("revision", "0")
        if name == "path":
            self.collect = True
            action = attrs.get("action", "")
            self.copy_from = attrs.get("copyfrom-path", "")
            if action == "M" or action == "A":
                self.action = action

    def updateDicts(self, in_source, in_destination):
        new_created = {name.replace(in_source, in_destination): revision \
                       for (name, revision) in self.created.iteritems()}
        self.created = new_created
        new_modified = {name.replace(in_source, in_destination): revision \
                        for (name, revision) in self.modified.iteritems()}
        self.modified = new_modified

    def endElement(self, name):
        if name == "logentry":
            self.applyActions()
        elif name == "path":
            # extracting file name
            path = self.url #[offset + len("texts/"):].lower()
            if self.action == "A":
                # this file was modified via 'svn del; svn add;'
                if path in copyfrom_paths:
                    self.copy_from = copyfrom_paths[path]
            if not self.copy_from:
                self.copy_from = ""
            action = {
                "type": self.action,
                "path": self.url,
                "copyfrom": self.copy_from,
                "revision": self.revision
            }
            if self.action in ['A', 'M']:
                self.actions.append(action)
            self.url = ""
            self.action = ""
            self.collect = False

    def applyActions(self):
        for action in sorted(self.actions,
                             key=lambda action: -len(re.findall("\/", action["copyfrom"]))):
            self.applyAction(action)
        self.actions = []

    def applyAction(self, in_action):
        if in_action["type"] == "M":
            path = in_action["path"]
            self.modified[path] = in_action["revision"]
            if path not in self.created:
                self.created[path] = in_action["revision"]
        elif in_action["type"] == "A":
            path = in_action["path"]
            copyfrom = in_action.get("copyfrom")
            revision = in_action["revision"]
            if copyfrom and path not in copyfrom_paths:
                self.updateDicts(copyfrom, path)
            if copyfrom:
                # file was renamed
                # if path != self.copy_from:
                if copyfrom in self.created:
                    self.created[path] = self.created[copyfrom]
                else:
                    self.created[path] = revision
                if path != copyfrom and copyfrom in self.created:
                    del self.created[copyfrom]
            else:
                self.created[path] = revision

    def characters(self, content):
        if self.collect:
            self.url += content


def to_map(path):
    mapHandler = XmlToMapHandler()
    xml.sax.parse(path, mapHandler)
    return mapHandler


def make_filename_metatable_correspondence(in_filename_map, in_corpus_name):
    corpus_texts_root = os.path.join(in_corpus_name, 'texts')
    result_map = {}
    for filename, revision in in_filename_map.iteritems():
        trimmed_filename = filename.lower().partition(corpus_texts_root)[2].lstrip('/')
        result_map[trimmed_filename] = revision
    return result_map


def main():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--tablein", dest="table", help="path to table")
    parser.add_option("--tableout", dest="out", help="new table outpath")
    parser.add_option("--svnlog", dest="svnlog", help="svn log in xml form")
    parser.add_option("--utf", action="store_true", default=False, help="enable utf decoding")
    parser.add_option("--copyfrom-paths", dest="copyfrom_paths", default=None, help="copyfrom svn paths: new \t old")

    (options, args) = parser.parse_args()

    tablein = os.path.abspath(options.table)
    tableout = os.path.abspath(options.out)
    svnlog = os.path.abspath(options.svnlog)

    if options.copyfrom_paths:
        f = open(os.path.abspath(options.copyfrom_paths))
        for l in f:
            new, old = l.rstrip().split("\t")
            copyfrom_paths[new] = old
        f.close()
    utf = options.utf

    error_msg = []

    if not os.path.exists(tablein):
        error_msg.append("table %s doesn't exist." % tablein)
    if not os.path.exists(svnlog):
        error_msg.append("svn log %s doesn't exist." % svnlog)

    if error_msg:
        print " ".join(error_msg)
        return

    svnlog_mapped = to_map(svnlog)
    corpus_name = os.path.splitext(os.path.basename(tablein))[0]

    svnlog_mapped.created = \
        make_filename_metatable_correspondence(svnlog_mapped.created, corpus_name)
    svnlog_mapped.modified = \
        make_filename_metatable_correspondence(svnlog_mapped.modified, corpus_name)
    update_table(tablein, svnlog_mapped, tableout, utf)


if __name__ == "__main__":
    csv.field_size_limit(sys.maxsize)
    main()
