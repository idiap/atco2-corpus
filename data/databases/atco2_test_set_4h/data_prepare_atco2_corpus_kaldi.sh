#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# This script is intended to format the ATCO2-test-set corpus for the experimentation.
# You can acquired this dataset in the following link:
#     Project Data : http://catalog.elra.info/en-us/repository/browse/ELRA-S0484/
#     ISLRN : 589-403-577-685-7
# A free sample (1 hour) is available in the following link:
#     ATCO2-test-set-1h corpus: https://www.atco2.org/data

set -euo pipefail

# Replace this with the PATH where you donwloaded and extracted the data:
DATA=/usr/downloads/ATCO2-ASRdataset-v1_final/DATA
EXP_FOLDER=experiments/data/

# this will parse options from command line, like $0 --DATA
. data/utils/parse_options.sh

# text normalization, standardize ATC text
TEXT_NORMALIZATION=data/utils/normalizer/text_normalization_lc.sh

# output folder
data=$EXP_FOLDER/atco2_test_set_4h; mkdir -p $data/prep

keyprefix=atco2_test-set-4h_
sampling_rate=16000

# do not overwrite!
[ ! -f $data/list_of_wav ] && find $DATA -name '*.wav' >$data/list_of_wav
[ ! -f $data/list_of_xml ] && find $DATA -name '*.xml' >$data/list_of_xml
[ ! -f $data/list_of_info ] && find $DATA -name '*.info' >$data/list_of_info

[ ! -f $data/xml_to_airport_mapping ] && {
  # Extract part of filename:
  # LKPR_RUZYNE_Radar_120_520MHz_20201025_174652.xml -> LKPR_RUZYNE_Radar_120_520MHz
  cat $data/list_of_xml | awk -v FS='/' \
    '{ print $0, gensub("_[0-9]*_[0-9]*.xml$","","",$NF); }' \
    >$data/xml_to_airport_mapping
}

sox=sox
! which $sox >/dev/null && echo "Missing sox $sox" && exit 1

PATH=$(readlink -m data/utils/):$PATH
! which spd_xml2csv_batch.py >/dev/null && echo "Missing spd_xml2csv_batch.py" && exit 1
! which spd_xml2callsign_list.py >/dev/null && echo "Missing spd_xml2callsign_list.py" && exit 1
! which expand_uc_acronyms.py >/dev/null && echo "Missing expand_uc_acronyms.py" && exit 1
! which remove_diacritics.sh >/dev/null && echo "Missing remove_diacritics.sh" && exit 1

set -euo pipefail

# WAV
[ ! -f $data/prep/wav.scp ] && \
for wav in $(cat $data/list_of_wav); do
    key="${keyprefix}$(basename $wav | cut -d. -f1)"
    echo "${key} $wav"
done | sort >$data/prep/wav.scp


# XML
LC_ALL=en_US.UTF-8 \
  data/utils/spd_xml2csv_batch.py \
  $data/list_of_xml \
  $data/xml_to_airport_mapping \
  ${keyprefix} \
  > $data/prep/transcripts.csv

# INFO
LC_ALL=en_US.UTF-8 \
  data/utils/spd_import_info_batch.py \
  $data/list_of_info \
  ${keyprefix} \
  $data/prep/rec2waypoint_list \
  $data/prep/rec2callsign_list

function mixed_case_filter {
    sed 's:^: :g;  s:$: :g;' | # Add spaces (hack for regexp)
    sed 's:\[unk\]: <unk> :g;
         s:\[hes\]: <hes> :g;
         s:\[spk\]: <breath> :g;
         s:\[noise\]: <noise> :g;' |
    # Keep what was pronounced, not what was intended:
    # (e.g. "Lufthansa(-hansa) -> -hansa" or "04R(zero four right)" -> "zero four right")
    # (but do not match with the greetings "schone_tag_(bye)" )
    sed 's: [^ ]*[^_](\([^)]*\)): \1 :g;' |
    # Remove non-english parts:
    # (when whole line is foreign: "[NE Dutch] Goeden Avond [/NE]" -> " <foreign> ")
    perl -pe 's:^ *\[NE[ \-\]].*\[/NE\] *$: <foreign> :gi' |
    # (when part of line is foreign, keep words + discard tags)
    LC_ALL=en_US.UTF-8 sed -r 's:\[/?NE[^]]*\]: :gi' |
    # Remove comma and ellipsis ...
    sed 's:,: :g; s:\?: :g; s:\.\.\.: :g;' |
    # Remove double spaces,
    tr -s ' '
}

