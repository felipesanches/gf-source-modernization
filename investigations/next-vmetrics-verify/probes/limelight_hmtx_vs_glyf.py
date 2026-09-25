#!/usr/bin/env python3
"""Were Limelight-Regular.ttf's glyph boxes recomputed AFTER FontForge wrote hmtx?

Question: the table gate reports 9 RELEASE-STALE hmtx rows for Limelight-Regular
(baseline-next/Limelight-Regular.gate.txt).  For each, is the release's hmtx lsb
FontForge's on-curve x-minimum while its glyf xMin is the minimum over ALL stored points
(fontTools' recalcBounds)?  A tool that recompiles glyf with recalculated boxes but keeps
hmtx (a fontTools/ttx compile does exactly that) leaves this fingerprint; FontForge writes
lsb and glyf xMin from the same box, and ttfautohint keeps glyf headers.

Release: google/fonts b5efa9c32e8f ofl/limelight/Limelight-Regular.ttf (blob 879e7f9d).
Run:  /home/fsanches/compartilhado/gftools/venv/bin/python3 limelight_hmtx_vs_glyf.py
"""
from fontTools.ttLib import TTFont

REL = '/home/fsanches/compartilhado/google/fonts/ofl/limelight/Limelight-Regular.ttf'
f = TTFont(REL)
g, h = f['glyf'], f['hmtx']
n_mismatch = n_allpt = 0
for n in f.getGlyphOrder():
    gl = g[n]
    if gl.numberOfContours <= 0:
        continue
    c, _, fl = gl.getCoordinates(g)
    allmin = min(x for x, y in c)
    onmin = min(x for (x, y), ff in zip(c, fl) if ff & 1)
    if h[n][1] != gl.xMin:
        n_mismatch += 1
        n_allpt += gl.xMin == allmin
        print(f'{n:14s} hmtx lsb {h[n][1]:5d}  glyf xMin {gl.xMin:5d}  all-point min x {allmin:5d}'
              f'  explicit on-curve min x {onmin:5d}')
print(f'{n_mismatch} glyphs with hmtx lsb != glyf xMin; in {n_allpt} of them glyf xMin is the '
      f'all-point minimum')
