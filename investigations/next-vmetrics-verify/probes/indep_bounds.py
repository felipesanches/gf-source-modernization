#!/usr/bin/env python3
"""Independent re-derivation of the vmetrics unit's offset-mode vertical metrics.

Question: for a FontForge .sfd whose win/hhea metrics are stated in OFFSET mode, what
does each candidate rule give, and which rule reproduces the paired release?  Written
from scratch (it does NOT reuse investigations/unifraktur/vmetrics_probe.py, which the
investigation under review used), so an agreement is two parsers agreeing.

Rules (FontForge C source quoted in the verifier's report, fetched into
sfd-reland-scratch/vmetrics-verify/ff/<commit>/):
  onc   FontForge before ee15007274e9 (2014-09-16): glyph box = floor/ceil of the
        ON-CURVE SplinePoints (SplineSetQuickBounds), refs decomposed with their
        transforms (dumpcomposite -> SplineCharLayerQuickBounds; dumpglyph ->
        SCttfApprox).  head box = union.  win = head.yMax + off, -head.yMin + off
        (WinBB).  hhea = max(trunc(true max), head.yMax) + off,
        min(trunc(true min), head.yMin) + off  (sethhead, C int conversion).
  allp  FontForge from ee15007274e9: as onc, but control points count too.
  bf85  babelfont 496e904 (PR #85): floor/ceil of the TRUE curve bounds for win and hhea.
  vmet  googlefontdirectory tools/bbox/vmetcheck.py at hg 927784141: int() of the
        TRUE bounds (FontForge boundingBox()), no offset.

Also prints the glyph that sets each extreme, so a claim like "Scaron sets win ascent"
can be checked.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY indep_bounds.py <file.sfd> <release.ttf>
Sources are the pipeline's own pairing (families-next.tsv): googlefontdirectory-hg
@52f780bc <lic>/<fam>/<source> vs google/fonts b5efa9c32e8f <shipped>.
"""
import math
import re
import sys

from fontTools.ttLib import TTFont


def parse(path):
    """Return (header dict, glyphs {orig_pos: dict}, order2 of layer 1)."""
    hdr = {}
    glyphs = {}
    order2 = None
    cur = None
    layer = None
    in_ss = False
    contour = None
    with open(path, 'rb') as fh:
        lines = fh.read().decode('latin-1').splitlines()
    for ln in lines:
        if cur is None:
            m = re.match(r'^(\w[\w]*):\s*(.*)$', ln)
            if ln.startswith('StartChar:'):
                cur = {'name': ln.split(':', 1)[1].strip(), 'contours': [], 'refs': [],
                       'pos': None}
                layer = None
                continue
            if m and m.group(1) not in hdr:
                hdr[m.group(1)] = m.group(2)
            m2 = re.match(r'^Layer:\s+1\s+(\d+)\s', ln)
            if m2:
                order2 = m2.group(1) == '1'
            continue
        if ln.startswith('EndChar'):
            glyphs[cur['pos']] = cur
            cur = None
            continue
        if ln.startswith('Encoding:'):
            cur['pos'] = int(ln.split()[3])
            continue
        if ln == 'Fore':
            layer = 1
            continue
        if ln == 'Back':
            layer = 0
            continue
        if ln.startswith('Layer:') and not in_ss:
            layer = int(ln.split()[1])
            continue
        if ln.startswith('SplineSet'):
            in_ss = True
            continue
        if ln.startswith('EndSplineSet'):
            in_ss = False
            continue
        if in_ss:
            if layer != 1:
                continue
            t = ln.split()
            if not t:
                continue
            op = t[-2] if len(t) >= 2 else None
            if op not in ('m', 'l', 'c'):
                continue
            nums = [float(x) for x in t[:-2]]
            flags = int(t[-1].split(',')[0])
            if op == 'm':
                contour = [('m', (nums[0], nums[1]), flags)]
                cur['contours'].append(contour)
            elif op == 'l':
                contour.append(('l', (nums[0], nums[1]), flags))
            else:
                contour.append(('c', (nums[0], nums[1]), (nums[2], nums[3]),
                                (nums[4], nums[5]), flags))
            continue
        if ln.startswith('Refer:') and layer == 1:
            t = ln.split()
            cur['refs'].append((int(t[1]), [float(x) for x in t[4:10]]))
    return hdr, glyphs, order2


def xf(p, m):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def compose(outer, inner):
    # point transformed by inner first, then outer
    a, b, c, d, e, f = inner
    A, B, C, D, E, F = outer
    return (A * a + C * b, B * a + D * b, A * c + C * d, B * c + D * d,
            A * e + C * f + E, B * e + D * f + F)


def flat(glyphs, pos, m=(1, 0, 0, 1, 0, 0), depth=0):
    """Contours of glyph `pos`, references decomposed, transformed by m."""
    g = glyphs[pos]
    out = []
    for ct in g['contours']:
        seg = []
        for s in ct:
            if s[0] in ('m', 'l'):
                seg.append((s[0], xf(s[1], m), s[2]))
            else:
                seg.append(('c', xf(s[1], m), xf(s[2], m), xf(s[3], m), s[4]))
        out.append(seg)
    for rpos, rm in g['refs']:
        if rpos in glyphs and depth < 20:
            out.extend(flat(glyphs, rpos, compose(m, rm), depth + 1))
    return out


def quad_ext(p0, q, p2):
    vals = [p0, p2]
    den = p0 - 2 * q + p2
    if den != 0:
        t = (p0 - q) / den
        if 0 < t < 1:
            vals.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * q + t * t * p2)
    return vals


