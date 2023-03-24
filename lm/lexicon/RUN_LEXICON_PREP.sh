#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

set -euo pipefail

LEXICON_CMU=resources/cmudict-0.7b.txt
EXTRA_QUESTIONS=resources/extra_questions.txt

KALDI_ROOT=/path/to/your/kaldi
ln -sf $KALDI_ROOT/egs/wsj/s5/utils .
ln -sf $KALDI_ROOT/egs/wsj/s5/steps .
cat $KALDI_ROOT/egs/wsj/s5/path.sh | sed "s:KALDI_ROOT=.*$:KALDI_ROOT=$KALDI_ROOT:" >path.sh
. path.sh

# -----------------------------

for f_or_d in $LEXICON_CMU $EXTRA_QUESTIONS $KALDI_ROOT; do
  [ ! -e $f_or_d ] && { echo "Missing $f_or_d"; exit 1; }
done

which phonetisaurus-train &>/dev/null || {
  echo "Missing phonetisaurus-train!"
  echo " please install it from: https://github.com/AdolfVonKleist/Phonetisaurus"
  exit 1
}

# ---------------------------------------------------------------------------
# CUSTOM PRONUNCIATIONS, SPECIFIC TO ATC DOMAIN AND TO OUR LiveATC TEST SETS,
#
bash MAKE_CUSTOM_PRONS.sh
#
# -----------------------------

# ---------------------------------------------------------------------------
# REBUILD SOME RESOURCES,
#
(cd src_word_lists/airline_table/; bash README.sh)
#
# -----------------------------

# BUILD 1st VERSION (mere import of cmu lexicon),

# copy the CMU lexicon
mkdir -p prep
cp $LEXICON_CMU prep/lexicon1_orig.txt

# map lexicon to lower case (words and prons),
cat prep/lexicon1_orig.txt | uconv -f utf8 -t utf8 -x "Any-Lower" >prep/lexicon2_lc.txt

# remove <spoken_noise>, <unk>, !sil,
egrep -v '^<|^!' prep/lexicon2_lc.txt > prep/lexicon3_filt.txt

{ # LIST OF 'SPECIAL WORDS' FOR LEXICON,
  # (taken from Material/Babel)
  # - hesitation,
  echo -e "<hes> hes" # other '<hes>' variants were in $LEXICON,
  # - human noise,
  echo -e "<breath> brth
<laugh> lgh
<cough> sil
<lipsmack> sil"
  # - technical noise (noise is not in data, but will be in LM),
  echo -e "<click> noi
<dtmf> noi
<ring> noi
<noise> noi"
  # - 'bad speech' (i.e. foreign words, overlapped speech, OOVs)
  echo -e "<foreign> gbg
<overlap> gbg
<unk> gbg
<gbg> gbg"
} > prep/special_words.txt


{ # Include ATC custom pronunciations,
  # - this is asslembled here and included and in atc_words
  # - custom prons are removed from OOVs (we have the prons),
  #   and the pronunciations are added only at the very end
  #   (adding them to G2P training led to bad results).
  cat prep/atc_specific_prons.txt
  cat prep/airline_prons.txt
  cat prep/places_prons.txt
  cat prep/other_prons.txt
  cat prep/greetings_prons.txt
} > prep/custom_prons.txt


dict=data/local/dict_no-g2p
{ # CREATE 1ST VERSION OF LEXICON (just librispeech, no OOVs)
  mkdir -p $dict
  cat prep/lexicon3_filt.txt prep/special_words.txt | tr -s ' ' >$dict/lexicon.txt

  # Prepare the phone lists for 'prepare_lang.sh',
  # - nonsilence_phones.txt,
  cat $dict/lexicon.txt | awk '{ $1=""; print $0; }' | tr ' ' '\n' | \
    sort | uniq | egrep -v 'sil|brth|lgh|noi|gbg' | awk '$1' >$dict/nonsilence_phones.txt
  # - silence_phones.txt
  echo "sil
brth
lgh
noi
gbg" >$dict/silence_phones.txt
  # - optional_silence.txt
  echo "sil" >$dict/optional_silence.txt
  # - extra_questions.txt
  cat $EXTRA_QUESTIONS | sed 's:SPN:gbg:g' | uconv -f utf8 -t utf8 -x "Any-Lower" | grep -v ' ae ' \
    >$dict/extra_questions.txt

  # Make sure the phoneme set is same as in original lexicon.
  diff <(cat $dict/lexicon.txt | awk '{ $1=""; print $0; }' | tr ' ' '\n' | sort | uniq | egrep -v 'sil|brth|lgh|noi|gbg|hes') \
       <(cat prep/lexicon3_filt.txt | awk '{ $1=""; print $0; }' | tr ' ' '\n' | sort | uniq) \
  || { echo "ERROR! Phoneme sets changed after adding custom words"; exit 1; }
}

# build the 1st version of lang-dir,
lang=data/lang_no-g2p
# utils/prepare_lang.sh --num_sil_states 6 $dict "<gbg>" data/local/$(basename $lang) $lang


