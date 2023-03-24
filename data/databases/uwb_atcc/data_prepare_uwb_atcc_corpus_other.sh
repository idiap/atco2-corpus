#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# This script is intended to format the UWB-ATCC corpus for the experimentation.
#   Corpus: AIR TRAFFIC CONTROL COMMUNICATION
#       (collected by UWB in Pilsen, recordings from LKPR - Prague Airport)
#
#       20.58h of recordings sampled at 8kHz
#       You can download for free this database in the link below:
# URL: https://lindat.mff.cuni.cz/repository/xmlui/handle/11858/00-097C-0000-0001-CCA1-0

set -euo pipefail

# Replace this with the PATH where you donwloaded and extracted the data:
DATA=/usr/downloads/PILSEN_DB/ZCU_CZ_ATC
EXP_FOLDER=experiments/data/other

# this will parse options from command line, like $0 --DATA
. data/utils/parse_options.sh

# normalization scripts
TEXT_NORMALIZATION=data/utils/normalizer/text_normalization_lc.sh
[ ! -f $TEXT_NORMALIZATION ] && echo "Missing $TEXT_NORMALIZATION !" && exit 1
number_expansion=data/utils/number_expansion_english.sh
[ ! -f $number_expansion ] && echo "Missing $number_expansion !" && exit 1
trs2stm=data/utils/trs2stm.py
[ ! -f $trs2stm ] && echo "Missing $trs2stm !" && exit 1

# output folder
data=$EXP_FOLDER/uwb_atcc; mkdir -p $data/prep
keyprefix=uwb-atcc

# filter for UWB-ATCC database
function local_filter {
    sed -e 's/^/ /g' -e 's/$/ /g' | # Add spaces (hack for regex)
    sed -e 's/\.\./ <sil> /g' -e 's/\[ehm_??\]/ <breath> /g' -e 's/\[noise\]/ <noise> /g' |
    sed -e 's/\[no_eng\]/ <foreign> /g' -e 's/\[unintelligible\]/ <unk> /g' |
    sed -e 's/\[background_speech\]/ <noise> /g' -e 's/\[speaker\]/ <breath> /g' |
    perl -pe 's/\[no_eng_\|].*?\[\|_no_eng]/ <foreign> /g' |
    perl -pe 's/\[comment_\|].*?\[\|_comment]//g' | # Remove comments
    perl -pe 's/\[unintelligible_\|](.*?)\[\|_unintelligible]/ \1 /g' | # Words are intelligible
    perl -pe 's/\[background_speech_\|](.*?)\[\|_background_speech]/ \1 /g' | # Words are OK
    perl -pe 's/\[czech_\|](.*?)\[\|_czech]/ <foreign> /g' |
    perl -pe 's/\[noise_\|](.*?)\[\|_noise]/ \1 /g' | # Words are intelligible
    perl -pe 's/\[speaker_\|](.*?)\[\|_speaker]/ \1 /g' | # Words are intelligible
    sed 's/(\(\(\w*\|\s*\)*\)\s*(\(\w*\|\s*\)*))/ \1 /g' | # Take label, e.g. H from (H(otel))
    sed 's:\([a-zA-Z0-9]\)?:\1 ?:g; s:\([0-9]\)+:\1:g; s:\([0-9]\)\([A-Z]\):\1 \2:g' | # '4?'\ -> '4 ?', 'accept?' -> 'accept ?', '6+' -> 6, '6T' -> '6 T',
    sed -e 's/ 0 / zero /g' -e 's/ 1 / one /g' -e 's/ 2 / two /g' -e 's/ 3 / three /g' |
    sed -e 's/ 4 / four /g' -e 's/ 5 / five /g' -e 's/ 6 / six /g' -e 's/ 7 / seven /g' |
    sed -e 's/ 8 / eight /g' -e 's/ 9 / nine /g' |
    sed -e 's/ 0 / zero /g' -e 's/ 1 / one /g' -e 's/ 2 / two /g' -e 's/ 3 / three /g' |
    sed -e 's/ 4 / four /g' -e 's/ 5 / five /g' -e 's/ 6 / six /g' -e 's/ 7 / seven /g' |
    sed -e 's/ 8 / eight /g' -e 's/ 9 / nine /g' |
    sed -e 's/ A / Alfa /g' -e 's/ B / Bravo /g' -e 's/ C / Charlie /g' -e 's/ D / Delta /g' |
    sed -e 's/ E / Echo /g' -e 's/ F / Foxtrot /g' -e 's/ G / Golf /g' -e 's/ H / Hotel /g' |
    sed -e 's/ I / India /g' -e 's/ J / Juliett /g' -e 's/ K / Kilo /g' -e 's/ L / Lima /g' |
    sed -e 's/ M / Mike /g' -e 's/ N / November /g' -e 's/ O / Oscar /g' -e 's/ P / Papa /g' |
    sed -e 's/ Q / Quebec /g' -e 's/ R / Romeo /g' -e 's/ S / Sierra /g' |
    sed -e 's/ T / Tango /g' -e 's/ U / Uniform /g' -e 's/ V / Victor /g' |
    sed -e 's/ W / Whiskey /g' -e 's/ X / X-ray /g' -e 's/ Y / Yankee /g' |
    sed -e 's/ Z / Zulu /g' |
    sed 's: RWY : runway :g; s: FL : flight level :g;' |
    sed -e 's/\(.\)\./\1 decimal/g' |
    cat
}


