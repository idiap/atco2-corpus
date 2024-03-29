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

num_bins = 35
hist_x_range = (-20, 50)

plt.figure(figsize=(6, 4.5))

# Add more colors to default cycler of 'plot()':
# https://datascientyst.com/full-list-named-colors-pandas-python-matplotlib/
import cycler

plt.rcParams["axes.prop_cycle"] = cycler.concat(
    plt.rcParams["axes.prop_cycle"],
    cycler.cycler("color", ["#FFD700", "#4B0082", "#CD853F"]),
)

for filt in airport_and_freqs:
    if filt == "EGPF_GLASGOW":
        continue  # we hide Glasgow, ATC recording is forbidden in UK!
    snr_filtered = data[data["f0"] == filt]["f2"]  # snr

    # weights arg could be used for durations...
    hist, x = np.histogram(
        snr_filtered, bins=num_bins, range=hist_x_range, density=True
    )
    plt.plot(x[1:], hist, label=filt)

# overall histogram
hist, x = np.histogram(data["f2"], bins=num_bins, range=hist_x_range, density=True)
plt.plot(
    x[1:], hist, label="ALL DATA", linewidth=6, color="k", linestyle="--", alpha=0.5
)

plt.legend()
plt.grid()
plt.xlabel("Signal-to-noise ratio (estimate)")
plt.ylabel("Nr. of recordings (normalized per airport)")

plt.savefig("show_snr.pdf", bbox_inches="tight")
plt.savefig("show_snr.png", bbox_inches="tight")
