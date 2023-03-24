#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# This script parses the LISP format of ATCC database.

set -eu
lisp_txt=$1

cat $lisp_txt | \
  awk -v fname=$(basename ${lisp_txt%.txt}) \
  '/^\(\(FROM / { spk_csgn1=$2; # speaker 1,
                  sub(")$", "", spk_csgn1); # remove ")",
                  while(length(spk_csgn1) < 8) { spk_csgn1 = spk_csgn1"_"; } # add the underscores "_" so length is 8,
                }
  /^\(TO / { spk_csgn2=$2; # speaker 2,
                  sub(")$", "", spk_csgn2); # remove ")",
                  while(length(spk_csgn2) < 8) { spk_csgn2 = spk_csgn2"_"; } # add the underscores "_" so length is 8,
            }
  /^ \(TO / { spk_csgn2=$2; # speaker 2,
                  sub(")$", "", spk_csgn2); # remove ")",
                  while(length(spk_csgn2) < 8) { spk_csgn2 = spk_csgn2"_"; } # add the underscores "_" so length is 8,
            }
       /^ ?\(TEXT / { $1=""; text=$0; text_on=1; next; }
       /^ ?\(TIMES / { t_beg=$2;
                     t_end=$3; sub(")*$", "", t_end);
                     sub(")$", "", text);
                     print fname, fname"_"spk_csgn1"_"spk_csgn2"_", spk_csgn1"|"spk_csgn2, t_beg, t_end, text;
                     text_on=0; }
       { if(text_on) { text=text" "$0; }}' | \
  sed 's|  *| |g;' | \
  sed "s| (QUOTE \\([A-Z]*\\))|'\\1|g" | \
  sed 's|(UNINTELLIGIBLE)|<unk>|g;
       s|(LAUGHTER)|<laughter>|g;
       s|\(<unk>\)\([A-Z]\)|\1 \2|g;
       s|\([A-Z]\)\(<unk>\)|\1 \2|g;' | \
  sed "s|\\([A-Z]\\) '\\([A-Z]\\)|\1'\2|g; s|\`|'|g;"

