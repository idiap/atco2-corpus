#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""
    Script to import the transcripts and metadata from ATCO2-PL-set and ATCO2-test-set-4h corpora. 
    The corpora are in XML format.
"""

import re
import sys

import numpy as np
from bs4 import BeautifulSoup


class SpdSegment:
    def __init__(self, segment_xml):
        """import data from xml"""
        self.start = float(segment_xml.start.get_text())
        self.end = float(segment_xml.end.get_text())
        self.spkr = segment_xml.speaker.get_text().strip()
        self.spkr_label = segment_xml.speaker_label.get_text().strip()
        self.text = segment_xml.find("text").get_text().strip()

    def to_csv(self, sep=";", reco_key="", airport_code=""):
        """create csv string, one segment per line"""
        # note: spkr_label is often empty,
        spkr, spkr_label, t_beg, t_end, text = (
            self.spkr,
            self.spkr_label,
            self.start,
            self.end,
            self.text,
        )

        # remove the NLP tags from the text,
        text = re.sub(r"(\[)", r" \1", text)
        text = re.sub(r"(\])", r"\1 ", text)
        text = re.sub(" +", " ", text).strip()

        # get the details for utterance id
        utt_key = "%s-%s--%06d-%06d" % (reco_key, spkr, t_beg * 100, t_end * 100)
        t_beg_ = "%.2f" % t_beg
        t_end_ = "%.2f" % t_end

        return sep.join(
            [utt_key, reco_key, spkr, spkr_label, airport_code, t_beg_, t_end_, text]
        )


def xml2csv(xml_fd, sep=";", reco_key="", airport_code=""):
    xml = BeautifulSoup(xml_fd, features="xml")
    ans = []
    for seg_tag in xml.find_all("segment"):
        # parse xml,
        segment = SpdSegment(seg_tag)
        # build csv record as string,
        segment_csv = segment.to_csv(
            sep=sep, reco_key=reco_key, airport_code=airport_code
        )
        ans.append(segment_csv)
    return ans


def main():
    # parse args,
    list_of_xml, xml_to_airport_mapping, keyprefix = sys.argv[1:]

    # load xml_to_airport_mapping,
    xml2airport = {
        xml: airport
        for xml, airport in np.loadtxt(xml_to_airport_mapping, dtype="object,object")
    }

    with open(list_of_xml) as fd:
        for line in fd:
            print(line.strip(), file=sys.stderr)

            xml = line.strip()
            airport_code = xml2airport[xml]
            reco_key = (
                keyprefix + xml.split("/")[-1].rsplit(".", maxsplit=2)[0]
            )  # ../file123.xml.trans -> keyprefix+file123

            with open(xml, "r") as xml_fd:
                ret = xml2csv(xml_fd, reco_key=reco_key, airport_code=airport_code)
                for r in ret:
                    print(r)


if __name__ == "__main__":
    main()
