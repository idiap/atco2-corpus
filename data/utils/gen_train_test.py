#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""
    Script to create train and test folds for the UWB dataset
"""

import argparse
import os
from sklearn.model_selection import train_test_split

parser = argparse.ArgumentParser()
parser.add_argument("--input-csv", help="Path to all csv file", type=str)
parser.add_argument(
    "--train-percentage",
    help="Percentage of data in train folder",
    default=80,
    type=int,
)
parser.add_argument("--seed", help="Random seed", default=1234, type=int)
args = parser.parse_args()


def main():

    output_dir_train = os.path.dirname(args.input_csv) + "/train/ids"
    output_dir_test = os.path.dirname(args.input_csv) + "/test/ids"

    # read the input list IDs
    with open(args.input_csv, "r") as f:
        lines = f.read().splitlines()

    # perform the split, train --> train/test
    x_train, x_test = train_test_split(
        lines,
        train_size=(args.train_percentage / 100),
        random_state=args.seed,
        shuffle=False,
    )

    print(f"printing the TRAIN SET IDS file in: {output_dir_train}")
    with open(output_dir_train, "w") as of:
        for row in x_train:
            of.write(str(row) + "\n")

    print(f"printing the TEST SET IDS file in: {output_dir_test}")
    with open(output_dir_test, "w") as of:
        for row in x_test:
            of.write(str(row) + "\n")


if __name__ == "__main__":
    main()
