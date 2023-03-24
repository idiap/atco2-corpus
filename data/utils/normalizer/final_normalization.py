#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Saeed Sarfjoo <saeed.sarfjoo@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

""" Script for normalizing input ATC text """

import argparse
import os
import re
import sys


def normalize_text(hype_text, corr_dic, ne_word_dic=None, is_ark=True):
    """
    Function to normalize text given a hypothesis and a list of mapping rules
    """

    key = ""
    if is_ark:
        words = hype_text.split()
        key = words[0]
        if len(words) > 1:
            hype_text = " ".join(words[1:])
        else:
            return hype_text

    hype_text = " " + hype_text + " "

    hes_array = [
        " umm ",
        " uhh ",
        " uhm ",
        " ahm ",
        " hmmm ",
        " hm ",
        " aaah ",
        " aah ",
        " aeh ",
        " ah ",
        " eh ",
        " err ",
        " em ",
        " <hes> ",
    ]
    # Converting hesitation
    for hes in hes_array:
        hype_text = hype_text.replace(hes, " [hes] ")

    # Fix double [unk]
    unk_list = ["<gbg>", "<unk>"]
    for unk in unk_list:
        while hype_text.find(unk) > -1:
            hype_text = hype_text.replace(unk, "[unk]")
    while hype_text.find(" [unk] [unk] ") > -1:
        hype_text = hype_text.replace(" [unk] [unk] ", " [unk] ")

    # Fix noise
    noise_list = ["<noise>", "<bg>", "<ring>", "<click>", "<dtmf>", "<prompt>"]
    for noise in noise_list:
        while hype_text.find(noise) > -1:
            hype_text = hype_text.replace(noise, "[noise]")

    # Fix speaker noise
    noise_list = ["<breath>", "<laugh>", "<cough>", "<lipsmack>", "<overlap>"]
    for noise in noise_list:
        while hype_text.find(noise) > -1:
            hype_text = hype_text.replace(noise, "[spk]")

    # Fix foreign
    foreign_list = ["<foreign>"]
    for foreign in foreign_list:
        while hype_text.find(foreign) > -1:
            hype_text = hype_text.replace(foreign, "[NE] [unk] [/NE]")

    # Fix compound words
    words = hype_text.split()
    end_idx = len(words) - 3
    j = 0
    while j < end_idx:
        if (
            words[j] + " " + words[j + 1] + " " + words[j + 2] + " " + words[j + 3]
            in corr_dic
        ):
            words[j] = corr_dic[
                words[j] + " " + words[j + 1] + " " + words[j + 2] + " " + words[j + 3]
            ]
            del words[j + 1]
            del words[j + 1]
            del words[j + 1]
            end_idx -= 3
        j += 1

    end_idx = len(words) - 2
    j = 0
    while j < end_idx:
        if words[j] + " " + words[j + 1] + " " + words[j + 2] in corr_dic:
            words[j] = corr_dic[words[j] + " " + words[j + 1] + " " + words[j + 2]]
            del words[j + 1]
            del words[j + 1]
            end_idx -= 2
        j += 1
    end_idx = len(words) - 1
    j = 0

    while j < end_idx:
        if words[j] + " " + words[j + 1] in corr_dic:
            words[j] = corr_dic[words[j] + " " + words[j + 1]]
            del words[j + 1]
            end_idx -= 1
        j += 1
    for j in range(len(words)):
        if words[j] in corr_dic:
            words[j] = corr_dic[words[j]]

    hype_text = " " + " ".join(words) + " "
    hype_text = re.sub("\_\([\w/]*\)", "", hype_text)

    # Add NE tag
    if len(ne_word_dic.keys()) > 0:
        words = hype_text.split()
        end_idx = len(words) - 5
        j = 0
        while j < end_idx:
            if (
                words[j]
                + " "
                + words[j + 1]
                + " "
                + words[j + 2]
                + " "
                + words[j + 3]
                + " "
                + words[j + 4]
                + " "
                + words[j + 5]
                in ne_word_dic
            ):
                words[j] = (
                    "[NE "
                    + ne_word_dic[
                        words[j]
                        + " "
                        + words[j + 1]
                        + " "
                        + words[j + 2]
                        + " "
                        + words[j + 3]
                        + " "
                        + words[j + 4]
                        + " "
                        + words[j + 5]
                    ]
                    + "] "
                    + words[j]
                    + " "
                    + words[j + 1]
                    + " "
                    + words[j + 2]
                    + " "
                    + words[j + 3]
                    + " "
                    + words[j + 4]
                    + " "
                    + words[j + 5]
                    + " [/NE]"
                )
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                end_idx -= 5
            j += 1

        end_idx = len(words) - 4
        while j < end_idx:
            if (
                words[j]
                + " "
                + words[j + 1]
                + " "
                + words[j + 2]
                + " "
                + words[j + 3]
                + " "
                + words[j + 4]
                in ne_word_dic
            ):
                words[j] = (
                    "[NE "
                    + ne_word_dic[
                        words[j]
                        + " "
                        + words[j + 1]
                        + " "
                        + words[j + 2]
                        + " "
                        + words[j + 3]
                        + " "
                        + words[j + 4]
                    ]
                    + "] "
                    + words[j]
                    + " "
                    + words[j + 1]
                    + " "
                    + words[j + 2]
                    + " "
                    + words[j + 3]
                    + " "
                    + words[j + 4]
                    + " [/NE]"
                )
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                end_idx -= 4
            j += 1

        end_idx = len(words) - 3
        j = 0
        while j < end_idx:
            if (
                words[j] + " " + words[j + 1] + " " + words[j + 2] + " " + words[j + 3]
                in ne_word_dic
            ):
                words[j] = (
                    "[NE "
                    + ne_word_dic[
                        words[j]
                        + " "
                        + words[j + 1]
                        + " "
                        + words[j + 2]
                        + " "
                        + words[j + 3]
                    ]
                    + "] "
                    + words[j]
                    + " "
                    + words[j + 1]
                    + " "
                    + words[j + 2]
                    + " "
                    + words[j + 3]
                    + " [/NE]"
                )
                del words[j + 1]
                del words[j + 1]
                del words[j + 1]
                end_idx -= 3
            j += 1

        end_idx = len(words) - 2
        j = 0
        while j < end_idx:
            if words[j] + " " + words[j + 1] + " " + words[j + 2] in ne_word_dic:
                words[j] = (
                    "[NE "
                    + ne_word_dic[words[j] + " " + words[j + 1] + " " + words[j + 2]]
                    + "] "
                    + words[j]
                    + " "
                    + words[j + 1]
                    + " "
                    + words[j + 2]
                    + " [/NE]"
                )
                del words[j + 1]
                del words[j + 1]
                end_idx -= 2
            j += 1
        end_idx = len(words) - 1
        j = 0

        while j < end_idx:
            if words[j] + " " + words[j + 1] in ne_word_dic:
                words[j] = (
                    "[NE "
                    + ne_word_dic[words[j] + " " + words[j + 1]]
                    + "] "
                    + words[j]
                    + " "
                    + words[j + 1]
                    + " [/NE]"
                )
                del words[j + 1]
                end_idx -= 1
            j += 1
        for j in range(len(words)):
            if words[j] in ne_word_dic:
                words[j] = "[NE " + ne_word_dic[words[j]] + "] " + words[j] + " [/NE]"
        hype_text = " " + " ".join(words) + " "

    # Fix abbreviation
    prog = re.compile("[ ]([a-z]_)+[a-z][ ]")
    match = prog.search(hype_text)
    while match:
        hype_text = hype_text.replace(
            match.group(0), match.group(0).replace("_", "").upper()
        )
        match = prog.search(hype_text)
    hype_text = hype_text.replace("_", " ")
    hype_text = hype_text.replace("-", " ")
    hype_text = hype_text.replace(" x ray ", " x-ray ").strip()

    if is_ark:
        hype_text = key + " " + hype_text

    return hype_text


