#!/usr/bin/env python3
"""Independent re-implementation (verifier's own, written from FontForge
v20110222 = 9ec8bff8 splinefont.c SFStandardHeight/SPLMaxHeight/SCMaxHeight,
splineorder2.c SplineRefigure2 and splineutil2.c SplineIsLinear) of the OS/2
sxHeight/sCapHeight rule, printing both the 2011 (tot += cnt) and the
post-4d34d21e (++tot) means. Does not import the other agent's probes or the oracle.
Usage: ff2011_heights.py <file.sfd>
"""
import re, sys, math

RANGE = None
CAP = [('A', 'Z'), (0x391, 0x3a9), 0x402, 0x404, 0x405, 0x406, (0x408, 0x40b), (0x40f, 0x418), 0x41a, 0x42f]
XH = ['a', 'c', 'e', 'g', 'm', 'n', 'o', 'p', 'q', 'r', 's', 'u', 'v', 'w', 'x', 'y', 'z', 0x131,
      0x3b3, 0x3b9, 0x3ba, 0x3bc, 0x3bd, 0x3c0, 0x3c3, 0x3c4, 0x3c5, 0x3c7, 0x3c8, 0x3c9,
      0x432, 0x433, 0x438, (0x43a, 0x43f), 0x442, 0x443, 0x445, 0x44c, 0x44f, 0x459, 0x45a]


def expand(lst):
    out = []
    for e in lst:
        if isinstance(e, tuple):
            a, b = [ord(x) if isinstance(x, str) else x for x in e]
            out += list(range(a, b + 1))
        else:
            out.append(ord(e) if isinstance(e, str) else e)
    return out


def parse(path):
    glyphs = {}  # name -> dict
    byuni = {}
    bygid = {}
    cur = None
    layer = None
    in_ss = False
    contour = None
    with open(path, encoding='latin-1') as fh:
        for line in fh:
            s = line.rstrip('\n')
            if s.startswith('StartChar: '):
                cur = {'name': s[11:].strip(), 'contours': {}, 'refs': {}, 'uni': -1, 'gid': None}
                layer = None
                continue
            if cur is None:
                continue
            if s.startswith('Encoding: '):
                p = s.split()
                cur['uni'] = int(p[2]); cur['gid'] = int(p[3])
            elif s == 'Fore':
                layer = 1
            elif s == 'Back':
                layer = 0
            elif s.startswith('Layer: '):
                layer = int(s.split()[1])
            elif s == 'SplineSet':
                in_ss = True; contour = None
                cur['contours'].setdefault(layer, [])
            elif s == 'EndSplineSet':
                in_ss = False
            elif in_ss:
                m = re.match(r'\s*([-0-9. e]+?)\s+([mlc])\s+(\S+)', s)
                if not m:
                    continue
                nums = [float(x) for x in m.group(1).split()]
                op = m.group(2)
                if op == 'm':
                    contour = [('m', nums)]
                    cur['contours'][layer].append(contour)
                else:
                    contour.append((op, nums))
            elif s.startswith('Refer: '):
                p = s.split()
                gid = int(p[1]); tr = [float(x) for x in p[4:10]]
                cur['refs'].setdefault(layer, []).append((gid, tr))
            elif s == 'EndChar':
                glyphs[cur['name']] = cur
                if cur['uni'] >= 0:
                    byuni.setdefault(cur['uni'], cur)
                bygid[cur['gid']] = cur
                cur = None
    return glyphs, byuni, bygid


def realnear(a, b):
    return abs(a - b) < 1e-5 * max(1.0, abs(a), abs(b)) or a == b


def segments(contours, tr=(1, 0, 0, 1, 0, 0)):
    a, b, c, d, e, f = tr
    T = lambda x, y: (a * x + c * y + e, b * x + d * y + f)
    for con in contours:
        prev = T(*con[0][1][:2])
        for op, nums in con[1:]:
            if op == 'l':
                to = T(*nums[:2]); cp1 = prev; cp2 = to
            else:
                cp1 = T(*nums[0:2]); cp2 = T(*nums[2:4]); to = T(*nums[4:6])
            yield prev, cp1, cp2, to, op
            prev = to


