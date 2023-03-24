#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import sys


def main():

    # parse arguments from CLI
    if len(sys.argv) != 3:
        print(f"Usage: {__file__} cnet_list segments_file")
        sys.exit(1)

    cnet_list = sys.argv[1]
    (segments_file,) = sys.argv[2:]
    rec_set = set()

    # crawl to 'cnet_list', store 'rec-keys' into 'rec_set'
    with open(cnet_list, "r") as fd_cnet_list:
        for line in fd_cnet_list:
            cnet_fname = line.strip().split()[0]
            rec_key = cnet_fname.rsplit("/", maxsplit=1)[-1].split(".")[0]
            rec_set.add(rec_key)

    # crawl 'segments' for 'utt-keys'
    with open(segments_file, "r") as fd_segments:
        for line in fd_segments:
            utt, rec, t_beg, t_end = line.strip().split()
            if rec in rec_set:
                print(utt)


if __name__ == "__main__":
    main()
