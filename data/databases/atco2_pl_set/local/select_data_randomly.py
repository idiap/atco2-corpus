#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import argparse
import numpy as np


def main():

    # parse arguments from CLI
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-fraction",
        type=float,
        default=0.8,
        help="keep fraction of original list",
    )
    parser.add_argument(
        "--cnet-list",
        type=str,
        default="experiments/data/atco2_pl_set/cnet_scores",
        help="List with CNET files (confidence)",
    )
    # parse arguments
    args = parser.parse_args()

    data = np.loadtxt(args.cnet_list, dtype="object,f4,object")
    rec_keys = data["f0"]

    sample_size = int(len(rec_keys) * args.keep_fraction)

    selected_keys = np.random.choice(rec_keys, size=sample_size, replace=False)
    selected_keys = np.sort(selected_keys)

    for key in selected_keys:
        print(key)


if __name__ == "__main__":
    main()
