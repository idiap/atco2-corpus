#!/bin/bash
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
#
# SPDX-License-Identifier: MIT-License 

# ---------------------------------------------------------------------------
# CUSTOM PRONUNCIATIONS, SPECIFIC TO ATC DOMAIN:

mkdir -p prep

{ # LIST OF ATC-SPECIFIC PRONUNCIATIONS FOR LEXICON,
  echo "nine n ay1 n er0" # 'nine' pronounced as 'niner',
  echo "nines n ay1 n er0 z" # 'nines' pronounced as 'niners',
  echo "three t r iy1" # 'three' pronounced as 'tree',
  echo "cleared k l ih1 r" # 'cleared' pronounced as 'clear',
  echo "affirm ey1 f er2 m" # add 'alternative' pronunciation,
  echo "hotel hh ao1 t eh0 l" # 'UK/Europe' pronunciation,
  echo "hotel ao1 t eh0 l" # 'french' pronunciation,
} > prep/atc_specific_prons.txt


{ # LIST OF NON-STANDARD AIRLINE COMPANY PRONUNCIATIONS,
  echo "lufthansa l uw1 f t hh ah2 n s ah0" # 'lufthansa' pronounced normally,
  echo "hansa hh ah1 n s ah0" # 'lufhansa' pronounced as 'hansa',
  echo "stobart s t ow1 b er0 t" # 'stobart' pronounced normally,
  echo "scandinavian s k ah2 n d ih0 n ah1 v iy0 eh0 n" # 'scandinavian' pronounced normally,
  echo "scan s k ah1 n" # 'scandinavian' pronounced as 'scan',
  echo "scanwing s k ah1 n w ih0 ng" # normally,
  echo "scan s k ah1 n" # 'scanwing' as 'scan',
  echo "pilatus p iy0 l ey1 t ah0 s" # U.S. pron
  echo "pilatus p iy1 l ah0 t uh0 s" # Swiss pron
  echo "transavia t r ae0 n s aa1 v iy0 ah0" # U.S. pron
  echo "transavia t r aa1 n s aa0 v iy0 ah0" # E.U. pron
  echo "avia aa1 v iy0 ah0" # 'transavia' pronounced as 'avia',
  echo "ryanair r ay1 eh0 n eh2 r" # correct version,
  echo "ryanair r ay1 ah0 n eh2 r" # G2P version,
  echo "ryan r ay1 eh0 n" # 'ryanair' pronounced as 'ryan',
  echo "speedbird s p iy1 d b er2 d" # normal
  echo "bird b er1 d" # shortened
  echo "c_s_a_lines s iy1 eh1 s ey1 l ay1 n z" # shortened

  echo "croix k r ow1 ah0"
  echo "croix_rouge k r ow1 ah0 r uw2 zh"
  echo "voila v ow1 ah0 l ah0"
} > prep/airline_prons.txt


{ # LIST OF PLACES (this is manually created),

  # CZ,
  echo "brno b r n ow0"
  echo "turany t uw1 r zh ah0 n iy0"
  echo "breclav b r zh eh1 t s l ah0 v"
  echo "praha p r aa1 hh ah0"
  echo "ruzyne r uw1 z ih0 n y eh0"
  echo "ruzyne r uw1 z ih0 n y"
  echo "benesov b eh1 n eh0 sh ao0 v"

  # SVK,
  echo "kosice k ao1 sh ih0 t s eh0"
  echo "nitra n y ih1 t r ah0"
  echo "stefanikovo sh t eh1 f ah0 n ih0 k ow0 v ow0"
  echo "styri sh t ih1 r iy0"

  # SUI/FR,
  echo "bramois b r ah1 m ow0 aa0"
  echo "chalet sh ah1 l ey0"
  echo "chermignon ch er1 m iy0 n y ao1 n"
  echo "coeur k ae1 r"
  echo "d'azur d ah1 z uw0 r"
  echo "saint-martin s ah0 n t m ah0 r t ah0 n"
  echo "sallest s ah1 l eh0 s t"
  echo "val v ah0 l"
  echo "val-d'annivier v ah0 l d ah1 n ih0 v ih0 y eh0 r"

  # DE,
  echo "gerzensee g er1 t s n s eh0"
  echo "inselspital ih1 n s l sh p ih0 t ah2 l"
  echo "bundeshaus b uh1 n d eh0 s hh aw2 s"
  echo "burg b uw1 r g"
  echo "d'heren d hh eh1 r eh0 n"
  echo "muhleberg m uw1 eh0 l eh0 b er0 g"
  echo "muhleberg m uw1 l eh0 b er0 g"
  echo "ruschmeyer r uw2 sh m ah1 y eh0 r"

} > prep/places_prons.txt


