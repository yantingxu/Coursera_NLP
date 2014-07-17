#! /usr/bin/python

__author__ = "yantingxu"
__date__ = "2014-07-15"

import sys
import itertools
import operator
from collections import defaultdict
from count_freqs import Hmm
import numpy as np
from replace_rare_words import get_word_class

class HmmTagger:

    def __init__(self, count_file):
        self.hmm = self.__read_counts(count_file)
        self.emission_probs = self.__calc_emission_prob()
        self.trans_probs = self.__calc_trans_prob()
        self.vocab = self.__get_vocab()
        self.tags = self.__get_tags()

    def __read_counts(self, count_file):
        fp = open(count_file, 'r')
        hmm = Hmm(3)
        hmm.read_counts(fp)
        fp.close()
        return hmm

    def __calc_emission_prob(self):
        emission_counts = self.hmm.emission_counts
        tag_counts = defaultdict(int)
        for word_tag in emission_counts:
            tag_counts[word_tag[1]] += emission_counts[word_tag]

        emission_probs = defaultdict(dict)
        for word_tag in emission_counts:
            word, tag = word_tag
            word_tag_count = emission_counts[word_tag]
            tag_count = tag_counts[word_tag[1]]
            emission_probs[word][tag] = 1.0*word_tag_count/tag_count

        return emission_probs

    def __calc_trans_prob(self):
        bigram_counts = self.hmm.ngram_counts[1]
        trigram_counts = self.hmm.ngram_counts[2]
        trans_prob = {}
        for words, trigram_count in trigram_counts.iteritems():
            bigram_count = bigram_counts[words[:2]]
            trans_prob[words] = 1.0*trigram_count/bigram_count
            print words, trans_prob[words]
        return trans_prob

    def __get_vocab(self):
        unigram = self.hmm.ngram_counts[0]
        return unigram

    def __get_tags(self):
        tags = set([])
        emission_counts = self.hmm.emission_counts
        for word, tag in emission_counts:
            tags.add(tag)
        all_tags = ['*', 'STOP']
        all_tags.extend(tags)
        return all_tags


    def baseline(self, dev_file, result_file):
        input = open(dev_file, 'r')
        output = open(result_file, 'w')

        emission_probs = self.emission_probs
        for line in input:
            word = line.strip()
            if word:
                if word not in emission_probs:
                    word_class = get_word_class(word)
                    tag_probs = emission_probs[word_class]
                    #tag_probs = emission_probs['_RARE_']
                else:
                    tag_probs = emission_probs[word]
                max_tag = max(tag_probs.iteritems(), key = operator.itemgetter(1))[0]
                output.write(" ".join([word, max_tag]))
            output.write("\n")

        input.close()
        output.close()


    def viterbi(self, dev_file, result_file):
        emission_probs = self.emission_probs
        trans_probs = self.trans_probs
        tags = self.tags
        print "TAG_DEF: ", tags
        tag_size = len(tags)

        output = open(result_file, 'w')
        for sentence in self.__get_sentence(dev_file):
            l = len(sentence)
            pi = np.zeros((l+1, tag_size, tag_size))
            bp = np.zeros((l+1, tag_size, tag_size))

            # base case
            star_idx = self.tags.index('*')
            pi[0, star_idx, star_idx] = 1

            # recursive
            for i in xrange(1, l+1):
                word = sentence[i-1]
                candidate_w, candidate_u, candidate_v = self.__get_tag_range(i, tag_size)
                for u in candidate_u:
                    tag_u = self.tags[u]
                    for v in candidate_v:
                        tag_v = self.tags[v]
                        # emission prob of word_v
                        if word in emission_probs:
                            e = emission_probs[word]
                        else:
                            word_class = get_word_class(word)
                            e = emission_probs[word_class]
                        #e = emission_probs[word] if word in emission_probs else emission_probs['_RARE_']
                        e = e.get(tag_v, 0.0)
                        # pi[i, u, v] = max_w( pi[i-1, w, u]*q(v|w, u)*e(word|v) )
                        max_prob = -1
                        optim_choice = -1
                        for w in candidate_w:
                            tag_w = self.tags[w]
                            q = trans_probs[(tag_w, tag_u, tag_v)] if (tag_w, tag_u, tag_v) in trans_probs else 0.0
                            prob = pi[i-1, w, u] * q * e
                            if prob > max_prob:
                                max_prob = prob
                                optim_choice = w
                        pi[i, u, v] = max_prob
                        bp[i, u, v] = optim_choice

            # last step: u, v to STOP
            optim_sequence = [None]*l
            optim_prob = -1
            for u in xrange(2, tag_size):
                for v in xrange(2, tag_size):
                    tag_u = self.tags[u]
                    tag_v = self.tags[v]
                    prob = pi[l, u, v] * trans_probs.get((tag_u, tag_v, 'STOP'), 0.0)
                    if prob > optim_prob:
                        optim_prob = prob
                        optim_sequence[-2:] = [u, v]

            # backtrace the max_prob sequence
            #print sentence, len(sentence)
            for k in np.arange(l-2)[::-1]:
                optim_sequence[k] = bp[k+3, optim_sequence[k+1], optim_sequence[k+2]]
            #print optim_sequence, len(optim_sequence)
            optim_sequence = [self.tags[int(t)] for t in optim_sequence]
            #print optim_sequence, len(optim_sequence)

            # output
            for word, tag in itertools.izip(sentence, optim_sequence):
                #print word, tag
                output.write(word + " " + tag + "\n")
            output.write("\n")

        output.close()


    def __get_tag_range(self, i, tag_size):
        if i == 1:
            candidate_w = [0]
            candidate_u = [0]
            candidate_v = xrange(2, tag_size)
        elif i == 2:
            candidate_w = [0]
            candidate_u = xrange(2, tag_size)
            candidate_v = xrange(2, tag_size)
        else:
            candidate_w = xrange(2, tag_size)
            candidate_u = xrange(2, tag_size)
            candidate_v = xrange(2, tag_size)
        return candidate_w, candidate_u, candidate_v


    def __get_sentence(self, dev_file):
        cnt = 0
        input = open(dev_file, 'r')
        sentence = []
        for line in input:
            word = line.strip()
            if word:
                sentence.append(word)
            else:
                #sentence.append('STOP')
                yield sentence
                sentence = []
                # sentence counter
                cnt += 1
                print "Sentence Counter: ", cnt
        input.close()


if __name__ == '__main__':
    count_file = 'gene.counts.rare'
    count_file = 'gene.counts.class'
    hmm = HmmTagger(count_file)

    """
    dev_file = 'gene.dev'
    result_file = 'gene_dev.p1.out'
    dev_file = 'gene.test'
    result_file = 'gene_test.p1.out'
    hmm.baseline(dev_file, result_file)
    """

    """
    dev_file = 'gene.dev'
    result_file = 'gene_dev.p2.out'
    dev_file = 'gene.test'
    result_file = 'gene_test.p2.out'
    hmm.viterbi(dev_file, result_file)
    """

    dev_file = 'gene.dev'
    result_file = 'gene_dev.p3.out'
    dev_file = 'gene.test'
    result_file = 'gene_test.p3.out'
    hmm.viterbi(dev_file, result_file)

