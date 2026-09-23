#!/usr/bin/env python3
"""Independent re-derivation (verifier's own code, not the investigator's probes).

Question: from the unmodified UnifrakturMaguntia.sfd, what do the FontForge
20100501 exporter rules give for (a) head.yMin/yMax (floor/ceil of on-curve points
incl. implied ones), (b) the true-curve y extremes used by sethhead (int()), and
(c) SFStandardHeight x-height / cap-height under the 2010 mean (sum of DISTINCT
tops / GLYPH count) and the post-2012-05-14 mean (sum distinct / distinct count)?

Usage: python3 indep_probe.py <file.sfd>
"""
import math, sys

def parse(path):
    glyphs = {}; order = []
    cur = None; in_fore = False; in_ss = False
    for line in open(path, encoding='latin-1'):
        line = line.rstrip('\n')
        if line.startswith('StartChar: '):
            cur = {'name': line[11:], 'uni': None, 'contours': [], 'refs': [], 'width': None}
            in_fore = False; in_ss = False
            continue
        if cur is None:
            continue
        if line.startswith('Encoding: '):
            p = line.split(); cur['uni'] = int(p[2]); cur['gid'] = int(p[3])
        elif line.startswith('Width: '):
            cur['width'] = int(line.split()[1])
        elif line == 'Fore':
            in_fore = True
        elif line.startswith('Back') or line.startswith('Layer: '):
            in_fore = False
        elif line == 'SplineSet' and in_fore:
            in_ss = True
        elif line == 'EndSplineSet':
            in_ss = False
        elif in_ss:
            t = line.split()
            cmd = t[-2] if len(t) >= 2 else None
            flags = int(t[-1].split(',')[0])
            nums = [float(x) for x in t[:-2]]
            if cmd == 'm':
                cur['contours'].append([('m', nums, flags)])
            else:
                cur['contours'][-1].append((cmd, nums, flags))
        elif line.startswith('Refer: ') and in_fore:
            p = line.split()
            cur['refs'].append((int(p[1]), [float(x) for x in p[4:10]]))
        elif line == 'EndChar':
            glyphs[cur['gid']] = cur; order.append(cur['gid']); cur = None
    return glyphs

def segments(g, glyphs, xf=(1, 0, 0, 1, 0, 0)):
    """Return list of contours; each contour list of (p0, cp or None, p1, p0flags)
    in font units after transform. Quadratic: one control point."""
    a, b, c, d, e, f = xf
    T = lambda x, y: (a * x + c * y + e, b * x + d * y + f)
    out = []
    for con in g['contours']:
        pts = []  # list of (oncurve point, cp_before or None, flags)
        segs = []
        start = T(*con[0][1][:2]); prev = start; prevflags = con[0][2]
        onpts = [(start, con[0][2])]
        for cmd, nums, fl in con[1:]:
            if cmd == 'l':
                p1 = T(nums[0], nums[1]); segs.append((prev, None, p1)); prev = p1
            elif cmd == 'c':
                cp1 = T(nums[0], nums[1]); cp2 = T(nums[2], nums[3]); p1 = T(nums[4], nums[5])
                if cp1 != cp2:
                    raise SystemExit('not quadratic: %s' % g['name'])
                cp = None if (cp1 == prev or cp1 == p1) else cp1
                segs.append((prev, cp, p1)); prev = p1
            onpts.append((prev, fl))
        out.append((segs, onpts))
    for gid, m in g['refs']:
        # compose transforms: ref matrix then parent
        ra, rb, rc, rd, re_, rf = m
        comp = (ra * a + rb * c, ra * b + rb * d, rc * a + rd * c, rc * b + rd * d,
                re_ * a + rf * c + e, re_ * b + rf * d + f)
        out.extend(segments(glyphs[gid], glyphs, comp))
    return out