{ # OTHER WORDS, NOT LISTED ELSEWHERE,

  # EN, ;-)
  echo "climbout k l ay1 m b aw2 t"
  echo "convinient k ah0 n v ih1 n iy0 eh0 n t"
  echo "corridor k ao1 r ih0 d ao0 r"
  echo "evacuated ih0 v ae1 k y uw0 ey2 t ih0 d"
  echo "operated ow1 p er0 ey2 t ih0 d"
  echo "toprate t ao1 p r ey0 t"

  # FR,
  echo "alle ah1 l eh0" # merci alle
  echo "beaucoup b ao1 k uw0"
  echo "bonsoir b ao1 n s ao0 aa2 r"
  echo "cinq s eh1 n k"
  echo "d'office d ao1 f ih0 s"
  echo "j'attends jh ah1 t ah0 n d"
  echo "journee jh uw1 r n eh0"
  echo "l'espace l eh1 s p ah0 s"
  echo "pardon p aa1 r d ow0 n"
  echo "pareil p aa1 r ey0"
  echo "pied p y eh0"
  echo "piste p iy1 s t"
  echo "poursuis p uw1 r s uw0 ih0"
  echo "pouvez p uw1 v eh0"
  echo "quais k w ey1"
  echo "quittez k ih1 t eh0"
  echo "rappeler r ah1 p eh0 l er0"
  echo "rapport r ah1 p ao0 r"
  echo "rarogne r ah1 r ow0 n y"
  echo "rebonjour r eh1 b ow0 n zh uh1 r"
  echo "resalut r eh1 s ah0 l uw0"
  echo "rive r ih1 v"
  echo "salut s ah1 l uw0"
  echo "salutation s ah1 l uw0 t ah0 s ih0 y ow0 n"
  echo "sept s eh1 t"
  echo "sous s uw1"
  echo "tard t aa1 r"
  echo "vingt v ah1 ng"
  echo "voile v ow1 ah0 l"
  echo "vous v uw1 z"

  # DE,
  echo "burgdorf b uw1 r g d ao0 r f"
  echo "flug f l uw1 g"
  echo "gute g uw1 t eh0"
  echo "salut s ah0 l uw1 t"
  echo "spaeter s p ae1 t r"

  # CZ,
  echo "ano ah1 n ao0"
  echo "bude b uw1 d eh0"
  echo "budem b uw1 d eh0 m"
  echo "budeme b uw1 d eh0 m eh0"
  echo "budete b uw1 d eh0 t eh0"
  echo "budu b uw1 d uw0"
  echo "ctvrte sh t v r t eh0"
  echo "ctyri sh t ih0 r zh iy0"
  echo "dekuji d y eh1 k uw0 y iy0"
  echo "dobry d ao1 b r iy0"
  echo "dost d ao1 s t"
  echo "peking p eh1 k ih0 ng"
  echo "pekne p y eh1 k n eh0"
  echo "pekny p y eh1 k n iy0"
  echo "slysenou s l ih1 sh eh0 n ao0 uw0"
  echo "spravne s p r ah1 v n y eh0"
  echo "spustit s p uw1 s t ih0 t"
  echo "takze t ah1 k z eh0"

  # SVK,
  echo "cez t s eh2 z"
  echo "chlapom k hh l ah1 p ao0 m"
  echo "dakujem d y ah1 k uw0 y eh2 m"
  echo "dame d ah1 m eh0"
  echo "drahu d r aa1 hh uw0"
  echo "finale f ih1 n ah0 l eh0"
  echo "hangare hh ah1 ng ah0 r eh0"
  echo "ked k eh0 d y"
  echo "krizujte k r ih1 z uw0 y t eh0"
  echo "levelovacou l eh1 v eh0 l ow1 v ah0 t s ow0"
  echo "moct m ow1 t s t"
  echo "odpoludnie ow1 d p ow0 l uh0 d n iy0 eh0"
  echo "ohlasim ow1 hh l aa0 s iy1 m"
  echo "pekne p eh1 k n eh0"
  echo "pekny p eh1 k n iy0"
  echo "popradu p ow1 p r aa0 d uw0"
  echo "povedzte p ow1 v eh0 d z t eh0"
  echo "prednost p r eh1 d n ow0 s t"
  echo "pristatie p r ih1 s t ah0 t y eh0"
  echo "profil p r ow1 f ih0 l"
  echo "radsej r ah1 d s hh ey0"
  echo "rolovacou r ow1 l ow0 v ah0 t s ow0"
  echo "rolovac- r ow1 l ow0 v ah0 t s"
  echo "rolujte r ow1 l uw1 y t eh0"
  echo "sedem s eh1 d y eh0 m"
  echo "senica s eh1 n ih0 t s ah0"
  echo "sest sh eh0 s t"
  echo "silne s ih1 l n eh0"
  echo "sme s m eh0"
  echo "tisic t ih1 s ih0 t s"
  echo "tymto t iy1 m t ow0"
  echo "tymze t ih1 m z eh0"
  echo "vam v ah1 m"
  echo "veza v iy1 eh0 zh ah0"
  echo "vyckavajte v ih1 t sh k ah0 v ah0 y t eh0"
  echo "vyckavat v ih1 t sh k ah0 v ah0 t"

} > prep/other_prons.txt


