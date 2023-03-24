#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# This script is intended to format the LDC-ATCC corpus for the experimentation.
# You can acquired this dataset in the following link:
#     AIR TRAFFIC CONTROL COMPLETE (1994, LDC94S14A)
#     Recordints from 3 US airpots: DFW, BOS, DCA.
#     72.5h, 8kHz.
#     https://catalog.ldc.upenn.edu/LDC94S14A

set -euo pipefail

# Replace this with the PATH where you donwloaded and extracted the data:
DATA=/usr/downloads/atc0_comp/*/data
EXP_FOLDER=experiments/data/other

# this will parse options from command line, like $0 --DATA
. data/utils/parse_options.sh

# output folder
data=$EXP_FOLDER/ldc_atcc; mkdir -p $data/prep
keyprefix=ldc-atcc
sampling_rate=16000

TEXT_NORMALIZATION=data/utils/normalizer/text_normalization_lc.sh

sph2pipe=$(which sph2pipe)
[ ! -e $sph2pipe ] && echo "Missing sph2pipe $sph2pipe" && exit 1

sox=sox
! which $sox >/dev/null && echo "Missing sox $sox" && exit 1
LC_ALL=C

list=$(grep FROM $DATA/transcripts/* | tr -s ' ' | cut -d' ' -f2 | sort | grep "\-\|_" | uniq | sed 's/.$//' | tr "\n" " ")

#------
# wav.scp,
{ for sph in $(find $DATA -name '[^.]*.sph'); do
    echo "${keyprefix}_$(basename $sph .sph) $sph2pipe -f wav $sph | $sox -t wav - -t wav -r$sampling_rate -b16 - remix - |"
  done
  # There is only 1 wav, which is actually sphere file too (BUG in DB)
  for wav in $(find $DATA -name '[^.]*.wav'); do
    echo "${keyprefix}_$(basename $wav .wav) $sph2pipe -f wav $wav | $sox -t wav - -t wav -r$sampling_rate -b16 - remix - |"
  done
} >$data/prep/wav.scp
# WARNING: i had to fix the sph header for all the 'CA' files.
# 'sample_byte_format -s2 01' ==>> 'sample_byte_format -s2 10'


### transcripts,
for txt in $(find $DATA -iname '[^.]*.txt'); do
    echo $txt >>/dev/stderr
    ./data/databases/ldc_atcc/parse_lisp_array.sh $txt \
      || break # this version produce the speaker role tag
done >$data/prep/transcripts_no-prefix

# add the prefix and format the utterance,
awk -v pf=$keyprefix '{ $1=pf"_"$1; $2=pf"_"$2; print; }' \
  <$data/prep/transcripts_no-prefix \
  >$data/prep/transcripts_no-time

# transcripts with new timing in utt_id,
awk '{ utt=sprintf("%s_%06d_%06d",$2,$4*100,$5*100); if($5>$4) {print utt, $0; }}' \
  <$data/prep/transcripts_no-time\
  >$data/prep/transcripts

# getting a list with all the IDS for ATCOs
list=$(grep FROM $DATA/transcripts/* | tr -s ' ' | cut -d' ' -f2 | sort | grep "\-\|_" | uniq | sed 's/.$//' | tr "\n" " ")

# if the files exists, we dont get the speaker role and callsign-ICAO information
if [ ! -f $data/prep/utt2icao ]; then
    echo "Extracting speakerid and utt2icao files. This takes a while"

    while read -r line; do
    # get the utt id and remove '*' char in some samples
    utt_id=$(echo $line | cut -d' ' -f1 | sed 's/*//g')
    spk1=$(echo $line | cut -d' ' -f4 | cut -d'|' -f1 | sed 's/_//g' )
    spk2=$(echo $line | cut -d' ' -f4 | cut -d'|' -f2 | sed 's/_//g')

    rest=$(echo $line | cut -d' ' -f2-6)
    text=$(echo $line | cut -d' ' -f7-)

    # assigning speaker roles:
    if [[ " $list " =~ " $spk1 " ]]; then
        callsign=$spk2;
        role="atco"
        tag="_AT"
    else
        callsign=$spk1;
        role="pilot"
        tag="_PI"
    fi

    # printing the outputs 
    echo "${utt_id}${tag} $role" >> $data/prep/utt2speakerid
    echo "${utt_id}${tag} $callsign" >> $data/prep/utt2icao
    echo "${utt_id}${tag} $rest $role $callsign $text" >> $data/prep/transcripts_all_data
    done <$data/prep/transcripts
    wait
else
    echo "skiping speakerid/utt2icao extraction, already prepared"
fi

