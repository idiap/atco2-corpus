#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Script to evaluate one named entity recognition model based on BERT
# The default database is ATCO2-test-set-1h, as it is completly free! 
# You can download it from ReplayWell by following this link: https://www.replaywell.com/atco2/download/ATCO2-ASRdataset-v1_beta.tgz

set -euo pipefail

# static vars
cmd='none'
DATA=experiments/data/other

# model related vars
batch_size=10

# vars of the model and input/output folder
input_model=bert-base-uncased
dataset=atco2_test_set_1h
seed=1234
output_dir=experiments/results/ner/baseline

# with this we can parse options to this script
. data/utils/parse_options.sh

# Evaluate on the dataset available for free! 
test_set_atco2_1h=$DATA/$dataset/ner/5_kfold/test_fold1.csv
input_files="$test_set_atco2_1h"
test_names="$dataset"

# You can uncomment test_set_atco2_4h if you do have access to it
# test_set_atco2_4h=$DATA/atco2_test_set_4h/ner/5_kfold/test_fold1.csv
# input_files="$test_set_atco2_1h $test_set_atco2_4h"
# test_names="$dataset atco2_test_set_4h"

output_folder=$output_dir/$input_model/$seed/$dataset

# configure a GPU to use if we a defined 'CMD'
if [ ! "$cmd" == 'none' ]; then
  basename=inference_${dataset}_${seed}_${input_model}
  cmd="$cmd -N ${basename} ${output_folder}/inference/log/eval.log"
else
  cmd=''
fi

mkdir -p $output_folder/inference
# running the command
$cmd python3 ner/inference_ner.py \
  --input-model "$output_folder/" \
  --batch-size $batch_size \
  --input-files "$input_files" --test-names "$test_names" \
  --output-folder $output_folder/inference

echo "Done performing inference in the model with dataset: $dataset"
exit 0