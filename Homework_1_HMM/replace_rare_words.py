#! /usr/bin/python

__author__ = "yantingxu"
__date__ = "2014-07-15"

import re
from collections import defaultdict
from count_freqs import Hmm

def replace_rare(raw_data_file, raw_count_file, output_file, rare_counts = 5):
    # read in the raw counts from hmm
    fp = open(raw_count_file, 'r')
    hmm = Hmm(3)
    hmm.read_counts(fp)
    fp.close()

    # accumulate the word counts from emission_counts
    word_count = defaultdict(int)
    for word_tag in hmm.emission_counts:
        word_count[word_tag[0]] += hmm.emission_counts[word_tag]
    rare_words = set([word for word in word_count if word_count[word] < rare_counts])
    #print rare_words

    # replace rare words with _RARE_
    input = open(raw_data_file, 'r')
    output = open(output_file, 'w')
    for line in input:
        line = line.strip()
        if line:
            word, tag = line.split(" ")
            if word in rare_words:
                word_class = get_word_class(word)
                output.write(" ".join([word_class, tag]))
                #output.write(" ".join(['_RARE_', tag]))
            else:
                output.write(line)
        output.write("\n")
    input.close()
    output.close()


def get_rare_word_class(word):
    return '_RARE_'

def get_word_class(word):
    if re.search("^[A-Z]+$", word) is not None:
        return '_ALL_CAP_'
    elif re.search('\d', word) is not None:
        return '_NUM_'
    elif re.search('[A-Z]$', word) is not None:
        return '_LAST_CAP_'
    else:
        return '_RARE_'


if __name__ == '__main__':
    """
    raw_data_file = 'gene.train'
    raw_count_file = 'gene.counts'
    output_file = 'gene.train.rare'
    replace_rare(raw_data_file, raw_count_file, output_file)
    """

    raw_data_file = 'gene.train'
    raw_count_file = 'gene.counts'
    output_file = 'gene.train.class'
    replace_rare(raw_data_file, raw_count_file, output_file)

