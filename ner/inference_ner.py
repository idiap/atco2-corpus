#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to perform ONLY INFERENCE with a fine-tuned named entity recognition model. 
The model is built by fine-tuning a pretrained BERT-base-uncased model* fetched from HuggingFace.

- We perform inference to either generate the labels of a sentence or to evaluate a given file

* Other models can be used as well, e.g., bert-base-cased
BERT paper (ours): https://arxiv.org/abs/1810.04805
HuggingFace repository: https://huggingface.co/bert-base-uncased
"""

import argparse
import os

import numpy as np
import torch
from ner_utils import clean_input_utterance
from transformers import BertForTokenClassification, BertTokenizerFast, pipeline


def convert_to_utt2text_tags(predictions):
    """convert the pipeline output of HuggingFace to text and tags"""

    outputs = []
    for prediction in predictions:
        text_list = []
        tags_list = []
        for sample in prediction:
            # extract data
            entity = sample["entity_group"]

            # get the transcript and fix normalization
            word = sample["word"].rstrip()
            word = word.replace("x - ray", "x-ray") if "x - ray" in word else word
            word = word.replace(" ' ", "'") if "x - ray" in word else word
            word = word.split()

            # get the tags
            tags = np.full(shape=len(word), fill_value="I-" + entity)
            tags[0] = "B-" + entity

            # append text and tags
            text_list.append(word)
            tags_list.append(tags)
        # flatten the list
        text_list = [x for xs in text_list for x in xs]
        tags_list = [x for xs in tags_list for x in xs]
        assert len(text_list) == len(tags_list), "text and tags list have differnt size"

        # create the final object
        outputs.append({"text": text_list, "tags": tags_list})

    return outputs


class ATCDataset(torch.utils.data.Dataset):
    """\
    Dataset for NER of ATC data. We will extract the main entities, like
    callsign, command or values.
    """

    def __init__(self, path_to_file):

        sequences = []
        utt_id = []
        encodings = []

        with open(path_to_file, "r") as rd:
            # check if using utt2text_tags, the transcript is on column 4
            # otherwise is in column 2 [uttid text]
            is_utt2text_tags = True if "utt2text_tags" in path_to_file else False

            for line in rd:

                if is_utt2text_tags:
                    ids = line.split(";")[0].rstrip()
                    # clean the input utterance
                    sample = clean_input_utterance(line.split(";")[1].rstrip())
                else:
                    ids = line.split(" ")[0].rstrip()
                    # clean the input utterance
                    sample = clean_input_utterance(
                        " ".join(line.split(" ")[1:]).rstrip()
                    )

                # continue if sample is empty
                if sample == "" or sample == " ":
                    continue

                # append to output dictionaries
                sequences.append(sample)
                utt_id.append(ids)
                encodings.append([ids, sample])

        self.sequences = sequences
        self.utt_id = utt_id
        self.encodings = encodings

    def __getitem__(self, idx):
        item = self.encodings[idx]
        return item

    def __len__(self):
        return len(self.sequences)


def parse_args():
    parser = argparse.ArgumentParser()

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
        "-o", "--output-folder", required=True, help="Folder where to store the outputs"
    )

    return parser.parse_args()


def main(args):
    """Main code execution"""

    # input model and some detailed outputs
    token_classification_model = args.input_model
    path_to_files = args.input_files.rstrip().split(" ")
    test_set_names = args.test_names.rstrip().split(" ")
    output_folder = args.output_folder

    # evaluating that the number of test set names matches the amount of paths passed:
    assert len(path_to_files) == len(
        test_set_names
    ), "number of test files and their names differ"

    # create the output directory, in 'evaluations folder'
    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    # Fetch the Model and tokenizer
    print("\nLoading the TOKEN classification recognition model (NER)\n")
    eval_model = BertForTokenClassification.from_pretrained(token_classification_model)
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

    # Pipeline for sequence classification
    seq_cla = pipeline(
        "token-classification",
        model=eval_model,
        tokenizer=tokenizer,
        aggregation_strategy="average",
        ignore_labels=["O"],
    )

    # main loop,
    for path_to_file, dataset_name in zip(path_to_files, test_set_names):

        print(f"******  NAMED-ENTITY RECOGNITION (for ATC)  ******")
        print(f"----    Evaluating dataset: --> {dataset_name} -----")

        # create the dataset and DataLoader objects
        test_dataset = ATCDataset(path_to_file)
        dataLoader_ATC = torch.utils.data.DataLoader(
            test_dataset, batch_size=args.batch_size, shuffle=False
        )

        inference_out, utt_ids_out = [], []
        # run inference on the whole database
        for local_batch in dataLoader_ATC:
            utt_ids_out += local_batch[0]
            inference = seq_cla(list(local_batch[1]), batch_size=args.batch_size)
            inference_out += convert_to_utt2text_tags(inference)

        # join the predictions
        output_dict = []
        for ids, predictions in zip(utt_ids_out, inference_out):
            text = " ".join(predictions["text"])
            tags = ",".join(predictions["tags"])
            output_dict.append(f"{ids};{text};{tags}")

        # print the results in a txt file
        path_to_output_file = f"{output_folder}/{dataset_name}_inference"

        print("\n".join(map(str, output_dict)), file=open(path_to_output_file, "w"))
        print(
            f"Done performing inference on: {dataset_name}. Output in: '{path_to_output_file}'"
        )
        print(f"Done. Outputs in {output_folder}")


if __name__ == "__main__":
    args = parse_args()
    main(args)
