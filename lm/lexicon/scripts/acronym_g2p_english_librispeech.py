#!/usr/bin/env python3

import sys

# GET THE RAW G2P MAPPING,
#
# egrep '^[a-z] ' prep/lexicon3_filt.txt | awk '{ $2=":"; print; }' | sed 's:^:":; s| : |" : "|; s:$:",:;' | tr '"' "'"
#

g2p_map_en = {
    "a": "ey1",
    "b": "b iy1",
    "c": "s iy1",
    "d": "d iy1",
    "e": "iy1",
    "f": "eh1 f",
    "g": "jh iy1",
    "h": "ey1 ch",
    "i": "ay1",
    "j": "jh ey1",
    "k": "k ey1",
    "l": "eh1 l",
    "m": "eh1 m",
    "n": "eh1 n",
    "o": "ow1",
    "p": "p iy1",
    "q": "k y uw1",
    "r": "aa1 r",
    "s": "eh1 s",
    "t": "t iy1",
    "u": "y uw1",
    "v": "v iy1",
    "w": "d ah1 b ah0 l y uw0",
    "x": "eh1 k s",
    "y": "w ay1",
    "z": "z eh1 d",
}


def acronym_g2p(wrd, g2p_dict):
    acronym_letters = wrd.split("_")
    acronym_pron = [g2p_dict[l] for l in acronym_letters]
    return " ".join(acronym_pron)


def main(argv):
    # print the pronunciation of acronyms,
    for line in sys.stdin:
        acronym = line.strip()
        try:
            print("%s\t%s" % (acronym, acronym_g2p(acronym, g2p_map_en)))
        except KeyError:
            pass
    # print also the alphabet,
    for grapheme, pron in g2p_map_en.items():
        print("%s\t%s" % (grapheme, pron))


if __name__ == "__main__":
    main(sys.argv)
