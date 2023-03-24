#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Martin Kocour <ikocour@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License

"""\
Script to import information of ATCO2-test-set-4h corpus.
The database is in XML format.
"""

import re
import sys
import numpy as np


def main():
    # parse args,
    list_of_info, keyprefix, rec2waypoints_fout, rec2callsign_list_fout = sys.argv[1:]

    rec2waypoints = []
    rec2callsign_list = []

    # MAIN LOOP over 'info' files,
    with open(list_of_info) as fd:
        for line in fd:
            print(line.strip(), file=sys.stderr)
            info_file = line.strip()

            # key for the records,
            reco_key = (
                keyprefix + info_file.split("/")[-1].rsplit(".", maxsplit=1)[0]
            )  # ../file123.xml.trans -> keyprefix+file123

            # search for waypoints,
            with open(info_file, "r") as info_fd:
                waypoints = ""
                for line in info_fd:
                    if re.search(r"^waypoints nearby:", line):
                        waypoints = re.sub(r"^waypoints nearby:", "", line).strip()
                        break
                # note: waypoints can be empty
                rec2waypoints.append([reco_key, waypoints])

            # parse the callsign lists,
            with open(info_file, "r") as info_fd:
                callsign_list = []
                for line in info_fd:
                    if re.search(r"^callsigns nearby:", line):
                        # lines after 'callsigns nearby:' look like: "BLA131 : All Charter One Three One"
                        # we take the callsign code (i.e. "BLA131") from each line.
                        for line in info_fd:
                            if len(line.strip()) == 0:
                                break
                            if re.search(r":", line):
                                # with ':' it is one per line,
                                callsign_list.append(line.strip().split()[0])  # BLA131
                            else:
                                # without ':' there is N callsign codes per line
                                callsign_list.extend(line.strip().split())  # BLA131
                # add the callsign list (it can be empty...)
                rec2callsign_list.append([reco_key, " ".join(callsign_list)])

    # save the outputs,
    np.savetxt(rec2waypoints_fout, rec2waypoints, fmt="%s")
    np.savetxt(rec2callsign_list_fout, rec2callsign_list, fmt="%s")


if __name__ == "__main__":
    main()
