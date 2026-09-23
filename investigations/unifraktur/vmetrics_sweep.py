#!/usr/bin/env python3
"""Across every style in families.tsv: which offset-base rule reproduces the release?

For each style whose .sfd states at least one hhea/win metric in offset mode, compare
the release's value with vmetrics_probe.predict() under the ff2012, ffmaster and
babelfont(f725e6a) rules. Absolute-mode metrics are skipped (no base involved).
Reads sources from the repo archive (read-only, via git show); builds nothing.

    <python3 with fontTools> vmetrics_sweep.py [families.tsv]
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vmetrics_probe as vp  # noqa: E402

ARC = '/home/fsanches/compartilhado/upstream_repos/repo_archive'
TSV = sys.argv[1] if len(sys.argv) > 1 else '/home/fsanches/compartilhado/sfd-reland/families.tsv'


def main():
    rows = [l.rstrip('\n').split('\t') for l in open(TSV)][1:]
    tally = {r: [0, 0] for r in ('ff2012', 'ffmaster', 'babelfont')}
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        path = '%s/%s/%s' % (lic, fam, src) if kind == 'hg' else src
        blob = subprocess.run(['git', '-C', '%s/%s.git' % (ARC, base), 'show',
                               '%s:%s' % (commit, path)], capture_output=True)
        if blob.returncode:
            print('%-34s NO-SOURCE' % style)
            continue
        with tempfile.NamedTemporaryFile(suffix='.sfd') as t:
            t.write(blob.stdout); t.flush()
            try:
                res = vp.predict(t.name)
            except SystemExit as e:
                print('%-34s SKIP %s' % (style, e)); continue
        if res is None or not os.path.exists(shipped):
            continue
        _, out = res
        rel = vp.release_values(shipped)
        for label, _, _, _ in vp.FIELDS:
            o = out[label]
            if not o['offset']:
                continue
            marks = []
            for r in tally:
                ok = o[r] == rel[label]
                tally[r][0 if ok else 1] += 1
                marks.append('%s=%d%s' % (r, o[r], '' if ok else '*'))
            print('%-34s %-18s release=%-6d %s' % (style, label, rel[label], ' '.join(marks)))
    print('offset-mode metrics reproduced (match / miss):')
    for r, (a, b) in tally.items():
        print('  %-10s %d / %d' % (r, a, b))


if __name__ == '__main__':
    main()
