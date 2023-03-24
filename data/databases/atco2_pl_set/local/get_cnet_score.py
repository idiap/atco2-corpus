#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import sys, os


def get_mean_wordconf_in_cnet(cnet_file):
    """compute mean word_confidence, exclude confidences of <eps>"""

    confidences = []

    with open(cnet_file, "r") as f_in:
        for line in f_in:
            name, channel, t_beg, dur, wrd, wrd_conf, rest = (
                line + " DUMMY DUMMY DUMMY"
            ).split(maxsplit=6)
            if wrd != "<eps>":
                try:
                    confidences.append(float(wrd_conf))
                except:
                    print(f"[WARNING]", file=sys.stderr)
                    print(f"wrd_conf '{wrd_conf}' is not a float... ", file=sys.stderr)
                    print(f"  line '{line}'", file=sys.stderr)
                    print(f"  file '{cnet_file}'", file=sys.stderr)

    if len(confidences) == 0:
        return -1
    mean_conf = sum(confidences) / len(confidences)

    return mean_conf


def main():
    # parse arguments from CLI
    cnet_list = sys.argv[1]

    with open(cnet_list, "r") as f_cl:
        for cnet_file in f_cl:
            cnet_file = cnet_file.strip()  # remove \n
            cnet_key = os.path.basename(cnet_file).split(".")[0]
            mean_conf = get_mean_wordconf_in_cnet(cnet_file)
            print(f"{cnet_key} {mean_conf:.8f} {cnet_file}")


if __name__ == "__main__":
    main()
