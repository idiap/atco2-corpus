#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright © <2022> Idiap Research Institute <contact@idiap.ch>
#
# SPDX-FileContributor: Karel Vesely <iveselyk@fit.vutbr.cz>
# SPDX-FileContributor: Juan Zuluaga-Gomez <jzuluaga@idiap.ch>
#
# SPDX-License-Identifier: MIT-License 


cat /dev/stdin | \
sed 's:i l s:|i_l_s|:g;
     s:d m e:|d_m_e|:g;
     s:t w a:|t_w_a|:g;
     s:v f r:|v_f_r|:g;
     s:t c a:|t_c_a|:g;
     s:d c u:|d_c_u|:g;
     s:a t c:|a_t_c|:g;
     s:u s:|u_s|:g;
     ' | \
sed 's: \([a-z]\) \([a-z]\) : \1_\2 :g;
     s: \([a-z]\) \([a-z]\)$: \1_\2:g;
     s:^\([a-z]\) \([a-z]\) :\1_\2 :g;
     s:^\([a-z]\) \([a-z]\)$:\1_\2:g;
     s:_\([a-z]\) \([a-z]\) :_\1_\2 :g;
     s:_\([a-z]\) \([a-z]\)$:_\1_\2:g;
     s:_\([a-z]\) \([a-z]\)_:_\1_\2_:g;
     s: \([a-z]\) \([a-z]\)_: \1_\2_:g;
     ' | \
sed 's: \([a-z]\) \([a-z]\) : \1_\2 :g;
     s: \([a-z]\) \([a-z]\)$: \1_\2:g;
     s:^\([a-z]\) \([a-z]\) :\1_\2 :g;
     s:^\([a-z]\) \([a-z]\)$:\1_\2:g;
     s:_\([a-z]\) \([a-z]\) :_\1_\2 :g;
     s:_\([a-z]\) \([a-z]\)$:_\1_\2:g;
     s:_\([a-z]\) \([a-z]\)_:_\1_\2_:g;
     s: \([a-z]\) \([a-z]\)_: \1_\2_:g;
     ' >/dev/stdout