#########
# Train #
#########
mkdir -p $data/prep

# wav.scp,
[ ! -f $data/prep/wav.scp ] && \
for wav in $(find $DATA/audio -name '*.wav'); do
    echo "${keyprefix}_$(basename $wav .wav) sox $wav -twav -r16k - remix - |"
done >$data/wav.scp


# stm,
# [ THIS TAKES A WHILE ]
[ ! -f $data/prep/text0_stm ] && \
for trs in $(find $DATA/transcripts -name '*.trs'); do
  LC_ALL=en_US.UTF-8 $trs2stm <(uconv -f cp1250 -t utf8 $trs | \
                                sed 's:encoding="CP1250":encoding="UTF8":' | \
                                sed 's:audio_filename="e2_\(.*\)\.wav":audio_filename="\1":')
done >$data/prep/text0_stm

# text,
paste -d ' ' <(cat $data/prep/text0_stm | awk -v prefix=$keyprefix '{ rec=$1; t_beg=$4;
t_end=$5; printf("%s_%s_%06d_%06d %s_%s\n", prefix, rec, t_beg*100, t_end*100, prefix, rec); }') \
             <(cut -d ' ' -f4-5 $data/prep/text0_stm) \
             <(cut -d' ' -f7- $data/prep/text0_stm | local_filter) | \
             tr -s ' ' >$data/prep/text1_raw_spk

# remove the 'actual' pronunciation: '(radar (rýdar)) -> radar', fix typos,
paste -d' ' <(cut -d' ' -f1-4 $data/prep/text1_raw_spk) \
            <(cut -d' ' -f5- $data/prep/text1_raw_spk | \
              sed -e 's:(\([^()]*\) ([^)]*)):\1:g;
                      s:(\([^()]*\)([^)]*)):\1:g;' \
                  -e "s:´:':g; s:?::g; s:¨::g;" \
                  -e 's:6raha:Praha:g; s:0direct:zero direct:g; s:6t:six t:g;') \
            >$data/prep/text2_rem-act-pron

# 'ILS' -> 'I_L_S', remove <sil>,
# also removing diacritics,
cat $data/prep/text2_rem-act-pron | data/utils/expand_uc_acronyms.py | data/utils/remove_diacritics.sh | sed 's:<sil>::g;' > $data/prep/text3_acron

# conver to low case, then normalize and expand numbers
# then add spaces between speakers roles
# finally delete all words between <>
paste -d' ' <(cut -d' ' -f1-4 $data/prep/text3_acron) \
            <(cut -d' ' -f5- $data/prep/text3_acron | \
            uconv -f utf8 -t utf8 -x "Any-Lower" | \
            sed 's/\[/ \[/g; s/\]/\] /g' | sed -e 's/<[^<>]*>//g' | \
            sed 's:+:-:g;' | $number_expansion | $TEXT_NORMALIZATION) | \
            tr -s ' ' | awk 'NF>4' >$data/prep/text_tags

# extract only the text
cut -d' ' -f1,5- $data/prep/text_tags > $data/prep/text_tags2

# Perform the last normalization step 
python3 data/utils/normalizer/final_normalization.py \
  --mapping data/utils/normalizer/words.txt \
  --input $data/prep/text_tags2 \
  --output $data/prep/text_tags3


paste -d' ' <(cut -d' ' -f1-4 $data/prep/text_tags) \
            <(cut -d' ' -f2- $data/prep/text_tags3 | sed 's/ |/_|/g; s/| /|_/g' | \
              uconv -f utf8 -t utf8 -x "Any-Lower" | tr -s ' ') \
            > $data/prep/text_tags_final

# getting the speaker role information
python3 data/databases/uwb_atcc/spk_id_tagger.py $data/prep/text_tags_final

# text, 
cut -d' ' -f1,5- $data/prep/text2_raw_spk  >$data/text

# segments,
awk '{print $1, $2, $3, $4}' $data/prep/text2_raw_spk | sort >$data/segments

# utt2spk,
awk '{print $1, $2}' $data/prep/text2_raw_spk | sort >$data/utt2spk

# utt2speakerid,
cp $data/prep/utt2speakerid $data/

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
  echo "creating the $ds folder:"
  
  files_to_filter="text segments utt2spk utt2speakerid"
  for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/$ds/ids \
      $data/$file_to_filter >$data/$ds/$file_to_filter
  done

  # creating the the wav.scp file for each subset (train/test)
  cut -d' ' -f2 $data/$ds/segments > $data/$ds/ids_wav
  perl data/utils/filter_scp.pl $data/$ds/ids_wav \
    $data/wav.scp >$data/$ds/wav.scp
done

# ------
echo "UWB-ATCC corpus was sucessfully created"
exit 0


