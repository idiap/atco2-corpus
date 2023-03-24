#!/usr/bin/env python3

# Assleble the prounciation of 'mixed lexica' of type:
# 'a_b_c_hungary', 'air_l_a'

import os
import re
import sys

import numpy as np
from acronym_g2p_english_librispeech import acronym_g2p, g2p_map_en

# parse args,
word_and_acronym, wordprons = sys.argv[1:]

# preload wordprons into dict,
word2pron = {
    word: pron
    for word, pron in np.loadtxt(wordprons, dtype="object,object", delimiter="\t")
}

# main loop over 'word_and_acronym',
with open(word_and_acronym, "r") as fd:
    for line in fd:
        lexeme = line.strip()
        assert re.search(r"\s", lexeme) == None  # no whitespace,

        m1 = re.search(r"^([a-z]_)*", lexeme)
        m2 = re.search(r"(_[a-z])*$", lexeme)

        prefix_acronym = m1.group() if m1 else ""
        suffix_acronym = m2.group() if m2 else ""

        word_in_middle = lexeme[len(prefix_acronym) : len(lexeme) - len(suffix_acronym)]
        assert len(word_in_middle) > 0

        prefix_pron = ""
        if prefix_acronym:
            prefix_pron = acronym_g2p(prefix_acronym[:-1], g2p_map_en)

        suffix_pron = ""
        if suffix_acronym:
            suffix_pron = acronym_g2p(suffix_acronym[1:], g2p_map_en)

        word_pron = word2pron[word_in_middle]

        final_pron = " ".join(
            list(filter(None, [prefix_pron, word_pron, suffix_pron]))
        )  # filter removes '' elements,

        print("%s\t%s" % (lexeme, final_pron))
