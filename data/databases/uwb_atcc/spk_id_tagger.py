#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script that infers the speaker role (ATCO or pilot) based on the transcripts
of UWB-ATCC dataset. This script is only used for this dataset.
"""

import os
import sys


def main():
    """Command line interface..."""

    transcripts_file = sys.argv[1]

    # defining output variables and paths
    output_path = os.path.dirname(transcripts_file)
    out_text = f"{output_path}/text2_raw_spk"
    out_utt2spk_id = f"{output_path}/utt2speakerid"

    cnt_empty = 0

    out_text_list, out_spkid_list = [], []
    with open(transcripts_file, "r") as fd:
        # fetch the transcript line by line,
        for line in fd:
            data = line.rstrip().split(" ")

            # check that the utterance has annotations
            if len(data) < 6:
                print(f"Empty utterance: {line.rstrip()}")
                cnt_empty += 1
                continue
            else:
                utt_id = data[0]
                rest = " ".join(data[1:4])
                text = data[4:]

                speaker = "none"
                is_first = True
                prefix_tag = "B"

                # detect whether this segment has only atco, only pilot or both
                # we also update the utt_id indentifier
                overall_utt_spk = "none"

                if "[air_|]" in text or "[ground_|]" in text:
                    overall_utt_spk = "atco_pilot"
                    utt_id = utt_id + "_PIAT"
                elif "[air]" in text:
                    overall_utt_spk = "pilot"
                    utt_id = utt_id + "_PI"
                elif "[ground]" in text:
                    overall_utt_spk = "atco"
                    utt_id = utt_id + "_AT"
                else:
                    cnt_empty += 1
                    continue

                # where to save the output
                transcript, tag_list = [], []
                for word in text:
                    # if there is a tag, do not add it to the transcript
                    if "[" in word or "]" in word:

                        # conditions to set to true the B- token
                        if any(
                            special in word
                            for special in ["[ground]", "[ground_|", "[|_ground]"]
                        ):
                            speaker = "atco"
                            is_first = True

                        elif any(
                            special in word
                            for special in ["[air]", "[air_|", "[|_air]"]
                        ):
                            speaker = "pilot"
                            is_first = True

                    # appending the words and tags to produce the transcript and tags lists
                    else:
                        if is_first:
                            prefix_tag = "B"
                            is_first = False
                        else:
                            prefix_tag = "I"

                        transcript.append(word)
                        tag = prefix_tag + "-" + speaker
                        tag_list.append(tag)

                assert len(transcript) == len(
                    tag_list
                ), "transcript and tag list have different size"
                if len(transcript) < 1:
                    cnt_empty += 1
                    continue

                # saving the output transcript and tag list in the lists:
                transcript = " ".join(transcript)
                tag_list = " ".join(tag_list)

                out_text_list.append(f"{utt_id} {rest} {transcript}")
                out_spkid_list.append(
                    f"{utt_id} {overall_utt_spk} {transcript};{tag_list}"
                )

    print(f"there were {cnt_empty} empty or blank utterances")

    out_text = f"{output_path}/text2_raw_spk"
    out_utt2spk_id = f"{output_path}/utt2speakerid"

    print(f"printing the text file in: {out_text}")
    with open(out_text, "w") as of:
        for row in out_text_list:
            of.write(str(row) + "\n")

    print(f"printing the text and tags file in: {out_utt2spk_id}")
    with open(out_utt2spk_id, "w") as of:
        for row in out_spkid_list:
            of.write(str(row) + "\n")


if __name__ == "__main__":
    main()
