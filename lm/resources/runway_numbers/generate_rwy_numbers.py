#!/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

digits = {
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
}

numbers = {
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
    21: "twenty one",
    22: "twenty two",
    23: "twenty three",
    24: "twenty four",
    25: "twenty five",
    26: "twenty six",
    27: "twenty seven",
    28: "twenty eight",
    29: "twenty nine",
    30: "thirty",
    31: "thirty one",
    32: "thirty two",
    33: "thirty three",
    34: "thirty four",
    35: "thirty five",
    36: "thirty six",
}


def generate_runway_pattern(fmt):
    """fmt is a string of this type: "... %s ..." """

    for i in range(1, 37):
        rwy_id = "%s %s" % (digits[i // 10], digits[i % 10])
        print(fmt % rwy_id)

    for i in range(1, 10):
        rwy_id = "%s left" % (digits[i])
        print(fmt % rwy_id)
        rwy_id = "%s right" % (digits[i])
        print(fmt % rwy_id)
        rwy_id = "%s center" % (digits[i])
        print(fmt % rwy_id)

    for i in range(11, 37):
        rwy_id = "%s %s left" % (digits[i // 10], digits[i % 10])
        print(fmt % rwy_id)
        rwy_id = "%s %s right" % (digits[i // 10], digits[i % 10])
        print(fmt % rwy_id)
        rwy_id = "%s %s center" % (digits[i // 10], digits[i % 10])
        print(fmt % rwy_id)


def main():

    # This is standard, it is repeated,
    for jj in range(6):
        generate_runway_pattern("runway %s")

    # This is also standard, it is repeated,
    for jj in range(3):
        generate_runway_pattern("runway %s cleared for takeoff")
        generate_runway_pattern("cleared for takeoff runway %s")
        generate_runway_pattern("cleared for takeoff %s")
        generate_runway_pattern("line up runway %s cleared for takeoff")

        generate_runway_pattern("touch and go runway %s")
        generate_runway_pattern("approach runway %s")

        generate_runway_pattern("cleared to land runway %s wind")
        generate_runway_pattern("land runway %s")
        generate_runway_pattern("runway %s cleared to land")

    # This is a wildcard for non-covered contexts,
    generate_runway_pattern("%s")

    # "thirteen" instead of "one three")
    # -> this is not standard, but still entering it...
    for i in range(1, 37):
        print("runway %s" % (numbers[i]))
        print("runway %s left" % (numbers[i]))
        print("runway %s right" % (numbers[i]))
        print("runway %s center" % (numbers[i]))


if __name__ == "__main__":
    main()
