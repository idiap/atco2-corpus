#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

import os
import re
import shlex
import subprocess
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path

DESCRIPTION = """\
Train and optimize a KenLM language model for a given text data. 
We also could perform optimization.
"""


def correct_kenLM(path_lm, path_lm_correct):
    """When we create the LM with KenLM, we need to fix the LM --> we need to add <s/> symbol"""

    with open(path_lm, "r") as read_file, open(path_lm_correct, "w") as write_file:
        has_added_eos = False
        for line in read_file:
            if not has_added_eos and "ngram 1=" in line:
                count = line.strip().split("=")[-1]
                write_file.write(line.replace(f"{count}", f"{int(count)+1}"))
            elif not has_added_eos and "<s>" in line:
                write_file.write(line)
                write_file.write(line.replace("<s>", "</s>"))
                has_added_eos = True
            else:
                write_file.write(line)
    return print(f"corrected Ken LM in {path_lm_correct}")


def remove_special_characters(text):
    """Function to remove some special chars/symbols from the given transcript"""

    text = text.split(" ")
    # first remove words between [] and <>
    text = " ".join(
        [
            x
            for x in text
            if "[" not in x and "]" not in x and "<" not in x and ">" not in x
        ]
    )

    # regex with predifined symbols to ignore/remove,
    chars_to_ignore_regex2 = '[\{\[\]\<\>\/\,\?\.\!\u00AC\;\:"\\%\\\]|[0-9]'

    text = re.sub(chars_to_ignore_regex2, "", text).lower()
    sentence = text.replace("\u2013", "-")
    sentence = sentence.replace("\u2014", "-")
    sentence = sentence.replace("\u2018", "'")
    sentence = sentence.replace("\u201C", "")
    sentence = sentence.replace("\u201D", "")
    sentence = sentence.replace("ñ", "n")
    sentence = sentence.replace(" - ", " ")
    sentence = sentence.replace("-", "")
    sentence = sentence.replace("'", " ")
    return sentence.lower().rstrip()


def train(lm_dir, dataset_path, n_gram=4, dataset_name="not-defined"):
    """Train a KenLM with a defined order, default 4-gram"""

    print(dataset_name, dataset_path)

    Path(lm_dir).mkdir(parents=True, exist_ok=True)
    corpus_file_path = os.path.join(lm_dir, str(n_gram) + "_corpus.txt")

    print("\nExporting dataset to text file {}...".format(corpus_file_path))
    with open(corpus_file_path, "w", encoding="utf-8") as corpus_file:
        with open(dataset_path, "r", encoding="utf-8") as text_f:
            for line in text_f:
                if len(line.split(" ")) > 1:
                    _, transcript = line.split(" ", maxsplit=1)
                    transcript = remove_special_characters(transcript)
                    corpus_file.write(transcript + " ")  # we only write the text file

    # generate KenLM ARPA file language model
    lm_arpa_file_path_no_fixed = os.path.join(
        lm_dir, f"{dataset_name}_{n_gram}g_no_fix.arpa"
    )
    lm_arpa_file_path = os.path.join(lm_dir, f"{dataset_name}_{n_gram}g.arpa")
    lm_bin_file_path = os.path.join(lm_dir, f"{dataset_name}_{n_gram}g.binary")

    # define the bash command to be executed to train the arpa LM with KenLM
    cmd = "lmplz -o {n} --text {corpus_file} --arpa {lm_file}".format(
        n=n_gram, corpus_file=corpus_file_path, lm_file=lm_arpa_file_path_no_fixed
    )
    print(cmd)

    # run the LM training
    subprocess.run(shlex.split(cmd), stderr=sys.stderr, stdout=sys.stdout)

    # now we need to fix the LM --> we add <s/> symbol
    correct_kenLM(lm_arpa_file_path_no_fixed, lm_arpa_file_path)

    # generate the binary version of the LM (which is faster to be loaded by PyCTCdecode)
    cmd = "build_binary trie {arpa_file} {bin_file}".format(
        arpa_file=lm_arpa_file_path, bin_file=lm_bin_file_path
    )
    print(cmd)

    # run the arpa to bin converter:
    subprocess.run(shlex.split(cmd), stderr=sys.stderr, stdout=sys.stdout)

    # remove some files that we don't need to store (corpus and LM in arpa format)
    [
        os.remove(x)
        for x in [lm_arpa_file_path, lm_arpa_file_path_no_fixed, corpus_file_path]
    ]

    return lm_dir


def main(lm_root_dir, dataset_path, **args):
    """Main function. Train the KENLM"""

    lm_file_path = train(
        lm_dir=lm_root_dir,
        dataset_path=dataset_path,
        n_gram=args["n_gram"],
        dataset_name=args["dataset_name"],
    )
    print(f"done doing training of KenLM \n check the output folder: {lm_file_path}")


if __name__ == "__main__":

    parser = ArgumentParser(
        description=DESCRIPTION, formatter_class=RawTextHelpFormatter
    )
    # optionals,
    parser.add_argument(
        "-nlm",
        "--n-gram",
        dest="n_gram",
        default=4,
        type=int,
        help="Defines the order (n-gram) for the n-gram KenLM training.",
    )
    parser.add_argument(
        "-dn",
        "--dataset-name",
        dest="dataset_name",
        default="not-defined",
        type=str,
        help="Name of the dataset. This will be the name of the final mdoel.",
    )

    parser.add_argument(
        "--target_dir",
        dest="lm_root_dir",
        required=True,
        help="target directory for language model",
    )
    parser.add_argument(
        "--dataset_path",
        dest="dataset_path",
        required=True,
        help="Path to the transcripts file (in kaldi format)",
    )

    parser.set_defaults(func=main)
    args = parser.parse_args()
    args.func(**vars(args))
