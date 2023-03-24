#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import os
import re
import sys

try:
    # when imported as 'module',
    from .mapping_tables import letter_to_word, number_to_word
except:
    # when called as 'standalone tool' from CLI,
    from mapping_tables import letter_to_word, number_to_word

AIRLINE_TABLE_PATH = "../callsign_table/callsign_table.csv"


def load_airline_table(airline_table, icao_to_callword=dict()):

    for line in open(airline_table, "r"):
        # replace non-break space by normal space,
        line = line.replace("\xa0", " ")

        # parse table of airlines,
        if line.strip().split("\t")[0] == "ICAO":
            continue
        if line.strip() == "":
            continue

        arr = line.rstrip().split("\t")
        if len(arr) < 3:
            print(arr, file=sys.stderr)
        icao, name, callword = arr[:3]

        # add to dict, while replacing "[ -]" -> "_",
        if icao not in icao_to_callword:
            icao_to_callword[icao] = set()
        icao_to_callword[icao].add(re.sub("[ -]", "_", callword.lower()))

    return icao_to_callword


def rewrite_by_words(input_string):
    """ICAO standard, 1 letter/digit -> 1 word"""

    ans = []
    for char in input_string:
        if char in letter_to_word:
            ans.append(letter_to_word[char])
        elif char in number_to_word:
            ans.append(number_to_word[char])
        elif char == " ":
            continue
        else:
            raise Exception(
                "Unknown char '%s' in input_string '%s'" % (char, input_string)
            )

    return ans


def rewrite_special(words):
    """Rewrite alredy expanded input to cover special cases"""

    ans = []

    # 'triple'
    prev_word = None
    counter = 1
    for i, word in enumerate(words):
        if word == prev_word:
            counter += 1
        else:
            counter = 1

        if counter == 3:
            ans.append(words[: (i - 2)] + ["triple"] + [word] + words[(i + 1) :])
            if word == "zero":
                ans.append(words[: (i - 2)] + ["triple"] + ["o"] + words[(i + 1) :])
            # shortened,
            ans.append(["triple"] + [word] + words[(i + 1) :])

        prev_word = word

    # 'double'
    prev_word = None
    counter = 1
    for i, word in enumerate(words):
        if word == prev_word:
            counter += 1
        else:
            counter = 1

        next_word = None
        try:
            next_word = words[i + 1]
        except:
            pass

        if counter == 2 and next_word != word:
            ans.append(words[: (i - 1)] + ["double"] + [word] + words[(i + 1) :])
            if word == "zero":
                ans.append(words[: (i - 1)] + ["double"] + ["o"] + words[(i + 1) :])
            # shortened,
            ans.append(["double"] + [word] + words[(i + 1) :])

        prev_word = word

    return ans


