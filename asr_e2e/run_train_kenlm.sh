#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to train a (default) 4-gram LM with KenLM toolkit for fusing with PyCTCdecode and Transformers
#######################################
# COMMAND LINE OPTIONS,
set -euo pipefail

dataset_name="atco2_pl_set"
text_file="experiments/data/atco2_pl_set/train/text"
n_gram_order="4"

. data/utils/parse_options.sh

output_lmdir=$(dirname $text_file)/lm

echo "*** About to start the KenLM ***"
echo "*** Dataset name: $dataset_name ***"
echo "*** Output folder: $output_lmdir ***"

python3 asr_e2e/train_kenlm.py \
  --n-gram "${n_gram_order}" \
  --dataset-name "$dataset_name" \
  --dataset_path "$text_file" \
  --target_dir "$output_lmdir"

echo "Done training ${n_gram_order}-gram in $output_lmdir"
exit 0