# -----------------------------

# BUILD 2nd VERSION (incl. G2P of 'atc' words and acronyms, custom pronunciations),

atc_words=prep/wordlist_atc_dbs.txt
{ # Assemble the list of ATC words,
  sed 's:$: :g;' ../../experiments/data/atco2_pl_set/text | cut -d' ' -f2- | tr -s ' ' | \
    tr ' ' '\n' | awk "NF>0" | sort | uniq

  # you can add more data here, like LDC-ATCC or UWB-ATCC or ATCOSIM, etc, 
  # one example below:
  # sed 's:$: :g;' ../../experiments/data/uwb_atcc/text | cut -d' ' -f2- | \
    # tr -s ' ' | tr ' ' '\n' | awk "NF>0" | sort | uniq

  # Add words from test sets,
  sed 's:$: :g;' ../../experiments/data/atco2_test_set_4h/text | cut -d' ' -f2- | \
    tr -s ' ' | tr ' ' '\n' | awk "NF>0" | sort | uniq

  # And, include 'hand-prepared' lists of words,
  cat src_word_lists/plane_models_and_brands | uconv -f utf8 -t utf8 -x "Any-Lower"
  cat src_word_lists/alphabet_icao
  cat src_word_lists/alphabet_spelling
  cat src_word_lists/numbers
  cat src_word_lists/abbrev_aero | ../../data/utils/expand_uc_acronyms.py | uconv -f utf8 -t utf8 -x "Any-Lower"

  # Proper names (wiki, busiest european airports),
  cat src_word_lists/airports/{country,airport,city,extra_words} | uconv -f utf8 -t utf8 -x "Any-Lower"

  # Tower names,
  cat ../resources/tower_names/tower_text_for_lm.txt | ../../data/utils/expand_uc_acronyms.py | uconv -f utf8 -t utf8 -x "Any-Lower"

  # Callsign codewords (wiki),
  cat src_word_lists/airline_table/callsign_codewords.txt # ../resources/callsign_mapping/callsign_mapping.csv

  # Custom pronunciations,
  awk '{ print $1 }' prep/custom_prons.txt

} | tr ' ' '\n' | egrep -v '^<|^\[|^\(' | sort | uniq >${atc_words}_non-ascii

# Filter the ${atc_words} word-list to keep ascii symbols only.
egrep "^[-a-zA-Z_()]*$" < ${atc_words}_non-ascii >${atc_words}

# Exclude custom pronunciations,
join -v1 ${atc_words} \
         <(awk '{ print $1; }' prep/custom_prons.txt | sort -u) \
         >${atc_words}_non-custom-prons

# Define the OOV list,
oov_list=prep/wordlist_atc_dbs_oovs.txt
join -v2 <(awk '{print $1;}' $dict/lexicon.txt | sort -u) \
         <(cat ${atc_words}_non-custom-prons | sort -u) \
         >$oov_list

# waypoint names,
waypoint_list=prep/waypoints.txt
cat ../resources/waypoints_europe.txt | uconv -f utf8 -t utf8 -x "Any-Lower" >$waypoint_list

# train and apply the G2P (phonetisaurus),
dict_g2p=data/local/dict_g2p
scripts/prepare_dict_g2p.sh $dict $dict_g2p $oov_list $waypoint_list

# build the 2nd version of lang-dir (incl. G2P),
lang_g2p=data/lang_g2p
# utils/prepare_lang.sh --num_sil_states 6 $dict_g2p "<gbg>" data/local/$(basename $lang_g2p) $lang_g2p

# -----------------------------

# BUILD 3rd VERSION (incl. G2P, with atc words only),

# make a dict with atc words only (and special words),
dict_g2p_atc=data/local/dict_g2p_atc; mkdir -p $dict_g2p_atc
cp $dict_g2p/{extra_questions.txt,nonsilence_phones.txt,optional_silence.txt,silence_phones.txt} $dict_g2p_atc

{ # ATC words
  join -j1 <(cat $atc_words $waypoint_list | sort) <(sort -k1,1 $dict_g2p/lexicon.txt)

  # Special words: <unk> <hes>,
  egrep '^<' $dict_g2p/lexicon.txt

  # Include ATC custom pronunciations here,
  cat prep/custom_prons.txt

} | egrep -v "^\s*$" | sort -u | sort -k1,1 >$dict_g2p_atc/lexicon.txt

# remove out-of-date lexiconp (if it exists),
rm -f $dict_g2p_atc/lexiconp.txt

# build the 3rd version of lang-dir,
lang_g2p_atc=data/lang_g2p_atc
utils/prepare_lang.sh --num_sil_states 6 $dict_g2p_atc "<gbg>" data/local/$(basename $lang_g2p_atc) $lang_g2p_atc

# get the list of graphemes from words.txt (check visually it is all ascii chars),
awk '{ print $1; }' $dict_g2p_atc/lexicon.txt | sed 's:.:&\n:g;' | sort | uniq | tr -d '\n' >grapheme_set

echo "done preparing the lexicon in $lang_g2p_atc"
exit 0
