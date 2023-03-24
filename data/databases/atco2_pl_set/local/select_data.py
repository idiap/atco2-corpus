#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import sys, os
import numpy as np


def main(data, cnet_path=None):
    """get the lid/snr scores"""

    data_selected = []
    data_selected_english = []

    if cnet_path == None:
        print("give a cnet file as input")
        sys.exit(0)

    # get the dirname to store again the filtered cnet files
    dirname_cnet = os.path.dirname(cnet_path)

    for rec_key, cnet_conf, cnet_file in data:

        path, lid_score, snr, fname = cnet_file.rsplit("/", maxsplit=3)
        lid_score = float(lid_score)
        snr = int(snr)

        # SELECTION RULEs !!!
        # first, only get the data that LID>=0.5
        if lid_score >= 0.5:
            data_selected_english.append((rec_key, cnet_conf, cnet_file))

            # (removes 1/3 of audio files)
            if lid_score >= 0.7 and snr >= 0 and cnet_conf > 0.8:
                data_selected.append((rec_key, cnet_conf, cnet_file))

    data_selected = np.array(data_selected, dtype="object,f4,object")
    data_selected_english = np.array(data_selected_english, dtype="object,f4,object")

    # save the file with all data LID>=0.5
    np.savetxt(
        f"{dirname_cnet}/cnet_scores.selected-lid-0.5",
        data_selected_english,
        fmt=["%s", "%f", "%s"],
    )
    np.savetxt(
        f"{dirname_cnet}/cnet_scores.selected-cn-thr08",
        data_selected,
        fmt=["%s", "%f", "%s"],
    )


if __name__ == "__main__":

    # argparse
    cnet_score_file = sys.argv[1]

    # load the object in memory:
    data = np.loadtxt(cnet_score_file, dtype="object,f4,object")
    main(data, cnet_score_file)
