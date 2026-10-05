#!/usr/bin/env python3
"""Does the Rust prototype filter compute what the independent model predicts, on every
offset-mode metric of both pairing tables -- and does it leave every other metric alone?

Question: for each style in families.tsv + families-next.tsv (the pipeline's pairing),
convert the unmodified source with tools/recipe.py's flags twice:
  base   the pinned converter (integration-ff-prs 17ea899 = upstream 496e904 + #91-#93)
  proto  the verifier's own build of that tree + next-vmetrics/runs/babelfont-proto.diff,
         with --fontforge-legacy-offset-metrics FIRST
and compare the six vertical metrics written into the .glyphs:
  - offset-mode win/hhea metrics: proto must equal probes/indep_bounds.py's `onc` rule
    (an independent parser), base must equal its `bf85` rule;
  - every other metric (typo, absolute-mode win/hhea) must be identical in base and proto.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY impl_vs_model.py > ../runs/impl_vs_model.txt
Scratch: /home/fsanches/compartilhado/sfd-reland-scratch/vmetrics-verify/implsweep/
"""
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indep_bounds as ib  # noqa: E402
import indep_sweep as isw  # noqa: E402

W = '/home/fsanches/compartilhado/gf-source-modernization'
PY = '/home/fsanches/compartilhado/gftools/venv/bin/python3'
BASE = ('/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/'
        'target-heights/release/babelfont')
PROTO = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics-verify/target/release/babelfont'
SCR = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics-verify/implsweep'
FLAG = '--fontforge-legacy-offset-metrics'
GKEYS = {'win_asc': 'winAscent', 'win_desc': 'winDescent', 'hhea_asc': 'hheaAscender',
         'hhea_desc': 'hheaDescender', 'typo_asc': 'typoAscender',
         'typo_desc': 'typoDescender'}
SFD = {'win_asc': ('OS2WinAscent', 'OS2WinAOffset'),
       'win_desc': ('OS2WinDescent', 'OS2WinDOffset'),
       'hhea_asc': ('HheadAscent', 'HheadAOffset'),
       'hhea_desc': ('HheadDescent', 'HheadDOffset')}


def gmetrics(path):
    t = open(path, encoding='utf-8').read()
    out = {}
    for k, g in GKEYS.items():
        m = re.search(r'name = %s;\s*\n\s*value = (-?\d+);' % g, t)
        out[k] = int(m.group(1)) if m else None
    return out


def model(sfd):
    hdr, glyphs, order2 = ib.parse(sfd)
    per = [b for b in (ib.glyph_bounds(ib.flat(glyphs, p), order2) for p in glyphs) if b]
    lo_on = math.floor(min(b[0][0] for b in per))
    hi_on = math.ceil(max(b[0][1] for b in per))
    lo_t = math.floor(min(b[2][0] for b in per))
    hi_t = math.ceil(max(b[2][1] for b in per))
    tmax_t = max(max(int(b[2][1]), 0) for b in per)
    tmin_t = min(min(int(b[2][0]), 0) for b in per)
    out = {}
    for k, (v, o) in SFD.items():
        if hdr.get(o, '0').strip() != '1':
            continue
        d = int(hdr.get(v, '0'))
        onc = {'win_asc': hi_on + d, 'win_desc': -lo_on + d,
               'hhea_asc': max(tmax_t, hi_on) + d, 'hhea_desc': min(tmin_t, lo_on) + d}[k]
        bf = {'win_asc': hi_t + d, 'win_desc': -lo_t + d, 'hhea_asc': hi_t + d,
              'hhea_desc': lo_t + d}[k]
        out[k] = (onc, bf)
    return out


def main():
    os.makedirs(SCR, exist_ok=True)
    env = dict(os.environ)
    agree = disagree = untouched_ok = untouched_bad = 0
    changed_styles = set()
    for table, c in isw.rows():
        style = c[6]
        env['FAMILIES'] = os.path.join(W, table)
        flags = subprocess.run([PY, os.path.join(W, 'tools/recipe.py'), style],
                               capture_output=True, text=True, env=env).stdout.split()
        sfd = isw.fetch(c)
        if sfd is None or not flags:
            print(f'{style}\tSKIP (no source or recipe)')
            continue
        gb, gp = os.path.join(SCR, style + '.base.glyphs'), os.path.join(SCR, style + '.proto.glyphs')
        rb = subprocess.run([BASE, sfd, gb] + flags, capture_output=True)
        rp = subprocess.run([PROTO, sfd, gp, FLAG] + flags, capture_output=True)
        if rb.returncode or rp.returncode:
            print(f'{style}\tCONVERT-FAILED base={rb.returncode} proto={rp.returncode}')
            continue
        mb, mp = gmetrics(gb), gmetrics(gp)
        mod = model(sfd)
        notes = []
        for k in GKEYS:
            if k in mod:
                onc, bf = mod[k]
                ok = mp[k] == onc and mb[k] == bf
                agree += ok
                disagree += not ok
                if not ok:
                    notes.append(f'{k}: proto={mp[k]} model-onc={onc} base={mb[k]} model-bf85={bf}')
            else:
                if mb[k] == mp[k]:
                    untouched_ok += 1
                else:
                    untouched_bad += 1
                    notes.append(f'{k} (not offset-mode) moved: base={mb[k]} proto={mp[k]}')
            if mb[k] != mp[k]:
                changed_styles.add(style)
        print(f'{style}\t' + ('; '.join(notes) if notes else 'ok'))
    print(f'\noffset-mode metrics: implementation = model {agree}, differs {disagree}')
    print(f'other metrics: unchanged {untouched_ok}, moved {untouched_bad}')
    print(f'styles whose .glyphs metrics the filter changes: {len(changed_styles)} '
          f'{sorted(changed_styles)}')


if __name__ == '__main__':
    main()
