# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

import os
import time

SKIP_DIRS = ['.svn']

def process_directory(indir, outdir, process_function, indent = ""):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    curdirname = os.path.basename(indir)

    # print "%sEntering %s" % (indent, curdirname)
    starttime = time.time()
    nextindent  = indent + "  "

    filelist = os.listdir(indir)
    subdirs = [f for f in filelist if os.path.isdir(os.path.join(indir, f))]
    files = [f for f in filelist if not os.path.isdir(os.path.join(indir, f))]

    for subdir in subdirs:
        if subdir in SKIP_DIRS:
            continue
        inpath = os.path.join(indir, subdir)
        outpath = os.path.join(outdir, subdir)
        process_directory(inpath, outpath, process_function, nextindent)

    for f in files:
        inpath = os.path.join(indir, f)
        outpath = os.path.join(outdir, f)
        # print '%s%s' % (nextindent, os.path.basename(inpath))
        process_function(inpath, outpath)

    # print "%sTime: %.2f s" % (indent, time.time() - starttime)
