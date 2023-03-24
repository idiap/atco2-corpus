#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to upload a BERT model fine-tuned on the token-classification task to HuggingFace hub
# This model has been fine-tuned on ATCO2-test-set-1h corpus. The subset corpus open-sourced for free!!,
set -euo pipefail

path_to_model="experiments/results/ner/baseline/bert-base-uncased/1234/atco2_test_set_1h/"
output_folder=".cache/"
repository_name="bert-base-ner-atc-en-atco2-1h"

. data/utils/parse_options.sh

output_folder=$output_folder/$repository_name
mkdir -p $output_folder

echo "*** Uploading model to HuggingFace hub ***"
echo "*** repository will be stored in: $output_folder ***"

python3 ner/push_to_hub/upload_token_classification_model.py \
  --model "$path_to_model" \
  --output-folder "$output_folder" \
  --output-repo-name "$repository_name"

echo "Done uploading the model in: ${path_to_model}"
exit 0
