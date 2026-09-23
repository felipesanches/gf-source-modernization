#!/usr/bin/env python3
"""Does FontForge's pre-2012-05-14 height rule reproduce the releases the oracle misses?

tools/ff_heights_oracle.py ports FontForge MASTER's SFStandardHeight. When no glyph in
the list has a flat top, master takes the MEAN of the DISTINCT round/pointy heights.
Before fontforge commit 4d34d21ef866 (2012-05-14, "Patch by Khaled Hosny for
calculating wrong x and cap height for some fonts ... it was dividing by the wrong
value") the loop was

    for ( i=0; i<ccnt; ++i ) { test += curves[i].pos; tot += curves[i].cnt; }

i.e. the sum of the DISTINCT heights divided by the number of GLYPHS. The two agree
only when no two glyphs share a top. (Verified in fontforge/splinefont.c at
cd438ca99d76, the commit current at the FFTM FontForge timestamp of the
unifrakturmaguntia release, 2010-04-29T03:43:27Z.)

For each style in families.tsv: the value each rule exports, the release's, and the
release's FFTM FontForge build timestamp (the exporter's own source date).

    <venv python3> heights_pre2012_probe.py [families.tsv]
"""
import datetime
import subprocess
import sys

sys.path.insert(0, '/home/fsanches/compartilhado/sfd-reland/tools')
import ff_heights_oracle as o  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

TSV = sys.argv[1] if len(sys.argv) > 1 else '/home/fsanches/compartilhado/sfd-reland/families.tsv'
MAC_EPOCH = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)


def standard_height(sfd, lst, pre2012):
    """o.standard_height with the denominator of the curve mean switchable."""
    flats, curves = [], []
    for ch in o.expand(lst):
        gid = sfd.by_uni.get(ch)
        if gid is None:
            continue
        t, f = o.sc_max(sfd, gid)
        bucket = flats if f == o.FLAT else (curves if f != o.UNKNOWN else None)
        if bucket is None:
            continue
        for e in bucket:
            if e[0] == t:
                e[1] += 1
                break
        else:
            bucket.append([t, 1])
    if len(flats) == 1:
        result = flats[0][0]
    elif flats:
        top = max(c for _, c in flats)
        tied = [p for p, c in flats if c == top]
        result = sum(tied) / len(tied)
    elif not curves:
        return None
    else:
        den = sum(c for _, c in curves) if pre2012 else len(curves)
        result = sum(p for p, _ in curves) / den
    if sfd.blues:
        vals = []
        for tok in sfd.blues.replace('[', ' ').replace(']', ' ').split():
            try:
                vals.append(float(tok))
            except ValueError:
                break
        best, bestdiff = result, (sfd.ascent + sfd.descent) / 100.0
        for v in vals[0::2]:
            if abs(v - result) < bestdiff:
                best, bestdiff = v, abs(v - result)
        result = best
    return result


def main():
    rows = [l.rstrip('\n').split('\t') for l in open(TSV)][1:]
    tally = {'master': 0, 'pre2012': 0}
    checked = 0
    print('%-28s %-19s %-17s %-17s %s' % ('style', 'FontForge build', 'x mst/pre/rel',
                                          'cap mst/pre/rel', 'verdict'))
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        path = '%s/%s/%s' % (lic, fam, src) if kind == 'hg' else src
        r = subprocess.run(['git', '-C', '%s/%s.git' % (o.ARC, base), 'show',
                            '%s:%s' % (commit, path)], capture_output=True)
        if r.returncode:
            continue
        text = r.stdout.decode('utf-8', 'replace')
        sfd = o.Sfd(text)
        hdr = {k: v for k, v in (l.split(':', 1) for l in
                                 text.split('\nStartChar:', 1)[0].split('\n') if ':' in l)}
        sx = float(hdr['OS2XHeight']) if 'OS2XHeight' in hdr else 0
        sc = float(hdr['OS2CapHeight']) if 'OS2CapHeight' in hdr else 0
        f = TTFont(shipped)
        o2 = f['OS/2']
        if o2.version < 2:
            continue
        stamp = '-'
        if 'FFTM' in f:
            stamp = (MAC_EPOCH + datetime.timedelta(seconds=f['FFTM'].FFTimeStamp)
                     ).strftime('%Y-%m-%d %H:%M')
        res = {}
        for rule in ('master', 'pre2012'):
            x = int(sx) if sx else o.exported(standard_height(sfd, o.XH, rule == 'pre2012'))
            c = int(sc) if sc else o.exported(standard_height(sfd, o.CAP, rule == 'pre2012'))
            res[rule] = (x, c)
        rel = (o2.sxHeight, o2.sCapHeight)
        checked += 1
        v = []
        for rule in res:
            if res[rule] == rel:
                tally[rule] += 1
                v.append(rule)
        print('%-28s %-19s %-17s %-17s %s%s' % (
            style, stamp,
            '%d/%d/%d' % (res['master'][0], res['pre2012'][0], rel[0]),
            '%d/%d/%d' % (res['master'][1], res['pre2012'][1], rel[1]),
            '+'.join(v) if v else 'NEITHER',
            '  (stated in .sfd)' if (sx or sc) else ''))
    print('\nstyles whose release carries the fields: %d' % checked)
    for rule, n in tally.items():
        print('  %-8s reproduces %d' % (rule, n))


if __name__ == '__main__':
    main()
