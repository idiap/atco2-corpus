#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

set -euxo pipefail

# Note:
# - We search for the mapping rules on 'text' data that do not have
#   the 'common/text_normalization_lc.sh' mapping applied yet.
# - This script will find only the mapping that

DATA_DIR="../../kaldi_data_preparations"
{
    cut -d' ' -f2- $DATA_DIR/AIRBUS_CHALLENGE/kaldi_data/airbus_train-dev/prep/text2_acron
    cut -d';' -f5  $DATA_DIR/ATCO_RECORDINGS/LKTB_TEST/kaldi_data/airport_lktb_test_v1/prep/data.csv
    cut -d';' -f8  $DATA_DIR/ATCO_RECORDINGS/ATCO2_TEST_EN_V3/kaldi_data/atco2_test-set-v3_en/prep/transcripts1.csv
    cut -d' ' -f2- $DATA_DIR/HAAWAII/*/kaldi_data/*/prep/text1
    cut -d' ' -f2- $DATA_DIR/HIWIRE/kaldi_data/hiwire/prep/text_raw
    cut -d' ' -f2- $DATA_DIR/LDC_ATCC/kaldi_data/ldc_atcc/prep/text_raw
    cut -d';' -f7  $DATA_DIR/LIVEATC_TEST_BUT/*/kaldi_data/liveatc*/prep/transcripts1.csv
    cut -d' ' -f2- $DATA_DIR/MALORCA/kaldi_data/*/prep/raw/text
    cut -d' ' -f2- $DATA_DIR/N4_NATO/kaldi_data/n4_nato/prep/text_raw
    cut -d',' -f7  $DATA_DIR/TUGRAZ_ATCOSIM/kaldi_data//atcosim/prep/fulldata.csv
    cut -d' ' -f2- $DATA_DIR/UWB_ATCC/kaldi_data/uwb_atcc/prep/text3_acron
} | uconv -f utf8 -t utf8 -x "Any-Lower" | tr -s ' ' | sort -u >text

./create_normalized_mapping.py --text text | tee -a callword_rules.txt

# sort the rules,
sort -u callword_rules.txt >callword_rules.tmp
mv callword_rules.tmp callword_rules.txt

