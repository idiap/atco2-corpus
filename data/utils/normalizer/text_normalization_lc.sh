#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 

# Main file to apply mapping rules and standardize ATC text

resources_dir=$(dirname $0)/

# apply several mappings to input text, check the mapping rules for more information
$resources_dir/apply_text_mapping.py $resources_dir/mapping_tables/general_mapping.txt | \
$resources_dir/apply_text_mapping.py $resources_dir/mapping_tables/greetings_prons_mapping.txt | \
$resources_dir/apply_text_mapping.py $resources_dir/mapping_tables/callword_rules.txt | \
$resources_dir/apply_text_mapping.py $resources_dir/mapping_tables/callsign_underscore_mapping.txt | \
cat