def seg_info(fr, cp1, cp2, to, op):
    """returns (knownlinear, y-spline (b,c,d)) for an order2 spline"""
    nonext = (op == 'l') or (cp1 == fr)
    noprev = (op == 'l') or (cp2 == to)
    if nonext or noprev:
        return True, (0.0, to[1] - fr[1], fr[1])
    # quadratic: cp1 == cp2
    cx = 2 * (cp1[0] - fr[0]); cy = 2 * (cp1[1] - fr[1])
    bx = to[0] - fr[0] - cx; by = to[1] - fr[1] - cy
    if realnear(cx, 0): cx = 0
    if realnear(cy, 0): cy = 0
    if realnear(bx, 0): bx = 0
    if realnear(by, 0): by = 0
    if bx == 0 and by == 0:
        return True, (0.0, to[1] - fr[1], fr[1])
    # SplineIsLinear: control points on the line between the base points
    if realnear(fr[0], to[0]):
        lin = realnear(fr[0], cp1[0]) and realnear(fr[0], cp2[0])
        if not ((cp1[1] >= fr[1] and cp1[1] <= to[1] and cp2[1] >= fr[1] and cp2[1] <= to[1]) or
                (cp1[1] <= fr[1] and cp1[1] >= to[1] and cp2[1] <= fr[1] and cp2[1] >= to[1])):
            lin = 'MINMAX'
    elif realnear(fr[1], to[1]):
        lin = realnear(fr[1], cp1[1]) and realnear(fr[1], cp2[1])
        if not ((cp1[0] >= fr[0] and cp1[0] <= to[0] and cp2[0] >= fr[0] and cp2[0] <= to[0]) or
                (cp1[0] <= fr[0] and cp1[0] >= to[0] and cp2[0] <= fr[0] and cp2[0] >= to[0])):
            lin = 'MINMAX'
    else:
        t1 = (cp1[1] - fr[1]) / (to[1] - fr[1]); t2 = (cp1[0] - fr[0]) / (to[0] - fr[0])
        t3 = (to[1] - cp2[1]) / (to[1] - fr[1]); t4 = (to[0] - cp2[0]) / (to[0] - fr[0])
        lin = (abs(t1 - t2) < 1e-9 or (abs(t1) < 1e-9 and abs(t2) < 1e-9)) and \
              (abs(t3 - t4) < 1e-9 or (abs(t3) < 1e-9 and abs(t4) < 1e-9))
        if lin and (min(t1, t2, t3, t4) < 0 or max(t1, t2, t3, t4) > 1):
            lin = 'MINMAX'
    if lin == 'MINMAX':
        raise RuntimeError('MinMaxWithin case not implemented: %r' % ((fr, cp1, to),))
    if lin:
        return True, (0.0, to[1] - fr[1], fr[1])
    return False, (by, cy, fr[1])


def spl_max(contours, tr=(1, 0, 0, 1, 0, 0)):
    f = 'unknown'; mx = -1e23
    for fr, cp1, cp2, to, op in segments(contours, tr):
        kl, (b, c, d) = seg_info(fr, cp1, cp2, to, op)
        if kl:
            cp1 = fr; cp2 = to
        if fr[1] >= mx or to[1] >= mx or cp1[1] > mx or cp2[1] > mx:
            if not kl:
                if fr[1] > mx: f = 'round'; mx = fr[1]
                if to[1] > mx: f = 'round'; mx = to[1]
                if b != 0:
                    t = -c / (2 * b)
                    if 0 < t < 1:
                        y = (b * t + c) * t + d
                        if y > mx: f = 'round'; mx = y
            elif fr[1] == to[1]:
                if fr[1] >= mx: mx = fr[1]; f = 'flat'
            else:
                if fr[1] > mx: f = 'pointy'; mx = fr[1]
                if to[1] > mx: f = 'pointy'; mx = to[1]
    return mx, f


def ref_contours(g, bygid, layer, tr):
    """all contours of a referenced glyph (incl. its nested refs), transformed"""
    out = []
    for con in g['contours'].get(layer, []):
        out.append((con, tr))
    for gid, t2 in g['refs'].get(layer, []):
        a, b, c, d, e, f = t2; A, B, C, D, E, F = tr
        comp = (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F)
        out += ref_contours(bygid[gid], bygid, layer, comp)
    return out


