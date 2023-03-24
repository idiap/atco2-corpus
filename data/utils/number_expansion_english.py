#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

# English number expansion,
# According to: http://omniglot.com/language/numbers/somali.ht://stackoverflow.com/questions/8982163/how-do-i-tell-python-to-convert-integers-into-words

# Extended to process ordinal numbers.

import sys


def cardinal_number(num_str, limit=99999):
    try:
        num = int(num_str)

        # (avoid over-generating numbers),
        if num > limit:
            raise (Exception("number too big"))

        # here part of the original function begins,
        d = {
            0: "zero",
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine",
            10: "ten",
            11: "eleven",
            12: "twelve",
            13: "thirteen",
            14: "fourteen",
            15: "fifteen",
            16: "sixteen",
            17: "seventeen",
            18: "eighteen",
            19: "nineteen",
            20: "twenty",
            30: "thirty",
            40: "forty",
            50: "fifty",
            60: "sixty",
            70: "seventy",
            80: "eighty",
            90: "ninety",
        }
        k = 1000
        m = k * 1000

        assert 0 <= num

        if num < 20:
            return d[num]

        if num < 100:
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + " " + d[num % 10]

        if num < k:
            if num % 100 == 0:
                return d[num // 100] + " hundred"
            else:
                return d[num // 100] + " hundred and " + cardinal_number(num % 100)
        if num < m:
            if num % k == 0:
                return cardinal_number(num // k) + " thousand"
            else:
                return (
                    cardinal_number(num // k) + " thousand " + cardinal_number(num % k)
                )

        raise (Exception("number too big"))

    except Exception as e:
        print(
            "{}: WARNING, could not translate number:".format(__file__),
            num_str,
            str(e),
            file=sys.stderr,
        )
        return num_str


def ordinal_number(n_str):
    ordinals = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "nineth",
        10: "tenth",
        11: "eleventh",
        12: "twelfth",
        13: "thirteenth",
        14: "fourteenth",
        15: "fifteenth",
        16: "sixteenth",
        17: "seventeenth",
        18: "eighteenth",
        19: "nineteenth",
        20: "twentieth",
        21: "twenty first",
        22: "twenty second",
        23: "twenty third",
        24: "twenty fourth",
        25: "twenty fifth",
        26: "twenty sixth",
        27: "twenty seventh",
        28: "twenty eighth",
        29: "twenty nineth",
        30: "thirtieth",
        31: "thirty first",
    }

    try:
        n = int(n_str)
        if n in ordinals:
            return ordinals[n]
        else:
            return cardinal_number(n_str)
    except Exception as e:
        print(
            "{}: WARNING, could not translate number:".format(__file__),
            n,
            str(e),
            file=sys.stderr,
        )
        return n_str


def process_word(wrd):
    ordinal_suffix = set(["st", "nd", "rd", "th"])

    if wrd[-1] == "." and wrd[:-1].isdigit():
        ans = ordinal_number(wrd[:-1])
    elif wrd[-2:] in ordinal_suffix and wrd[:-2].isdigit():
        ans = ordinal_number(wrd[:-2])
    elif wrd.isdigit():
        ans = cardinal_number(wrd)
    elif wrd[0] == "-" and wrd[1:].isdigit():
        limit = 99
        if int(wrd[1:]) <= limit:
            ans = "minus " + cardinal_number(wrd[1:], limit=99)
        else:
            ans = wrd
    else:
        ans = wrd

    return str(ans)


### main function,
if __name__ == "__main__":
    if len(sys.argv) == 2:
        # for testing, parse the argument,
        print(process_word(sys.argv[1]))
    else:
        # parse text from stdin,
        for line in sys.stdin:
            ans = []
            for wrd in line.split():
                ans.append(process_word(wrd))
            print(" ".join(ans))
