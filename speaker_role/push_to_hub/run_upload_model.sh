#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to upload a BERT model fine-tuned on the text-classification task to HuggingFace hub
# This model has been fine-tuned on UWB-ATCC CORPUS,
set -euo pipefail

path_to_model="experiments/results/spk_id/bert-base-uncased/1234/uwb_atcc/"
output_folder=".cache/"
repository_name="bert-base-speaker-role-atc-en-uwb-atcc"

. data/utils/parse_options.sh

output_folder=$output_folder/$repository_name
mkdir -p $output_folder

echo "*** Uploading model to HuggingFace hub ***"
echo "*** repository will be stored in: $output_folder ***"

python3 speaker_role/push_to_hub/upload_sequence_classification_model.py \
  --model "$path_to_model" \
  --output-folder "$output_folder" \
  --output-repo-name "$repository_name"

echo "Done uploading the model in ${path_to_model}"
exit 0
