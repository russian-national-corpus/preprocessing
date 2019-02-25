import sys
import os
import re


def mark(in_stream):
    gr_re = re.compile('(gr=".+?")')
    marked_lines = [gr_re.sub('\g<1> disamb="yes"', line) for line in in_stream]
    return marked_lines


def process(in_text_root):
    for root, dirs, files in os.walk(in_text_root, followlinks=True):
        for filename in files:
            full_filename = os.path.join(root, filename)
            input_file = open(full_filename)
            processed_lines = mark(input_file)
            input_file.close()
            output_file = open(full_filename, 'w')
            for line in processed_lines:
                output_file.write(line)
            output_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: mark_everything_disamb.py <texts root>'
        exit()
    texts_root = sys.argv[1]
    process(texts_root)