#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

python3 import_scores.py >airport_eld_snr_cnet.txt

# Edited manually, 2nd column added:
# cut -d' ' -f1 airport_eld_snr_cnet.txt | sort -u >airport_freqs_mapping.txt

cat airport_eld_snr_cnet.txt | \
../../../utils/apply_text_mapping.py airport_freqs_mapping.txt | \
grep -v SEATTLE \
>airport_eld_snr_cnet.airport-mapped.txt