def qextrema_y(p0, cp, p1):
    ys = [p0[1], p1[1]]
    if cp is not None:
        den = p0[1] - 2 * cp[1] + p1[1]
        if den != 0:
            t = (p0[1] - cp[1]) / den
            if 0 < t < 1:
                ys.append((1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * cp[1] + t * t * p1[1])
    return min(ys), max(ys)

def near(a, b):
    return abs(a - b) < 1e-5 if abs(b) < 1e-5 else abs((a - b) / b) < 1e-5

def is_linear(p0, cp, p1):
    if cp is None:
        return True
    # SplineIsLinear, horizontal/vertical/general cases (cp on the chord, within)
    if near(p0[0], p1[0]):
        return near(p0[0], cp[0]) and min(p0[1], p1[1]) <= cp[1] <= max(p0[1], p1[1])
    if near(p0[1], p1[1]):
        return near(p0[1], cp[1]) and min(p0[0], p1[0]) <= cp[0] <= max(p0[0], p1[0])
    t1 = (cp[1] - p0[1]) / (p1[1] - p0[1]); t2 = (cp[0] - p0[0]) / (p1[0] - p0[0])
    return abs(t1 - t2) < 1e-5 and 0 <= t1 <= 1

def splmaxheight(contours):
    f = 'unknown'; mx = -1e23
    for segs, _ in contours:
        for p0, cp, p1 in segs:
            cpy = cp[1] if cp is not None else None
            if not (p0[1] >= mx or p1[1] >= mx or (cpy is not None and cpy > mx)):
                continue
            if not is_linear(p0, cp, p1):
                if p0[1] > mx: f = 'round'; mx = p0[1]
                if p1[1] > mx: f = 'round'; mx = p1[1]
                lo, hi = qextrema_y(p0, cp, p1)
                if hi > mx: f = 'round'; mx = hi
            elif p0[1] == p1[1]:
                if p0[1] >= mx: mx = p0[1]; f = 'flat'
            else:
                if p0[1] > mx: f = 'pointy'; mx = p0[1]
                if p1[1] > mx: f = 'pointy'; mx = p1[1]
    return mx, f

def scmaxheight(g, glyphs):
    own = segments({'contours': g['contours'], 'refs': [], 'name': g['name']}, glyphs)
    mx, f = splmaxheight(own)
    for gid, m in g['refs']:
        rc = segments({'contours': [], 'refs': [(gid, m)], 'name': g['name']}, glyphs)
        t, cf = splmaxheight(rc)
        if t > mx or (t == mx and cf == 'flat'):
            mx, f = t, cf
    return mx, f

CAP = list(range(ord('A'), ord('Z') + 1)) + list(range(0x391, 0x3a9 + 1)) + \
    [0x402, 0x404, 0x405, 0x406] + list(range(0x408, 0x40b + 1)) + list(range(0x40f, 0x418 + 1)) + \
    list(range(0x41a, 0x42f + 1))
XH = [ord(ch) for ch in 'acegmnopqrsuvwxyz'] + [0x131, 0x3b3, 0x3b9, 0x3ba, 0x3bc, 0x3bd, 0x3c0, 0x3c3,
    0x3c4, 0x3c5, 0x3c7, 0x3c8, 0x3c9, 0x432, 0x433, 0x438] + list(range(0x43a, 0x43f + 1)) + \
    [0x442, 0x443, 0x445, 0x44c, 0x44f, 0x459, 0x45a]

def standard_height(glyphs, lst):
    by_uni = {g['uni']: g for g in glyphs.values() if g['uni'] is not None and g['uni'] >= 0}
    flats = {}; curves = {}; detail = []
    for u in lst:
        g = by_uni.get(u)
        if g is None:
            continue
        v, f = scmaxheight(g, glyphs)
        detail.append((g['name'], round(v, 4), f))
        if f == 'flat': flats[v] = flats.get(v, 0) + 1
        elif f != 'unknown': curves[v] = curves.get(v, 0) + 1
    if len(flats) == 1:
        r = list(flats)[0]; return r, r, detail, flats, curves
    if len(flats) > 1:
        c = max(flats.values()); top = [p for p, n in flats.items() if n == c]
        r = sum(top) / len(top); return r, r, detail, flats, curves
    s = sum(curves)  # distinct positions, each once
    old = s / sum(curves.values()); new = s / len(curves)
    return old, new, detail, flats, curves

def main():
    glyphs = parse(sys.argv[1])
    onmin = (1e9, None); onmax = (-1e9, None); tmin = (1e9, None); tmax = (-1e9, None)
    allmin = (1e9, None)
    for g in glyphs.values():
        cons = segments(g, glyphs)
        for segs, onpts in cons:
            for p, fl in onpts:
                if p[1] < onmin[0]: onmin = (p[1], g['name'])
                if p[1] > onmax[0]: onmax = (p[1], g['name'])
            for p0, cp, p1 in segs:
                lo, hi = qextrema_y(p0, cp, p1)
                if lo < tmin[0]: tmin = (lo, g['name'])
                if hi > tmax[0]: tmax = (hi, g['name'])
                for q in (p0, p1) + ((cp,) if cp else ()):
                    if q[1] < allmin[0]: allmin = (q[1], g['name'])
    print('on-curve (incl. implied) min y %.4f (%s) floor %d' % (onmin[0], onmin[1], math.floor(onmin[0])))
    print('on-curve max y %.4f (%s) ceil %d' % (onmax[0], onmax[1], math.ceil(onmax[0])))
    print('all points min y %.4f (%s)' % allmin)
    print('true-curve min y %.4f (%s) int %d round %d' % (tmin[0], tmin[1], int(tmin[0]), round(tmin[0])))
    print('true-curve max y %.4f (%s) int %d' % (tmax[0], tmax[1], int(tmax[0])))
    for label, lst in (('xheight', XH), ('capheight', CAP)):
        old, new, detail, flats, curves = standard_height(glyphs, lst)
        print('%s: 2010 mean %.4f -> %d ; post-2012 mean %.4f -> %d ; flats=%s ; distinct curves=%d glyphs=%d sum=%.4f'
              % (label, old, int(old), new, int(new), flats, len(curves), sum(curves.values()), sum(curves)))
        print('   ', detail)

main()