class ExpandCallsign:
    """Class which expands callsigns:
    'LUF123AB' -> 'lufthansa one two three alfa bravo'
    it also generates the shortened versions...
    """

    EXP_LVL_STANDARD = 5  # standard ICAO expansion
    EXP_LVL_SPECIAL = 9  # e.g. BAW777 -> speedbird triple seven
    EXP_LVL_FULL = 10  # e.g. BAW7703 -> seven zero three

    EXP_LVL_MAPPING = {
        "standard": EXP_LVL_STANDARD,
        "special": EXP_LVL_SPECIAL,
        "full": EXP_LVL_FULL,
    }

    def __init__(self, airline_table=AIRLINE_TABLE_PATH, level="standard"):
        # load the callsign mapping tables,
        self.icao_to_callword = load_airline_table(airline_table)
        self.level = self.EXP_LVL_MAPPING[level]  # indicates the strategy

        # National prefixes:
        # https://en.wikipedia.org/wiki/List_of_aircraft_registration_prefixes
        self.national_prefixes = {
            "OK": "Czechia",
            "SP": "Poland",
            "OE": "Austria",
            "OM": "Slovakia",
            "HB": "Switzerland",
            "D": "Germany",
            "OO": "Belgium",
            "PH": "Netherlands",
            "LU": "Luxembourgh",
            "F": "France",
            "I": "Italy",
            "M": "Spain",
            "CR": "Portugal",
            "CS": "Portugal",
            "K": "UK",
            "GE": "UK",
            "EI": "Ireland",
            "EJ": "Ireland",
            "SA": "Sweden",
            "LN": "Noraway",
            "OH": "Finland",
            "RA": "Russia",
            "RF": "Russia",
            "RR": "Russia",
            "N": "USA",
        }

    def expand_callsign(self, callsign):
        expansions = self.expand_callsign_impl(callsign)

        if not expansions:
            return None

        ans = []

        # remove duplicities and keep original ranking,
        already_have = set()
        for expan in expansions:
            key = ",".join(expan)
            if key not in already_have:
                ans.append(expan)
                already_have.add(key)

        return ans

    def expand_callsign_impl(self, callsign):
        """Expand single callsign.

        input: callsign (i.e. 'LUF123AB')
        output: list(list(str)) representing variants of 'verbalization'
                return None, if callsign cannot be expanded
        """

        # callsign with code from "airline table",
        # - e.g. CSA123AB, BAW777C, BAW79
        three_chars = callsign[:3]
        if three_chars in self.icao_to_callword:
            return self.expand_callsign_airline(callsign)

        # callsign with "national" prefix (two-char or one-char),
        # - e.g. OKA2730, OKHTM, N1003F, N1777R
        two_chars = callsign[:2]
        one_char = callsign[:1]
        if (two_chars in self.national_prefixes) or (
            one_char in self.national_prefixes
        ):
            return self.expand_callsign_national(callsign)

        # other callsign, shorter that 5 chars,
        if len(callsign) <= 5:
            ans = list()  # return value,

            # standard expansion,
            arr = rewrite_by_words(callsign)
            ans.append(arr)

            # special expansions,
            if self.level >= self.EXP_LVL_SPECIAL:
                # prepare special version ('double', 'triple' rewritten)
                for arr_special in rewrite_special(arr[1:]):
                    ans.append(arr[:1] + arr_special)  # whole callsign (special)

            # non-standard expansions,
            if self.level >= self.EXP_LVL_FULL:
                if len(arr) > 3:
                    # append last three words
                    ans.append(arr[-3:])

            return ans

        # otherwise throw it away...
        print(
            f"{os.path.basename(__file__)}: Warning! Unrecognized callsign {callsign}",
            file=sys.stderr,
        )

        return None

    def expand_callsign_airline(self, callsign):
        # return value
        ans = []

        # three chars encoding airline,
        three_chars = callsign[:3]
        # translate the rest,
        leftover = rewrite_by_words(callsign[3:])

        # prepare special version ('double', 'triple' rewritten)
        leftover_special = rewrite_special(leftover)

        # there might be more airlines with same ICAO code,
        # (or shortened airline designators...)
        for codeword in sorted(self.icao_to_callword[three_chars]):

            # standard expansions,
            if self.level >= self.EXP_LVL_STANDARD:
                # whole callsign
                ans.append([codeword] + leftover)

                # last three chars of leftover,
                if len(leftover) > 3:
                    ans.append([codeword] + leftover[-3:])

                # last two chars of leftover,
                if len(leftover) > 2:
                    ans.append([codeword] + leftover[-2:])

            # special expansions,
            # (777 -> triple seven, 00 -> double zero, double o)
            if self.level >= self.EXP_LVL_SPECIAL:
                # add special spelling, e.g. 777 -> "triple seven"
                for leftover_ in leftover_special:
                    ans.append([codeword] + leftover_)

            # non-standard expansions
            if self.level >= self.EXP_LVL_FULL:

                # with airline designator,
                if len(leftover) > 3:
                    # first two chars and last char of leftover,
                    ans.append([codeword] + leftover[:2] + leftover[-1:])
                    # first char and last two chars of leftover,
                    ans.append([codeword] + leftover[:1] + leftover[-2:])

                # no airline designator,
                ans.append(leftover)
                if len(leftover) > 3:
                    # last three chars of leftover (no airline designator)
                    ans.append(leftover[-3:])

                # with 'triple', 'double' rewritten, no designator,
                for leftover_ in leftover_special:
                    ans.append(leftover_)

        # also add callsign fully "spelled" by ICAO alphabet,
        ans.append(rewrite_by_words(callsign))

        return ans

    def expand_callsign_national(self, callsign):
        # return value
        ans = []

        # callsign with "national" prefix (two-char),
        two_chars = callsign[:2]
        if two_chars in self.national_prefixes:
            arr = rewrite_by_words(callsign)

            # standard expansions,
            ans.append(arr)  # whole callsign,

            if len(arr) > 5:
                # first 2, last 3 words
                ans.append(arr[:2] + arr[-3:])
            if len(arr) > 4:
                # first 2, last 2 words
                ans.append(arr[:2] + arr[-2:])

            # special expansion,
            if self.level >= self.EXP_LVL_SPECIAL:
                # prepare special version ('double', 'triple' rewritten)
                for arr_special in rewrite_special(arr[2:]):
                    ans.append(arr[:2] + arr_special)  # whole callsign (special)

            # non-standard expansions,
            if self.level >= self.EXP_LVL_FULL:
                if len(arr) > 5:
                    # first word, last 3 words
                    ans.append(arr[:1] + arr[-3:])
                    # last 3 words only,
                    ans.append(arr[-3:])
                if len(arr) > 4:
                    # first word, last 2 words
                    ans.append(arr[:1] + arr[-2:])
                # special without national prefix,
                for arr_special in rewrite_special(arr[2:]):
                    ans.append(arr_special)

            return ans

        # callsign with "national" prefix (one-char),
        one_char = callsign[0]
        if one_char in self.national_prefixes:
            arr = rewrite_by_words(callsign)

            # standard expansions,
            ans.append(arr)  # whole callsign,
            if len(arr) > 4:
                # first 1, last 3 words
                ans.append([arr[0]] + arr[-3:])
            if len(arr) > 3:
                # first 1, last 2 words
                ans.append([arr[0]] + arr[-2:])

            # special expansion,
            if self.level >= self.EXP_LVL_SPECIAL:
                # prepare special version ('double', 'triple' rewritten)
                for arr_special in rewrite_special(arr[1:]):
                    ans.append(arr[:1] + arr_special)  # whole callsign (special)

            # non-standard expansions
            if self.level >= self.EXP_LVL_FULL:
                if len(arr) > 4:
                    ans.append(arr[-3:])
                # special without national prefix,
                for arr_special in rewrite_special(arr[1:]):
                    ans.append(arr_special)

            return ans


def main():
    """Command line interface..."""
    import argparse

    lvl_mapping = ExpandCallsign.EXP_LVL_MAPPING

    parser = argparse.ArgumentParser(description="CLI for callsign expansion.")
    parser.add_argument(
        "--expansion-level", choices=list(lvl_mapping.keys()), default="standard"
    )
    args = parser.parse_args()

    exp_csl = ExpandCallsign(level=args.expansion_level)

    # do the translation,
    for line in sys.stdin:

        # remove whitespace,
        callsign = line.strip()

        # skip header,
        if callsign == "callsigns":
            continue
        # skip empty line,
        if callsign == "":
            continue

        # expand callsign,
        expanded = exp_csl.expand_callsign(callsign)

        # print all variants,
        if not expanded:
            continue  # None returned?
        for variant in expanded:
            print(" ".join(variant))


if __name__ == "__main__":
    main()
