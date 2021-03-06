import argparse
import os
import codecs
import ntpath

from corpustools.corpus.io.csv import load_corpus_csv
from corpustools.corpus.io.binary import save_binary


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def main():

    #### Parse command-line arguments
    parser = argparse.ArgumentParser(description = \
             'Phonological CorpusTools: corpus object creation CL interface')
    parser.add_argument('csv_file_name', help='Name of input CSV file')
    parser.add_argument('-f', '--feature_file_name', default = '', type=str, help='Name of input feature file')
    parser.add_argument('-d', '--delimiter', default='\t', type=str, help='Character that delimits columns in the input file')
    parser.add_argument('-t', '--trans_delimiter', default='', type=str, help='Character that delimits segments in the input file')

    args = parser.parse_args()

    ####

    delimiter = codecs.getdecoder("unicode_escape")(args.delimiter)[0]

    try: # Full path specified
        filename, extension = os.path.splitext(args.csv_file_name)
        filename = path_leaf(filename)
        corpus = load_corpus_csv(args.csv_file_name, args.csv_file_name, 
                delimiter, args.trans_delimiter, args.feature_file_name)
        save_binary(corpus, filename+'.corpus')
    except FileNotFoundError:
        try: # Unix filepaths
            filename, extension = os.path.splitext(os.path.dirname(os.path.realpath(__file__))+'/'+args.csv_file_name)
            corpus = load_corpus_csv(args.csv_file_name, os.path.dirname(os.path.realpath(__file__))+'/'+args.csv_file_name, 
                    delimiter, args.trans_delimiter, os.path.dirname(os.path.realpath(__file__))+'/'+args.feature_file_name)
            save_binary(corpus, filename+'.corpus')
        except FileNotFoundError: # Windows filepaths
            filename, extension = os.path.splitext(os.path.dirname(os.path.realpath(__file__))+'\\'+args.csv_file_name)
            corpus = load_corpus_csv(args.csv_file_name, os.path.dirname(os.path.realpath(__file__))+'\\'+args.csv_file_name, 
                    delimiter, args.trans_delimiter, os.path.dirname(os.path.realpath(__file__))+'\\'+args.feature_file_name)
            save_binary(corpus, filename+'.corpus')


if __name__ == '__main__':
    main()