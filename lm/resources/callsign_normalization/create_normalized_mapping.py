#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

# Analyze the callwords and eventually
# map them to correct form.

import argparse
import json
import os
import re
import sys

import numpy as np
from tqdm import tqdm

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

speciffic_mapping = {
    "air france": "airfrans",
    "air_france": "airfrans",
    "airfrance": "airfrans",
    "air_frans": "airfrans",
    "ryan air": "ryanair",
    "ryan_air": "ryanair",
    "ryanair": "ryanair",
    "snow cab": "snowcap",
    "snow_cab": "snowcap",
}


def load_callwords(airline_table):
    with open(airline_table, "r") as fp:
        # parse table of airlines,
        # it is either DLR json or WIKI csv file
        if os.path.splitext(airline_table)[1] == ".json":
            data = json.load(fp)
            for _, callwords in data.items():
                yield callwords[0]
        else:
            for line in fp:
                if line.strip().split("\t")[0] == "ICAO":
                    continue
                if line.strip() == "":
                    continue

                arr = line.rstrip().split("\t")
                if len(arr) < 3:
                    print(arr, file=sys.stderr)
                yield arr[2]


def analyze(airline_table, text_file, callword_mapping=dict()):
    # TODO: can we make it faster ?

    skip_words = set(list(letters.values()) + list(numbers.values()))

    ## preload the text file,
    text_file_lines = []
    with open(text_file) as f:
        for line in f:
            text_file_lines.append(" " + line + " ")

    ## main loop over airline_table,
    for callword in tqdm(load_callwords(airline_table)):
        print("INFO: Analyzing %s..." % callword, file=sys.stderr)

        callword = callword.lower()
        callword_ = re.sub("[ -]", "_", callword)  # with underscores,

        # skip 'callword' with any 'alphabet word' or a 'number',
        if np.sum([(wrd in skip_words) for wrd in callword.split()]) > 0:
            # print("skipping %s, contains alphabet word or number..." % callword, file=sys.stderr)
            continue

        # build regular expression,
        # "a_bc de-f" -> "a[ _-]{0,1}b[ _-]{0,1}c[ _-]{0,1}d[ _-]{0,1}e[ _-]{0,1}f"
        # - i.e. space, underscore, hyphen can be anywhere between letters...
        #
        # remove '[ -_]',
        split_to_char = [str(c) for c in re.sub("[ -_]", "", callword)]
        # add '[ _-]{0,1}' between letters, pad by spaces,
        regex = re.compile(" " + "[ _-]{0,1}".join(split_to_char) + " ")

        # search 'regex' in 'text_file_lines',
        for line in text_file_lines:
            for matched in re.findall(regex, " " + line + " "):
                matched_ = matched.strip()
                if matched_ != callword_ and matched_ not in callword_mapping:
                    # new mapping rule...
                    callword_mapping[matched_] = callword_

    return callword_mapping


def main():
    parser = argparse.ArgumentParser(
        description="Create normalized callword mappings based on airline designator tables."
    )
    parser.add_argument(
        "--text", default="/dev/stdin", help="Text file to analyze the callwords."
    )
    args = parser.parse_args()
    text = args.text

    blacklist = []
    with open("./blacklist.lst") as f:
        for line in f:
            blacklist.append(line.strip())

    callword_mapping = {}
    for (k, v) in speciffic_mapping.items():
        callword_mapping[k] = v

    # Analayze text and create mappings
    airline_table = "../callsign_mapping/callsign_mapping.csv"
    callword_mapping = analyze(
        airline_table,
        text,
        callword_mapping,
    )

    # Remove items in blacklist,
    for k, v in sorted(callword_mapping.items()):
        if k in blacklist:
            print(
                'Skiping callword: "%s" since it is on blacklist ["%s" -> "%s"]'
                % (k, k, v),
                file=sys.stderr,
            )
        elif k and v and k != v:
            print("%s\t%s" % (k, v))


if __name__ == "__main__":
    main()
