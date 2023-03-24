#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to evaluate a sequence classification model. The model is built by
fine-tuning a pretrained BERT-base-uncased model* fetched from HuggingFace.

The format of the test set should be:
<id> <0/1> <atco/pilot> <transcript/ground truth>

* Other models can be used as well, e.g., bert-base-cased
BERT paper (ours): https://arxiv.org/abs/1810.04805
HuggingFace repository: https://huggingface.co/bert-base-uncased
"""

import argparse
import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from sec_classification_utils import (
    clean_input_utterance,
    eval_dataset,
    get_index_value,
)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-pm",
        "--print-metrics",
        action="store_true",
        help="Flag whether to print an output file, if set you need to pass an utt2spkid file",
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
        help="String with paths to text or utt2spk_id files to be evaluated, it needs to match the 'test_names' variales",
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


def batch(input_list, batch=1):
    """Iterator to go efficiently across the list of utterances to perform
    inference.
    input_list: input list with utterances
    batch: batch size
    """
    l = len(input_list)
    for ndx in range(0, l, batch):
        yield input_list[ndx : min(ndx + batch, l)]


def main():
    """Main code execution"""
    args = parse_args()

    # input model and some detailed outputs
    sec_classification_model = args.input_model
    path_to_files = args.input_files.rstrip().split(" ")
    test_set_names = args.test_names.rstrip().split(" ")
    output_folder = args.output_folder

    # evaluating that the number of test set names matches the amount of paths
    # passed:
    assert len(path_to_files) == len(
        test_set_names
    ), "you gave different number of paths and test sets"

    # create the output directory, in 'evaluations folder'
    os.makedirs(output_folder, exist_ok=True)

    print("\nLoading the sequence classification recognition model (speaker ID)\n")
    # Fetch the Model and tokenizer
    eval_model = AutoModelForSequenceClassification.from_pretrained(
        sec_classification_model
    )
    tokenizer = AutoTokenizer.from_pretrained(
        sec_classification_model, use_fast=True, do_lower_case=True
    )

    # get the labels of the model
    tag2id = eval_model.config.label2id
    id2tag = eval_model.config.id2label

    # Pipeline for sequence classification
    seq_cla = pipeline(
        "text-classification",
        model=eval_model,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1,
    )

    # main loop,
    for path_to_file, dataset_name in zip(path_to_files, test_set_names):

        print("         ******SEQUENCE CLASSIFICATION****** ")
        print(f"----    Evaluating dataset --> {dataset_name} -----")

        # where to store the input data
        sequences = []
        utt_id = []

        # loading the data into memory
        with open(path_to_file, "r") as rd:
            column_id = 3 if "utt2spk_id" in path_to_file else 1
            for line in rd:
                ids = line.split(" ")[0].rstrip()

                # clean the input utterance
                sample = clean_input_utterance(
                    " ".join(line.split(" ")[column_id:]).rstrip()
                )

                # continue if sample is empty
                if sample == "" or sample == " ":
                    continue

                # append the output
                sequences.append(sample)
                utt_id.append(line.split(" ")[0])

        print("Loaded dataset into memory (text or utt2spk_id)")

        # run once the sequence classification system
        inference_out = []
        output_dict = []

        # print the results in a txt file
        path_to_output_file = f"{output_folder}/{dataset_name}_utt2spk_id_extracted"

        # there are two options, either we evaluate or we do inference
        if "utt2spk_id" in path_to_file:
            #  we perform inference and evaluate
            perf_metrics, scores = eval_dataset(eval_model, tokenizer, path_to_file)

            metrics_file = open(f"{output_folder}/{dataset_name}_metrics", "w")
            metrics_file.write(f"\nEvaluation of model:{sec_classification_model}\n")
            metrics_file.write(f"\n TEST DATASET: {dataset_name}\n")
            metrics_file.write(f"{perf_metrics['report']}")
            metrics_file.close()

            # get the indices and value confides
            indices, scores = get_index_value(scores)
            inference_out = [
                {"label": idx, "score": score} for idx, score in zip(indices, scores)
            ]

        # you passed a 'text' file, only inference
        else:
            if args.print_metrics:
                for x in batch(sequences, args.batch_size):
                    inference = seq_cla(x, batch_size=args.batch_size)
                    inference_out += inference
            else:
                print(
                    "you paseed and only 'text' file and did not set --print-metrics flag... exit"
                )

        if args.print_metrics:
            # printing the inference data
            for utterance, transcript, seqcla_output in zip(
                utt_id, sequences, inference_out
            ):
                # Assemble the output one by one
                spk_id = f"{seqcla_output['label']}"
                confidence = f"{seqcla_output['score']:.2f}"

                output_dict.append(f"{utterance} {spk_id} {confidence} {transcript}")

            # print the inference file
            print("\n".join(map(str, output_dict)), file=open(path_to_output_file, "w"))
        else:
            print("Not doing evaluation because of the flag given")
            continue

if __name__ == "__main__":
    main()