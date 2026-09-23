#!/usr/bin/env python3
"""Which base does FontForge's exporter add an offset-mode hhea/win metric to?

A FontForge source may state a vertical metric as an OFFSET (OS2WinDOffset: 1,
HheadDOffset: 1, ...): the exported value is a base FontForge computes at export
time plus the stated delta. This probe computes, from the .sfd alone, the base
under three rules and prints the metric each rule yields, beside the release's.

  ff2012  FontForge's exporter as of 2012-06-28 (tottf.c/splineutil.c at
          e4aa2e030c7d), which is also what the 2010 build that made the
          unifrakturmaguntia release did:
            head.yMin/yMax = min floor / max ceil of SplineSetQuickBounds over each
                             exported glyph -- ON-CURVE points only (interpolated
                             on-curve points included; off-curve points NOT);
            win   base     = head.yMax, -head.yMin                    (WinBB)
            hhea  base     = int() -- truncation toward zero -- of the TRUE curve
                             bounds (SplineCharLayerFindBounds), widened to
                             head.yMin/yMax when those reach further  (sethhead)
  ffmaster FontForge master (splineutil.c today): QuickBounds also counts the
          off-curve control points; the rest as ff2012.
  babelfont gf-sfd-conversion f725e6a (offsetmetrics.rs): round() of the true
          curve bounds, for win AND hhea alike.

    <python3 with fontTools> vmetrics_probe.py <file.sfd> [<release.ttf>]
"""
import math
import re
import sys

from fontTools.misc.bezierTools import calcCubicBounds, calcQuadraticBounds


def parse(path):
    hdr, glyphs = {}, {}
    order2 = {}
    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().split('\n')
    i = 0
    cur = None
    layer = None
    in_ss = False
    while i < len(lines):
        ln = lines[i]
        if cur is None:
            m = re.match(r'^(\w+):\s*(.*)$', ln)
            if ln.startswith('StartChar:'):
                cur = {'name': ln.split(':', 1)[1].strip(), 'contours': [], 'refs': [],
                       'enc': None}
                layer = None
            elif m and m.group(1) == 'Layer':
                p = m.group(2).split()
                order2[int(p[0])] = p[1] == '1'
            elif m and m.group(1) not in hdr:
                hdr[m.group(1)] = m.group(2)
            i += 1
            continue
        if ln.startswith('EndChar'):
            glyphs[cur['name']] = cur
            cur = None
        elif ln.startswith('Encoding:'):
            cur['enc'] = [int(x) for x in ln.split(':', 1)[1].split()[:3]]
        elif ln == 'Fore':
            layer = 1
        elif ln == 'Back':
            layer = 0
        elif ln.startswith('Layer: '):
            layer = int(ln.split()[1])
        elif ln == 'SplineSet':
            in_ss = True
            contour = None
        elif ln == 'EndSplineSet':
            in_ss = False
        elif in_ss and layer == 1:
            t = ln.split()
            if not t:
                pass
            elif 'm' in t:
                k = t.index('m')
                x, y = float(t[k - 2]), float(t[k - 1])
                contour = [('m', (x, y), t[k + 1] if k + 1 < len(t) else '0')]
                cur['contours'].append(contour)
            elif 'l' in t:
                k = t.index('l')
                contour.append(('l', (float(t[k - 2]), float(t[k - 1])),
                                t[k + 1] if k + 1 < len(t) else '0'))
            elif 'c' in t:
                k = t.index('c')
                v = [float(x) for x in t[k - 6:k]]
                contour.append(('c', ((v[0], v[1]), (v[2], v[3]), (v[4], v[5])),
                                t[k + 1] if k + 1 < len(t) else '0'))
        elif ln.startswith('Refer:') and layer == 1:
            t = ln.split()
            # Refer: <orig_pos> <unicode> <S|N> xx xy yx yy dx dy <flags>
            cur['refs'].append((int(t[1]), [float(x) for x in t[4:10]]))
        i += 1
    return hdr, glyphs, order2


def flatten(glyphs):
    """Each glyph's contours with references resolved (full affine transform)."""
    by_pos = {g['enc'][2]: g for g in glyphs.values() if g['enc']}
    memo = {}

    def tf(m, pt):
        xx, xy, yx, yy, dx, dy = m
        return (xx * pt[0] + yx * pt[1] + dx, xy * pt[0] + yy * pt[1] + dy)

    def get(g):
        if g['name'] not in memo:
            cs = [list(c) for c in g['contours']]
            for pos, m in g['refs']:
                for c in get(by_pos[pos]):
                    cs.append([(k, tf(m, p) if k != 'c' else tuple(tf(m, q) for q in p), f)
                               for k, p, f in c])
            memo[g['name']] = cs
        return memo[g['name']]

    return {n: get(g) for n, g in glyphs.items()}


def geometry(contours, quad):
    """(on-curve ys, all-point ys, true-bounds (ymin,ymax))."""
    on, allp, lo, hi = [], [], math.inf, -math.inf
    for c in contours:
        prev = None
        for kind, pts, _ in c:
            if kind in ('m', 'l'):
                on.append(pts[1]); allp.append(pts[1])
                lo, hi = min(lo, pts[1]), max(hi, pts[1])
                prev = pts
            else:
                c1, c2, p = pts
                on.append(p[1]); allp.extend([c1[1], c2[1], p[1]])
                if quad:
                    b = calcQuadraticBounds(prev, c1, p)
                else:
                    b = calcCubicBounds(prev, c1, c2, p)
                lo, hi = min(lo, b[1]), max(hi, b[3])
                prev = p
    return on, allp, (lo, hi)


