# -*- Encoding: windows-1251 -*-
import sys
import csv
import cStringIO
import os
import os.path
import codecs

class UTF8Recoder:
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    def __init__(self, f, dialect=csv.excel, encoding="windows-1251", **kwds):
        #dialect.doublequote = False
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, delimiter=";", dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self
        
class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="windows-1251", **kwds):
        #dialect.doublequote = False
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, delimiter=";", dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            