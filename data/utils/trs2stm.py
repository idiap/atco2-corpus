#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Trs2Stm
"""

import logging
import re
import sys
from argparse import ArgumentParser

import bs4 as bs

logging.basicConfig(
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
)


class Trs2Stm:
    """
    Class for conversion Transcriber(http://trans.sourceforge.net/en/presentation.php) to NIST STM
    """

    # __PATTERN_1SPK = re.compile('^spk[0-9]+$')
    # __PATTERN_2SPK = re.compile('^spk[0-9]+ spk[0-9]+$')

    def __init__(self, filename="", linked_audio_file=""):
        """
        Init
        :param filename: Transcriber file .trs
        :param linked_audio_name: Audio file linked to Transcriber's file
        """
        self.__trs_filename = ""  # filename from xml format .trs
        self.__linked_audio_file = linked_audio_file  # Specific linked name
        self.__segments = []
        # self.__seg_iter = None
        self.__spks = {}

        self.__start_flag = True
        self.__act_spk = None
        self.__cross_speakers = None
        self.__cross_start = False
        self.__start = "0"
        self.__end = "0"
        self.__end_time_turn = "0"
        self.__text = ""

        self.parse(filename, linked_audio_file)

    # def __iter__(self):
    #     self.__seg_iter = iter(self.__segments)
    #     return self
    #
    # def next(self):
    #     return next(self.__seg_iter)

    def parse(self, filename, linked_audio_file=""):
        """
        Parse TRS file
        :param filename: File name
        :param linked_audio_name: Name of audio file linked to transcription
        :return:
        """

        # For creation without file / parse nothing
        if not filename:
            return

        if linked_audio_file:
            self.__linked_audio_file = linked_audio_file
        else:
            self.__linked_audio_file = ""

        self.__segments = []

        # Load/Parse file in .trs format
        try:
            soup = bs.BeautifulSoup(open(filename, "r", encoding="utf-8"), "lxml-xml")
        except (IOError):
            logging.error("Error: %s: No such file IOError", filename)
            # return
            raise
        except (UnicodeDecodeError):
            logging.error("Error: %s: UnicodeDecodeError", filename)
            # return
            raise

        try:
            self.__trs_filename = soup.Trans["audio_filename"]
        except TypeError:
            logging.error(
                """ERROR parsing '%s'
                    The attribute <Trans audio_filename="..."> is missing.
                    Probably encoding error. Please check that XML header is:
                    <?xml version="1.0" encoding="UTF8"?>
                    if not, use:
                    <(uconv -f cp1250 -t utf8 $trs | sed 's:"CP1250":"UTF8":') """,
                filename,
            )
            # return
            raise

        if soup.Speakers:
            for spk in soup.Speakers.children:
                if spk.name == "Speaker":
                    self.__spks[spk["id"]] = (
                        spk["name"].replace(" ", ""),
                        spk["dialect"].replace(" ", "")
                        if "dialect" in spk.attrs
                        else "",
                        spk["accent"].replace(" ", "") if "accent" in spk.attrs else "",
                        self.__linked_audio_file if self.__linked_audio_file else "",
                    )

        for turn in soup.find_all("Turn"):
            self.__process_turn(turn)

    def __process_turn(self, turn):
        """
        Process Turn tag
        :param turn: BeautifulSoup's object contained <Turn> tag properties
        :return:
        """

        try:
            # self.__act_spk = turn['speaker']
            speakers = turn["speaker"].split()
            if len(speakers) == 2:
                self.__cross_speakers = [speakers[0], speakers[1]]
            elif len(speakers) > 2:
                logging.error(
                    "Error: Unexpected number of speakers - [%s]", turn["speaker"]
                )
            else:
                self.__act_spk = turn["speaker"]

        except KeyError:
            self.__act_spk = None
            if self.__spks:
                return  # On start was <Speakers> tag, <Turn> without spk => dump

        self.__start = "0"
        self.__end = "0"
        self.__start_flag = True
        self.__cross_start = False
        self.__end_time_turn = turn["endTime"]
        self.__text = ""

        for tag in turn.children:
            if tag.name is not None:
                if tag.name == "Sync":
                    self.__process_sync(tag)
                elif tag.name == "Event":
                    self.__process_event(tag)
                elif tag.name == "Who":
                    if self.__cross_start == True:
                        self.__save_segment()
                        self.__text = ""
                        # self.__cross_speakers = False
                    else:
                        self.__cross_start = True

                    self.__act_spk = self.__cross_speakers[int(tag["nb"]) - 1]
                    # print("Cross spk:", self.__cross_speakers[int(tag['nb']) - 1])

                elif tag.name == "Comment":
                    logging.info("IgnoringComment: %s" % tag)

                else:
                    logging.error("Error: Unknown tag - %s", tag.name)
            else:
                self.__process_text(tag)
        self.__save_segment(is_last=True)

    def __process_sync(self, tag):
        """
        Process Sync tag
        :param tag: BeautifulSoup's object contained <Sync> tag properties
        :return:
        """
        if self.__start_flag:
            self.__start_flag = False
            self.__start = tag["time"]
            return
        self.__end = tag["time"]
        self.__save_segment()
        self.__text = ""
        self.__start = self.__end

        if self.__cross_start == True:
            self.__segments[-2][4] = self.__end.strip()
            self.__cross_start = False

    def __process_event(self, tag):
        """
        Process Event tag
        :param tag: BeautifulSoup's object contained <Event> tag properties
        :return:
        """
        extent_attrib = tag["extent"]
        type_attrib = tag["type"]
        desc_attrib = tag["desc"]

        noise_types = {
            "lip": "<lipsmack>",
            "click": "<click>",
            "breath": "<breath>",
            "laughter": "<laughter>",
            "noise": "<noise>",
        }

        if type_attrib == "noise":
            if extent_attrib in set(["instantaneous", "prev", "previous", "next"]):
                if desc_attrib in set(noise_types.keys()):
                    noise = noise_types[desc_attrib]
                else:
                    noise = "<noise>"
                self.__text = self.__text + " " + noise
            elif extent_attrib == "begin":
                self.__text = self.__text + " <noise>"
            elif extent_attrib == "end":
                self.__text = self.__text + " </noise>"
            else:
                raise Exception("Error parsing 'noise' Event: %s" % tag)

        elif type_attrib == "language":
            if extent_attrib in set(["begin", "instantaneous", "prev", "previous"]):
                self.__text = self.__text + " " + ("<lang_%s>" % desc_attrib)
            elif extent_attrib == "end":
                self.__text = self.__text + " " + ("</lang_%s>" % desc_attrib)
            # the foreign word will become OOV:
            elif extent_attrib == "next":
                self.__text = self.__text + " " + ("<oov_%s:>" % desc_attrib)
            else:
                raise Exception("Error parsing 'language' Event: %s" % tag)

        elif type_attrib == "pronounce":
            if desc_attrib == "unintelligible":
                self.__text = self.__text + " " + "<unk>"
            elif desc_attrib == "*":
                self.__text = self.__text + " " + "<unk>"
            elif desc_attrib == "spelled":
                self.__text = self.__text + " " + "[spelled:]"
            elif desc_attrib == "whispered":
                self.__text = self.__text + " " + "[whispered:]"
            elif desc_attrib == "read" and extent_attrib == "next":
                self.__text = self.__text + " " + "[read:]"
            # arbitrary 'desc', fixing the pronunciation...
            elif extent_attrib == "prev" or extent_attrib == "previous":
                self.__text = self.__text + " " + ("[pron<<:%s]" % desc_attrib)
            elif extent_attrib == "next":
                self.__text = self.__text + " " + ("[pron>>:%s]" % desc_attrib)
            elif extent_attrib == "instantaneous":
                self.__text = self.__text + " " + ("[pron:%s]" % desc_attrib)
            # any other,
            else:
                print(
                    "WARNING: '<Event type=pronounce ..>' ignored : %s" % tag,
                    file=sys.stderr,
                )

        else:
            print("WARNING: '<Event ..>' ignored : %s" % tag, file=sys.stderr)

    def __process_text(self, tag):
        """
        Process text (transcription)
        :param tag: BeautifulSoup's object contained tag contain text
        :return:
        """
        if tag.string:
            self.__text = " ".join((self.__text, tag.string))

    def __save_segment(self, is_last=False):
        """
        Process text (transcription)
        :param tag: BeautifulSoup's object contained text (pseudo tag)
        :return:
        """
        self.__segments.append(
            [
                self.__trs_filename,
                "A",
                "-".join((self.__trs_filename, self.__act_spk))
                if self.__act_spk
                else self.__trs_filename,
                self.__start.strip(),
                self.__end.strip() if not is_last else self.__end_time_turn.strip(),
                self.__get_spk_attributes(),
                self.__text.strip().encode("utf-8"),
            ]
        )

        if self.__cross_start == True and is_last:
            self.__segments[-2][4] = self.__end_time_turn.strip()

    def __get_spk_attributes(self):
        """
        Get speaker's attribute as STM's column
        :return: String format like '<name,dialect,accent,linked_file>'
        """

        if self.__act_spk:
            return "".join(
                ("<", ",".join(self.__spks[self.__act_spk]).replace(" ", ""), ">")
            )
        else:
            if self.__linked_audio_file:
                return "".join(("<,,,", self.__linked_audio_file, ">"))
            else:
                return "<,,,>"

    def print_segments(self, separator=" "):
        """
        Print segments in STM format
        :param separator: Separator between columns stm
        :return:
        """
        for audio_filename, channel, spk, start, end, label, text in self.__segments:
            if text.strip():
                ptext = separator.join(
                    (
                        audio_filename,
                        channel,
                        spk,
                        start,
                        end,
                        label,
                        " ".join(text.decode("utf-8").split()),
                    )
                )
                print(ptext)


def main(args):
    """
    Main function
    :param args:
    :return:
    """
    trs_parser = Trs2Stm(args.trs, args.audio)
    trs_parser.print_segments()
    return 0


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert '.trs' file to '.stm' file")
    parser.add_argument("trs", help="trs file")
    parser.add_argument(
        "--audio", default="", help="audio file linked to transcription (not necessary)"
    )
    args = parser.parse_args()
    sys.exit(main(args))
