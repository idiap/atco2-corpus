#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

# File with some utils for the train/eval Sequence Classification scripts
#   - Speaker ID from ASR/ground truth transcripts (NLP-based)

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import DataCollatorWithPadding, Trainer


class ATCO2Dataset_seqcla(torch.utils.data.Dataset):
    """Dataset for Sequence Classification of ATC data.
    We will classify whether the ATC transcript is from
    Pilot or ATCO.
    """

    def __init__(self, encodings, labels=None):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        if self.labels:
            item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.encodings["input_ids"])


def clean_input_utterance(input_text):
    """Function to clean the input utterance
    Inputs:
        - input text
    Output:
        - cleaned text
    """
    # remove all the words starting with <> or [],
    sequence = " ".join(filter(lambda x: x[0] != "<", input_text.strip().split()))
    sequence = " ".join(filter(lambda x: x[-1] != ">", sequence.split()))
    sequence = " ".join(filter(lambda x: x[0] != "[", sequence.split()))
    sequence = " ".join(filter(lambda x: x[-1] != "]", sequence.split()))

    # remove the greetings in ATCO2 format dobry_den_(greet)
    sequence = " ".join(filter(lambda x: "(" not in x, sequence.split()))
    return sequence.lower()


def load_data_from_text_file(path_to_data):
    """Function to load the data for Sequence Classification task.
    The input path is converted in the format required by the model
    and the torch.utils.data.Dataset module
    """
    data, spk_id, tags = [], [], []

    with open(path_to_data, "r") as utt2spk_id:
        for line in utt2spk_id:
            
            # clean the input utterance
            sample = clean_input_utterance(" ".join(line.split(" ")[3:]).rstrip())
            
            # Get the data, spk_id and tags in lists
            data.append(sample.lower())
            spk_id.append(int(line.split(" ")[1]))
            tags.append(line.split(" ")[2])

    return data, spk_id, tags

def compute_metrics(p):
    """Compute basic metrics (accuracy, precision, recall and F1-score
    for the input p = [y_pred y_labels]
    """
    pred, labels = p
    pred = np.argmax(pred, axis=1)

    # computing several metrics
    accuracy = accuracy_score(y_true=labels, y_pred=pred)
    recall = recall_score(y_true=labels, y_pred=pred)
    precision = precision_score(y_true=labels, y_pred=pred)
    f1 = f1_score(y_true=labels, y_pred=pred)
    report = classification_report(y_true=labels, y_pred=pred)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "report": report,
    }


def eval_dataset(model_ojb, tokenizer, path_eval_data):
    """Function to eval a given dataset.
    Inputs:
        - model, object of the model
        - path to eval dataset
    """
    # Load test data
    eval_data, eval_spk_id, eval_tags = load_data_from_text_file(path_eval_data)
    X_test_tokenized = tokenizer(eval_data, padding="max_length", truncation=True)

    # Create torch dataset
    test_dataset = ATCO2Dataset_seqcla(X_test_tokenized)

    # data collator
    data_collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)

    # Define test trainer
    test_trainer = Trainer(model_ojb, data_collator=data_collator)

    # Make prediction
    raw_pred, _, _ = test_trainer.predict(test_dataset)
    # Preprocess the labels
    y_lbl = np.array(eval_spk_id)
    # Obtain the results:
    results = compute_metrics([raw_pred, y_lbl])

    return results, raw_pred
