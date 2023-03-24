#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to train a named entity recognition model. The model is built by
fine-tuning a pretrained BERT-base-uncased model* fetched from HuggingFace.

The format of the train/dev/test sets should be:
<id>;<text>;<tokens>

* Other models can be used as well, e.g., bert-base-cased
BERT paper (ours): https://arxiv.org/abs/1810.04805
HuggingFace repository: https://huggingface.co/bert-base-uncased
"""

import argparse
import logging
import random
import sys

import datasets
import numpy as np
import torch
import transformers
from datasets import load_metric
from ner_utils import (
    ATCDataset_for_ner,
    compute_metrics,
    encode_tags,
    read_atc_ner_data,
)

# importing all utils functions for ATC datasets
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
    set_seed,
)

logger = logging.getLogger(__name__)

# getting the device (CPU/GPU)
if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"There are {torch.cuda.device_count()} GPU(s) available.")
    print("Device name:", torch.cuda.get_device_name(0))
else:
    print("No GPU available, using the CPU instead.")
    device = -1


def parse_args():
    parser = argparse.ArgumentParser()

    # reporting vars
    parser.add_argument(
        "--report-to",
        type=str,
        default=None,
        help="Where to report the results, you can choose e.g., WANDB",
    )

    # some training parameters
    parser.add_argument(
        "-e",
        "--epochs",
        type=int,
        default=5,
        help="Number of epochs of fine-tuning/training",
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=1234, help="Seed for training"
    )
    parser.add_argument(
        "-tb", "--train-batch-size", type=int, default=32, help="Training batch size"
    )
    parser.add_argument(
        "-eb", "--eval-batch-size", type=int, default=16, help="Evaluation batch size"
    )
    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=1,
        help="Number of gradient accumulation steps",
    )
    parser.add_argument(
        "--warmup-steps", type=int, default=500, help="Number of warm up steps"
    )
    parser.add_argument(
        "--logging-steps", type=int, default=1000, help="Logging steps size"
    )
    parser.add_argument(
        "--save-steps", type=int, default=1000, help="Number of steps to save the model"
    )
    parser.add_argument(
        "--eval-steps", type=int, default=500, help="Perform evaluation each N steps"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=3000,
        help="Maximum number of steps to train the model",
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=-1,
        help="Maximum number of training samples to use during training. pass -1 to use the whole training set",
    )

    parser.add_argument(
        "--input-model",
        default=None,
        help="Path to a previously trained model, to fine tune it",
    )
    parser.add_argument(
        "--val-data",
        default=None,
        help="Validation file for the NER model (utt2text_tags)",
    )
    parser.add_argument(
        "--test-data", default=None, help="Test file for the NER model (utt2text_tags)"
    )

    parser.add_argument(
        "train_data",
        help="Train file used for training the NER model (utt2text_tags)",
    )
    parser.add_argument(
        "output_folder",
        help="name of the output folder to store the NER model and tokenizer",
    )
    return parser.parse_args()


def main(args):
    """Main code execution"""

    # Setup logging (following HuggingFace style)
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    log_level = logging.INFO
    logger.setLevel(log_level)
    datasets.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.enable_default_handler()
    transformers.utils.logging.enable_explicit_format()

    # first, set all the seeds:
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    random.seed(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    set_seed(args.seed)

    # change "model name" to use another NLP system from Huggingface
    model_name = (
        args.input_model if args.input_model is not None else "bert-base-uncased"
    )
    output_directory = args.output_folder

    logger.info("*** Loading the Tokenizer (FastTokenizer) ***")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, use_fast=True, do_lower_case=True
    )

    # read train and validation data
    logger.info("*** Loading and preparing training and validation data ***")

    # read train and validation data
    # split the train data in case there is not val data available
    if args.val_data == "" or args.val_data == None:
        logger.info(
            "*** You did not give validation data, splitting it in train/dev from train ***"
        )
        train_texts, train_tags = read_atc_ner_data(args.train_data)

        # getting max number of samples in the val set:
        percentage = 0.1 if len(train_texts) < 100000 else 5000 / len(train_texts)
        logger.info(f"*** taking {percentage*100}% of train data for dev set ***")

        train_texts, val_texts, train_tags, val_tags = train_test_split(
            train_texts, train_tags, test_size=percentage
        )
    else:
        logger.info("*** Using the validation data file ***")
        train_texts, train_tags = read_atc_ner_data(args.train_data)
        val_texts, val_tags = read_atc_ner_data(args.val_data)

    # create sets with the tags, this will be added into the end model to
    # perform inference (and know which tags correspond to what),
    unique_tags_train = set(tag for doc in train_tags for tag in doc)
    unique_tags_val = set(tag for doc in val_tags for tag in doc)
    unique_tags = unique_tags_train | unique_tags_val
    logger.info(f"*** There are {len(unique_tags)} unique tags ***")

    # we need to add the 'O' label in tag2id: standard in NER systems
    unique_tags.add("O")
    # get the tag2id and id2tag
    tag2id = {tag: id for id, tag in enumerate(unique_tags)}
    id2tag = {id: tag for tag, id in tag2id.items()}

    # Tokenize text and generate encodings
    logger.info("*** Tokenizing the train/val sets ***")
    train_encodings = tokenizer(
        train_texts,
        is_split_into_words=True,
        return_offsets_mapping=True,
        padding=True,
        truncation=True,
    )
    val_encodings = tokenizer(
        val_texts,
        is_split_into_words=True,
        return_offsets_mapping=True,
        padding=True,
        truncation=True,
    )

    train_labels = encode_tags(tag2id, train_tags, train_encodings)
    val_labels = encode_tags(tag2id, val_tags, val_encodings)

    # Last before training, generate train/val datasets
    train_encodings.pop("offset_mapping")  # we don't want to pass this to the model
    val_encodings.pop("offset_mapping")

    # generate the datasets generators
    train_dataset = ATCDataset_for_ner(train_encodings, train_labels)
    val_dataset = ATCDataset_for_ner(val_encodings, val_labels)

    # reduce the data in the training set in case we want to use less samples
    if args.max_train_samples is not None and args.max_train_samples != -1:
        max_train_samples = min(len(train_dataset), args.max_train_samples)
        logger.info(
            f"*** Reducing the training dataset size to: {max_train_samples} ***"
        )

        indices = torch.arange(max_train_samples)
        train_dataset = torch.utils.data.Subset(train_dataset, indices)

    # either, prepare the test set passed or use validation as 'final' test set
    if args.test_data is not None:
        test_texts, test_tags = read_atc_ner_data(args.test_data)
        test_encodings = tokenizer(
            test_texts,
            is_split_into_words=True,
            return_offsets_mapping=True,
            padding=True,
            truncation=True,
        )

        test_labels = encode_tags(tag2id, test_tags, test_encodings)
        test_encodings.pop("offset_mapping")  # we don't want to pass this to the model
        test_dataset = ATCDataset_for_ner(test_encodings, test_labels)
    else:
        test_dataset, test_tags = val_dataset, val_labels

    # Fetch the model (Token Classification)
    logger.info("*** Loading the Token Classification model (NER model) ***")
    base_model = AutoModelForTokenClassification.from_pretrained(
        model_name, num_labels=len(unique_tags)
    )

    # Modify the configuration that contains the labels2ID mapping
    base_model.config.label2id = tag2id
    base_model.config.id2label = id2tag

    # function to compute metrics during training
    def compute_metrics_training(p):
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)
        label_list = id2tag

        # Remove ignored index (special tokens)
        true_predictions = [
            [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        # Metrics
        metric = load_metric("seqeval")
        results = metric.compute(predictions=true_predictions, references=true_labels)

        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    # Define TrainingArguments for Trainer object
    training_args = TrainingArguments(
        report_to=args.report_to,
        output_dir=output_directory,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        load_best_model_at_end=True,
        warmup_steps=args.warmup_steps,
        weight_decay=0.001,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        evaluation_strategy="steps",
        logging_dir=output_directory + "/logs",
        logging_steps=args.logging_steps,
        max_steps=args.max_steps,
        save_steps=args.save_steps,
        eval_steps=args.eval_steps,
        save_total_limit=0,
    )

    # Define Trainer object
    trainer = Trainer(
        model=base_model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics_training,
        data_collator=DataCollatorForTokenClassification(tokenizer),
    )

    # fine-tune the model
    logger.info("*** Training ***")
    train_results = trainer.train()
    metrics = train_results.metrics

    # saving the final model and tokenizer after fine-tuning it,
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()
    trainer.save_model(output_dir=f"{output_directory}/")
    tokenizer.save_pretrained(f"{output_directory}/")

    # Performing a last evaluation of the dev dataset,
    logger.info("*** Evaluate ***")

    # Make prediction and compute metrics,
    raw_pred, raw_labels, _ = trainer.predict(test_dataset)
    metrics = compute_metrics(
        raw_pred,
        raw_labels,
        label_list=id2tag,
        log_folder=f"{output_directory}/classification_report",
    )

    # Creating a model card to upload or to store training metadata,
    kwargs = {
        "finetuned_from": model_name,
        "tasks": "token-classification",
    }
    trainer.create_model_card(**kwargs)


if __name__ == "__main__":
    args = parse_args()
    main(args)
