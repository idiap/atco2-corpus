#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# script to train one system based for Text-based SPEAKER ID for ATC data 
set -euo pipefail

# static vars
cmd='none'

# reporting:
report_to=none

# model related vars
input_model=bert-base-uncased

# training params
epochs=4
seed=1234
train_batch_size=32
eval_batch_size=16
gradient_accumulation_steps=2
warmup_steps=500
logging_steps=1000
eval_steps=500
save_steps=30000
max_steps=3000

# default is -1, which means using the full set
max_number_of_samples="-1"
output_dir=experiments/results/spk_id

# data folder: default dataset for training is UWB-ATCC (it is free!) 
# data folder test: default is UWB-ATCC, however, you can use ATCO2-test-set-1h (as it is free access!)
dataset=uwb_atcc
# dataset=atco2_test_set_1h
train_data=experiments/data/other/$dataset/train/spkid_exp/utt2spk_id
test_data=experiments/data/other/$dataset/test/spkid_exp/utt2spk_id

# empty, pass it in CLI
validation_data=''

# with this we can parse options to this script
. ./utils/parse_options.sh

# if the number of training samples is less 1000, we do training for less steps
if ((  $max_number_of_samples < 1000 )); then
  if ((  $max_number_of_samples > 0 )); then
    max_steps=2500
  fi
fi

output_folder=$output_dir/$(basename $input_model)/$seed/$dataset

# configure a GPU to use if we define 'CMD'
if [ ! "$cmd" == 'none' ]; then
  basename=train_${dataset}_${seed}_${max_steps}steps_${max_number_of_samples}samples
  cmd="$cmd -N ${basename} ${output_folder}/log/${basename}.log"
else
  cmd=''
fi

$cmd python3 speaker_role/train_sec_classification.py \
  --report-to $report_to \
  --epochs $epochs \
  --seed $seed \
  --max-train-samples $max_number_of_samples \
  --train-batch-size $train_batch_size \
  --eval-batch-size $eval_batch_size \
  --gradient-accumulation-steps $gradient_accumulation_steps \
  --warmup-steps $warmup_steps \
  --logging-steps $logging_steps \
  --save-steps $save_steps \
  --eval-steps $eval_steps \
  --max-steps $max_steps \
  --input-model $input_model \
  --test-data $test_data \
  $train_data $output_folder

echo "Done training a $input_model model with $dataset corpus (for sequence classification)"
exit 0
