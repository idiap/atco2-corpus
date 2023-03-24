#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Base script to fine-tunine a wav2vec 2.0 model on a given dataset with HuggingFace
#######################################
# COMMAND LINE OPTIONS,
# high-level variables for training the model. TrainingArguments (HuggingFace)
# You can pass a qsub command (SunGrid Engine)
#       :an example is passing --cmd "src/sge/queue.pl h='*'-V", add your configuration
set -euo pipefail

# static vars
cmd='none'

_VOCABULARY_PATH="config/vocab.json"

# model and dataset
model_name_or_path="facebook/wav2vec2-base"
dataset_name="experiments/data/atco2_pl_set/train"
eval_dataset_name="experiments/data/atco2_test_set_4h"
train_split_name="train"

# training hyper-params
preprocessing_num_workers=$(echo "$(( $(nproc)-1 ))" )
num_epochs=50
max_steps=10000
per_device_train_batch_size=12
per_device_eval_batch_size=12
gradient_acc=3
learning_rate="1e-4"
save_steps=1000
eval_steps=500
warmup_steps=1000
logging_steps=1000
max_train_samples=
exp='experiments/results'
overwrite_dir=true
freeze_feature_encoder=true

# Data augmentation details
layerdrop="0.0"
activation_dropout="0.0"
attention_dropout="0.0"
feat_proj_dropout="0.0"
mask_time_prob="0.0"
mask_time_length="12"
mask_feature_prob="0.0"
mask_feature_length="12"

. data/utils/parse_options.sh

optional_args="--max_steps $max_steps"

if [ ! -f "$_VOCABULARY_PATH" ]; then
  echo "Vocabulary is empty, you passed $_VOCABULARY_PATH"
  echo "We will create a new vocabulary from the training+test file"
else
  optional_args="$optional_args --vocab_path=$_VOCABULARY_PATH"
fi

# check if you want to use only a portion of the data and define a new output dir
dataset_dir_name=$(basename $(dirname $dataset_name))
if [ -z "$max_train_samples" ]; then
  output_dir=$exp/$(basename $model_name_or_path)/$dataset_dir_name
else
  output_dir=$exp/$(basename $model_name_or_path)/${dataset_dir_name}_${max_train_samples}s
  optional_args="--max_train_samples=$max_train_samples"
fi

if [ "$overwrite_dir" = "true" ]; then
  optional_args="$optional_args --overwrite_output_dir"
elif [ "$overwrite_dir" = "false" ]; then
  optional_args="$optional_args"
else
  echo "Please give 'true' or 'false' to overwrite_dir, you passed: $overwrite_dir"
  exit 0
fi

if [ "$freeze_feature_encoder" = "true" ]; then
  optional_args="$optional_args --freeze_feature_encoder"
fi

# redefine the output_dir name:
basename_dir=${layerdrop}ld_${activation_dropout}ad_${attention_dropout}attd_${feat_proj_dropout}fpd_${mask_time_prob}mtp_${mask_time_length}mtl_${mask_feature_prob}mfp_${mask_feature_length}mfl_${gradient_acc}acc
output_dir=${output_dir}/$basename_dir/

# configure a GPU to use if we a defined 'CMD'
if [ ! "$cmd" == 'none' ]; then
  basename=train_$(basename $model_name_or_path)_${dataset_dir_name}_${basename_dir}
  cmd="$cmd -N ${basename} ${output_dir}/log/train_log"
else
  cmd=''
fi

echo "*** About to start the training ***"
echo "*** output folder: $output_dir ***"

# call the training script, use "$cmd" if defined
$cmd python3 asr_e2e/run_speech_recognition_ctc.py \
  --report_to="none" \
  --run_name="$output_dir" \
  --preprocessing_num_workers="$preprocessing_num_workers" \
  --model_name_or_path=$model_name_or_path \
  --dataset_name=$dataset_name \
  --min_duration_in_seconds=0.2 \
  --max_duration_in_seconds=20 \
  --eval_dataset_name=$eval_dataset_name \
  --train_split_name=$train_split_name \
  --output_dir=$output_dir \
  --num_train_epochs=$num_epochs \
  --per_device_train_batch_size=$per_device_train_batch_size \
  --per_device_eval_batch_size=$per_device_eval_batch_size \
  --gradient_accumulation_steps=$gradient_acc \
  --learning_rate=$learning_rate \
  --weight_decay=0.001 \
  --warmup_steps=$warmup_steps \
  --evaluation_strategy="steps" \
  --text_column_name="text" \
  --audio_column_name="audio" \
  --length_column_name="input_length" \
  --chars_to_ignore=", ? . ! \; \: \" “ % ‘ ” � — ’ … –" \
  --save_steps=$save_steps \
  --eval_steps=$eval_steps \
  --logging_steps=$logging_steps \
  --layerdrop=$layerdrop \
  --activation_dropout=$activation_dropout \
  --attention_dropout=$attention_dropout \
  --save_total_limit="1" \
  --feat_proj_dropout=$feat_proj_dropout \
  --mask_time_prob=$mask_time_prob \
  --mask_time_length=$mask_time_length \
  --mask_feature_prob=$mask_feature_prob \
  --mask_feature_length=$mask_feature_length \
  --gradient_checkpointing \
  --freeze_feature_encoder \
  --fp16 \
  --group_by_length \
  --do_train --do_eval \
  $optional_args

echo "Done training of $model_name_or_path in $output_dir"
exit 0
