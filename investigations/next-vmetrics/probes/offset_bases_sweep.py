#!/usr/bin/env python3
"""Which base does each FontForge vintage add an offset-mode win/hhea metric to, and
which one reproduces each release?

Question: across every style the pipeline pairs (families.tsv and families-next.tsv,
source from the repo archive at the pinned commit, release = the table's `shipped`
column), for every hhea/win metric the .sfd states in OFFSET mode, is the release's value
what this rule gives:

  ff_legacy  FontForge built before ee15007274e9 (2014-09-16), e.g. b69c9652 (20110222):
             head bbox = floor(min)/ceil(max) of each exported glyph's ON-CURVE points
             (SplineSetQuickBounds; interpolated quadratic points count, control points do
             not); win base = head.yMax / -head.yMin (WinBB);
             hhea base = int() (truncation toward zero) of the TRUE curve bounds
             (SplineCharLayerFindBounds), widened to the head bbox (sethhead).
  ff_master  FontForge from ee15007274e9 on: as ff_legacy, but QuickBounds also counts the
             control points, so the head bbox is floor/ceil of ALL points.
  bf496e904  babelfont upstream main 496e904 (PR #85): floor(min)/ceil(max) of the true
             curve bounds, for win and hhea alike.

It also reports each release's FFTM FontForge build stamp, and every style whose
HheadAOffset differs from HheadDOffset (FontForge <= 20110222 took the hhea DESCENDER's
mode from HheadAOffset -- tottf.c sethhead at b69c9652 -- a quirk no rule here models).

Reads sources with `git show` from the repo archive (read-only). Builds nothing.
Parsing, reference flattening and curve bounds reuse
investigations/unifraktur/vmetrics_probe.py.

    /home/fsanches/compartilhado/gftools/venv/bin/python3 offset_bases_sweep.py \
        [families.tsv ...]            (default: gf-source-modernization families.tsv families-next.tsv)
    ... offset_bases_sweep.py --sfd <file.sfd> <release.ttf>     (one pair, any source)
"""
import datetime
import math
import os
import subprocess
import sys
import tempfile

W = '/home/fsanches/compartilhado/gf-source-modernization'
sys.path.insert(0, os.path.join(W, 'investigations', 'unifraktur'))
import vmetrics_probe as vp  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

# scratch on /home, not the small /tmp tmpfs
tempfile.tempdir = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/tmp'
os.makedirs(tempfile.tempdir, exist_ok=True)

ARC = '/home/fsanches/compartilhado/upstream_repos/repo_archive'
UNIX_FROM_1904 = 2082844800
RULES = ('ff_legacy', 'ff_master', 'bf496e904')
# (label, sfd value key, sfd offset flag, base key)
FIELDS = [('OS/2.usWinAscent', 'OS2WinAscent', 'OS2WinAOffset', 'win_asc'),
          ('OS/2.usWinDescent', 'OS2WinDescent', 'OS2WinDOffset', 'win_desc'),
          ('hhea.ascender', 'HheadAscent', 'HheadAOffset', 'hhea_asc'),
          ('hhea.descender', 'HheadDescent', 'HheadDOffset', 'hhea_desc')]


def bases(sfd_path):
    hdr, glyphs, order2 = vp.parse(sfd_path)
    quad = order2.get(1, False)
    geos = [vp.geometry(c, quad) for c in vp.flatten(glyphs).values()]
    geos = [g for g in geos if g[0]]
    if not geos:
        return hdr, quad, None
    on_lo = math.floor(min(min(g[0]) for g in geos))
    on_hi = math.ceil(max(max(g[0]) for g in geos))
    all_lo = math.floor(min(min(g[1]) for g in geos))
    all_hi = math.ceil(max(max(g[1]) for g in geos))
    t_lo = min(g[2][0] for g in geos)
    t_hi = max(g[2][1] for g in geos)
    out = {}
    for rule, (hlo, hhi) in (('ff_legacy', (on_lo, on_hi)), ('ff_master', (all_lo, all_hi))):
        out[rule] = dict(win_asc=hhi, win_desc=-hlo,
                         hhea_asc=max(int(t_hi), hhi), hhea_desc=min(int(t_lo), hlo))
    out['bf496e904'] = dict(win_asc=math.ceil(t_hi), win_desc=-math.floor(t_lo),
                            hhea_asc=math.ceil(t_hi), hhea_desc=math.floor(t_lo))
    out['_geo'] = dict(on=(on_lo, on_hi), all=(all_lo, all_hi), true=(t_lo, t_hi))
    return hdr, quad, out


def release(path):
    f = TTFont(path)
    stamp = None
    if 'FFTM' in f:
        stamp = datetime.datetime.fromtimestamp(f['FFTM'].FFTimeStamp - UNIX_FROM_1904,
                                                datetime.UTC).strftime('%Y-%m-%d')
    return stamp, {'OS/2.usWinAscent': f['OS/2'].usWinAscent,
                   'OS/2.usWinDescent': f['OS/2'].usWinDescent,
                   'hhea.ascender': f['hhea'].ascent, 'hhea.descender': f['hhea'].descent}


def compare(style, sfd_path, shipped, tally, quirks):
    hdr, quad, b = bases(sfd_path)
    if b is None:
        return
    I = lambda k: int(hdr.get(k, '0').split()[0])  # noqa: E731
    if I('HheadAOffset') != I('HheadDOffset'):
        quirks.append('%s HheadAOffset=%d HheadDOffset=%d' % (style, I('HheadAOffset'),
                                                             I('HheadDOffset')))
    stamp, rel = release(shipped)
    for label, key, flag, bk in FIELDS:
        if not I(flag):
            continue
        v = I(key)
        marks = []
        for r in RULES:
            pred = b[r][bk] + v
            ok = pred == rel[label]
            tally[r][0 if ok else 1] += 1
            marks.append('%s=%d%s' % (r, pred, '' if ok else '*'))
        print('%-32s %-10s %-4s %-18s release=%-6d %s' % (
            style, stamp or 'no-FFTM', 'quad' if quad else 'cub', label, rel[label],
            ' '.join(marks)))


def main(argv):
    tally = {r: [0, 0] for r in RULES}
    quirks = []
    if argv[:1] == ['--sfd']:
        compare(os.path.basename(argv[1]), argv[1], argv[2], tally, quirks)
    else:
        for tsv in argv or [os.path.join(W, 'families.tsv'), os.path.join(W, 'families-next.tsv')]:
            print('== %s' % tsv)
            rows = [l.rstrip('\n').split('\t') for l in open(tsv)][1:]
            for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
                path = '%s/%s/%s' % (lic, fam, src) if kind == 'hg' else src
                blob = subprocess.run(['git', '-C', '%s/%s.git' % (ARC, base), 'show',
                                       '%s:%s' % (commit, path)], capture_output=True)
                if blob.returncode or not os.path.exists(shipped):
                    print('%-32s NO-SOURCE-OR-RELEASE' % style)
                    continue
                with tempfile.NamedTemporaryFile(suffix='.sfd') as t:
                    t.write(blob.stdout)
                    t.flush()
                    compare(style, t.name, shipped, tally, quirks)
    print('offset-mode win/hhea metrics reproduced (match / miss):')
    for r, (a, m) in tally.items():
        print('  %-10s %d / %d' % (r, a, m))
    print('styles whose HheadAOffset != HheadDOffset: %d' % len(quirks))
    for q in quirks:
        print('  ' + q)


if __name__ == '__main__':
    main(sys.argv[1:])
