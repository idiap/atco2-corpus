#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script for loading air traffic control (ATC) speech datasets for automatic speech recognition (ASR).
This script has been designed for ATC datasets that are in Kaldi format

Required files: text, wav.scp and segments files

- Databases
    - Training: 
        - ATCO2 corpora.
    - Testing:
        - ATCO2-test-set-1h or ATCO2-test-set-4h corpus.
"""

import os
import re

import datasets
import numpy as np
import soundfile as sf
from datasets.tasks import AutomaticSpeechRecognition

_CITATION = """\
@article{zuluaga2022atco2,
  title={ATCO2 corpus: A Large-Scale Dataset for Research on Automatic Speech Recognition and Natural Language Understanding of Air Traffic Control Communications},
  author={Zuluaga-Gomez, Juan and Vesel{\'y}, Karel and Sz{\"o}ke, Igor and Motlicek, Petr and others},
  journal={arXiv preprint arXiv:2211.04054},
  year={2022}
}    
@article{zuluaga2022does,
  title={How Does Pre-trained Wav2Vec 2.0 Perform on Domain Shifted ASR? An Extensive Benchmark on Air Traffic Control Communications},
  author={Zuluaga-Gomez, Juan and Prasad, Amrutha and Nigmatulina, Iuliia and others},
  journal={2022 IEEE Spoken Language Technology Workshop (SLT), Doha, Qatar},
  year={2022}
}
@article{zuluagabertraffic,
  title={BERTraffic: BERT-based Joint Speaker Role and Speaker Change Detection for Air Traffic Control Communications (submitted to @ SLT-2022)},
  author={Zuluaga-Gomez, Juan and Sarfjoo, Seyyed Saeed and Prasad, Amrutha and others},
  journal={2022 IEEE Spoken Language Technology Workshop (SLT), Doha, Qatar},
  year={2022}
}
"""

_DESCRIPTION = """\
ATC speech DATASET. This DataLoader works with data in Kaldi format.
    - We use the following files: text, segments and wav.scp 
            - text --> utt_id transcript
            - segments --> utt_id recording_id t_begin t_end
            - wav.scp --> recording_id /path/to/wav/
The default dataset is from ATCO2 project, a 1-hour sample: https://www.replaywell.com/atco2/download/ATCO2-ASRdataset-v1_beta.tgz
"""

_DATA_URL = "http://catalog.elra.info/en-us/repository/browse/ELRA-S0484/"

_HOMEPAGE = "https://github.com/idiap/w2v2-air-traffic"

logger = datasets.logging.get_logger(__name__)

# Our models work with audio data at 16kHZ,
_SAMPLING_RATE = int(16000)


class ATCDataASRConfig(datasets.BuilderConfig):
    """BuilderConfig for air traffic control datasets."""

    def __init__(self, **kwargs):
        """
        Args:
          data_dir: `string`, the path to the folder containing the files required to read: json or wav.scp
          **kwargs: keyword arguments forwarded to super.
        """
        super(ATCDataASRConfig, self).__init__(**kwargs)


class ATCDataASR(datasets.GeneratorBasedBuilder):

    DEFAULT_WRITER_BATCH_SIZE = 256
    DEFAULT_CONFIG_NAME = "all"
    BUILDER_CONFIGS = [
        # TRAIN, DEV AND TEST DATASETS
        ATCDataASRConfig(name="train", description="ATC train dataset."),
        ATCDataASRConfig(name="dev", description="ATC dev dataset."),
        ATCDataASRConfig(name="test", description="ATC test dataset."),
        # UNSUPERVISED DATASETS
        ATCDataASRConfig(name="unsupervised", description="ATC unsupervised dataset."),
    ]

    # provide some information about the Dataset we just gathered
    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "file": datasets.Value("string"),
                    "audio": datasets.features.Audio(sampling_rate=_SAMPLING_RATE),
                    "text": datasets.Value("string"),
                    "segment_start_time": datasets.Value("float"),
                    "segment_end_time": datasets.Value("float"),
                    "duration": datasets.Value("float"),
                }
            ),
            supervised_keys=("audio", "text"),
            homepage=_HOMEPAGE,
            citation=_CITATION,
            task_templates=[
                AutomaticSpeechRecognition(
                    audio_column="audio", transcription_column="text"
                )
            ],
        )

    def _split_generators(self, dlmanager):
        """Returns SplitGenerators."""

        split = self.config.name

        # UNSUPERVISED set (used only for decoding)
        if "unsupervised" in split:
            split_name = datasets.Split.TEST
        elif "test" in split or "dev" in split or "dummy" in split:
            split_name = datasets.Split.TEST
        # The last option left is: Train set
        else:
            split_name = datasets.Split.TRAIN

        # you need to pass a data directory where the Kaldi folder is stored
        filepath = self.config.data_dir

        return [
            datasets.SplitGenerator(
                name=split_name,
                # These kwargs will be passed to _generate_examples
                gen_kwargs={
                    "filepath": filepath,
                    "split": split,
                },
            )
        ]

    def _generate_examples(self, filepath, split):
        """You need to pass a path with the kaldi data, the folder should have
        audio: wav.scp,
        transcripts: text,
        timing information: segments
        """

        logger.info("Generating examples located in: %s", filepath)

        text_file = os.path.join(filepath, "text")
        wavscp = os.path.join(filepath, "wav.scp")
        segments = os.path.join(filepath, "segments")

        id_ = ""
        text_dict, wav_dict = {}, {}
        segments_dict, utt2wav_id = {}, {}

        line = 0
        # get the text file
        with open(text_file) as text_f:
            for line in text_f:
                if len(line.split(" ")) > 1:
                    id_, transcript = line.split(" ", maxsplit=1)
                    transcript = _remove_special_characters(transcript)
                    if len(transcript.split(" ")) == 0:
                        continue
                    if len(transcript) < 2:
                        continue
                    text_dict[id_] = transcript
                else:  # line is empty
                    # if unsupervised set, then it's normal. else, continue
                    if not "test_unsup" in self.config.name:
                        continue
                    id_ = line.rstrip().split(" ")[0]
                    text_dict[id_] = ""

        # get wav.scp and load data into memory
        with open(wavscp) as text_f:
            for line in text_f:
                if line:
                    if len(line.split()) < 2:
                        continue
                    id_, wavpath = line.split(" ", maxsplit=1)
                    # only selects the part that ends of wav, flac or sph
                    wavpath = [
                        x
                        for x in wavpath.split(" ")
                        if ".wav" in x or ".WAV" in x or ".flac" in x or ".sph" in x
                    ][0].rstrip()

                    # make the output
                    segment, sampling_rate = sf.read(wavpath, dtype=np.int16)
                    wav_dict[id_] = [wavpath.rstrip(), segment, sampling_rate]

        # get segments dictionary
        with open(segments) as text_f:
            for line in text_f:
                if line:
                    if len(line.split()) < 4:
                        continue
                    id_, wavid_, start, end = line.rstrip().split(" ")
                    segments_dict[id_] = start.rstrip(), end.rstrip()
                    utt2wav_id[id_] = wavid_

        for rec_id, text in text_dict.items():
            if rec_id in utt2wav_id and rec_id in segments_dict:

                # get audio data from memory and the path of the file
                wavpath, segment, sampling_rate = wav_dict[utt2wav_id[rec_id]]
                # get timing information
                seg_start, seg_end = segments_dict[rec_id]
                seg_start, seg_end = float(seg_start), float(seg_end)
                duration = round((seg_end - seg_start), 3)

                # get the samples, bytes, already cropping by segment,
                samples = _extract_audio_segment(
                    segment, sampling_rate, float(seg_start), float(seg_end)
                )

                # output data for given dataset
                example = {
                    "audio": {
                        "path": wavpath,
                        "array": samples,
                        "sampling_rate": sampling_rate,
                    },
                    "id": rec_id,
                    "file": wavpath,
                    "text": text,
                    "segment_start_time": format(float(seg_start), ".3f"),
                    "segment_end_time": format(float(seg_end), ".3f"),
                    "duration": format(float(duration), ".3f"),
                }

                yield rec_id, example


def _remove_special_characters(text):
    """Function to remove some special chars/symbols from the given transcript"""

    text = text.split(" ")
    # first remove words between [] and <>
    text = " ".join(
        [
            x
            for x in text
            if "[" not in x and "]" not in x and "<" not in x and ">" not in x
        ]
    )

    # regex with predifined symbols to ignore/remove,
    chars_to_ignore_regex2 = '[\{\[\]\<\>\/\,\?\.\!\u00AC\;\:"\\%\\\]|[0-9]'

    text = re.sub(chars_to_ignore_regex2, "", text).lower()
    sentence = text.replace("\u2013", "-")
    sentence = sentence.replace("\u2014", "-")
    sentence = sentence.replace("\u2018", "'")
    sentence = sentence.replace("\u201C", "")
    sentence = sentence.replace("\u201D", "")
    sentence = sentence.replace("ñ", "n")
    sentence = sentence.replace(" - ", " ")
    sentence = sentence.replace("-", "")
    sentence = sentence.replace("'", " ")
    
    return sentence.lower().rstrip()


def _extract_audio_segment(segment, sampling_rate, start_sec, end_sec):
    """Extracts segment of audio samples (as an ndarray) from the given segment."""
    # The dataset only contains mono audio.
    start_sample = int(start_sec * sampling_rate)
    end_sample = min(int(end_sec * sampling_rate), segment.shape[0])
    samples = segment[start_sample:end_sample]
    return samples