# transcripts,
# - apply mixed_case_filter mapping, identify acronyms,
paste -d';' <(cut -d';' -f1-7 $data/prep/transcripts.csv) \
            <(cut -d';' -f8 $data/prep/transcripts.csv | mixed_case_filter | expand_uc_acronyms.py | remove_diacritics.sh) \
            >$data/prep/transcripts1.csv
# - to lower,
paste -d';' <(cut -d';' -f1-7 $data/prep/transcripts1.csv) \
            <(cut -d';' -f8 $data/prep/transcripts1.csv | uconv -f utf8 -t utf8 -x "Any-Lower" | $TEXT_NORMALIZATION) \
            >$data/prep/transcripts2.csv
# - discard empty sentences, just <unk> sentences, just <foreign> sentences, just <noise> sentences
awk -F';' -v OFS=';' '{ if($8 ~ /^\s*$/) { next; }
                        if($8 ~ /^\s*<unk>\s*$/) { next; }
                        if($8 ~ /^\s*<foreign>\s*$/) { next; }
                        if($8 ~ /^\s*<noise>\s*$/) { next; }
                        print $0;
                      }' <$data/prep/transcripts2.csv >$data/prep/transcripts2_2.csv

# extract the transcripts to do a last normalization                    
cut -d';' -f1,8- $data/prep/transcripts2_2.csv | sed 's/;/ /' > $data/prep/text_final 

# joint text file again,
paste -d';' <(cut -d';' -f1-7 $data/prep/transcripts2_2.csv) \
            <(cut -d' ' -f2- $data/prep/text_final |\
                uconv -f utf8 -t utf8 -x "Any-Lower") \
            > $data/prep/transcripts_norm.csv

# script to extract tags in IOB format:
python3 data/utils/spd_xml2csv_tags_batch.py \
  $data/prep/transcripts_norm.csv > $data/prep/transcripts3.csv 

# stm,
{ # Labels in STM: <(FOR,ENG) (UNK,CLN) ,O>
  # (use airport code $5 as speaker)
echo ';; MARKUP LEGEND:
;; LABEL "FOR" "has <foreign>" "sentences with some foreign speech,"
;; LABEL "ENG" "no <foreign>" "sentences completely in english,"
;; LABEL "UNK" "has <unk>" "sentences with incomprehensible words,"
;; LABEL "CLN" "no <unk>" "fully comprehensible sentences,"
;; LABEL "O" "overall" "all the data,"'

paste -d ' ' <(awk -F';' '{ print $1, "A", $5, $6, $7; }' $data/prep/transcripts3.csv) \
             <(cut -d';' -f8 $data/prep/transcripts3.csv | \
                 awk '{ foreign_flag="ENG"; if($0 ~ "<foreign>") { foreign_flag="FOR"; }
                        unk_flag="CLN"; if($0 ~ "<unk>") { unk_flag="UNK"; }
                        printf("<%s,%s,O>\n", foreign_flag, unk_flag);
                      }') \
             <(cut -d';' -f8 $data/prep/transcripts3.csv | \
               sed 's:$: :; s: \([a-z][a-z]*-\) : (\1) :g;' | \
               sed 's:$: :; s: \(-[a-z][a-z]*\) : (\1) :g;' | \
               sed 's:<unk>:(&):g; s:<foreign>:(&):g;' | \
               sed 's:<breath>::g; s:<noise>::g; s:<hes>::g;') \
  | tr -s ' ' | LC_ALL=C sort -k1,1 -k2,2 -k4,4n
} >$data/prep/stm

