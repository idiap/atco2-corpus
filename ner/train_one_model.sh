#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# script to train one named entity recognition model based on BERT
# The default database is ATCO2-test-set-1h, as it is completly free! 
# You can download it from ReplayWell by following this link: https://www.replaywell.com/atco2/download/ATCO2-ASRdataset-v1_beta.tgz

# You can pass a qsub command (SunGrid Engine)
#       :an example is passing --cmd "src/sge/queue.pl h='*'-V", add your configuration

set -euo pipefail

# static vars
cmd='none'

# reporting, default=none, you can use Weight & Biases, report_to=wandb
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
output_dir=experiments/results/ner/baseline

# data folder, default dataset is ATCO2-test-set-1h (as it is free access!)
# You can uncomment the next one to use the ATCO2-test-set-4h (accessible through ELDA))
dataset=atco2_test_set_1h
# dataset=atco2_test_set_4h
train_data=experiments/data/other/$dataset/ner/5_kfold/train_fold1.csv
test_data=experiments/data/other/$dataset/ner/5_kfold/test_fold1.csv

# empty, pass it in CLI
validation_data=''

# with this we can parse options from CLI
. data/utils/parse_options.sh

# train/test data and output experiments folder:
output_folder=$output_dir/$(basename $input_model)/$seed/$dataset

# configure a GPU to use if we a defined 'CMD'
if [ ! "$cmd" == 'none' ]; then
  basename=train_${dataset}_${seed}_${max_steps}steps_${max_number_of_samples}samples
  cmd="$cmd -N ${basename} ${output_folder}/log/${basename}.log"
else
  cmd=''
fi

$cmd python3 ner/train_ner.py \
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
  --val-data "$validation_data" \
  --test-data $test_data \
  $train_data $output_folder

echo "Done training a $input_model model with $dataset corpus (NER)"
exit 0
