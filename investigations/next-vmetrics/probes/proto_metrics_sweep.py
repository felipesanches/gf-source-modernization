#!/usr/bin/env python3
"""Does the prototype --fontforge-legacy-offset-metrics filter move any style's
vertical metrics AWAY from its release, anywhere in the two pairing tables?

For every style in families.tsv and families-next.tsv (the pipeline's own pairing:
source from the repo archive at the pinned commit, release = the `shipped` column), this
converts the unmodified source twice with the flags tools/recipe.py gives it:

  upstream   the pinned converter (babelfont-rs upstream 496e904 + PRs #91-#93,
             integration-ff-prs 17ea899), which resolves offset-mode metrics with
             floor/ceil of the true outline bounds (PR #85)
  proposed   the scratch prototype (the same tree + the filter), with the filter
             placed FIRST, where recipe.py would put it

and compares the six hhea/win/typo values written into each .glyphs with the release.
No font is built: these values are settled in the .glyphs (fontc copies them). The
filter only changes win/hhea metrics the source states in offset mode, so a style
without them must come out identical.

    /home/fsanches/compartilhado/gftools/venv/bin/python3 proto_metrics_sweep.py \
        [--proto <babelfont>] [--upstream <babelfont>] [tables...]
Scratch: /home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/proto_sweep/
"""
import argparse
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

W = '/home/fsanches/compartilhado/sfd-reland'
ARC = '/home/fsanches/compartilhado/upstream_repos/repo_archive'
PY = '/home/fsanches/compartilhado/gftools/venv/bin/python3'
SCR = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/proto_sweep'
FLAG = '--fontforge-legacy-offset-metrics'
KEYS = [('winAscent', 'OS/2', 'usWinAscent'), ('winDescent', 'OS/2', 'usWinDescent'),
        ('hheaAscender', 'hhea', 'ascent'), ('hheaDescender', 'hhea', 'descent'),
        ('typoAscender', 'OS/2', 'sTypoAscender'), ('typoDescender', 'OS/2', 'sTypoDescender')]


def glyphs_metrics(path):
    t = open(path, encoding='utf-8').read()
    out = {}
    for k, _, _ in KEYS:
        m = re.search(r'name = %s;\s*\n\s*value = (-?\d+);' % k, t)
        out[k] = int(m.group(1)) if m else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--proto', default='/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/target/release/babelfont')
    ap.add_argument('--upstream', default='/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont')
    ap.add_argument('tables', nargs='*', default=[os.path.join(W, 'families.tsv'),
                                                  os.path.join(W, 'families-next.tsv')])
    a = ap.parse_args()
    os.makedirs(SCR, exist_ok=True)
    tally = {'upstream': [0, 0], 'proposed': [0, 0]}
    changed_styles = []
    for tsv in a.tables:
        print('== %s' % tsv)
        env = dict(os.environ, FAMILIES=tsv)
        rows = [l.rstrip('\n').split('\t') for l in open(tsv)][1:]
        for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
            path = '%s/%s/%s' % (lic, fam, src) if kind == 'hg' else src
            blob = subprocess.run(['git', '-C', '%s/%s.git' % (ARC, base), 'show',
                                   '%s:%s' % (commit, path)], capture_output=True)
            if blob.returncode:
                print('%-32s NO-SOURCE' % style)
                continue
            sfd = os.path.join(SCR, style + '.sfd')
            open(sfd, 'wb').write(blob.stdout)
            flags = subprocess.run([PY, os.path.join(W, 'tools', 'recipe.py'), style],
                                   capture_output=True, text=True, env=env).stdout.split()
            res = {}
            for label, bf, fl in (('upstream', a.upstream, flags),
                                  ('proposed', a.proto, [FLAG] + flags)):
                g = os.path.join(SCR, '%s.%s.glyphs' % (style, label))
                p = subprocess.run([bf, sfd, g] + fl, capture_output=True, text=True)
                if p.returncode:
                    res[label] = None
                    continue
                res[label] = glyphs_metrics(g)
            if res['upstream'] is None or res['proposed'] is None:
                print('%-32s CONVERT-FAILED' % style)
                continue
            f = TTFont(shipped)
            rel = {k: getattr(f[t], attr) for k, t, attr in KEYS}
            diffs = []
            for k, _, _ in KEYS:
                u, p = res['upstream'][k], res['proposed'][k]
                for label, v in (('upstream', u), ('proposed', p)):
                    tally[label][0 if v == rel[k] else 1] += 1
                if u != p or u != rel[k]:
                    diffs.append('%s rel=%s up=%s%s prop=%s%s' % (
                        k, rel[k], u, '' if u == rel[k] else '*', p, '' if p == rel[k] else '*'))
            if res['upstream'] != res['proposed']:
                changed_styles.append(style)
            print('%-32s %s' % (style, '; '.join(diffs) if diffs else 'all six match the release under both'))
    print('six vertical metrics x styles, matching the release (match / miss):')
    for k, (m, x) in tally.items():
        print('  %-9s %d / %d' % (k, m, x))
    print('styles whose metrics the filter changes: %d %s' % (len(changed_styles), ' '.join(changed_styles)))


if __name__ == '__main__':
    sys.exit(main())
