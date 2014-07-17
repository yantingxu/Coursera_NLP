#! /usr/bin/python

__author__ = "yantingxu"
__date__ = "2014-07-17"

import json
from collections import defaultdict

class Parser:

    def __init__(self):
        self.unary_prob = defaultdict(dict)     # T => N
        self.binary_prob = defaultdict(dict)    # N, N => N
        self.nonterminal_counts = defaultdict(int)
        self.word_counts = defaultdict(int)

    def train(self, count_file):
        fp = open(count_file, 'r')
        for line in fp:
            parts = line.strip().split(" ")
            num = int(parts[0])
            if parts[1] == 'NONTERMINAL':
                self.nonterminal_counts[parts[2]] += num
            elif parts[1] == 'UNARYRULE':
                if parts[2] not in self.unary_prob[parts[3]]:
                    self.unary_prob[parts[3]][parts[2]] = 0
                self.unary_prob[parts[3]][parts[2]] += num
                self.word_counts[parts[3]] += num
            elif parts[1] == 'BINARYRULE':
                if (parts[3], parts[4]) not in self.binary_prob[parts[2]]:
                    self.binary_prob[(parts[3], parts[4])][parts[2]] = 0
                self.binary_prob[(parts[3], parts[4])][parts[2]] += num
            else:
                raise Excpetion("Invalid File Format!!")
        fp.close()

        for T in self.unary_prob:
            for N in self.unary_prob[T]:
                self.unary_prob[T][N] /= 1.0*self.nonterminal_counts[N]
        #print self.unary_prob

        for T in self.binary_prob:
            for N in self.binary_prob[T]:
                self.binary_prob[T][N] /= 1.0*self.nonterminal_counts[N]
        #print self.binary_prob

        print len([k for k in self.word_counts if self.word_counts[k] < 5])
        print len(self.word_counts)

    def parse(self, dev_file, result_file):
        input = open(dev_file, 'r')
        output = open(result_file, 'w')
        for line in input:
            words = line.strip().split(" ")
            tree, prob = self.__CYK_parse(words)
            output.write(json.dumps(tree))
            output.write("\n")
        input.close()
        output.close()

    def __CYK_parse(self, words):
        pi = {}     # (i, j), N/T => prob
        bp = {}     # (i, j), N/T => (k, ltag, rtag)

        words_with_rare = [w if w in self.word_counts else '_RARE_' for w in words]

        # base case
        for i, word in enumerate(words_with_rare):
            possible_tags = self.unary_prob[word]
            pi[(i, i)] = possible_tags.copy()

        # recursive
        word_count = len(words_with_rare)
        for l in xrange(1, word_count):
            for i in xrange(word_count-l):
                j = i + l
                pi[(i, j)] = {}
                bp[(i, j)] = {}
                for k in xrange(i, j):
                    left_tags = pi[(i, k)]
                    right_tags = pi[(k+1, j)]
                    for ltag, rtag in self.__combination(left_tags, right_tags):
                        parent_tags = self.binary_prob[(ltag, rtag)]
                        for ptag in parent_tags:
                            prob = left_tags[ltag] * right_tags[rtag] * parent_tags[ptag]
                            if ptag not in pi[(i, j)] or prob > pi[(i, j)][ptag]:
                                pi[(i, j)][ptag] = prob
                                bp[(i, j)][ptag] = (k, ltag, rtag)

        # reconstruct parse tree
        max_prob = pi[(0, word_count-1)]['SBARQ']
        optim_tree = self.__construct_tree(0, word_count-1, 'SBARQ', bp, words)
        return optim_tree, max_prob


    def __construct_tree(self, start, end, tag, bp, words):
        if start == end:
            return [tag, words[start]]
        else:
            k, ltag, rtag = bp[(start, end)][tag]
            left_tree = self.__construct_tree(start, k, ltag, bp, words)
            right_tree = self.__construct_tree(k+1, end, rtag, bp, words)
            return [tag, left_tree, right_tree]


    def __combination(self, left_tags, right_tags):
        for left_tag in left_tags:
            for right_tag in right_tags:
                if (left_tag, right_tag) in self.binary_prob:
                    yield (left_tag, right_tag)


if __name__ == '__main__':
    '''
    parser = Parser()
    parser.train('parse_train.counts.out')

    dev_file = 'parse_dev.dat'
    result_file = 'parse_dev.out'
    dev_file = 'parse_test.dat'
    result_file = 'parse_test.p2.out'
    parser.parse(dev_file, result_file)
    '''

    parser = Parser()
    parser.train('parse_train_vert.counts.out')

    dev_file = 'parse_dev.dat'
    result_file = 'parse_dev_vert.out'
    dev_file = 'parse_test.dat'
    result_file = 'parse_test.p3.out'
    parser.parse(dev_file, result_file)

