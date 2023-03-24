#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License


DESCRIPTION = """\
Script for evaluating a Wav2Vec 2.0 / XLS-R model from Huggingface. 
We eval by greedy decoding and shallow fusion of 4-gram LM.

We need to:
    - Define a train and test dataset (or several). 
    - Process the data and obtain the vocabulary, etc.
    - Pre-process the training datasets (ARROW)
"""

import argparse
import os
import sys
from pathlib import Path

import evaluate
import torch
from datasets import load_dataset
from pyctcdecode import build_ctcdecoder
from transformers import (
    AutoModelForCTC,
    AutoProcessor,
    Wav2Vec2CTCTokenizer,
    Wav2Vec2ProcessorWithLM,
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_kenlm_processor(model_path, path_lm=None):
    """Function that instantiate the models and then gives them back for evaluation"""

    path_tokenizer = model_path

    # check that we send the right dir where the model is stored
    if Path(model_path).is_dir():
        processor = AutoProcessor.from_pretrained(path_tokenizer)
        model = AutoModelForCTC.from_pretrained(model_path)
    else:
        print(f"Error. Models were not found in {model_path}")

    # In case we don't pass any language model path, we just send back the model and processor
    if path_lm is None:
        return processor, None, None, model

    vocab = processor.tokenizer.convert_ids_to_tokens(
        range(0, processor.tokenizer.vocab_size)
    )
    # we need to add these tokens in the tokenizer
    vocab.append("<s>")
    vocab.append("</s>")

    # instantiate the tokenizer
    tokenizer = Wav2Vec2CTCTokenizer(
        path_tokenizer + "/vocab.json",
        unk_token="[UNK]",
        pad_token="[PAD]",
        word_delimiter_token="|",
    )

    # load CTC decoder WITH a LM and HuggingFace processor with CTC decoder and LM
    ctcdecoder_kenlm = build_ctcdecoder(
        labels=vocab,
        kenlm_model_path=path_lm,
    )
    # HuggingFace processor with CTC decoder (with LM)
    processor_ctc_kenlm = Wav2Vec2ProcessorWithLM(
        feature_extractor=processor.feature_extractor,
        tokenizer=tokenizer,
        decoder=ctcdecoder_kenlm,
    )

    return processor, processor_ctc_kenlm, model


def parse_args():
    """parser"""
    parser = argparse.ArgumentParser(description=DESCRIPTION,
        usage="Usage: eval_model.py --lm /path/to/lm_4g._binary --w2v2 /path/to/model/checkpoint --test-set /path/to/kaldi"
    )
    # reporting vars

    # optional,
    parser.add_argument(
        "--dl",
        "--data-loader-file",
        dest="data_loader",
        default="src/atc_data_loader.py",
        help="Data loader file, normally it should be in src/atc_data_loader.py",
    )
    parser.add_argument(
        "--lm",
        "--language-model",
        dest="path_lm",
        default=None,
        help="Directory with an in-domain LM. Needs to match the symbol table",
    )
    parser.add_argument(
        "--print-output",
        dest="print_output",
        default=False,
        help="whether to print the output into the models' fodler.",
    )

    # must give,
    parser.add_argument(
        "--w2v2",
        "--pretrained-model",
        dest="path_model",
        required=True,
        help="Directory with pre-trained Wav2Vec 2.0 model (or XLS-R-300m).",
    )
    parser.add_argument(
        "--test-set",
        dest="test_set",
        required=True,
        help="Directory with a test set folder in Kaldi format.",
    )

    return parser.parse_args()


def main():
    """Main code execution"""
    args = parse_args()

    path_model = args.path_model
    path_test_set = args.test_set
    path_lm = args.path_lm
    
    if args.print_output == "true" or args.print_output == "True":
        args.print_output = True

    if not Path(path_lm).is_file():
        print(f"You pass a path to LM ({path_lm}), but file does not exists")
        sys.exit(1)
    else:
        print("Integrating a LM by shallow fusion, results should be better")
    
    print("*** Loading the Wav2Vec 2.0 model, loading... ***")
    # Loading the models and the processors,tokenizer and also we load the models with CTC decoding and decoding CTC with LM
    processor, processor_ctc_kenlm, model = get_kenlm_processor(path_model, path_lm)

    if torch.cuda.is_available():
        model.to("cuda")

    print("*** Loading the dataset... ***")    
    # load the test set with our data loader
    test_dataset = load_dataset(
        args.data_loader,
        "test",
        data_dir=path_test_set,
        split="test",
        cache_dir = f".cache/eval/{path_test_set}",
    )

    def prepare_dataset(batch):
        """Function to prepare the batch of data to be passed to the model. It is used for testing"""
        audio = batch["audio"]

        # batched output is "un-batched" to ensure mapping is correct
        batch["input_values"] = processor(
            audio["array"], sampling_rate=audio["sampling_rate"]
        ).input_values[0]

        with processor.as_target_processor():
            batch["labels"] = processor(batch["text"]).input_ids
        return batch

    # remove samples shorter than 1 and then prepare test set,
    test_dataset = test_dataset.filter(lambda x: len(x["text"]) > 1)
    test_dataset = test_dataset.map(prepare_dataset, num_proc=4)

    def map_to_result(batch):
        """\
            Function to pass to the test_dataset. This allows us to perform batch processing. 
            We are generating the output of CTC decode and also CTC+LM (if LM provided)
            """

        # get the logits
        with torch.no_grad():
            input_values = torch.tensor(batch["input_values"], device=device).unsqueeze(0)
            logits = model(input_values).logits

        # get the prediction for the raw model with BeamSearch or LM
        pred_ids = torch.argmax(logits, dim=-1)
        batch["pred_str"] = processor.batch_decode(pred_ids)[0]
        batch["text"] = processor.decode(batch["labels"], group_tokens=False)

        # Perform BeamSearch + LM (if given), (we get [0] to only extract the string)
        if processor_ctc_kenlm is not None:
            batch["pred_str_ctc_lm"] = processor_ctc_kenlm.batch_decode(
                logits.cpu().numpy()
            ).text[0]
        else:
            batch["pred_str_ctc_lm"] = batch["text"]

        return batch

    # get the result by passing it to the model. If there is LM we perform BeamSearch CTC+LM (better performance)
    print(f"\n\nPerforming inference on dataset... Loading \n\n")
    results = test_dataset.map(map_to_result, batch_size=8, desc="inference")

    # Define evaluation metrics for testing, *i.e.* word error rate, character error rate
    eval_metrics = {metric: evaluate.load(metric) for metric in ["wer", "cer"]}

    wer_nolm = 100 * eval_metrics["wer"].compute(
        predictions=results["pred_str"], references=results["text"]
    )
    wer_lm_ctc = 100 * eval_metrics["wer"].compute(
        predictions=results["pred_str_ctc_lm"], references=results["text"]
    )

    if args.print_output is not None:
        output_folder = path_model + "/output/" + os.path.basename(os.path.dirname(Path(path_test_set)))

        # create the folder if not present
        if not os.path.isdir(f"{output_folder}"):
            os.makedirs(f"{output_folder}", exist_ok=True)
        
        # write the WER output to a file
        with open(f"{output_folder}/wer_metrics", "a") as o:
            o.write("---------------Test Statistics---------------\n")
            o.write(f"----LM used {path_lm}---\n")
            o.write("WER: \t\t{:2f}\n".format(wer_nolm))
            o.write("WER with CTC+LM: \t\t{:2f}\n".format(wer_lm_ctc))
            o.write("-------------END STATISTICS------------------\n")

        print(f"*** printing the ASR results in {output_folder}/hypo ***")
        with open(f"{output_folder}/gt", mode="w") as trans_f:
            with open(f"{output_folder}/hypo", mode="w") as hypo_f:
                for id, transcript, hypo in zip(results["id"], results["text"], results["pred_str_ctc_lm"]):
                    trans_f.write(f"{id} {transcript}\n")
                    hypo_f.write(f"{id} {hypo}\n")

        print("Done!")
            

if __name__ == "__main__":
    main()
