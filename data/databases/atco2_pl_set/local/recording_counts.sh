#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

if [ $# != 1 ]; then
  echo "Usage: $0 <list-of-wavs>"
  exit 1
fi

#list=get_cnet_lists_3/merged.list
#list=wav_list_nofilter.list

list=$1

# whole list
echo "TOTAL NUMBER OF RECORDINGS"
wc -l $list

# by LID score
echo "LID_SCORE"
for lid_score in "/0.5/" "/0.6/" "/0.7/" "/0.8/" "/0.9/"; do
  n_wavs=$(grep $lid_score $list | wc -l)
  echo "$lid_score $n_wavs"
done

# by SNR score
echo "SNR_VALUE"
for snr_value in $(seq -20 100); do
  n_wavs=$(grep "/$snr_value/" $list | wc -l)
  [ $n_wavs -gt 0 ] && echo "/$snr_value/ $n_wavs"
done


# by airport
# get airport codes,
awk '{ airport=$1; sub(/^.*\//, "", airport); sub(/_.*$/, "", airport);
       if(!(airport in airport_dict)) {
         print airport;
         airport_dict[airport] = 1;
       }
     }' $list > ${list}.airport_codes

# show amount per airport
echo "AIRPORT"
for airport in $(cat ${list}.airport_codes); do
  n_wavs=$(grep $airport $list | wc -l)
  echo "$airport $n_wavs"
done

