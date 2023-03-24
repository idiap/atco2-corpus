#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to evaluate a NER model. The model is built by
fine-tuning a pretrained BERT-base-uncased model* fetched from HuggingFace.

* Other models can be used as well, e.g., bert-base-cased
BERT paper (ours): https://arxiv.org/abs/1810.04805
HuggingFace repository: https://huggingface.co/bert-base-uncased
"""

import argparse
import os

from ner_utils import (
    ATCDataset_for_ner,
    compute_metrics,
    encode_tags,
    read_atc_ner_data,
)
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-pm",
        "--print-metrics",
        action="store_true",
        help="Flag whether to print an output file, if set you need to pass an utt2text_tags file",
    )

    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=1,
        help="Batch size you want to use for decoding",
    )

    parser.add_argument(
        "-m",
        "--input-model",
        required=True,
        help="Folder where the final model is stored",
    )
    parser.add_argument(
        "-i",
        "--input-files",
        required=True,
        help="String with paths to text or utt2text_tags files to be evaluated, it needs to match the 'test_names' variables",
    )
    parser.add_argument(
        "-n",
        "--test-names",
        required=True,
        help="Name of the test sets to be evaluated",
    )

    parser.add_argument(
        "-o",
        "--output-folder",
        required=True,
        help="Folder where the final model is stored",
    )

    return parser.parse_args()


def main(args):
    """Main code execution"""

    # input model and some detailed outputs
    token_classification_model = args.input_model
    path_to_files = args.input_files.rstrip().split(" ")
    test_set_names = args.test_names.rstrip().split(" ")
    output_folder = args.output_folder

    # evaluating that the number of test set names matches the amount of paths passed
    assert len(path_to_files) == len(
        test_set_names
    ), "number of test files and their names differ"

    # create the output directory, in 'evaluations folder'
    os.makedirs(os.path.dirname(output_folder) + "/evaluations", exist_ok=True)

    # Fetch the Model and tokenizer
    print("\nLoading the TOKEN classification recognition model (NER)\n")
    eval_model = AutoModelForTokenClassification.from_pretrained(
        token_classification_model
    )
    tokenizer = AutoTokenizer.from_pretrained(
        token_classification_model, use_fast=True, do_lower_case=True
    )

    # get the labels of the model
    tag2id = eval_model.config.label2id
    id2tag = eval_model.config.id2label

    # Trainer, only  instantiated for testing, and using standard DataCollator,
    trainer = Trainer(
        model=eval_model, data_collator=DataCollatorWithPadding(tokenizer)
    )

    # main loop,
    for path_to_file, dataset_name in zip(path_to_files, test_set_names):

        print(f"******  NAMED-ENTITY RECOGNITION (for ATC)  ******")
        print(f"----    Evaluating dataset: --> {dataset_name} -----")

        # converting the data to model's format,
        eval_texts, eval_tags = read_atc_ner_data(path_to_file)

        # Tokenize, pad and package data for forward pass,
        eval_encodings = tokenizer(
            eval_texts,
            is_split_into_words=True,
            return_offsets_mapping=True,
            padding=True,
            truncation=True,
        )
        eval_labels = encode_tags(tag2id, eval_tags, eval_encodings)
        eval_encodings.pop("offset_mapping")  # we don't want to pass this to the model
        eval_dataset = ATCDataset_for_ner(eval_encodings, eval_labels)

        # run forward pass, evaluate and, print the metrics
        raw_pred, raw_labels, _ = trainer.predict(eval_dataset)
        path_to_output_file = f"{output_folder}/{dataset_name}_metrics"

        metrics = compute_metrics(
            raw_pred, raw_labels, label_list=id2tag, log_folder=path_to_output_file
        )


if __name__ == "__main__":
    args = parse_args()
    main(args)
