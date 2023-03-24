#!/bin/bash
set -euxo pipefail

# callsign code-words,
tail -n+2 ../../../resources/callsign_table/callsign_table.csv | \
  awk -v FS="\t" '{ print $3; }' | uconv -f utf8 -t utf8 -x "Any-Lower" | \
  tr ' -' '_' | sort | uniq > callsign_codewords.txt

# airline companies,
tail -n+2 ../../../resources/callsign_table/callsign_table.csv | \
  awk -v FS="\t" '{ print $2; }' | uconv -f utf8 -t utf8 -x "Any-Lower" | iconv -f utf8 -t "ascii//TRANSLIT" | \
  tr ',-' ' ' | sort | uniq | grep '^[a-z ]*$' > airline_companies.txt