# text,
awk -F';' '{ print $1, $8; }' <$data/prep/transcripts3.csv | sort >$data/prep/text

# segments,
awk -F';' '{ print $1, $2, $6, $7; }' <$data/prep/transcripts3.csv | sort >$data/prep/segments

# utt2spk, spk2utt
awk -F';' '{ print $1, $2"-"$3; }' <$data/prep/transcripts3.csv | sort >$data/prep/utt2spk
utils/utt2spk_to_spk2utt.pl $data/prep/utt2spk >$data/prep/spk2utt

# reco2file_and_channel
awk -F';' '{ print $2, $2, "A"; }' <$data/prep/transcripts3.csv |sort >$data/prep/reco2file_and_channel

# utt2waypoint_list
join <(awk '{ print $2, $1; }' $data/prep/segments | sort) <(sort $data/prep/rec2waypoint_list) | cut -d' ' -f2- >$data/prep/utt2waypoint_list

# utt2callsign_list
join <(awk '{ print $2, $1; }' $data/prep/segments | sort) <(sort $data/prep/rec2callsign_list) | cut -d' ' -f2- >$data/prep/utt2callsign_list

# utt2airport
join <(awk '{ print $1; }' $data/prep/segments | sort) <(awk -v FS=';' '{ print $1, $5; }' $data/prep/transcripts.csv | sort -k1,1) >$data/prep/utt2airport

# utt2speaker_callsign
awk -F';' '{ print $1";"$4; }' <$data/prep/transcripts3.csv >$data/prep/utt2speaker_callsign_raw
awk -F';' '{ if ($2 ~ "[Tt]ower" || $2 ~ "[Aa]pproach" || $2 ~ "[Rr]adar" || $2 ~ "[Aa]pron" || $2 ~ "[Gg]round") { $2="atco"; }
            else if ($2 ~ "^UNK-") { $2 = "unk"; }
            else { $2 = "pilot" } 
             gsub("-","",$2);
             print($1, $2);
           }' <$data/prep/utt2speaker_callsign_raw >$data/prep/utt2speaker_callsign


mkdir -p $data/valid
cp $data/prep/{utt2spk,spk2utt,text,stm,reco2file_and_channel,segments,wav.scp} $data/valid
utils/fix_data_dir.sh $data/valid

# check also line-counts for lists of metadata:
num_utts=$(cat $data/valid/segments | wc -l)
#
num_utt2waypoint_list=$(cat $data/prep/utt2waypoint_list | wc -l)
[ $num_utts -ne $num_utt2waypoint_list ] && echo "Error, num_utts=$num_utts utt2waypoint_list=$num_utt2waypoint_list" && exit 1
#
num_utt2callsign_list=$(cat $data/prep/utt2callsign_list | wc -l)
[ $num_utts -ne $num_utt2callsign_list ] && echo "Error, num_utts=$num_utts utt2callsign_list=$num_utt2callsign_list" && exit 1
#
num_utt2airport=$(cat $data/prep/utt2airport | wc -l)
[ $num_utts -ne $num_utt2airport ] && echo "Error, num_utts=$num_utts utt2airport=$num_utt2airport" && exit 1

num_utt2speaker_callsign=$(cat $data/prep/utt2speaker_callsign | wc -l)
[ $num_utts -ne $num_utt2speaker_callsign ] && echo "Error, num_utts=$num_utts utt2speaker_callsign=$num_utt2speaker_callsign" && exit 1

# copy the final versions,
utils/copy_data_dir.sh --validate-opts "--no-feats" $data/valid $data

# ------
# export all files to main folder,
cp $data/prep/{utt2waypoint_list,utt2callsign_list,utt2airport,utt2speaker_callsign} $data/
# ------

# word_counts.lst,
dict=$data/dict; mkdir -p $dict
cut -d' ' -f2- $data/text | tr -s ' ' | tr ' ' '\n' | awk "NF>0" | sort | uniq -c | sort -k1,1nr -k2 >$dict/word_counts.lst

echo "ATCO2-test-set corpus was sucessfully created"
exit 0

