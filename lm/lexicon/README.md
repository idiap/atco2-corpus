# README

preparation of lexicon for ATCO2 project

## How it's done?
- import of Librispeech lexicon (incl. probabilities of pronunciation)
   - involves conversion to lowercase by `uconv -f utf8 -t utf8 -x "Any-Lower"`
- we assemble texts from ATC databases to get `$atc_words` and `$oov_list`
- there are also our custom word-lists in `src_word_lists/`
   - we can add words here easily!
- next, g2p with Phonetisaurus trained on full Librispeech lexicon
- next, pronunciations of OOVs are made, separately for
   - regular words: Phonetisaurus model
   - 'spelled' acronyms: `scripts/acronym-g2p_english-librispeech.sh`

## What is prepared?
- in total we prepare 3 versions of `$lang` dirs with lexicons
   - `$lang` : mere import of Librispeech lexicon
   - `$lang_g2p` : Librispeech lexicon + `$atc_words`
   - `$lang_g2p_atc` : `$atc_words` only... (limited vocabulary)
