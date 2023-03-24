#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

set -euxo pipefail

expand_callsign=expand_callsign.py

# LSZH callsigns from Alex,
cat /mnt/matylda5/iveselyk/ATCO2/DATA/zurich_callsigns_from_alex/callsigns/LSZH_*.csv | tr -d ' ' | sort | uniq >LSZH_from_alex.lst
$expand_callsign <LSZH_from_alex.lst >LSZH_from_alex.txt 2>LSZH_from_alex.rejected || { echo "ERROR!"; cat LSZH_from_alex.rejected; exit 1; }

# you can put here some databases or callsigns in ICAO format and the script will expand
# the callsigns into words
# OpenSky databases, example is:
cat /mnt/matylda5/iveselyk/ATCO2/DATA/opensky-network_datasets/covid-19/callsigns-world_2020_Q1_Q2.lst | $expand_callsign >callsigns-world_2020_Q1_Q2.txt 2>callsigns-world_2020_Q1_Q2.rejected
