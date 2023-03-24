#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: 2022 Juan Pablo Zuluaga  (jzulua@idiap.ch)

import sys


def tagger_fixer(tag_list):
    """Function to tag the sequence given a transcript with tags"""

    # output tag list
    clean_tags_list = []

    prev_tag = ""
    prev_iob = ""

    #  import pdb; pdb.set_trace()
    for word in tag_list.split():

        # edge case, no_tag class
        if word == "NO_TAGGED":
            clean_tags_list.append(word)
            break

        crt_iob = word.split("-")[0]
        crt_tag = word.split("-")[1]

        if (crt_iob == "B") and (prev_tag == crt_tag) and (prev_iob == crt_iob):
            # we make the change of B --> I
            clean_tags_list.append(f"I-{crt_tag}")
            #  import pdb; pdb.set_trace()
        else:
            clean_tags_list.append(word)
        prev_tag = crt_tag
        prev_iob = crt_iob

    assert len(clean_tags_list) == len(tag_list.split())

    return " ".join(clean_tags_list)


def main():
    # parse args,
    transcripts_file = sys.argv[1]

    # for loop in the csv transcripts
    with open(transcripts_file) as fd:
        for line in fd:
            utt_id, tag_list = line.split(" ", maxsplit=1)
            tag_list = tag_list.strip()

            tags_list_fixed = tagger_fixer(tag_list)
            print(utt_id, tags_list_fixed, sep=" ")


if __name__ == "__main__":
    main()
