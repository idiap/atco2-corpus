#!/usr/bin/env python3
# Author: Juan Pablo Zuluaga (Idiap) <juan-pablo.zuluaga@idiap.ch>

# Script to create k-fold cross-validation files for experimentation

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

parser = argparse.ArgumentParser()
parser.add_argument("--input_csv", help="Path to all csv file", type=str)
parser.add_argument("--k", help="Number of folds", type=int)
parser.add_argument("--save_dir", help="Folder to save split files to", type=str)
parser.add_argument("--seed", help="Random seed", type=int)
args = parser.parse_args()


def main():
    df = pd.read_csv(args.input_csv, sep=";", header=0)
    np.random.seed(args.seed)
    # create folder:
    os.makedirs(args.save_dir, exist_ok=True)

    kf = KFold(n_splits=args.k, random_state=args.seed, shuffle=True)
    for fold, (train_index, test_index) in enumerate(kf.split(df)):
        print("FOLD:", fold + 1, "TRAIN:", train_index, "TEST:", test_index)
        df_train = df.iloc[train_index]
        df_test = df.iloc[test_index]
        df_train.to_csv(
            os.path.join(args.save_dir, f"train_fold{fold+1}.csv"), index=False, sep=";"
        )
        df_test.to_csv(
            os.path.join(args.save_dir, f"test_fold{fold+1}.csv"), index=False, sep=";"
        )


if __name__ == "__main__":
    main()
