#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

""" Script to apply a text mapping given a mapping rules file """

import argparse
import re
import sys


def main():
    # Option parsing,
    parser = argparse.ArgumentParser(
        description="Apply mapping table to stdin with text file."
    )
    parser.add_argument(
        "mapping_file",
        help="tab-separated mapping for the transcripts (1st column interpreted as regexp)",
    )
    args = parser.parse_args()

    # Read the mapping,
    # - represented as: [ (from1, to1), (from2, to2), ... ]
    # - empty lines are ignored,
    # - make sure the tuples have 2 elements,

    # load mapping table,
    with open(args.mapping_file, "r") as fd:
        mapping = [
            tuple(l.strip().split("\t"))
            for l in fd
            if (len(l.strip()) > 0 and l[0] != "#")
        ]

    # check that tuples are binary,
    for tpl in mapping:
        if len(tpl) != 2:
            raise Exception(
                "Wrong tuple: '%s' in table '%s'" % (str(tpl), args.mapping_file)
            )

    # precompile the regular expressions,
    mapping_compiled = [
        tuple((re.compile(" " + orig + " "), " " + new + " ")) for orig, new in mapping
    ]  # extra spaces,

    for line in sys.stdin:
        line_ = " " + line.strip() + " "  # adding spaces,
        for regexp, replace in mapping_compiled:
            line_ = regexp.sub(replace, line_)
            line_ = regexp.sub(replace, line_)
        print(line_[1:-1])  # removing spaces,


if __name__ == "__main__":
    main()
