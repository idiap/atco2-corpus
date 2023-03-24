#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

set -euo pipefail

# folder with the kaldi data prepared
data=$1

# A) SELECT ACCORDING 'AUTOMATIC' EXPERT KNOWLEDGE
#    - lid score >0.7
#    - snr >= 0
#    - cnet_score > 0.6
#
#    - this sholud remove ~1/3 of data...

# Create filtered list of recordings:
# - reads: data/atco_unsup_import_cnet/cnet_scores
# - writes: data/atco_unsup_import_cnet/cnet_scores.selected-lid-0.5 (above 0.5 LID)
# - writes: data/atco_unsup_import_cnet/cnet_scores.selected-cn-thr08

# make 'data' dir with the list
# - the local/make_utt_list.py converts wav-keys to utt-keys

# create a file with the cnet scores, to filter the initial dataset based on quality
python3 data/databases/atco2_pl_set/local/select_data.py $data/cnet_scores

# Default, all data:
utils/copy_data_dir.sh $data/ $data/train

# All data with LID >=0.5
utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/cnet_scores.selected-lid-0.5 $data/segments) \
  $data/ $data/train__subset_lid_0.5

# All data with LID >=0.6 and CNET CONF>=0.8
utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/cnet_scores.selected-cn-thr08 $data/segments) \
  $data/ $data/train__subset_3600h__confidences

# create the files with utt-id to filter and create sub-sets
data/databases/atco2_pl_set/local/select_data_randomly.py \
  --keep-fraction=0.8 > $data/list.subset_3600h__randomly
data/databases/atco2_pl_set/local/select_data_randomly.py \
  --keep-fraction=0.55 > $data/list.subset_2500h__randomly
data/databases/atco2_pl_set/local/select_data_randomly.py \
  --keep-fraction=0.33 > $data/list.subset_1500h__randomly
data/databases/atco2_pl_set/local/select_data_randomly.py \
  --keep-fraction=0.11 > $data/list.subset_500h__randomly

# B) SELECT RANDOMLY
utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/list.subset_3600h__randomly $data/train__subset_lid_0.5/segments) \
  $data/ $data/train__subset_3600h__randomly

utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/list.subset_2500h__randomly $data/train__subset_lid_0.5/segments) \
  $data/ $data/train__subset_2500h__randomly

utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/list.subset_1500h__randomly $data/train__subset_lid_0.5/segments) \
  $data/ $data/train__subset_1500h__randomly

utils/subset_data_dir.sh \
  --utt-list <(data/databases/atco2_pl_set/local/make_utt_list.py \
  $data/list.subset_500h__randomly $data/train__subset_lid_0.5/segments) \
  $data/ $data/train__subset_500h__randomly

echo "done splitting the ATCO2-PL-set corpus in $data/"
exit 0

