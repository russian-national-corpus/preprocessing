#!/usr/bin/env python
from optparse import OptionParser

import sys
import os.path
import xml.sax

import multiprocessing

VALID_FILE_EXTENSIONS = ['.xml', '.xhtml', '.tgt']
FILES_LIST = []


class ValidateHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        pass


def validate(inpath):
    handler = ValidateHandler()
    try:
        xml.sax.parse(inpath, handler)
    except xml.sax.SAXException as exc:
        print >> sys.stdout, inpath
        print >> sys.stderr, exc
        return 1
    return 0


def validate_directory(indir, in_handler):
    filelist = os.listdir(indir)
    subdirs = [f for f in filelist if os.path.isdir(os.path.join(indir, f))]
    files = [f for f in filelist if not os.path.isdir(os.path.join(indir, f))]
    for subdir in subdirs:
        if subdir == ".svn": continue
        inpath = os.path.join(indir, subdir)
        validate_directory(inpath, in_handler)
    for f in files:
        if os.path.splitext(f)[1] not in VALID_FILE_EXTENSIONS:
            continue
        inpath = os.path.join(indir, f)
        in_handler(inpath)


def main():
    parser = configure_option_parser()
    options, args = parser.parse_args()
    if len(args) < 1:
        print 'Usage: validate_xml.py <xml root> [--jobs <jobs number>]'
        exit(0)
    if os.path.isdir(args[0]):
        validate_directory(args[0],
                           in_handler=lambda path: FILES_LIST.append(path))
        pool = multiprocessing.Pool(processes=int(options.jobs_number))
        partial_results = pool.map(validate, FILES_LIST)
        errors_number = sum(partial_results)
    else:
        errors_number = validate(args[0])
    print errors_number, 'invalid document(s) found'
    exit(errors_number != 0)


def configure_option_parser():
    parser = OptionParser()
    parser.add_option('--jobs',
                      dest='jobs_number',
                      help='parallel jobs number',
                      default=1)
    return parser


if __name__ == '__main__':
    main()