def parse_args():
    # parse the arguments
    parser = argparse.ArgumentParser(
        usage="Usage: normalizer.py <hypothesis-file> <output-file> <words-file> [<ne-word-list>]"
    )
    # reporting vars
    parser.add_argument(
        "--mapping",
        type=str,
        required=True,
        help="mapping rules file",
        default="data/utils/normalizer/words.txt",
    )

    parser.add_argument(
        "--input", type=str, default=None, required=True, help="input file to normalize"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        required=True,
        help="output file to normalize",
    )
    parser.add_argument(
        "--ne-list", type=str, default=None, help="Non-English words list"
    )

    return parser.parse_args()


def main():

    arguments = parse_args()
    hyp_file = arguments.input
    out_file = arguments.output
    corr_file = arguments.mapping

    ne_word_list = ""
    if arguments.ne_list is not None:
        ne_word_list = arguments.ne_list

    corr_dic = {}
    ne_word_dic = {}

    if sys.version_info.major > 2:
        do_open = lambda filename: open(filename, encoding="utf-8")
        do_open_w = lambda filename: open(filename, encoding="utf-8", mode="w")
    else:
        do_open = lambda filename: open(filename)
        do_open_w = lambda filename: open(filename, mode="w")

    with do_open(corr_file) as rf:
        # Read the mapping rules from input file
        lines = rf.readlines()
        for line in lines:
            line = line.strip()
            if len(line) > 0 and not line.startswith("#"):
                line_parts = line.split(";")
                if len(line_parts) > 1:
                    corr_dic[line_parts[0]] = line_parts[1]

    if ne_word_list != "" and os.path.exists(ne_word_list):
        # read the non-english words file
        with do_open(ne_word_list) as rf:
            lines = rf.readlines()
            for line in lines:
                line = line.strip()
                if len(line) > 0 and not line.startswith("#"):
                    line_parts = line.split()
                    if len(line_parts) > 1:
                        ne_word_dic[" ".join(line_parts[:-1])] = line_parts[-1]

    with do_open(hyp_file) as rf:
        hyp_lines = rf.readlines()

    with do_open_w(out_file) as fw:
        # generate the normalized outputs
        for hyp in hyp_lines:
            if len(hyp.strip()) > 0:
                norm_text = normalize_text(hyp.strip(), corr_dic, ne_word_dic)
                fw.write(norm_text + os.linesep)


if __name__ == "__main__":
    main()
