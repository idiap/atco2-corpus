#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""
    Script to import the named-entity recognition tags from ATCO2-test-set-4h corpora. 
    - We produce a file with the tags aligned with the 'text' file that are:
        - Callsigns, commands and values
    
    Help: how to run this script?
        - python3 data/utils/spd_xml2csv_tags_batch.py \
            experiments/data/atco2_corpus/prep/transcripts_norm.csv \
            > experiments/data/atco2_corpus/prep/transcripts3.csv
"""

import sys


def tagger(transcript):
    """Function to tag the sequence given a transcript with tags"""

    # output lists
    clean_transcript = []
    tags_list = []
    callsing_seq = []

    prefix_tag, current_tag = "O", "O"
    is_first = True
    no_tagged = True

    for word in transcript.split():

        special_characters = [
            "[unk]",
            "[hes]",
            "[xt]",
            "[noise]",
            "[spk]",
            "[key]",
            "[/ne}",
            "[\\ne]",
            "[xs]",
            "[unk",
            "[ukn]",
            "[hes ]",
            "[hes",
            "[#nonenglish]",
            "[/#nonenglish]",
            "<hes>",
            "<unk>",
            "<noise>",
            "<breath>",
        ]

        if any(special in word for special in special_characters):
            continue

        if "[#" in word:  # Begining of tag
            current_tag = word.split("[#")[1][:-1]
            if current_tag == "unnamed":
                current_tag = "O"
            is_first, no_tagged = True, False
        elif "[/#" in word:  # Re-init the tagging
            current_tag = "O"
            is_first = True

        if "#" not in word:
            clean_transcript.append(word)

            # Append the tag depending on 'is first' or not
            if is_first:
                prefix_tag = "B-"
                tag = prefix_tag + current_tag
                is_first = False
            elif not is_first:
                prefix_tag = "I-"
                tag = prefix_tag + current_tag

            tags_list.append(tag)
            if "callsign" in current_tag:
                callsing_seq.append(word)

    assert len(clean_transcript) == len(tags_list)

    # some edge cases, 1) no tags provided i.e., [#] not present
    #                  2) no callsign detected
    if no_tagged:
        tags_list = ["NO_TAGGED"]
    if len(callsing_seq) == 0:
        callsing_seq = ["NO_CALLSIGN"]
    return " ".join(clean_transcript), " ".join(tags_list), " ".join(callsing_seq)


def main():
    # parse args,
    transcripts_file = sys.argv[1]

    # for loop in the csv transcripts
    with open(transcripts_file) as fd:
        for line in fd:
            data = ";".join(line.split(";")[:-1])
            transcript = line.split(";")[-1].strip()

            clean_transcript, tags_list, callsing_seq = tagger(transcript)
            print(data, clean_transcript, tags_list, callsing_seq, sep=";")


if __name__ == "__main__":
    main()
