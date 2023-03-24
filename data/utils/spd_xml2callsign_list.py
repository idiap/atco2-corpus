#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""
    Script to import the callsign list of ATCO2-PL-set and ATCO2-test-set-4h corpora. 
    The database is in XML format.
"""

import argparse
import sys

from bs4 import BeautifulSoup


class SpdSegment:
    def __init__(self, segment_xml):
        self.spkr = segment_xml.speaker.get_text()
        self.start = float(segment_xml.start.get_text())
        self.end = float(segment_xml.end.get_text())
        # callsign list (some files may not have it -> it will be empty)
        self.callsign_list = []
        try:
            self.callsign_list = list(eval(segment_xml.callsigns.get_text()))
        except:
            print("Warning, could not load callsigns", file=sys.stderr)

    def to_csv(self, sep=";", label=""):
        spkr, s, e, callsign_list = self.spkr, self.start, self.end, self.callsign_list
        s, e = f"{s:.2f}", f"{e:.2f}"
        return sep.join([label, spkr, s, e, " ".join(callsign_list)])


def get_args():
    parser = argparse.ArgumentParser(
        description="Converts XML transcripts (ReplayWell format) to CSV format."
    )
    parser.add_argument("--separator", help="CSV output separator", default=";")
    parser.add_argument("--label", help="label for output csv (1st column)", default="")
    parser.add_argument("xml", type=argparse.FileType("r"), help="Spoken Data XML file")
    return parser.parse_args()


def xml2csv(xml_fd, sep=";", label=""):
    xml = BeautifulSoup(xml_fd, features="xml")
    for seg_tag in xml.find_all("segment"):
        segment = SpdSegment(seg_tag)
        print(segment.to_csv(sep=sep, label=label))


def main():
    args = get_args()
    xml2csv(args.xml, sep=args.separator, label=args.label)


if __name__ == "__main__":
    main()
