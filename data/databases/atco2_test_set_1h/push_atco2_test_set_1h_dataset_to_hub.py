#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

DESCRIPTION="""\
Script to push the ATCO2-TEST-SET-1H dataset to HuggingFace Hub. 
You can download a free 1-hour sample in: https://www.replaywell.com/atco2/download/ATCO2-ASRdataset-v1_beta.tgz
"""
import os

from datasets import DatasetDict, load_dataset
import huggingface_hub
from huggingface_hub import HfApi

# global variable, where the data loader script is located:
_LOADER_SCRIPT = "asr_e2e/atc_data_loader.py"
_DATASET_NAME = "atco2_test_set_1h"
_DATA_FOLDER = "experiments/data/other"

def main():
    """ function to load a dataset and then push it to the HuggingFace-Hub"""

    # 1. First, get the information where to store the dataset
    get_user_name = huggingface_hub.whoami()['name']
    # repo name:
    dataset_repo_id = f"{get_user_name}/atco2_corpus_1h"

    # 2. Second, let's load the dataset, train and test splits
    raw_datasets = DatasetDict()

    raw_datasets["test"] = load_dataset(
        _LOADER_SCRIPT,
        "test",
        data_dir=os.path.join(_DATA_FOLDER,_DATASET_NAME),
        split="test",
        keep_in_memory=True,
        )
    
    # remove this column that is not neccesary:
    raw_datasets = raw_datasets.remove_columns('file')

    # 3. Third, push the dataset to the hub, set to private for now. 
    # We should open-access the dataset later, directly in HF platform.
    raw_datasets.push_to_hub(dataset_repo_id, private=True)

    # 4. Upload the loader script to the dataset folder:
    api = HfApi()
    api.upload_file(
        path_or_fileobj=_LOADER_SCRIPT,
        path_in_repo="atc_data_loader.py",
        repo_id=dataset_repo_id,
        repo_type="dataset",
        commit_message="updating the repo with the loader script"
    )
   
    return print("pushed to hub the ATCO2-TEST-SET-1H dataset succesfully")

if __name__ == "__main__":
    main()
