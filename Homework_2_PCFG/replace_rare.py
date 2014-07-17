#! /usr/bin/python

__author__ = "yantingxu"
__date__ = "2014-07-17"

import json
from collections import defaultdict

class ReplaceRARE:

    def __init__(self, count_file):
        self.__stat = defaultdict(int)
        self.__get_stat_counts(count_file)
        print len([k for k in self.__stat if self.__stat[k] < 5])
        print len(self.__stat)
        print self.__stat['Africa']
        print self.__stat['African']

    def __get_stat_counts(self, count_file):
        fp = open(count_file, 'r')
        for line in fp:
            parts = line.strip().split(" ")
            if parts[1] == 'UNARYRULE':
                word = parts[-1]
                self.__stat[word] += int(parts[0])
        fp.close()

    def replace_rare(self, input_file, output_file):
        input = open(input_file, 'r')
        output = open(output_file, 'w')
        for line in input:
            tree = json.loads(line)
            self.__tranverse(tree)
            output.write(json.dumps(tree))
            output.write("\n")
        input.close()
        output.close()

    def __tranverse(self, tree):
        if len(tree) == 3:
            self.__tranverse(tree[1])
            self.__tranverse(tree[2])
        else:
            word = tree[1]
            if self.__stat[word] < 5:
                tree[1] = '_RARE_'

if __name__ == '__main__':
    '''
    count_file = 'cfg.counts'
    r = ReplaceRARE(count_file)
    input_file = 'parse_train.dat'
    output_file = 'parse_train.rare.dat'
    r.replace_rare(input_file, output_file)
    '''

    count_file = 'cfg_vert.counts'
    r = ReplaceRARE(count_file)
    input_file = 'parse_train_vert.dat'
    output_file = 'parse_train_vert.rare.dat'
    r.replace_rare(input_file, output_file)

