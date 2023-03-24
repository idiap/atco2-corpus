#!/bin/bash -x

# TODO:
# - Should we refactor it, so that we keep original 'pronunciation probabilities'
#   and introduce the new 'g2p pronunciation probabilities'?
# - Or, we can train the pronunciation probabilities from the data...

set -euo pipefail

ACRONYM_G2P=scripts/acronym_g2p_english_librispeech.py
ASSEMBLE_MIXED_G2P=scripts/assemble_mixed_word_acronym_g2p.py

. utils/parse_options.sh

[ $# != 4 ] && echo "$0 <dict> <dict-g2p> <oov-list> [<waypoint-list>]" && exit 1

dict=$1
dict_g2p=$2
oov_list=$3
waypoint_list=${4:-/dev/null}

export LC_ALL=${UTF_LOCALE-en_US.UTF-8} # set the Locale,

mkdir -p $dict_g2p
cp $dict/{nonsilence_phones.txt,silence_phones.txt,optional_silence.txt,extra_questions.txt} $dict_g2p/

which phonetisaurus-train &>/dev/null || {
  echo "Missing phonetisaurus-train!"
  echo "please install it from: https://github.com/AdolfVonKleist/Phonetisaurus"
  exit 1
}

# extract set of graphemes from original lexicon (excluding the <...> symbols),
mkdir -p $dict_g2p/g2p
cat $dict/lexicon.txt | gawk '{ print $1; }' | egrep -v '^<' | sed 's/./&\n/g' | sort | uniq | \
  egrep -v -e '[<>_\-]' -e "'" -e '[0-9]' -e '\[' -e '\]' | tr '\n' ' ' | sed 's: ::g' >$dict_g2p/g2p/graphemes


### PREPARE WORD-LISTS,

# merge oovs (filter with set of graphemes),
graphemes=$(cat $dict_g2p/g2p/graphemes)
cat $oov_list | sort | uniq | \
  gawk -v regexp="^[-'_${graphemes}]*$" '$0 ~ regexp { print $0; }' | \
  egrep -v -e '--' -e '^-$' -e "^'$" | \
  gawk 'NF>0' >$dict_g2p/g2p/wrdlist.oovs

### split the set into 'words', 'acronyms' and 'mixed' of both,

# 'acronyms',
# - 'c_p_d_l_c'
egrep '^[a-z](_[a-z])*$' $dict_g2p/g2p/wrdlist.oovs \
  >$dict_g2p/g2p/wrdlist.new-acronyms # to be done separately,

{ # 'mixed',
  # - 'a_b_c_hungary'
  egrep '^([a-z]_){1,10}[a-z][a-z]' $dict_g2p/g2p/wrdlist.oovs
  # - 'air_l_a'
  egrep '[a-z][a-z](_[a-z]){1,10}$' $dict_g2p/g2p/wrdlist.oovs
} >$dict_g2p/g2p/wrdlist.new-mixed-word-acro

# all the rest are 'words',
join -v1 $dict_g2p/g2p/wrdlist.oovs \
  <(cat $dict_g2p/g2p/wrdlist.new-acronyms $dict_g2p/g2p/wrdlist.new-mixed-word-acro | sort) \
  | tr '_' '*' >$dict_g2p/g2p/wrdlist.new-words # '_' -> '*' (required by phonetisaurus),

# get word-list from mixed...
cat $dict_g2p/g2p/wrdlist.new-mixed-word-acro | \
  sed -r 's:^([a-z]_)*::; s:(_[a-z])*$::;' | sort -u | tr '_' '*' \
  >$dict_g2p/g2p/wrdlist.new-mixed-word-acro.wordparts

# synthesize acronyms,
# Note: requires UTF-8 locale,
python3 $ACRONYM_G2P <$dict_g2p/g2p/wrdlist.new-acronyms >$dict_g2p/g2p/lexicon_new-acronyms.txt

# Train g2p,
# - dataprep: replace '_' -> '*' (required by phonetisaurus), eventually add '\t' to separate (word, pron)
tr '_' '*' <$dict/lexicon.txt | awk '{ if($0 !~ "\t") {$1=$1"\t";} print $0; }' | sed "s:\t *:\t:" >$dict_g2p/g2p/lexicon_train.txt
# - run the training (retrain always),
#[ ! -f $dict_g2p/g2p/model.fst ] &&
python3 $(which phonetisaurus-train) --lexicon $dict_g2p/g2p/lexicon_train.txt --seq1_del --dir_prefix $dict_g2p/g2p

# - generate new pronunciations (oovs),
python3 $(which phonetisaurus-apply) --model $dict_g2p/g2p/model.fst --lexicon $dict_g2p/g2p/lexicon_train.txt \
  --word_list $dict_g2p/g2p/wrdlist.new-words --nbest 2 --pmass 0.60 | \
  tr '*' '_' >$dict_g2p/g2p/lexicon_new-words.txt

# - generate new pronunciations (waypoints),
cat $waypoint_list >$dict_g2p/g2p/wrdlist.waypoints
python3 $(which phonetisaurus-apply) --model $dict_g2p/g2p/model.fst --lexicon $dict_g2p/g2p/lexicon_train.txt \
  --word_list $dict_g2p/g2p/wrdlist.waypoints --nbest 1 | \
  tr '*' '_' >$dict_g2p/g2p/lexicon_new-waypoints.txt

# - generate new pronunciations (fragments of 'mixed' word+acronym items),
python3 $(which phonetisaurus-apply) --model $dict_g2p/g2p/model.fst --lexicon $dict_g2p/g2p/lexicon_train.txt \
  --word_list $dict_g2p/g2p/wrdlist.new-mixed-word-acro.wordparts --nbest 1 | \
  tr '*' '_' >$dict_g2p/g2p/wrdlist.new-mixed-word-acro.wordparts.pron

# - assemble pronunciation of 'mixed' word+acronym items
#   (calls function from $ACRONYM_G2P)
python3 $ASSEMBLE_MIXED_G2P \
  $dict_g2p/g2p/wrdlist.new-mixed-word-acro \
  $dict_g2p/g2p/wrdlist.new-mixed-word-acro.wordparts.pron \
  >$dict_g2p/g2p/lexicon_new-mixed-word-acro.txt

# Assemble the new lexicon,
cat $dict/lexicon.txt \
  $dict_g2p/g2p/lexicon_new-acronyms.txt \
  $dict_g2p/g2p/lexicon_new-words.txt \
  $dict_g2p/g2p/lexicon_new-mixed-word-acro.txt \
  $dict_g2p/g2p/lexicon_new-waypoints.txt | sort | uniq | sort -k1,1 >$dict_g2p/g2p/lexicon_final.txt
cp $dict_g2p/g2p/lexicon_final.txt $dict_g2p/lexicon.txt

# remove out-of-date lexiconp (if it exists),
rm -f $dict_g2p/lexiconp.txt

