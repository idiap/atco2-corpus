#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import numpy as np
import matplotlib.pyplot as plt

plt.ion()

data = np.loadtxt("airport_eld_snr_cnet.airport-mapped.txt", dtype="object,f4,f4,f4")

# remap the airport strings: LKTB_BRNO_Tower_119_605MHz -> LKTB_BRNO
airport_remapped = []
for elem in data["f0"]:
    arr = elem.split("_")
    airport_remapped.append("%s_%s" % (arr[0], arr[1]))
data["f0"] = airport_remapped

airport_and_freqs = np.unique(data["f0"])

# get airports and counts,
airports_counts = []
for filt in airport_and_freqs:
    if filt == "EGPF_GLASGOW":
        continue  # we hide Glasgow, ATC recording is forbidden in UK!
    airports_counts.append((filt, np.sum(data["f0"] == filt)))

# descending sort by count,
airports_counts.sort(key=lambda tup: tup[1], reverse=False)

ax = plt.figure(figsize=(6, 4.5))

plt.barh([tup[0] for tup in airports_counts], [tup[1] for tup in airports_counts])

plt.xlabel("Count of recordings per airport")
plt.ticklabel_format(axis="x", style="plain")
plt.grid()

plt.subplots_adjust(left=0.3)
plt.savefig("show_segment_counts.pdf", bbox_inches="tight")
plt.savefig("show_segment_counts.png", bbox_inches="tight")
