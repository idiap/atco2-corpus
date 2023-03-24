#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to fine-tunine a wav2vec 2.0 wav2vec2-xls-r-300m model with ATCO2-pl-set corpus
# We call the fine-tuning BASH script: src/run_asr_fine_tuning.sh
# which later calls PYTHON script: src/run_speech_recognition_ctc.py

#######################################
# COMMAND LINE OPTIONS,
# You can pass a qsub command (SunGrid Engine)
#       :an example is passing --cmd "src/sge/queue.pl h='*'-V", add your configuration
cmd="none"
cmd="utils/queue.pl -l gpu -P minerva -V"

# model
model="facebook/wav2vec2-xls-r-300m"

# train/test subsets
dataset_name="experiments/data/atco2_pl_set/train"
eval_dataset_name="experiments/data/atco2_test_set_4h"


# some static vars for this experiment
exp="experiments/results/baseline"
max_steps=10000
per_device_train_batch_size=16
gradient_acc=2
learning_rate="5e-4"
mask_time_prob="0.01"

# calling the bash script
bash asr_e2e/run_asr_fine_tuning.sh \
  --cmd "$cmd" \
  --model-name-or-path "$model" \
  --dataset-name "$dataset_name" \
  --eval-dataset-name "$eval_dataset_name" \
  --max-steps "$max_steps" \
  --per-device-train-batch-size "$per_device_train_batch_size" \
  --gradient-acc "$gradient_acc" \
  --learning_rate "$learning_rate" \
  --mask-time-prob "$mask_time_prob" \
  --overwrite-dir "true" \
  --exp "$exp"
  
echo "Done training facebook/wav2vec2-xls-r-300m model for ATCO2-pl-set corpus in: $exp"
exit 1
