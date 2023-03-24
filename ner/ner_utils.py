#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script with some utils functions to train and evaluate a NER model. 
We fine-tune a pretrained BERT-base-uncased model* fetched from HuggingFace.

* Other models can be used as well, e.g., bert-base-cased
BERT paper (ours): https://arxiv.org/abs/1810.04805
HuggingFace repository: https://huggingface.co/bert-base-uncased
"""

import numpy as np
import torch
from sklearn.metrics import classification_report, jaccard_score


class ATCDataset_for_ner(torch.utils.data.Dataset):
    """Standard dataset object used by PyTorch and Huggingface.
    We use it to load the data for training and fine-tuning.
    """

    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


def encode_tags(tag2id, tags, encodings):
    """Function to encode the tags in the format needed by the model.
    This is due to using of subword units
    """

    labels = [[tag2id[tag] for tag in doc] for doc in tags]
    encoded_labels = []
    cnt = 0
    for doc_labels, doc_offset in zip(labels, encodings.offset_mapping):

        # create an empty array of -100, not used during loss calculation
        doc_enc_labels = np.ones(len(doc_offset), dtype=int) * -100
        arr_offset = np.array(doc_offset)
        try:
            doc_enc_labels[
                (arr_offset[:, 0] == 0) & (arr_offset[:, 1] != 0)
            ] = doc_labels
        except:
            print(f"Error generating the encoding of line: {cnt}")
            continue
        encoded_labels.append(doc_enc_labels.tolist())
        cnt += 1

    return encoded_labels


def clean_input_utterance(input_text):
    """Function to clean the input utterance
    Inputs:
        - input text
    Output:
        - cleaned text
    """
    # remove all the words starting with <> or [],
    sequence = " ".join(filter(lambda x: x[0] != "<", input_text.rstrip().split()))
    sequence = " ".join(filter(lambda x: x[-1] != ">", sequence.split()))
    sequence = " ".join(filter(lambda x: x[0] != "[", sequence.split()))
    sequence = " ".join(filter(lambda x: x[-1] != "]", sequence.split()))

    # remove the greetings in ATCO2 format dobry_den_(greet)
    sequence = " ".join(filter(lambda x: "(" not in x, sequence.split()))
    return sequence


def read_atc_ner_data(file_path, max_seq_len=120):
    """Function to read a ATC text file with speaker roles tags to train NER system.
    This function is only meant for training purposes ideally we will create a
    PyTorch dataset object with the data for faster loading.

    max_seq_len: max number of words in the sequence, otherwise
        we might get out-of-memmory issues
    """

    token_docs = []
    tag_docs = []
    with open(file_path, "r", encoding="utf8") as f:
        for sample in f:
            line = sample.strip().split(";")

            # getting the text and tags (separated by ',')
            text = line[1].rstrip().split(" ")
            tags = line[2].rstrip().split(",")

            if len(text) > max_seq_len:
                continue
            token_docs.append(text)
            tag_docs.append(tags)

    return token_docs, tag_docs


def compute_metrics_sklearn(p):
    """Compute basic metrics (accuracy, precision, recall and F1-score
    for the input p = [y_pred y_labels]
    """
    pred, labels = p

    # metrics related to token classification with different classes
    jaccard_s = jaccard_score(y_true=labels, y_pred=pred, average=None)
    jaccard_weighted = jaccard_score(y_true=labels, y_pred=pred, average="weighted")

    report = classification_report(y_true=labels, y_pred=pred)

    # get report of merged classes
    pred = ["O" if i == "O" else i.split("-")[1] for i in p[0]]
    labels = ["O" if i == "O" else i.split("-")[1] for i in p[1]]

    report_merged = classification_report(y_true=labels, y_pred=pred)

    report = (
        "\t************* Report B/I tags*************\t\n"
        + report
        + "\n \t************ Report with merged classes ***********\t\n"
    )
    report = report + report_merged
    report = report + f"\n\n JACCARD ERROR RATE (JER): {(1 - jaccard_s)*100}"
    report = report + f"\n JER - WEIGHTED          : {(1 - jaccard_weighted)*100} \n\n"

    return report


def compute_metrics(predictions, labels, label_list, log_folder=None):
    """Function to compute the 'seqeval' metric used for NER datasets
    First we load the function and then we evaluate a specific dataset:
    predictions, labels and label_list (id2tag) are used to compute it.
    """
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (special tokens)
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    # producing a classification report
    true_labels2 = [item for sublist in true_labels for item in sublist]
    true_predictions2 = [item for sublist in true_predictions for item in sublist]
    results = compute_metrics_sklearn([true_predictions2, true_labels2])

    # save the metrics in file if log_folder is given, otherwise only print
    if log_folder is not None:
        print(results, file=open(log_folder, "w"))
    else:
        print(results)

    return results
