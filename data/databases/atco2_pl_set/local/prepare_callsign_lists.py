#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

import os
import sys


def main():

    # parse arguments from CLI
    (data_csv,) = sys.argv[1:]

    with open(data_csv, "r") as fd:
        for line in fd:
            key, wav_link = line.split(" ")

            # get wav_symlink_origin,
            try:
                wav_symlink_origin = os.readlink(wav_link)
            except:
                wav_symlink_origin = wav_link

            if not os.path.exists(wav_symlink_origin):
                print(
                    "Skipping, Broken symlink: %s -> %s"
                    % (wav_link, wav_symlink_origin),
                    file=sys.stderr,
                )
                continue

            # get .rttm_diar,
            callsigns_file = wav_symlink_origin.replace(".wav", ".boosting")
            if not os.path.exists(callsigns_file):
                print(
                    "Warning, empty callsign list, missing file: %s" % callsigns_file,
                    file=sys.stderr,
                )
                print(key)  # empty list,
            else:
                with open(callsigns_file, "r") as fd:
                    lines = fd.readlines()
                    assert len(lines) == 1
                    print(key, lines[0].strip())


if __name__ == "__main__":
    main()
