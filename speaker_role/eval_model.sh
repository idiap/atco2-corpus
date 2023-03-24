#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# script to evaluate a sequence classification model on given test sets

set -euo pipefail

# static vars
cmd='none'

# TEST datasets availables. We pass the path to the utt2spk id
# commercial databases
atco2_test_set_1h=experiments/data/other/atco2_test_set_1h/spkid_exp/utt2spk_id
uwb_atcc=experiments/data/other/uwb_atcc/test/spkid_exp/utt2spk_id

input_files="$atco2_test_set_1h $uwb_atcc"
test_names="atco2_test_set_1h uwb_atcc"

# model related vars
batch_size=16

# vars of the model and input/output folder
input_model=bert-base-uncased
training_dataset=uwb_atcc
seed=1234
output_dir=experiments/results/spk_id

# with this we can parse options to this script
. ./utils/parse_options.sh

output_folder=$output_dir/$(basename $input_model)/$seed/$training_dataset

# configure a GPU to use if we define 'CMD'
if [ ! -z "$cmd" ]; then
  basename=train_${training_dataset}_${seed}_${max_steps}steps_${max_number_of_samples}samples
  cmd="$cmd -N ${basename} ${output_folder}/log/${basename}.log"
else
  cmd=''
fi

# running the command
$cmd python3 speaker_role/eval_sec_classification.py \
  --batch-size $batch_size \
  --input-model "$output_folder" \
  --input-files "$input_files" \
  --test-names "$test_names" \
  --output-folder $output_folder/evaluations

echo "Done evaluating $input_model model (sequence classification)"
exit 0
