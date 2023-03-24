#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

DESCRIPTION="Script to upload model to HuggingFace hub"

import argparse
import os
import sys
import subprocess
from pathlib import Path

from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
)

import huggingface_hub
from huggingface_hub import HfApi, create_repo

def parse_args():
    """parser"""
    parser = argparse.ArgumentParser(description=DESCRIPTION,
        usage="Usage: upload_model_with_lm.py --ph True --model /path/to/model/checkpoint"
    )

    # must give,
    parser.add_argument(
        "--output-repo-name",
        dest="output_repo_name",
        required=True,
        help="name of the output repository name, e.g., bert-base-ner-atc-en-atco2-1h",
    )
    parser.add_argument(
        "--model",
        "--finetuned-model",
        dest="path_model",
        required=True,
        help="Directory with pre-trained BERT model.",
    )
    parser.add_argument(
        "--of",
        "--output-folder",
        dest="output_folder",
        required=True,
        help="Directory where to put the model with its model-card.",
    )

    return parser.parse_args()

def main():
    """Main code execution"""
    args = parse_args()

    path_model = args.path_model + '/'
    path_output_dir = args.output_folder

    # get the repo_id name, based on <args>,
    output_repo_name = args.output_repo_name
    get_user_name = huggingface_hub.whoami()['name']
    repo_id = f"{get_user_name}/{output_repo_name}"

    if not Path(path_model + "/pytorch_model.bin").is_file():
        print(f"You pass a path to model, but pytorch_model.bin is not present. Exit")
        sys.exit(1)

    # create the output folder if is not present
    if len(os.listdir(path_output_dir)) > 0:
        print(f"you passed a non-empty folder ({path_output_dir}), this cannot be managed automatically by HF.")
        sys.exit(1)

    # First, create the repo in HuggingFace-Hub, we fetch the local username 
    try:
        create_repo(repo_id=repo_id, repo_type="model")
    except Exception as e:
        print(f"Repo already create, the error was: \n{e}")
        print(f"\n we continue...")

    print("*** copying model to output folder, loading... ***")    

    if Path(path_output_dir + '/pytorch_model.bin').is_file():
        print("pytorch_model.bin is already present in the output folder, not copying it")
        print(f"output folder is: {path_output_dir}")
    else:
        print(f"Copying the model folder to: {path_output_dir}")
        # copy the folder with the model and log subfolder
        subprocess.run(
            f"cp {path_model}/* {path_output_dir}/", 
            shell=True, 
            stderr=sys.stderr, 
            stdout=sys.stdout
        )
        subprocess.run(
            f"cp -r {path_model}/log {path_output_dir}/", 
            shell=True, 
            stderr=sys.stderr,
            stdout=sys.stdout
        )
    
    print("*** Loading the fine-tuned model (bert-base-uncased), loading... ***")
    # Fetch the Model and tokenizer
    eval_model = AutoModelForTokenClassification.from_pretrained(path_model)
    tokenizer = AutoTokenizer.from_pretrained(path_model)

    print(f"*** Storing model and tokenizer into {path_output_dir}... ***")

    eval_model.save_pretrained(path_output_dir)
    tokenizer.save_pretrained(path_output_dir)
    
    print("*** Uploading the model to HuggingFace Hub... ***")
    api = HfApi()
    api.upload_folder(
        folder_path=path_output_dir,
        repo_id=repo_id,
        repo_type="model",
        ignore_patterns="**/checkpoint-*",
        commit_message="updating the repo with the fine-tuned model"
    )

    return None


if __name__ == "__main__":
    main()
