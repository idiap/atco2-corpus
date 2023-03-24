#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

set -euo pipefail

# Kill sub-processes on exit,
trap "pkill -P $$" EXIT SIGINT SIGTERM

#######
# LOCATION OF RAW DATASET
DATA_ROOT=/path/to/dataset/atco2_VHF_DATA/
#######

data=experiments/data/atco2_pl_set; mkdir -p $data/prep

# Location of Kaldi:
KALDI_ROOT=/path/to/your/kaldi
ln -sf $KALDI_ROOT/egs/wsj/s5/utils .
ln -sf $KALDI_ROOT/egs/wsj/s5/steps .
cat $KALDI_ROOT/egs/wsj/s5/path.sh | sed "s:KALDI_ROOT=.*$:KALDI_ROOT=$KALDI_ROOT:" >path.sh
. path.sh

# make list of wav files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  find $data_bin/ -name '*.wav' >$data/prep/wav_files_$(basename $data_bin).list &
done; wait

# make wav.scp
cat $data/prep/wav_files_*.list | \
  awk '{ rec_key=$1; wav=$1
         sub(/^.*\//, "", rec_key);
         sub(/\.wav$/, "", rec_key);
         print rec_key, wav;
       }' > $data/wav.scp

### import the automatic transcripts

# make lists of 'cnet' files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  find $data_bin/ -name '*.cnet_10_b15-13-400' >$data/prep/cnet_files_$(basename $data_bin).list &
done; wait

# import the 'cnet' files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  cnet_list=$data/prep/cnet_files_$(basename $data_bin).list
  transcript=$data/prep/transcripts_$(basename $data_bin)
  segments=$data/prep/segments_cnet_$(basename $data_bin)
  python3 data/databases/atco2_pl_set/local/import_transcripts.py \
    $cnet_list $transcript $segments &
done; wait

# merge the 'segments' files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  cat $data/prep/segments_cnet_$(basename $data_bin)
done >$data/segments

# merge the 'text' files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  cat $data/prep/transcripts_$(basename $data_bin)
done >$data/text

# make utt2spk, spk2utt
cat $data/segments | awk '{ print $1, $1; }' >$data/utt2spk
utils/utt2spk_to_spk2utt.pl $data/utt2spk >$data/spk2utt

# sort the data
utils/fix_data_dir.sh $data

# ----

# compute mean cnet confidence per wav
# - this is used for data filtering
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  cnet_list=$data/prep/cnet_files_$(basename $data_bin).list
  cnet_score_file=$data/prep/cnet_scores_$(basename $data_bin)
  python3 data/databases/atco2_pl_set/local/get_cnet_score.py \
    $cnet_list > $cnet_score_file &
done
wait

# merge the 'cnet_scores' files
for data_bin in $(ls -d $DATA_ROOT/DATA_BINS_20*); do
  cat $data/prep/cnet_scores_$(basename $data_bin)
done >$data/cnet_scores

# compute recording counts
tmp_wav_list=$(mktemp)
cut -d' ' -f2 $data/wav.scp >$tmp_wav_list
python3 data/databases/atco2_pl_set/local/recording_counts.sh \
  $tmp_wav_list | tee recording_counts.log

# ----

# get the subsets of data
bash data/databases/atco2_pl_set/create_subsets.sh $data

# train lm with all the automatic transcripts
bash data/databases/atco2_pl_set/prepare_lm.sh

exit 0

