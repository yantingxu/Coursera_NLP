#!/usr/bin/env python

__author__ = 'yantingxu'
__date__ = '2014-07-21'

import numpy as np
import itertools
import collections
from collections import defaultdict

class IBM:

    def __init__(self, en_file, fs_file):
        self.en_file = en_file
        self.fs_file = fs_file
        self.t = self.init_t_params()
        self.q = self.init_q_params()

    def init_q_params(self):
        align_prob = defaultdict(dict)
        en_fp = open(self.en_file, 'r')
        fs_fp = open(self.fs_file, 'r')
        for lidx, (en_line, fs_line) in enumerate(itertools.izip(en_fp, fs_fp)):
            en_line = en_line.strip()
            if not en_line:
                continue
            en_words = en_line.split(" ")
            l = len(en_words)
            en_words.insert(0, 'NULL')

            fs_line = fs_line.strip()
            if not fs_line:
                continue
            fs_words = fs_line.split(" ")
            m = len(fs_words)

            if (l, m) not in align_prob:
                align_prob[(l, m)] = {}
                for i in xrange(1, m+1):
                    align_prob[(l, m)][i] = dict((j, 1.0/(l+1)) for j in xrange(0, l+1))

        en_fp.close()
        fs_fp.close()
        return align_prob


    def init_t_params(self):
        trans_prob = defaultdict(dict)
        en_gen_set = defaultdict(set)
        en_fp = open(self.en_file, 'r')
        fs_fp = open(self.fs_file, 'r')

        for lidx, (en_line, fs_line) in enumerate(itertools.izip(en_fp, fs_fp)):
            if lidx % 1000 == 0:
                print "Line: ", lidx

            # word list for both langs
            en_line = en_line.strip()
            if not en_line:
                continue
            en_words = en_line.split(" ")

            fs_line = fs_line.strip()
            if not fs_line:
                continue
            fs_words = fs_line.split(" ")

            # for NULL word
            for fs_word in fs_words:
                trans_prob[fs_word]['NULL'] = 1
            en_gen_set['NULL'] = en_gen_set['NULL'].union(fs_words)

            # en_word
            for en_word, fs_word in itertools.product(en_words, fs_words):
                trans_prob[fs_word][en_word] = 1
                en_gen_set[en_word] = en_gen_set[en_word].union(fs_word)

        # t params
        for fs_word in trans_prob:
            trans_prob[fs_word] = dict((en_word, 1.0/len(en_gen_set[en_word])) for en_word in trans_prob[fs_word])

        en_fp.close()
        fs_fp.close()

        return trans_prob


    def run_em(self, iter_num = 5, is_IBM2 = True):
        trans_prob = self.t
        align_prob = self.q

        for iter_idx in xrange(iter_num):
            # for t param
            bigram_count = defaultdict(int)
            unigram_count = defaultdict(int)
            # for q param
            bialign_count = defaultdict(dict)
            unialign_count = defaultdict(dict)

            en_fp = open(self.en_file, 'r')
            fs_fp = open(self.fs_file, 'r')

            # E-Step
            for lidx, (en_line, fs_line) in enumerate(itertools.izip(en_fp, fs_fp)):
                if lidx % 100 == 0:
                    print lidx
                en_line = en_line.strip()
                if not en_line:
                    continue
                en_words = en_line.split(" ")
                l = len(en_words)
                en_words.insert(0, 'NULL')

                fs_line = fs_line.strip()
                if not fs_line:
                    continue
                fs_words = fs_line.split(" ")
                m = len(fs_words)

                for i in xrange(1, m+1):
                    fs_word = fs_words[i-1]
                    '''
                    if not is_IBM2:
                        numerator = sum(trans_prob[fs_word][en] for en in en_words)
                    else:
                        numerator = sum(trans_prob[fs_word][en_words[pos]]*align_prob[(l, m)][i][pos] for pos in xrange(0, l+1))
                    '''
                    numerator = sum(trans_prob[fs_word][en_words[pos]]*align_prob[(l, m)][i][pos] for pos in xrange(0, l+1))

                    for j in xrange(0, l+1):
                        en_word = en_words[j]
                        '''
                        if not is_IBM2:
                            delta = trans_prob[fs_word][en_word] / numerator
                        else:
                            delta = trans_prob[fs_word][en_word]*align_prob[(l, m)][i][j]/numerator
                        '''
                        delta = trans_prob[fs_word][en_word]*align_prob[(l, m)][i][j]/numerator

                        bigram_count[(fs_word, en_word)] += delta
                        unigram_count[en_word] += delta

                        if is_IBM2:
                            if i not in bialign_count[(l, m)]:
                                bialign_count[(l, m)][i] = {}
                            if j not in bialign_count[(l, m)][i]:
                                bialign_count[(l, m)][i][j] = 0
                            bialign_count[(l, m)][i][j] += delta
                            if i not in unialign_count[(l, m)]:
                                unialign_count[(l, m)][i] = 0
                            unialign_count[(l, m)][i] += delta

            # M-Step
            iter_trans_prob = defaultdict(dict)
            for fs_word, en_word in bigram_count:
                iter_trans_prob[fs_word][en_word] = bigram_count[(fs_word, en_word)] / unigram_count[en_word]
            trans_prob = iter_trans_prob

            if is_IBM2:
                iter_align_prob = defaultdict(dict)
                for pair_len in bialign_count:
                    for i in bialign_count[pair_len]:
                        numerator = unialign_count[pair_len][i]
                        iter_align_prob[pair_len][i] = dict((j, 1.0*bialign_count[pair_len][i][j]/numerator) for j in bialign_count[pair_len][i])
                align_prob = iter_align_prob

            en_fp.close()
            fs_fp.close()

        self.t = trans_prob
        self.q = align_prob


    def translate(self, dev_en_file, dev_fs_file, dev_out):
        trans_prob = self.t
        align_prob = self.q
        en_file = open(dev_en_file, 'r')
        fs_file = open(dev_fs_file, 'r')
        output_file = open(dev_out, 'w')
        for k, (en_line, fs_line) in enumerate(itertools.izip(en_file, fs_file)):
            en_words = en_line.strip().split(" ")
            l = len(en_words)
            en_words.insert(0, "NULL")
            fs_words = fs_line.strip().split(" ")
            m = len(fs_words)
            for i, fs_word in enumerate(fs_words):
                probs = [trans_prob[fs_word].get(en_words[pos], 0)*align_prob[(l, m)].get(i+1, {}).get(pos, 0) for pos in xrange(l+1)]
                j = np.argmax(probs)
                output_file.write("%d %d %d\n" % (k+1, j, i+1))
        output_file.close()
        en_file.close()
        fs_file.close()


if __name__ == '__main__':
    en_file = 'corpus.en'
    fs_file = 'corpus.es'
    print "Generating Init Params..."
    mt = IBM(en_file, fs_file)
    print "Running EM..."
    mt.run_em(iter_num = 5, is_IBM2 = False)
    #mt.run_em(iter_num = 5, is_IBM2 = True)

    dev_en_file = 'dev.en'
    dev_fs_file = 'dev.es'
    dev_out_file = 'dev.out'
    '''
    dev_en_file = 'test.en'
    dev_fs_file = 'test.es'
    dev_out_file = 'alignment_test.p1.out'
    '''
    print "Testing on DEV data..."
    mt.translate(dev_en_file, dev_fs_file, dev_out_file)
    print "DONE."