{ # LIST OF GREETINGS (this is manually created),
  #SUI,
  echo "gruezi_(greet) k r eh1 t s ih0"
  echo "gruezi_(greet) g r eh1 t s ih0"
  echo "gueten_abig_(greet) g uw1 t eh0 n aa2 b ih0 g"
  echo "ade_(bye) ah1 d eh0"
  echo "schone_namittag_(bye) sh ow1 n eh0 n ah1 m ih0 t ah2 g"
  echo "schone_nami_(bye) sh ow1 n eh0 n ah1 m ih0"

  # FR,
  echo "bonne_soiree_(bye) b ao1 n s ao1 ah0 r eh0"
  echo "a_toute_a_l'heure_(bye) ah0 t uh1 t ah0 l eh1 r"
  echo "aurevoir_(bye) ao1 r eh0 v ao0 aa2 r"

  #SWE,
  echo "godkvall_(greet) g uh1 d k v eh0 l"
  echo "hejda_(bye) hh ey1 d ow0"

  #DE,
  echo "schoenen_guten_abend_(bye) sh eh1 n eh0 n g uw1 t n ah0 b eh0 n d"
  echo "guten_morgen_(greet) g uw1 t eh0 n m ow1 r g eh0 n"
  echo "guten_morgen_(greet) g uw1 t n m ow1 r g n"
  echo "guten_tag_(greet) g uw1 t n t ah1 g"
  echo "guten_abend_(greet) g uw1 t n ah1 b eh0 n d"
  echo "danke_schoen_(thank) d ah1 n k eh0 sh eh1 n"
  echo "schoenen_tag_(bye) sh eh1 n eh0 n t ah1 g"
  echo "tschuess_(bye) t sh uh0 s"
  echo "servus_(hi/bye) s eh1 r v uh0 s"
  echo "danke_(thank) d ah1 n k eh0"
  echo "bis_spater_(bye) b ih1 s sh p eh1 t r"
  echo "beste b eh1 s t eh0"
  echo "schone sh eh1 n eh0"

  #NL,
  echo "hullo_(greet) hh ah1 l ow0"
  echo "goeden_dag_(greet) hh ow1 ih0 d ah0 hh"

  #CZ,
  echo "dobry_den_(greet) d ao1 b r iy0 d eh1 n"
  echo "dobre_rano_(greet) d ao1 b r eh0 r ah1 n aa0"
  echo "dobre_dopoledne_(greet) d ao1 b r eh0 d ao1 p ao0 l eh2 d n eh0"
  echo "dobre_odpoledne_(greet) d ao1 b r eh0 ao1 d p ao0 l eh2 d n eh0"
  echo "dobry_vecer_(greet) d ao1 b r iy0 v eh1 ch eh0 r"
  echo "dobry_podvecer_(greet) d ao1 b r iy0 p ao1 d v eh1 ch eh0 r"
  echo "pekny_den_(bye) p y eh1 k n iy0 d eh1 n"
  echo "hezky_vecer_(bye) hh eh1 s k iy0 v eh1 t sh eh0 r"
  echo "naslysenou_(bye) n ah1 s l ih0 sh eh0 n ow0"
  echo "naslys_(bye) n ah1 s l ih0 sh"
  echo "ahoj_(hi/bye) ah1 hh oy0"
  echo "podvecer p ao1 d v eh0 t sh eh0 r"
  echo "vecer v eh1 t sh eh0 r"
  echo "ahojte ah1 hh oy0 t eh0"

  # SVK,
  echo "dobre_popoludnie_(greet) d ao1 b r eh0 p ao1 p ao0 l uw1 d n y eh0"
  echo "pekne_popoludnie_(bye) p y eh1 k n eh0 p ao1 p ao0 l uw1 d n y eh0"
  echo "pekne_popoludnie_(bye) p eh1 k n eh0 p ao1 p ao0 l uw1 d n y eh0"
  echo "pekny_let_(bye) p y eh1 k n ih0 l eh0 t"
  echo "pekny_let_(bye) p eh1 k n ih0 l eh0 t"
  echo "dopocutia_(bye) d ao1 p ao0 t sh uh0 t y ah0"

} > prep/greetings_prons.txt

# prepare mapping tables for greetings corpus,
paste <(cut -d' ' -f1 prep/greetings_prons.txt | sed 's:_(.*$::' | tr '_' ' ') \
      <(cut -d' ' -f1 prep/greetings_prons.txt) \
      >../resources/greetings_prons_mapping.txt


