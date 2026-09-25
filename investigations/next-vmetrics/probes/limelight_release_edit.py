#!/usr/bin/env python3
"""Were Limelight-Regular.ttf's vertical metrics set AFTER FontForge exported it, and
by what rule?

Pair: source googlefonts/googlefontdirectory-hg @52f780bc
ofl/limelight/src/Limelight-Regular-TTF.sfd (the families-next.tsv pairing), release
google/fonts b5efa9c32e8f ofl/limelight/Limelight-Regular.ttf (blob 879e7f9d, identical to
the hg file added by 927784141, Dave Crossland, 2012-08-20, "Updating limelight with
ttfautohint hinting and extended character set").

Prints, for this release and for control releases exported by FontForge with nothing
after it (MountainsofChristmas-Bold v1.002 at google/fonts 90abd17b4, NothingYouCouldDo),
the signals that tell a FontForge export from a later rewrite:

  1. head.created / head.modified next to FFTM sourceModified (= the .sfd's
     ModificationTime). FontForge 20090914/20110222 write created = modified = the
     export time (tottf.c sethead: time(&now)); a later tool that stamps only
     `modified` (ttfautohint does: tattf.c "update modification time") leaves them
     different.
  2. each glyf header's y-extent, classified: 'ff' = floor/ceil of the ON-CURVE points
     including the implied midpoints (FontForge before ee15007274e9), 'all' = the extent
     of every stored point (a recompiling tool such as fontTools), 'both', 'neither'.
  3. the six metrics under FontForge's own exporter rule for this .sfd (offsets added to
     the on-curve head box / truncated outline, typo to Ascent/Descent), and under the
     rule of googlefontdirectory's tools/bbox/vmetcheck.py at 927784141 -- int() of the
     font's true outline extremes (FontForge glyph.boundingBox()) for win/typo/hhea.

    /home/fsanches/compartilhado/gftools/venv/bin/python3 limelight_release_edit.py
"""
import datetime
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import offset_bases_sweep as ob  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

# scratch on /home, not the small /tmp tmpfs
tempfile.tempdir = '/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/tmp'
os.makedirs(tempfile.tempdir, exist_ok=True)

GF = '/home/fsanches/compartilhado/google/fonts'
HG = '/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git'
HGC = '52f780bc9d197280a9f430574e179a5f233c56b6'
U = 2082844800


def ts(v):
    return datetime.datetime.fromtimestamp(v, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')


def header_classes(font):
    glyf = font['glyf']
    raw = TTFont(font.reader.file.name)['glyf']
    counts = {'ff': 0, 'all': 0, 'both': 0, 'neither': 0}
    for name in font.getGlyphOrder():
        data = getattr(raw.glyphs[name], 'data', None)
        g = glyf[name]
        if not data or g.isComposite() or g.numberOfContours <= 0:
            continue
        ymin, ymax = int.from_bytes(data[4:6], 'big', signed=True), int.from_bytes(data[8:10], 'big', signed=True)
        coords, ends, flags = g.getCoordinates(glyf)
        ys_all = [c[1] for c in coords]
        ys_ff = []
        start = 0
        for end in ends:
            pts = list(range(start, end + 1))
            for k, i in enumerate(pts):
                j = pts[(k + 1) % len(pts)]
                if flags[i] & 1:
                    ys_ff.append(coords[i][1])
                elif not flags[j] & 1:
                    ys_ff.append((coords[i][1] + coords[j][1]) / 2)
            start = end + 1
        ff = (math.floor(min(ys_ff)), math.ceil(max(ys_ff))) == (ymin, ymax) if ys_ff else False
        al = (min(ys_all), max(ys_all)) == (ymin, ymax)
        counts['both' if ff and al else 'ff' if ff else 'all' if al else 'neither'] += 1
    return counts


def show(label, ttf):
    f = TTFont(ttf)
    h, t = f['head'], f['FFTM']
    print('%s' % label)
    print('  FFTM build %s  sourceModified %s' % (ts(t.FFTimeStamp - U), ts(t.sourceModified - U)))
    print('  head.created %s  head.modified %s  %s' % (
        ts(h.created - U), ts(h.modified - U),
        'EQUAL (nothing re-stamped it)' if h.created == h.modified else 'DIFFER (re-stamped after export)'))
    print('  head yMin/yMax %d/%d; glyf headers %s' % (h.yMin, h.yMax, header_classes(f)))


def main():
    rel = GF + '/ofl/limelight/Limelight-Regular.ttf'
    with tempfile.TemporaryDirectory() as d:
        moc = os.path.join(d, 'MoC-Bold-v1.002.ttf')
        open(moc, 'wb').write(subprocess.run(
            ['git', '-C', GF, 'show', '90abd17b4:apache/mountainsofchristmas/MountainsofChristmas-Bold.ttf'],
            capture_output=True, check=True).stdout)
        show('Limelight-Regular.ttf (release)', rel)
        show('MountainsofChristmas-Bold.ttf v1.002 (control)', moc)
        show('NothingYouCouldDo.ttf (control)', GF + '/ofl/nothingyoucoulddo/NothingYouCouldDo.ttf')
        sfd = os.path.join(d, 'Limelight-Regular-TTF.sfd')
        open(sfd, 'wb').write(subprocess.run(
            ['git', '-C', HG, 'show', HGC + ':ofl/limelight/src/Limelight-Regular-TTF.sfd'],
            capture_output=True, check=True).stdout)
        hdr, quad, b = ob.bases(sfd)
    I = lambda k: int(hdr[k].split()[0])  # noqa: E731
    lo, hi = b['_geo']['true']
    L = b['ff_legacy']
    f = TTFont(rel)
    rows = [
        ('OS/2.sTypoAscender', 'OS2TypoAscent', I('Ascent') + I('OS2TypoAscent'), int(hi), f['OS/2'].sTypoAscender),
        ('OS/2.sTypoDescender', 'OS2TypoDescent', -I('Descent') + I('OS2TypoDescent'), int(lo), f['OS/2'].sTypoDescender),
        ('OS/2.usWinAscent', 'OS2WinAscent', L['win_asc'] + I('OS2WinAscent'), int(hi), f['OS/2'].usWinAscent),
        ('OS/2.usWinDescent', 'OS2WinDescent', L['win_desc'] + I('OS2WinDescent'), -int(lo), f['OS/2'].usWinDescent),
        ('hhea.ascender', 'HheadAscent', L['hhea_asc'] + I('HheadAscent'), int(hi), f['hhea'].ascent),
        ('hhea.descender', 'HheadDescent', L['hhea_desc'] + I('HheadDescent'), int(lo), f['hhea'].descent),
    ]
    print('source: true outline extremes %.4f / %.4f; on-curve head box %s' % (lo, hi, b['_geo']['on']))
    print('%-20s %-24s %16s %18s %8s' % ('metric', 'source states', 'FontForge export', 'vmetcheck.py rule', 'release'))
    for label, key, ffv, vm, r in rows:
        stated = '%s %s (%s)' % (key, hdr[key].strip(), 'offset' if I(key.replace('Ascent', 'AOffset').replace('Descent', 'DOffset')) else 'absolute')
        print('%-20s %-24s %16d %18d %8d %s' % (label, stated, ffv, vm, r,
              'release = FontForge' if r == ffv else 'release = vmetcheck' if r == vm else 'neither'))


if __name__ == '__main__':
    main()
