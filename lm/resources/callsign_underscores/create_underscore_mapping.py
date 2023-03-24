#!/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import re
import sys

import numpy as np

letters = {
    "A": "alfa",
    "B": "bravo",
    "C": "charlie",
    "D": "delta",
    "E": "echo",
    "F": "foxtrot",
    "G": "golf",
    "H": "hotel",
    "I": "india",
    "J": "juliett",
    "K": "kilo",
    "L": "lima",
    "M": "mike",
    "N": "november",
    "O": "oscar",
    "P": "papa",
    "Q": "quebec",
    "R": "romeo",
    "S": "sierra",
    "T": "tango",
    "U": "uniform",
    "V": "victor",
    "W": "whiskey",
    "X": "x-ray",
    "Y": "yankee",
    "Z": "zulu",
}

numbers = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}


def load_airline_table(airline_table):

    callword_mapping = dict()
    skip_words = set(list(letters.values()) + list(numbers.values()))

    for line in open(airline_table, "r"):
        # parse table of airlines,
        if line.strip().split("\t")[0] == "ICAO":
            continue
        if line.strip() == "":
            continue

        arr = line.rstrip().split("\t")
        if len(arr) < 3:
            print(arr, file=sys.stderr)
        icao, name, callword = arr[:3]

        callword_ = callword.lower()
        callword_underscore = re.sub("[ -]", "_", callword.lower())

        if not re.search(" ", callword_):
            continue  # only those containing underscore,
        if callword_ in callword_mapping:
            continue  # skip if already there,

        # skip 'callword' with any 'alphabet word' or a 'number',
        if np.sum([(wrd in skip_words) for wrd in callword_.split()]) > 0:
            # print("skipping %s, contains alphabet word or number..." % callword_, file=sys.stderr)
            continue

        # add to dict,
        callword_mapping[callword_] = callword_underscore

    return callword_mapping


def main():

    airline_table = "../callsign_mapping/callsign_mapping.csv"
    callword_mapping = load_airline_table(airline_table)

    blacklist_table = "../callsign_normalization/blacklist.lst"
    blacklist = set(np.loadtxt(blacklist_table, dtype="object", delimiter="#"))

    for k, v in sorted(callword_mapping.items()):
        if k not in blacklist:
            print("%s\t%s" % (k, v))


if __name__ == "__main__":
    main()
