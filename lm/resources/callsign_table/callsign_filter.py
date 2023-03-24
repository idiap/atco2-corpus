#!/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import re
import sys

callsigns = {}
for line in sys.stdin:
    row = line.split("\t")
    if len(row) < 3:
        print(f"ERROR: {row} contains less than 4 elements!", file=sys.stderr)
        continue
    elif len(row) == 3:
        print(f"WARNING: {row} contains less than 5 elements!", file=sys.stderr)
        icao, airline, callsign = row
        country = ""
    else:
        icao, airline, callsign, country = row

    callsign_ = re.sub(r"[_ -]*", "", callsign)
    if callsign_ in callsigns:
        if icao == callsigns[callsign_][0]:
            print(
                f"ERROR: Found callsign duplicate: '{callsign_}' in row: '{row}'\n...first seen in: '{callsigns[callsign_]}'",
                file=sys.stderr,
            )
            continue
        else:
            callsign2 = callsigns[callsign_][2]
            if callsign != callsign2:
                print(
                    f"WARNING: Replacing {callsign} with {callsign2}", file=sys.stderr
                )
            line = "\t".join([icao, airline, callsign2, country])
    else:
        callsigns[callsign_] = row

    print(line, end="")
