#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# This script is intended to format the ATCOSIM: AIR TRAFFIC CONTROL SIMULATION SPEECH corpus.
# ATCOSIM: AIR TRAFFIC CONTROL SIMULATION SPEECH CORPUS
#       Project data: https://www.spsc.tugraz.at/databases-and-tools/atcosim-air-traffic-control-simulation-speech-corpus.html
#   The data is recorded during ATC real-time simulations using a close-talk headset microphone.
#   The utterances are in English language and pronounced by ten non-native speakers.
#   Accents: German, Swiss-German, Swiss-French. 6 male, 4 female.)
#   Duration: 10h, sampled at 32kHz
# 

set -euo pipefail

# Replace this with the PATH where you donwloaded and extracted the data:
DATA=/usr/downloads/atcosim
EXP_FOLDER=experiments/data

# this will parse options from command line, like $0 --DATA
. data/utils/parse_options.sh

# text normalization, standardize ATC text
TEXT_NORMALIZATION=data/utils/normalizer/text_normalization_lc.sh

# output folder
data=$EXP_FOLDER/atcosim_corpus; mkdir -p $data/prep

keyprefix=atcosim_
sampling_rate=16000

function local_filter {
    sed -e 's/^/ /g' -e 's/$/ /g' | # Add spaces (hack for regex)
    sed -e 's/<FL>\s*<\/FL>/<foreign>/g' -e 's/\[EMPTY\] //g' -e 's/\[FRAGMENT\]/<unk>/g' |
    sed -e 's/\[HNOISE\]/<gbg>/g' -e 's/\[NONSENSE\]/<unk>/g'  -e 's/\[UNKNOWN\]/<unk>/g' |
    perl -pe 's/<OT>(.*?)<\/OT>/\1/g' |
    sed -e 's/\~\(\w\)/\U\1/g' | # Replace acronyms with single words
    data/databases/atcosim_corpus/link_acronyms.sh | # "K L M" -> "K_L_M"
    sed 's:=:-:g; s:@::g;' | # replace '=' -> '-', remove '@',
    cat
}

#########
# Train #
#########
for wav in $(find $DATA/WAVdata -name '*.wav'); do
  echo "atcosim_$(basename $wav .wav) sox $wav -c1 -twav -r16k - |"
done >$data/wav.scp
awk -F, 'NR>=2 {if($8 == 0) print}' $DATA/TXTdata/fulldata.csv >$data/prep/fulldata.csv

awk -F, '{printf("atcosim_%s_%06d_%06d atcosim_%s %.2f %.2f\n",$3,0,$10*100,$3,0,$10)}' \
  $data/prep/fulldata.csv >$data/segments

paste -d' ' <(cut -d' ' -f1 $data/segments) \
            <(awk -F, '{printf("atcosim_%s\n",$4)}' $data/prep/fulldata.csv ) \
            >$data/utt2spk

paste -d' ' <(cut -d' ' -f1 $data/segments) \
            <(awk -F, '{print $7}' $data/prep/fulldata.csv | local_filter | \
              uconv -f utf8 -t utf8 -x "Any-Lower" | $TEXT_NORMALIZATION) | \
              tr -s ' ' >$data/prep/text.nonorm

# removing some empty  
grep -v "[0-9] $\|<foreign>$" $data/prep/text.nonorm >$data/prep/text

# Perform the last normalization step 
python3 data/utils/normalizer/final_normalization.py \
  --mapping data/utils/normalizer/words.txt \
  --input $data/prep/text \
  --output $data/text

# this script will output in train/test folder 
mkdir -p $data/{train,test}

cut -d' ' -f1 $data/text > $data/ids

# get the ids for each folder, train and test,
python3 data/utils/gen_train_test.py \
  --seed 1234 \
  --train-percentage 80 \
  --input-csv $data/ids

# split the data by train and test
for ds in $(echo "train test"); do

  # copy each file from main folder and filter it:
  files_to_filter="text segments utt2spk wav.scp"
  for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/$ds/ids \
      $data/$file_to_filter >$data/$ds/$file_to_filter
  done

  # creating the the wav.scp file for each subset (train/test)
  cut -d' ' -f2 $data/$ds/segments > $data/$ds/ids_wav
  perl data/utils/filter_scp.pl $data/$ds/ids_wav \
    $data/wav.scp >$data/$ds/wav.scp

done

#############################
# Gender experiments

files_to_filter="text segments utt2spk wav.scp"
# creating the speaker list for train/test based on genders

# ONLY TRAIN FEMALE
grep "atcosim_zf1\|atcosim_zf2\|atcosim_gf1" $data/text | cut -d' ' -f1 > $data/ids.train.female
data_folder=train_female; mkdir -p $data/$data_folder/
for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/ids.train.female \
        $data/$file_to_filter >$data/$data_folder/$file_to_filter
done
cut -d' ' -f2 $data/$data_folder/segments > $data/$data_folder/ids_wav
perl data/utils/filter_scp.pl $data/$data_folder/ids_wav \
    $data/wav.scp >$data/$data_folder/wav.scp

# ONLY TEST FEMALE
grep "atcosim_zf3" $data/text | cut -d' ' -f1 > $data/ids.test.female
data_folder=test_female; mkdir -p $data/$data_folder/
for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/ids.test.female \
        $data/$file_to_filter >$data/$data_folder/$file_to_filter
done
cut -d' ' -f2 $data/$data_folder/segments > $data/$data_folder/ids_wav
perl data/utils/filter_scp.pl $data/$data_folder/ids_wav \
    $data/wav.scp >$data/$data_folder/wav.scp


# ONLY TRAIN MALE
grep "atcosim_sm1\|atcosim_sm2\|atcosim_sm3\|atcosim_sm4" $data/text | cut -d' ' -f1 \
    > $data/ids.train.male
data_folder=train_male; mkdir -p $data/$data_folder/
for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/ids.train.male \
        $data/$file_to_filter >$data/$data_folder/$file_to_filter
done
cut -d' ' -f2 $data/$data_folder/segments > $data/$data_folder/ids_wav
perl data/utils/filter_scp.pl $data/$data_folder/ids_wav \
    $data/wav.scp >$data/$data_folder/wav.scp


# ONLY TEST MALE
grep "atcosim_gm1\|atcosim_gm2" $data/text | cut -d' ' -f1 > $data/ids.test.male
data_folder=test_male; mkdir -p $data/$data_folder/
for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/ids.test.male \
        $data/$file_to_filter >$data/$data_folder/$file_to_filter
done
cut -d' ' -f2 $data/$data_folder/segments > $data/$data_folder/ids_wav
perl data/utils/filter_scp.pl $data/$data_folder/ids_wav \
    $data/wav.scp >$data/$data_folder/wav.scp

echo "ATCOSIM corpus was sucessfully created (also folders for gender-based experiments)"
exit 0