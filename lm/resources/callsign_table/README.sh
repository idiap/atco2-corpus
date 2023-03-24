#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

# other possible source of information:
# https://www.faa.gov/documentLibrary/media/Order/7340.2E_Basic.pdf (FAA 2014)

mkdir -p prep

join -a 1 -t'	' -j 2 -o 1.1,1.2,1.3,1.4,1.5 \
    <(sort -k2 -t'	' orig/callsign_table_major_corrected.csv) \
    <(sort -k2 -t'	' orig/callsign_table_wiki_filtered.csv) \
    >prep/major_wiki_leftjoin.csv

join -v 2 -t'	' -j 2 -o 2.1,2.2,2.3,2.4,2.5 \
    <(sort -k2 -t'	' orig/callsign_table_major_corrected.csv) \
    <(sort -k2 -t'	' orig/callsign_table_wiki_filtered.csv) \
    >prep/major_wiki_rightouter.csv

cat prep/major_wiki_leftjoin.csv prep/major_wiki_rightouter.csv | \
    sed '/IATA\s*ICAO/d' | sort -k2 -t'	' >prep/mapping_major_wiki.csv

join -a 1 -t'	' -j2 -o 1.1,1.2,1.3,1.4,1.5 \
    prep/mapping_major_wiki.csv \
    <(sort -k2 -t'	' orig/callsign_table_other.csv) \
    >prep/major_wiki_other_leftjoin.csv

join -v 2 -t'	' -j2 -o 2.1,2.2,2.3,2.4,2.5 \
    prep/mapping_major_wiki.csv \
    <(sort -k2 -t'	' orig/callsign_table_other.csv) \
    >prep/major_wiki_other_rightouter.csv

cat prep/major_wiki_other_leftjoin.csv prep/major_wiki_other_rightouter.csv | \
  sort -k2 -t'	' >prep/mapping_major_wiki_other.csv

echo "ICAO	Airline	CALL SIGN	Country" >prep/callsign_mapping.csv
sed '/^[[:space:]]*$/d' prep/mapping_major_wiki_other.csv | \
    awk -F $'\t' 'BEGIN {OFS=FS} {$4=toupper($4); print $0}' | \
    cut -d'	' -f2- | \
    sort -u \
    >>prep/callsign_mapping.csv


cat prep/callsign_mapping.csv | python3 callsign_filter.py >callsign_table.csv
