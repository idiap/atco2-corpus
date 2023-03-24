#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""
    This script create a file with the tags for training the text-based diarization system.
    The idea is to create tags in NER style fashion.
    This script is used by LDC-ATCC corpus and ATCO2 corpus
"""

import argparse


def clean_input_utterance(input_text):
    """Function to clean the input utterance
    Inputs:
        - input text
    Output:
        - cleaned text
    """

    # remove all the words starting with <> or [],
    sequence = " ".join(filter(lambda x: x[0] != "<", input_text.strip().split()))
    sequence = " ".join(filter(lambda x: x[-1] != ">", sequence.split()))
    sequence = " ".join(filter(lambda x: x[0] != "[", sequence.split()))
    sequence = " ".join(filter(lambda x: x[-1] != "]", sequence.split()))

    # remove the greetings in ATCO2 format dobry_den_(greet)
    sequence = " ".join(filter(lambda x: "(" not in x, sequence.split()))

    # return and lower case
    return sequence.lower()


def text_to_tags(text, tag="O"):
    """
    Function to generate tags for each word of the given text.
    Input:
            - text: transcript or text string (generate tags)
            - tag:  the desired tag for the given text
    Output:
            - ner_tags: generated tags in NER format (B I I I O O O O O...)
            - tags:     tags per each word depending on the class
    """
    transcript = text.split(" ")
    ner_list, tag_list = [], []
    cnt = 0

    # assemble the list by going one by one
    for i in enumerate(transcript):
        if cnt == 0:
            ner_list.append("B-" + tag)
            tag_list.append(tag)
            cnt += 1
            continue
        ner_list.append("I-" + tag)
        tag_list.append(tag)

    # check whether the number of words and tags is the same
    assert len(transcript) == len(tag_list)
    assert len(transcript) == len(ner_list)

    return transcript, tag_list, ner_list


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("input_folder", help="path to Kaldi folder. ")
    parser.add_argument("output_folder", help="folder where to write the files")

    return parser.parse_args()


def main(args):
    """Main function to extract the information from text file.

    The intention of this script is to create a training set for
    Idiap callsign/command/concept extractor
    """

    # reading the inputs from the main folder
    text_file = args.input_folder + "/text"
    spk_file = args.input_folder + "/utt2speakerid"

    # files to generate based on output folder
    utt2text = open(args.output_folder + "/utt2text", "w")
    utt2tags = open(args.output_folder + "/utt2tags", "w")
    utt2nertags = open(args.output_folder + "/utt2nertags", "w")
    utt2text_tags = open(args.output_folder + "/utt2text_tags", "w")

    # load the text and speaker data
    text_data, spk_data = {}, {}

    with open(text_file, "r") as path:
        lines = path.readlines()
    for line in lines:
        text_data[line.strip().split()[0]] = line.strip().split()[1:]

    with open(spk_file, "r") as path:
        lines_spk = path.readlines()
    for line in lines_spk:
        spk_data[line.strip().split()[0]] = line.strip().split()[1:]

    # MAIN LOOP,
    for key in text_data:

        # get utt_id and transcript
        transcript = text_data[key]
        spk_info = spk_data[key]

        # get transcript and clean it
        transcript = clean_input_utterance(" ".join(transcript))
        tag = spk_info[0].lower()

        # Obtain tags and ner tags
        a1, a2, a3 = text_to_tags(transcript, tag)
        # converting to only one list
        final_text = " ".join(a1)
        final_tags = ",".join(a2)
        final_ner_tags = ",".join(a3)
        final_text_tags = f"{final_text};{final_ner_tags}"

        # write the files,
        for file_to_write, text in [
            [utt2text, final_text],
            [utt2tags, final_tags],
            [utt2nertags, final_ner_tags],
            [utt2text_tags, final_text_tags],
        ]:
            # writing the files
            if "utt2text_tags" in file_to_write.name:
                line_to_write = "{0};{1}".format(key, text)
            else:
                line_to_write = "{0} {1}".format(key, text)
            file_to_write.write(line_to_write)
            file_to_write.write("\n")
            final_ner_tags = ",".join(final_ner_tags)
            final_text_tags = f"{final_text};{final_ner_tags}"


if __name__ == "__main__":
    args = parse_args()
    main(args)
