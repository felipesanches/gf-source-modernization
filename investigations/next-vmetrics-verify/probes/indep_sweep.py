#!/usr/bin/env python3
"""Independent sweep: across every style both pairing tables hold, which offset-base
rule reproduces each release's offset-mode win/hhea metric?

Question: re-count, with a parser written from scratch (probes/indep_bounds.py, not the
investigation's vmetrics_probe.py), the claim "pre-2014 rule 305, #85 298, FontForge-master
295 of 328 offset-mode metrics in 82 styles; the pre-2014 rule never misses a metric #85
gets".  Rules as in indep_bounds.py: onc (pre-2014 FontForge), allp (FontForge from
ee15007274e9), bf85 (babelfont 496e904).  Also lists each style's FFTM build date and
whether HheadAOffset != HheadDOffset.

Pairing is the pipeline's own: families.tsv + families-next.tsv (column `source`, taken
from the repo archive at `commit`; release = column `shipped`, google/fonts b5efa9c32e8f).

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY indep_sweep.py > ../runs/indep_sweep.txt
"""
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indep_bounds as ib  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
import math  # noqa: E402

W = '/home/fsanches/compartilhado/gf-source-modernization'
ARC = '/home/fsanches/compartilhado/upstream_repos/repo_archive'
SCR = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics-verify/sweep'
KEYS = [('win_asc', 'OS2WinAscent', 'OS2WinAOffset'),
        ('win_desc', 'OS2WinDescent', 'OS2WinDOffset'),
        ('hhea_asc', 'HheadAscent', 'HheadAOffset'),
        ('hhea_desc', 'HheadDescent', 'HheadDOffset')]


def rows():
    for t in ('families.tsv', 'families-next.tsv'):
        with open(os.path.join(W, t)) as fh:
            next(fh)
            for ln in fh:
                c = ln.rstrip('\n').split('\t')
                yield t, c


def fetch(c):
    repo, fam, lic, kind, base, commit, style, src, shipped = c
    path = f'{lic}/{fam}/{src}' if kind == 'hg' else src
    out = os.path.join(SCR, style + '.sfd')
    os.makedirs(SCR, exist_ok=True)
    data = subprocess.run(['git', '-C', f'{ARC}/{base}.git', 'show', f'{commit}:{path}'],
                          capture_output=True).stdout
    if not data:
        return None
    with open(out, 'wb') as fh:
        fh.write(data)
    return out


def evaluate(sfd, ttf):
    hdr, glyphs, order2 = ib.parse(sfd)
    per = []
    for pos, g in glyphs.items():
        b = ib.glyph_bounds(ib.flat(glyphs, pos), order2)
        if b:
            per.append(b)
    if not per:
        return None
    box = {}
    for key, idx in (('onc', 0), ('allp', 1), ('true', 2)):
        box[key] = (math.floor(min(b[idx][0] for b in per)),
                    math.ceil(max(b[idx][1] for b in per)))
    tmax_t = max(max(int(b[2][1]), 0) for b in per)
    tmin_t = min(min(int(b[2][0]), 0) for b in per)
    f = TTFont(ttf)
    rel = {'win_asc': f['OS/2'].usWinAscent, 'win_desc': f['OS/2'].usWinDescent,
           'hhea_asc': f['hhea'].ascent, 'hhea_desc': f['hhea'].descent}
    fftm = '-'
    if 'FFTM' in f:
        fftm = datetime.datetime.utcfromtimestamp(
            f['FFTM'].FFTimeStamp - 2082844800).strftime('%Y-%m-%d')
    out = []
    ha_off = hdr.get('HheadAOffset', '0').strip() == '1'
    for k, v, o in KEYS:
        if hdr.get(o, '0').strip() != '1':
            continue
        d = int(hdr.get(v, '0'))
        r = {}
        for rule in ('onc', 'allp'):
            lo, hi = box[rule]
            r[rule] = {'win_asc': hi + d, 'win_desc': -lo + d,
                       'hhea_asc': max(tmax_t, hi) + d,
                       'hhea_desc': min(tmin_t, lo) + d}[k]
        lo, hi = box['true']
        r['bf85'] = {'win_asc': hi + d, 'win_desc': -lo + d, 'hhea_asc': hi + d,
                     'hhea_desc': lo + d}[k]
        out.append((k, rel[k], r))
    mixed = hdr.get('HheadAOffset', '0').strip() != hdr.get('HheadDOffset', '0').strip()
    return fftm, order2, out, mixed


def main():
    tot = {'onc': 0, 'allp': 0, 'bf85': 0}
    n = styles = 0
    onc_miss_bf_hit = []
    for t, c in rows():
        style, shipped = c[6], c[8]
        sfd = fetch(c)
        if sfd is None or not os.path.exists(shipped):
            print(f'{style}\tNO-SOURCE-OR-RELEASE')
            continue
        res = evaluate(sfd, shipped)
        if res is None:
            continue
        fftm, order2, out, mixed = res
        if not out:
            continue
        styles += 1
        for k, relv, r in out:
            n += 1
            marks = []
            for rule in tot:
                if r[rule] == relv:
                    tot[rule] += 1
                marks.append(f'{rule}={r[rule]}{"*" if r[rule] == relv else ""}')
            if r['onc'] != relv and r['bf85'] == relv:
                onc_miss_bf_hit.append((style, k))
            flag = '' if r['onc'] == relv else '  <- onc miss'
            print(f'{style}\t{fftm}\t{"quad" if order2 else "cubic"}\t{k}\trelease={relv}\t'
                  + ' '.join(marks) + (' MIXED-HHEA-MODE' if mixed else '') + flag)
    print(f'\n{n} offset-mode metrics in {styles} styles; matches: {tot}')
    print(f'onc misses where bf85 hits: {onc_miss_bf_hit}')


if __name__ == '__main__':
    main()