def cubic_ext(p0, p1, p2, p3):
    vals = [p0, p3]
    a = -p0 + 3 * p1 - 3 * p2 + p3
    b = 2 * (p0 - 2 * p1 + p2)
    c = p1 - p0
    ts = []
    if abs(a) < 1e-12:
        if b != 0:
            ts.append(-c / b)
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r = math.sqrt(disc)
            ts += [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    for t in ts:
        if 0 < t < 1:
            vals.append((1 - t) ** 3 * p0 + 3 * t * (1 - t) ** 2 * p1
                        + 3 * t * t * (1 - t) * p2 + t ** 3 * p3)
    return vals


def glyph_bounds(contours, order2):
    """(on-curve y min/max, all-point y min/max, true y min/max) or None."""
    on, allp, tru = [], [], []
    for ct in contours:
        prev = None
        for s in ct:
            if s[0] in ('m', 'l'):
                p = s[1]
                on.append(p[1]); allp.append(p[1]); tru.append(p[1])
            else:
                c1, c2, p = s[1], s[2], s[3]
                on.append(p[1]); allp += [c1[1], c2[1], p[1]]
                if order2:
                    tru += quad_ext(prev[1], c1[1], p[1])
                else:
                    tru += cubic_ext(prev[1], c1[1], c2[1], p[1])
            prev = p
    if not on:
        return None
    return (min(on), max(on)), (min(allp), max(allp)), (min(tru), max(tru))


def trunc(x):
    return int(x)  # C double -> int: toward zero


def main(sfd, ttf):
    hdr, glyphs, order2 = parse(sfd)
    per = {}
    for pos, g in glyphs.items():
        b = glyph_bounds(flat(glyphs, pos), order2)
        if b:
            per[g['name']] = b
    has_notdef = any(g['name'] == '.notdef' for g in glyphs.values())
    print(f'sfd: {sfd}\nrelease: {ttf}\norder2={order2} glyphs={len(glyphs)} '
          f'with-outline={len(per)} has .notdef={has_notdef}')

    def ext(idx, which, fn):
        # glyph box per FontForge head: floor(min)/ceil(max) for box rules
        vals = [(fn(b[idx][which]), n, b[idx][which]) for n, b in per.items()]
        return vals

    res = {}
    for key, idx in (('onc', 0), ('allp', 1), ('true', 2)):
        ymax = max((math.ceil(b[idx][1]), n, b[idx][1]) for n, b in per.items())
        ymin = min((math.floor(b[idx][0]), n, b[idx][0]) for n, b in per.items())
        res[key] = (ymin, ymax)
        print(f'  {key:5s} box: yMin {ymin[0]} ({ymin[1]} {ymin[2]!r})  '
              f'yMax {ymax[0]} ({ymax[1]} {ymax[2]!r})')
    tmax = max((b[2][1], n) for n, b in per.items())
    tmin = min((b[2][0], n) for n, b in per.items())
    tmax_t = max(max(trunc(b[2][1]), 0) for b in per.values())
    tmin_t = min(min(trunc(b[2][0]), 0) for b in per.values())
    print(f'  true extremes: max {tmax[0]!r} ({tmax[1]}) min {tmin[0]!r} ({tmin[1]})')

    def st(v, o):
        return int(hdr.get(v, 0)), hdr.get(o, '0').strip() == '1'

    wa, wa_off = st('OS2WinAscent', 'OS2WinAOffset')
    wd, wd_off = st('OS2WinDescent', 'OS2WinDOffset')
    ha, ha_off = st('HheadAscent', 'HheadAOffset')
    hd, hd_off = st('HheadDescent', 'HheadDOffset')
    print(f'  stated: win {wa} (off={wa_off}) / {wd} (off={wd_off});'
          f' hhea {ha} (off={ha_off}) / {hd} (off={hd_off})')

    def rules():
        out = {}
        for r in ('onc', 'allp'):
            hmin, hmax = res[r][0][0], res[r][1][0]
            out[r] = {
                'win_asc': hmax + wa if wa_off else wa,
                'win_desc': -hmin + wd if wd_off else wd,
                'hhea_asc': max(tmax_t, hmax) + ha if ha_off else ha,
                # FontForge <=2014-10 took the descender's mode from HheadAOffset
                'hhea_desc': min(tmin_t, hmin) + hd if ha_off else hd,
            }
        fmin, fmax = res['true'][0][0], res['true'][1][0]
        out['bf85'] = {'win_asc': fmax + wa if wa_off else wa,
                       'win_desc': -fmin + wd if wd_off else wd,
                       'hhea_asc': fmax + ha if ha_off else ha,
                       'hhea_desc': fmin + hd if hd_off else hd}
        out['vmet'] = {'win_asc': trunc(tmax[0]), 'win_desc': -trunc(tmin[0]),
                       'hhea_asc': trunc(tmax[0]), 'hhea_desc': trunc(tmin[0])}
        return out

    f = TTFont(ttf)
    rel = {'win_asc': f['OS/2'].usWinAscent, 'win_desc': f['OS/2'].usWinDescent,
           'hhea_asc': f['hhea'].ascent, 'hhea_desc': f['hhea'].descent}
    print(f"  release head yMin/yMax {f['head'].yMin}/{f['head'].yMax}; "
          f"typo {f['OS/2'].sTypoAscender}/{f['OS/2'].sTypoDescender}")
    R = rules()
    print('  metric      release ' + ' '.join(f'{r:>6s}' for r in R))
    for k in rel:
        cells = []
        for r in R:
            v = R[r][k]
            cells.append(f'{v:>5d}{"*" if v == rel[k] else " "}')
        print(f'  {k:10s} {rel[k]:>7d} ' + ' '.join(cells))
    print('  (* = equals the release)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