def sc_max(g, bygid, layer=1):
    mx, f = spl_max(g['contours'].get(layer, []))
    for gid, tr in g['refs'].get(layer, []):
        best = -1e23; bf = 'unknown'
        # r->layers[0].splines: all splines of the ref, one SplineSet list
        allc = ref_contours(bygid[gid], bygid, layer, tr)
        # evaluate as one list, in order
        cur_f = 'unknown'; cur = -1e23
        for con, t in allc:
            m2, f2 = spl_max([con], t)
            if m2 > cur or (m2 == cur and False):
                pass
        # faithful: SPLMaxHeight over the concatenated list keeps state across contours
        test, curf = spl_max_list(allc)
        if test > mx or (test == mx and curf == 'flat'):
            mx = test; f = curf
    return mx, f


def spl_max_list(allc):
    f = 'unknown'; mx = -1e23
    for con, t in allc:
        for fr, cp1, cp2, to, op in segments([con], t):
            kl, (b, c, d) = seg_info(fr, cp1, cp2, to, op)
            if kl:
                cp1 = fr; cp2 = to
            if fr[1] >= mx or to[1] >= mx or cp1[1] > mx or cp2[1] > mx:
                if not kl:
                    if fr[1] > mx: f = 'round'; mx = fr[1]
                    if to[1] > mx: f = 'round'; mx = to[1]
                    if b != 0:
                        tt = -c / (2 * b)
                        if 0 < tt < 1:
                            y = (b * tt + c) * tt + d
                            if y > mx: f = 'round'; mx = y
                elif fr[1] == to[1]:
                    if fr[1] >= mx: mx = fr[1]; f = 'flat'
                else:
                    if fr[1] > mx: f = 'pointy'; mx = fr[1]
                    if to[1] > mx: f = 'pointy'; mx = to[1]
    return mx, f


def standard_height(byuni, bygid, lst, blues, em):
    flats = []; curves = []
    rows = []
    for u in expand(lst):
        g = byuni.get(u)
        if g is None:
            continue
        mx, f = sc_max(g, bygid)
        rows.append((g['name'], mx, f))
        tgt = flats if f == 'flat' else (curves if f != 'unknown' else None)
        if tgt is None:
            continue
        for e in tgt:
            if e[0] == mx:
                e[1] += 1; break
        else:
            tgt.append([mx, 1])
    res = {}
    if len(flats) == 1:
        res['2011'] = res['master'] = flats[0][0]
    elif len(flats) > 1:
        cnt = max(e[1] for e in flats)
        sel = [e[0] for e in flats if e[1] == cnt]
        res['2011'] = res['master'] = sum(sel) / len(sel)
    elif not curves:
        res['2011'] = res['master'] = None
    else:
        s = sum(e[0] for e in curves)
        res['2011'] = s / sum(e[1] for e in curves)
        res['master'] = s / len(curves)
    snapped = {}
    for k, v in res.items():
        best = v; bd = em / 100.0
        if v is not None and blues:
            for z in blues[0::2]:
                if abs(z - v) < bd:
                    best = z; bd = abs(z - v)
        snapped[k] = best
    return rows, flats, curves, res, snapped


def main():
    path = sys.argv[1]
    glyphs, byuni, bygid = parse(path)
    txt = open(path, encoding='latin-1').read()
    m = re.search(r'^BlueValues \d+ \[([^\]]*)\]', txt, re.M)
    blues = [float(x) for x in m.group(1).split()] if m else []
    asc = int(re.search(r'^Ascent: (\S+)', txt, re.M).group(1)); dsc = int(re.search(r'^Descent: (\S+)', txt, re.M).group(1))
    print('source', path, 'BlueValues', blues, 'snap window', (asc + dsc) / 100.0)
    for label, lst in (('xheight', XH), ('capheight', CAP)):
        rows, flats, curves, res, snapped = standard_height(byuni, bygid, lst, blues, asc + dsc)
        print('==', label, len(rows), 'glyphs')
        for r in rows:
            print('   %-10s %10.4f %s' % r)
        print('   flats', flats)
        print('   curves (pos,cnt)', curves, 'distinct', len(curves), 'glyphs', sum(e[1] for e in curves), 'sum', sum(e[0] for e in curves))
        for k in ('2011', 'master'):
            v = res[k]; sv = snapped[k]
            print('   rule %-6s mean %s snapped %s -> OS/2 int16 (C truncation) %s' % (k, v, sv, None if sv is None else int(sv)))


if __name__ == '__main__':
    main()
