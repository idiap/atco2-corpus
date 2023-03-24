#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to train a sequence classification recognition model. The model is built by
fine-tuning a pretrained BERT-base-uncased model* fetched from HuggingFace.

The format of the train/dev/test sets should be:
<id> <0/1> <atco/pilot> <transcript/ground truth>

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
from sklearn.model_selection import train_test_split

# importing all utils functions for ATC datasets
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from sec_classification_utils import (
    ATCO2Dataset_seqcla,
    compute_metrics,
    load_data_from_text_file,
)

logger = logging.getLogger(__name__)

# Define the tags of the model (in this case is only atco/pilot)
tag2id = {"atco": 0, "pilot": 1}
id2tag = {0: "atco", 1: "pilot"}

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
        default=4,
        help="Number of epochs of fine-tuning/training",
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=7778, help="Seed for training"
    )
    parser.add_argument(
        "-tb", "--train-batch-size", type=int, default=16, help="Training batch size"
    )
    parser.add_argument(
        "-eb", "--eval-batch-size", type=int, default=10, help="Evaluation batch size"
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
        default=5000,
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
        help="Validation text data for Seq Classification model (utt2spk_id)",
    )
    parser.add_argument(
        "--test-data",
        default=None,
        help="TEST data for Seq Classification model (utt2spk_id)",
    )

    parser.add_argument(
        "train_data",
        help="Train text data for sequence classification model (utt2spk_id)",
    )
    parser.add_argument(
        "output_folder",
        help="name of the output folder to store the sequence classification model and tokenizer",
    )
    return parser.parse_args()


def main():
    """Main code execution"""
    args = parse_args()

    # Setup logging
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

    # change "model name" to use another NLP system from Huggingface
    model_name = (
        args.input_model if args.input_model is not None else "bert-base-uncased"
    )
    output_directory = args.output_folder

    # Fetch the model (seq classification) and tokenizer
    #   - If you define an input_mode, tokenizer should be there as well
    num_labels = len(tag2id)
    
    logger.info("*** Loading the Tokenizer (FastTokenizer) ***")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, use_fast=True, do_lower_case=True
    )
    
    # Fetch the Sequence Classification model
    logger.info("*** Loading the Sequence Classification model ***")
    base_model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=num_labels
    )

    # Modify the configuration that contains the labels2ID mapping
    base_model.config.label2id = tag2id
    base_model.config.id2label = id2tag

    # read train and validation data
    # split the train data in case there is not val data available
    if args.val_data == "" or args.val_data == None:
        train_data, train_spk_id, train_tags = load_data_from_text_file(args.train_data)
        (
            train_data,
            val_data,
            train_spk_id,
            val_spk_id,
            train_tags,
            val_tags,
        ) = train_test_split(train_data, train_spk_id, train_tags, test_size=0.1)
    else:
        train_data, train_spk_id, train_tags = load_data_from_text_file(args.train_data)
        val_data, val_spk_id, val_tags = load_data_from_text_file(args.val_data)

    # Tokenize the train and validation data
    X_train_tokenized = tokenizer(train_data, padding="max_length", truncation=True)
    X_val_tokenized = tokenizer(val_data, padding="max_length", truncation=True)

    # Create the Dataset object
    train_dataset = ATCO2Dataset_seqcla(X_train_tokenized, train_spk_id)
    val_dataset = ATCO2Dataset_seqcla(X_val_tokenized, val_spk_id)

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
        test_data, test_spk_id, test_tags = load_data_from_text_file(args.test_data)
        X_test_tokenized = tokenizer(test_data, padding="max_length", truncation=True)
        test_dataset = ATCO2Dataset_seqcla(X_test_tokenized, test_spk_id)
    else:
        test_dataset, test_spk_id, test_tags = val_dataset, val_spk_id, val_tags

    # Standard DataCollator
    data_collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)

    # Define TrainingArguments for Trainer object
    args = TrainingArguments(
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
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        data_collator=data_collator,
    )

    logger.info("*** Training ***")
    # Train pre-trained model
    train_results = trainer.train()
    metrics = train_results.metrics

    # saving the final model and tokenizer after training it,
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    trainer.save_model(output_dir=f"{output_directory}/")
    tokenizer.save_pretrained(f"{output_directory}/")

    # Performing a last evaluation of the dev dataset
    logger.info("*** Evaluate ***")

    # Make prediction
    raw_pred, _, _ = trainer.predict(test_dataset)

    # Obtain the results:
    f_metrics = compute_metrics([raw_pred, np.array(test_spk_id)])
    print(f"Validation set metrics:\n {f_metrics}")

    kwargs = {
        "finetuned_from": model_name,
        "tasks": "sequence-classification",
    }
    trainer.create_model_card(**kwargs)

if __name__ == "__main__":
    main()
