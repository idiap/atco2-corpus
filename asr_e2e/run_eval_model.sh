#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to evaluate a Wav2Vec 2.0 model with PyCTCdecode and Transformers
#######################################
# COMMAND LINE OPTIONS,
set -euo pipefail

path_to_lm="experiments/data/atco2_pl_set/train/lm/atco2_pl_set_4g.binary"
path_to_model="experiments/results/baseline/wav2vec2-xls-r-300m/atco2_pl_set/0.0ld_0.0ad_0.0attd_0.0fpd_0.01mtp_12mtl_0.0mfp_12mfl_2acc/checkpoint-10000"
test_set="experiments/data/atco2_test_set_4h/"

print_output="true"

. data/utils/parse_options.sh

echo "*** About to evaluate a Wav2Vec 2.0 model***"
echo "*** Dataset in: $test_set ***"
echo "*** Output folder: $(dirname $path_to_model)/output ***"

python3 asr_e2e/eval_model.py \
  --language-model "$path_to_lm" \
  --pretrained-model "$path_to_model" \
  --print-output "$print_output" \
  --test-set "$test_set"

echo "Done evaluating model in ${path_to_model} with LM"
exit 0
