#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import sys
import numpy as np


def process_cnet_1best(cnet_fname, fd_transcripts, fd_segments):
    name = ""
    cnet = []

    with open(cnet_fname, "r") as fd_cnet:
        for line in fd_cnet:
            try:
                name, spk, t_beg, dur, wrd, wrd_conf, rest = (
                    line.strip() + " DUMMY"
                ).split(maxsplit=6)
                t_begin = float(t_beg)
                t_end = float(t_beg) + float(dur)
                cnet.append((wrd, t_begin, t_end, spk))
            except:
                # ValueError '<eps>' in place of 'dur'
                continue

    # empty cnet file
    if len(cnet) == 0:
        return

    # convert to np.array
    cnet = np.array(cnet, dtype="object,f8,f8,object")

    # split by 4th column
    split_indices = np.nonzero(np.hstack([[""], cnet["f3"][:-1]]) != cnet["f3"])[0]
    cnet_split = np.split(cnet, split_indices[1:])

    for cnet_part in cnet_split:
        words_in_segment = []
        for wrd, t_begin, t_end, spk in cnet_part:
            if wrd != "<eps>":
                words_in_segment.append(wrd)

        # prepare for prints
        utt_beg = cnet_part[0]["f1"]
        utt_end = cnet_part[-1]["f2"]

        int_beg = int(utt_beg * 100)
        int_end = int(utt_end * 100)

        # print the 'text' transcript of the segment
        print(
            f"{name}!{int_beg:07d}-{int_end:07d} {' '.join(words_in_segment)}",
            file=fd_transcripts,
        )
        # print 'segments' file record
        print(
            f"{name}!{int_beg:07d}-{int_end:07d} {name} {utt_beg:03.2f} {utt_end:03.2f}",
            file=fd_segments,
        )


def main():
    # parse args
    cnet_list_file, transcripts_out, segments_out = sys.argv[1:]

    # output files, transcripts and segments
    fd_transcripts = open(transcripts_out, "w")
    fd_segments = open(segments_out, "w")

    with open(cnet_list_file, "r") as fd_cnet_list:
        for line in fd_cnet_list:
            cnet_fname = line.strip()
            process_cnet_1best(cnet_fname, fd_transcripts, fd_segments)

    fd_transcripts.close()
    fd_segments.close()


if __name__ == "__main__":
    main()
