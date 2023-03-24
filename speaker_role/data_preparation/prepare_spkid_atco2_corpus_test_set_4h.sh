#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Script to prepare dataset for speaker role ID experiments
# We also prepare the dataset for the NER experiments

set -euo pipefail

exp_folder=experiments/data/other/atco2_test_set_4h

. data/utils/parse_options.sh

# define the folders where the files are going to be stored for experimentation
output_dir=$exp_folder/spkid_exp
output_dir_ner=$exp_folder/ner
mkdir -p $output_dir; mkdir -p $output_dir_ner/prep 

# first make the spkid_exp folder
cat $exp_folder/text | sort >$output_dir/text
cat $exp_folder/utt2speaker_callsign | sort >$output_dir/utt2speaker_callsign

paste -d' ' <(awk '{ if ($2 == "atco")  { $2="0 atco"; }
              else if ( $2 == "pilot") { $2="1 pilot"; } 
              print( $1,$2 ); }' $output_dir/utt2speaker_callsign) \
            <(cut -d' ' -f2- $output_dir/text) \
            | tr -s ' ' >$output_dir/utt2spk_id

# first, make a local copy in the NER folder
cp $exp_folder/{text,segments} $output_dir_ner/prep/
cp $exp_folder/utt2nertags $output_dir_ner/prep/utt2nertags.tofix

# fixt the NER tags file, some entities are B-ent B-ent B-ent instead of B-ent I-ent I-ent
python3 ner/fix_ner_tags_file.py \
  $output_dir_ner/prep/utt2nertags.tofix \
  >$output_dir_ner/prep/utt2nertags

# creating the main file, utt2text_tags,
paste -d';' <(cat $output_dir_ner/prep/text | sort | cut -d' ' -f1) \
            <(cat $output_dir_ner/prep/text | sort | cut -d' ' -f2-) \
            <(cat $output_dir_ner/prep/utt2nertags | sort | \
            cut -d' ' -f2- | tr ' ' ',') \
            >$output_dir_ner/prep/utt2text_tags.1.nofilter


# remove some empty lines that ends with ';$'
grep -v ';$' $output_dir_ner/prep/utt2text_tags.1.nofilter \
  >$output_dir_ner/prep/utt2text_tags.2.nofilter

# remove samples that has the NO_TAGGED <tag>
grep -v "NO_TAGGED" $output_dir_ner/prep/utt2text_tags.2.nofilter \
  >$output_dir_ner/prep/utt2text_tags

# create the final version of the dataset for NER 
cp $output_dir_ner/prep/utt2text_tags $output_dir_ner/
cut -d';' -f1 $output_dir_ner/utt2text_tags > $output_dir_ner/ids

perl data/utils/filter_scp.pl $output_dir_ner/ids \
  $output_dir_ner/prep/text >$output_dir_ner/text

perl data/utils/filter_scp.pl $output_dir_ner/ids \
  $output_dir_ner/prep/segments >$output_dir_ner/segments

echo Done processing the ATCO2 dataset

# gen kfolds
echo "generating folds for NER experiments"

python3 ner/gen_kfolds.py \
  --input_csv $output_dir_ner/utt2text_tags \
  --k 5 --seed 2222 --save_dir $output_dir_ner/5_kfold/


echo "finished preparing the NER and speaker role ID folders for data in $exp_folder"
exit 0
