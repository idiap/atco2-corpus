#!/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License

import sys


def generate_waypoint_pattern(fmt, waypoint_list):
    """fmt is a string of this type: "... %s ..." """
    for wpt in waypoint_list:
        print(fmt % wpt)


def main():

    # wpt_file = os.path.dirname(os.path.realpath(__file__)) + "/../../waypoints.txt"
    wpt_file = sys.argv[1]
    with open(wpt_file, "r") as fd:
        wpts = [l.strip() for l in fd]

    # the most ususal case,
    for ii in range(3):
        generate_waypoint_pattern("direct to %s", wpts)

    generate_waypoint_pattern("direct %s", wpts)
    generate_waypoint_pattern("turn %s", wpts)
    generate_waypoint_pattern("after %s", wpts)
    generate_waypoint_pattern("at %s", wpts)


if __name__ == "__main__":
    main()
