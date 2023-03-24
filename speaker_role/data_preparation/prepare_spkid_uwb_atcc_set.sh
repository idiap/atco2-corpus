#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Script to prepare dataset for speaker role ID experiments

# Script to prepare UWB-ATCC database
set -euo pipefail

exp_folder=experiments/data/other/uwb_atcc

# UWB_ATCC, we can get the info from the folders already prepared, we add a hack to avoid
# utterances with multiples segments 
for dataset in $(echo "$exp_folder/train $exp_folder/test"); do

  # define the folders where the files are going to be stored for experimentation
  output_dir=$dataset/spkid_exp
  mkdir -p $output_dir

  # first make the spkid_exp folder
  cat $dataset/utt2speakerid | sort >$output_dir/utt2speakerid

paste -d' ' <(awk '{ if ($2 == "atco")  { $2="0 atco"; }
              else if ( $2 == "pilot") { $2="1 pilot"; } 
              else if ( $2 == "atco_pilot" ) { $2="2 mixed"; } 
              print( $1,$2 ); }' $output_dir/utt2speakerid) \
            <(cut -d' ' -f3- $output_dir/utt2speakerid | cut -d';' -f1) \
            | tr -s ' ' >$output_dir/utt2spk_id_raw

  grep -v "2 mixed\|_N" $output_dir/utt2spk_id_raw > $output_dir/utt2spk_id 
done

echo "finished preparing the NER and speaker role ID folders for data in $exp_folder"
exit 0
