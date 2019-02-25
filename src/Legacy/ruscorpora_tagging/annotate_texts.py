import StringIO
import codecs
import os
import multiprocessing
import traceback
import sys

from modules import fs_walk, config, task_list
import morpho_tagger
import tokenizer
import global_trash

def convert(paths):
    (inpath, outpath) = paths
    encoding = config.CONFIG['out_encoding']
    intermediate_buffer = codecs.getwriter(encoding)(StringIO.StringIO(),
                                                     'xmlcharrefreplace')
    outfile = codecs.getwriter(encoding)(file(outpath, 'wb'),
                                         'xmlcharrefreplace')

    retcode = None
    try:
        tokenization_retcode = tokenizer.convert((inpath, intermediate_buffer))
        print '"%s" tokenized - %s' %\
              (inpath, 'OK' if tokenization_retcode == 0 else 'FAIL')

        intermediate_buffer.seek(0)
        tagging_retcode = morpho_tagger.convert((intermediate_buffer, outfile))
        print '"%s" morpho tagged - %s' %\
              (inpath, 'OK' if tagging_retcode == 0 else 'FAIL')
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        retcode = inpath
    return retcode


def main():
    usage_string =\
        'Usage: annotate_texts.py ' +\
        '--input <input path> --output <output path> [options]'
    parser = morpho_tagger.configure_option_parser(usage_string)
    (options, args) = parser.parse_args()

    global_trash.MYSTEM_PATH = options.mystem

    config.generate_config(options)
    if not options.input or not options.output:
        parser.print_help()
        exit(0)

    inpath = os.path.abspath(options.input)
    outpath = os.path.abspath(options.output)

    retcode = 0
    jobs_number = config.CONFIG['jobs_number']
    if os.path.isdir(inpath):
        fs_walk.process_directory(inpath, outpath, task_list.add_task)
    else:
        task_list.add_task(inpath, outpath)
    if 1 < jobs_number:
        worker_pool =\
            multiprocessing.Pool(processes=jobs_number,
                                 initializer=morpho_tagger.initialize_lemmers,
                                 initargs=[options])
        return_codes = task_list.execute_tasks(convert, worker_pool)
        retcode = sum([1 if code is not None else 0 for code in return_codes])
    else:
        morpho_tagger.initialize_lemmers(options)
        retcode = True
        for paths_pair in task_list.TASKS:
            retcode &= convert(paths_pair) is not None
    return retcode


if __name__ == '__main__':
    retcode = main()
    exit(retcode)
