#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

# In this script, we build LM in ARPA format.
#
# We only prepare the LM used the ATCO2-PL-SET as training
# and using ATCO2-test-set as devset. 
# You might need to change the paths or datasets used 
# (it is straighforward to add new databases into the 'mix')

set -euo pipefail

EXP_FOLDER=../../experiments

KALDI_ROOT=/path/to/your/kaldi
ln -sf $KALDI_ROOT/egs/wsj/s5/utils .
ln -sf $KALDI_ROOT/egs/wsj/s5/steps .
cat $KALDI_ROOT/egs/wsj/s5/path.sh | sed "s:KALDI_ROOT=.*$:KALDI_ROOT=$KALDI_ROOT:" >path.sh
. path.sh

# -----------------------------

which ngram-count || {
  echo "Missing ngram-count!"
  echo " please install SRI-LM (free only for non-commercial use)"
  exit 1
}

# -----------------------------

mkdir -p corpora/ lms/ prep/


### BUILD SOME RESOURCES, IF NOT READY YET,
[ ! -f ../resources/waypoint_text/waypoint_text.txt ] && { cd ../resources/waypoint_text/; bash README.sh || echo "Error!"; }


### IMPORT THE TRAINING CORPORA,

function f_preprocess { sed 's:<[a-z]*>::g; s:\[[^]]*\]::g; s:^  *::g; s:  *: :g;' - | sort | uniq; }

# you can import other train_data if you have access to them:
# cut -d' ' -f2- $EXP_FOLDER/data/ldc_atcc/text | f_preprocess >corpora/ldc_atcc
# cut -d' ' -f2- $EXP_FOLDER/data/uwb_atcc/text | f_preprocess >corpora/uwb_atcc
# cut -d' ' -f2- $EXP_FOLDER/data/atcosim/text | f_preprocess >corpora/atcosim

# import the  ATCO2-PL-set corpus data, default: is only this
cut -d' ' -f2- $EXP_FOLDER/data/atco2_pl_set/text | f_preprocess \
  >corpora/atco2_pl_set


{ # build a composite dev-data,
  # ATCO2-test-set-4h corpus,
  cut -d' ' -f2- $EXP_FOLDER/data/atco2_test_set_4h/text | f_preprocess 
} >corpora/dev_set_mix


{ # append multi-word airline/airport/city/country names,
  cat ../lexicon/src_word_lists/airports/airport
  cat ../lexicon/src_word_lists/airports/city
  cat ../lexicon/src_word_lists/airports/country
  cat ../lexicon/src_word_lists/airports/extra_words

  # callsigns - airline designators,
  cat ../lexicon/src_word_lists/airline_table/callsign_codewords.txt

  # verbalized callsigns, worldwide callsigns from 2019 and 2020,
  cat ../resources/callsign_expansion/liveatc-test-set1_2020_01_31.all_callsigns.txt
  # runway numbers,
  cat ../resources/runway_numbers/runway_numbers.txt

  # waypoints,
  cat ../resources/waypoint_text/waypoint_text.txt

  # towers, 3x
  cat ../resources/tower_names/tower_text_for_lm.txt | ../../data/utils/expand_uc_acronyms.py
  cat ../resources/tower_names/tower_text_for_lm.txt | ../../data/utils/expand_uc_acronyms.py
  cat ../resources/tower_names/tower_text_for_lm.txt | ../../data/utils/expand_uc_acronyms.py

  cat corpora/atco2_pl_set
} | uconv -f utf8 -t utf8 -x "Any-Lower" >corpora/all_data


# get vocab,
words_txt=../lexicon/data/lang_g2p_atc/words.txt

{ awk '$1 !~ /^[<#\-]|-$/ { print $1; }' $words_txt
  echo "<breath>
<gbg>
<hes>
<laugh>
<noise>
<prompt>"
} | LC_ALL=C sort | uniq >vocab


### TRAIN LM WITH ALL THE DATA,
corpus="all_data"
ngram_order=3

lm=$EXP_FOLDER/lm/lms/${corpus}.o${ngram_order}g.kn.gz
mkdir -p $(dirname $lm)

# train the actual LM
ngram-count -text corpora/$corpus -order $ngram_order -kndiscount -interpolate \
  -vocab vocab -limit-vocab -lm $lm # unk-symbol <gbg> as zerogram from 'vocab',

echo "%%% Check perplexity of final model"
ngram -lm $lm -ppl corpora/dev_set_mix -debug 2 | tee ${lm}.ppl_dev_final | tail -n2

lang=../lexicon/data/lang_g2p_atc/
lang_test=$EXP_FOLDER/lm/lang_test_o${ngram_order}g

# This ARPA-LM is to be imported to Kaldi as follows:
utils/format_lm_sri.sh --srilm-opts "-subset -prune-lowprobs -unk -map-unk <gbg>" \
  $lang $lm $lang_test


