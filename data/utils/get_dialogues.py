#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License


""" 
    Script to get dialogues for the LDC-ATCC database. 
    You need to first prepare the LDC-ATCC datbase by running: data/databases/ldc_atcc/README.sh

    Help: how to run this script?
        - python3 data/utils/get_dialogues.py \
            experiments/data/ldc_atcc/prep/transcripts_all_data_norm \
            >experiments/data/ldc_atcc/prep/dialogues
"""

import sys


def main():
    # parse args,
    transcripts_file = sys.argv[1]

    # getting number of lines of the file, formatting output utt_id
    num_lines = len(str(sum(1 for line in open(transcripts_file)))) + 1

    # state of dialogue and flags to flush the output and re-init
    new_dialogue = ""
    cnt_dialogue = 0
    speaker_list, identifier_list = [], []
    spk1 = ""
    spk2 = ""
    callsign = ""  # this var tells when to move to a new dialogue

    # for loop in the csv transcripts
    with open(transcripts_file) as fd:
        for line in fd:

            data = line.split()
            if len(data) < 9:
                print(
                    f"Empty utterance or error in loading it: {data[0]}"
                )  # denominator can't be 0
                continue
            else:
                identifier = data[0]
                speaker = data[6]
                text = " ".join(data[8:]).rstrip()
                segments = " ".join(data[4:5])

                # in this case we have a different callsign, thus, we create a new dialogue
                if data[7] != callsign:
                    # we flush the output

                    if len(new_dialogue) > 0:
                        utt_id = "{}_{}_{}".format(
                            "dialogue", callsign, str(cnt_dialogue).zfill(num_lines)
                        )

                        output_dialogue = (
                            "<bos> " + " <turn> ".join(new_dialogue) + " <eos>"
                        )
                        print(
                            utt_id,
                            callsign,
                            " ".join(speaker_list),
                            output_dialogue,
                            " ".join(identifier_list),
                            sep=";",
                        )

                    # update callsign and create outputs
                    callsign = data[7]
                    new_dialogue = [f"<{speaker}> {text}"]
                    speaker_list = [speaker]
                    identifier_list = [identifier]
                    cnt_dialogue += 1

                # in this case we have same callsign, we add it to the dialogue
                elif data[7] == callsign:
                    new_dialogue.append(f"<{speaker}> {text}")
                    speaker_list.append(speaker)
                    identifier_list.append(identifier)


if __name__ == "__main__":
    main()
