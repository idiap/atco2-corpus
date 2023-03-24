#!/usr/bin/env python3
## -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

""" Script to expand acronyms"""

import re
import sys

exception_rules = {
    "CPDLC": "C_P_D_L_C",
}

for l in sys.stdin:
    # don't expand whole lines written in capital letters,
    if len(l) > 20 and re.match("^[A-Z. ]+$", l):
        print(l)
        continue

    l_out = []
    for w in l.strip().split():
        if w in exception_rules:
            l_out.append(exception_rules[w])
        elif not re.match("^[A-Z][.]?[A-Z][A-Z.]*$", w):
            l_out.append(w)  # no expansion
        else:
            # roman numbers,
            if re.match("^II$|^III$|^IV$|^VI$|^VII$|^VIII$|^IX$|^XI$|^XV", w):
                l_out.append(w)
                continue
            # count capital letters,
            dummy, n_letter = re.subn("[A-Z]", "", w)
            if n_letter > 4:
                l_out.append(w)
                continue
                # don't expand words longer than 4 capital letters,
            # expand the acronym,
            w2, n = re.subn("\.", "_", w)
            w3 = "".join([w2[i] + "_" for i in range(len(w2))])
            w4, n = re.subn("_+", "_", w3)
            w5 = re.sub("_$", "", w4)
            l_out.append(w5)

    # print the line,
    print(" ".join(l_out))