def predict(sfd):
    """Per rule, the value each offset-mode (or absolute) hhea/win metric exports as."""
    hdr, glyphs, order2 = parse(sfd)
    quad = order2.get(1, False)
    geos = {n: geometry(c, quad) for n, c in flatten(glyphs).items()}
    ink = {n: v for n, v in geos.items() if v[0]}
    if not ink:
        return None

    def argmin(f):
        n = min(ink, key=f)
        return n, f(n)

    def argmax(f):
        n = max(ink, key=f)
        return n, f(n)

    head_on = (argmin(lambda n: math.floor(min(ink[n][0]))),
               argmax(lambda n: math.ceil(max(ink[n][0]))))
    head_all = (argmin(lambda n: math.floor(min(ink[n][1]))),
                argmax(lambda n: math.ceil(max(ink[n][1]))))
    true_lo = argmin(lambda n: ink[n][2][0])
    true_hi = argmax(lambda n: ink[n][2][1])
    geo = dict(quad=quad, head_on=head_on, head_all=head_all, true_lo=true_lo,
               true_hi=true_hi)

    def I(k):
        return int(hdr.get(k, '0').split()[0])

    bases = {}
    for rule, (hmin, hmax) in (('ff2012', (head_on[0][1], head_on[1][1])),
                               ('ffmaster', (head_all[0][1], head_all[1][1]))):
        tmin, tmax = int(true_lo[1]), int(true_hi[1])
        bases[rule] = dict(win_asc=hmax, win_desc=-hmin, hhea_asc=max(tmax, hmax),
                           hhea_desc=min(tmin, hmin), head_ymin=hmin, head_ymax=hmax)
    # Rust f64::round rounds half away from zero; Python's round() does not
    def rround(x):
        return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)
    bases['babelfont'] = dict(win_asc=rround(true_hi[1]), win_desc=-rround(true_lo[1]),
                              hhea_asc=rround(true_hi[1]), hhea_desc=rround(true_lo[1]),
                              head_ymin=None, head_ymax=None)
    out = {}
    for label, key, flag, rk in FIELDS:
        off, v = I(flag), I(key)
        out[label] = dict(stated=v, offset=bool(off),
                          **{r: (bases[r][rk] + v if off else v) for r in bases})
    out['head.yMin'] = {r: bases[r]['head_ymin'] for r in bases}
    out['head.yMax'] = {r: bases[r]['head_ymax'] for r in bases}
    return geo, out


FIELDS = [('OS/2.usWinAscent', 'OS2WinAscent', 'OS2WinAOffset', 'win_asc'),
          ('OS/2.usWinDescent', 'OS2WinDescent', 'OS2WinDOffset', 'win_desc'),
          ('hhea.ascender', 'HheadAscent', 'HheadAOffset', 'hhea_asc'),
          ('hhea.descender', 'HheadDescent', 'HheadDOffset', 'hhea_desc')]


def release_values(ttf):
    from fontTools.ttLib import TTFont
    f = TTFont(ttf)
    return {'OS/2.usWinAscent': f['OS/2'].usWinAscent,
            'OS/2.usWinDescent': f['OS/2'].usWinDescent,
            'hhea.ascender': f['hhea'].ascent, 'hhea.descender': f['hhea'].descent,
            'head.yMin': f['head'].yMin, 'head.yMax': f['head'].yMax}


def main():
    sfd = sys.argv[1]
    geo, out = predict(sfd)
    rel = release_values(sys.argv[2]) if len(sys.argv) > 2 else None
    h, a, lo, hi = geo['head_on'], geo['head_all'], geo['true_lo'], geo['true_hi']
    print('source: %s  (Fore layer %s)' % (sfd, 'quadratic' if geo['quad'] else 'cubic'))
    print('  on-curve min y   %-10s floor -> %d' % h[0])
    print('  all-point min y  %-10s floor -> %d' % a[0])
    print('  true-curve min y %-10s %.4f  int() -> %d  round() -> %d'
          % (lo[0], lo[1], int(lo[1]), round(lo[1])))
    print('  on-curve max y   %-10s ceil  -> %d' % h[1])
    print('  all-point max y  %-10s ceil  -> %d' % a[1])
    print('  true-curve max y %-10s %.4f  int() -> %d  round() -> %d'
          % (hi[0], hi[1], int(hi[1]), round(hi[1])))
    print('%-18s %-26s %8s %8s %9s %8s' % ('metric', 'source states', 'ff2012', 'ffmaster',
                                          'babelfont', 'release'))
    for label, key, _, _ in FIELDS:
        o = out[label]
        stated = '%s %d (%s)' % (key.replace('OS2', ''), o['stated'],
                                 'offset' if o['offset'] else 'absolute')
        print('%-18s %-26s %8d %8d %9d %8s' % (label, stated, o['ff2012'], o['ffmaster'],
                                               o['babelfont'], rel[label] if rel else '-'))
    for label in ('head.yMin', 'head.yMax'):
        o = out[label]
        print('%-18s %-26s %8d %8d %9s %8s' % (label, '(computed)', o['ff2012'], o['ffmaster'],
                                               '-', rel[label] if rel else '-'))


if __name__ == '__main__':
    main()
