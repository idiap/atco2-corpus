#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

cnet_scores = "../data/atco_unsup_import_cnet/cnet_scores"

with open(cnet_scores, "r") as fd:
    for line in fd:
        rec, cnet, cnet_file = line.strip().split()

        # LKTB_BRNO_Approach-Radar_127_350MHz_20200904_135436 -> LKTB_BRNO_Approach-Radar_127_350MHz
        airport_and_freq = rec.rsplit("_", maxsplit=2)[0]

        dirname, eld, snr, filename = cnet_file.rsplit("/", maxsplit=3)

        print(airport_and_freq, eld, snr, cnet)