# segments,
cut -d' ' -f1-2,5-6 <$data/prep/transcripts_all_data | sort >$data/prep/segments

# utt2spk,
cut -d' ' -f1-2 $data/prep/transcripts_all_data | sort > $data/prep/utt2spk

# text,
cut -d' ' -f1,9- <$data/prep/transcripts_all_data | tr -s ' ' >$data/prep/text_raw

# - convert to lowercase, link acronyms 't w a' -> 't_w_a'
paste -d' ' <(cut -d' ' -f1 $data/prep/text_raw) \
            <(cut -d' ' -f2- $data/prep/text_raw | \
              tr '[]' '()' | sed 's:([^)]*)::g; s:([^)]*$::g;' | \
              sed 's|^| |; s|$| |;' | \
              sed 's: KIL0 : KILO :g; s: 0H : OH :g; s: Y0U : YOU :g;' | \
              sed "s: 8'LL : I'LL :g;" | \
              sed 's: //* : :g; s: - : :g; ' | \
              sed 's| [A-Z0-9\-\.]*[0-9][A-Z0-9\-\.]* | <unk> |g' | \
              uconv -f utf8 -t utf8 -x "Any-Lower" | \
              data/databases/ldc_atcc/link_acronyms.sh | $TEXT_NORMALIZATION | \
              sed 's/|//g') | tr -s ' ' | sed 's: $::' \
              >$data/prep/text_raw_tmp

# - remove empty lines or lines with only 'unk',
awk 'NF>1' <$data/prep/text_raw_tmp | grep -v "AT <unk>$\|PI <unk>$" \
  >$data/prep/text_raw_tmp2

# Perform the last normalization step 
python3 data/utils/normalizer/final_normalization.py \
  --mapping data/utils/normalizer/words.txt \
  --input $data/prep/text_raw_tmp2 \
  --output $data/prep/text.pre_final

# convert text to lower case:
paste -d' ' <(cut -d' ' -f1 $data/prep/text.pre_final) \
            <(cut -d' ' -f2- $data/prep/text.pre_final |\
                uconv -f utf8 -t utf8 -x "Any-Lower") \
            > $data/prep/text

# get ids to filter:
cut -d' ' -f1 $data/prep/text > $data/prep/ids

# filter the files before concatenating
perl data/utils/filter_scp.pl $data/prep/ids \
  $data/prep/transcripts_all_data >$data/prep/all_data_filter

# update transcripts file with processed data
paste -d' ' <(cut -d' ' -f1-8 $data/prep/all_data_filter) \
            <(cut -d' ' -f2- $data/prep/text) \
            >$data/prep/transcripts_all_data_norm

# create the dialogues, based on the callsigns identifiers
python3 data/utils/get_dialogues.py \
  $data/prep/transcripts_all_data_norm >$data/prep/dialogues

# copy the final versions,
cp $data/prep/{segments,text,wav.scp,utt2spk,dialogues,transcripts_all_data_norm} $data

# filter some empty utterances,  
perl data/utils/filter_scp.pl $data/prep/ids $data/prep/utt2icao >$data/utt2icao
perl data/utils/filter_scp.pl $data/prep/ids $data/prep/utt2speakerid >$data/utt2speakerid

#################################################################
#       CREATING THE TRAIN/TEST SPLITS!
# There is no official train/test splits for this LDC-ATCC corpus 
# We split the data in train and test sets,
#################################################################

# these are the speakers for the test set, feel free to change it
speakers="AR1-1\|AR1-2\|AR2-1\|AR2-2"

# get the utterances ids for train and test setsm, 
mkdir -p $data/{train,test}
grep -v "$speakers" $data/text | cut -d' ' -f1 > $data/train/ids
grep "$speakers" $data/text | cut -d' ' -f1 > $data/test/ids

# split the data by train and test
for ds in $(echo "train test"); do

  # copy each file from main folder and filter it:
  files_to_filter="segments text utt2spk utt2speakerid utt2icao transcripts_all_data_norm"
  for file_to_filter in $(echo "$files_to_filter"); do
    perl data/utils/filter_scp.pl $data/$ds/ids \
      $data/$file_to_filter >$data/$ds/$file_to_filter
  done

  # creating the the wav.scp file for each subset (train/test)
  cut -d' ' -f2 $data/$ds/segments > $data/$ds/ids_wav
  perl data/utils/filter_scp.pl $data/$ds/ids_wav \
    $data/wav.scp >$data/$ds/wav.scp

  # create the dialogues, based on the callsigns identifiers for each subset
  python3 data/utils/get_dialogues.py \
    $data/$ds/transcripts_all_data_norm >$data/$ds/dialogues

done

echo "LDC-ATCC corpus was sucessfully created"
exit 0
