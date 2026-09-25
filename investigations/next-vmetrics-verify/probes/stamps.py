#!/usr/bin/env python3
"""Was a release re-stamped after FontForge exported it?

Question: for each release named on the command line, print head.created/head.modified
(FontForge 20090914/20110222 write created = modified = export time, tottf.c sethead) and
the FFTM table (FontForge build stamp, source CreationTime/ModificationTime), plus the six
vertical metrics.  Used for the vmetrics verification's controls and for GiveYouGlory
(google/fonts b5efa9c32e8f ofl/giveyouglory/GiveYouGlory.ttf), the one clean-looking
FontForge 20110222 export whose offset-mode metrics the pre-2014 rule misses.

Run:  /home/fsanches/compartilhado/gftools/venv/bin/python3 stamps.py <font.ttf>...
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampToString as ts

for p in sys.argv[1:]:
    f = TTFont(p)
    h, o, hh = f['head'], f['OS/2'], f['hhea']
    same = 'EQUAL' if h.created == h.modified else 'DIFFER'
    print(p)
    print(f'  head created {ts(h.created)}  modified {ts(h.modified)}  {same}; '
          f'yMin/yMax {h.yMin}/{h.yMax}')
    if 'FFTM' in f:
        t = f['FFTM']
        print(f'  FFTM build {ts(t.FFTimeStamp)}  sourceCreated {ts(t.sourceCreated)}  '
              f'sourceModified {ts(t.sourceModified)}')
    print(f'  typo {o.sTypoAscender}/{o.sTypoDescender}  win {o.usWinAscent}/{o.usWinDescent}'
          f'  hhea {hh.ascent}/{hh.descent}')
