#!/usr/bin/env python3
"""Question answered: for each .vfb converted by two babelfont builds, in which topics do the
.glyphs outputs differ -- names, font info, master metrics, kerning, groups, anchors, glyph
names, outlines, features?

Usage: compare_topics.py <convert_ab outdir> <label a> <label b> [--detail <topic>]
Reads <outdir>/convert-ab.tsv and <outdir>/<hash>.<label>.glyphs (convert_ab.sh). Prints, per
topic, how many files differ, then one line per file with the differing topics. --detail
prints, for one topic, the first differences of every file.
"""
import sys
import glyphsLib


def font_info(f):
    keys = ("familyName", "versionMajor", "versionMinor", "unitsPerEm", "copyright", "designer",
            "designerURL", "manufacturer", "manufacturerURL", "date")
    d = {k: str(getattr(f, k, None)) for k in keys if k != "date"}
    for p in f.properties:
        d["prop:" + p.key] = repr(p.value) if p.value is not None else repr(p.values)
    return d


def custom_params(f):
    return {"font:" + p.name: repr(p.value) for p in f.customParameters}


def master_info(f):
    d = {}
    for i, m in enumerate(f.masters):
        d["m%d.name" % i] = m.name
        for p in m.customParameters:
            d["m%d:%s" % (i, p.name)] = repr(p.value)
        for mv in getattr(m, "metrics", []) or []:
            pass
        for attr in ("ascender", "descender", "xHeight", "capHeight", "italicAngle"):
            d["m%d.%s" % (i, attr)] = repr(getattr(m, attr, None))
        d["m%d.axes" % i] = repr(list(m.axes))
    return d


def instances(f):
    d = {}
    for i, inst in enumerate(f.instances):
        d["i%d.name" % i] = inst.name
        d["i%d.weightClass" % i] = repr(getattr(inst, "weightClass", None))
        d["i%d.widthClass" % i] = repr(getattr(inst, "widthClass", None))
        for p in inst.customParameters:
            d["i%d:%s" % (i, p.name)] = repr(p.value)
        for p in inst.properties:
            d["i%d.prop:%s" % (i, p.key)] = repr(p.value) if p.value is not None else repr(p.values)
    return d


def kerning(f):
    d = {}
    for mid, pairs in f.kerning.items():
        for a, seconds in pairs.items():
            for b, v in seconds.items():
                d["%s %s" % (a, b)] = v
    return d


def groups(f):
    d = {}
    for g in f.glyphs:
        if g.leftKerningGroup:
            d[g.name + ".L"] = g.leftKerningGroup
        if g.rightKerningGroup:
            d[g.name + ".R"] = g.rightKerningGroup
    return d


def anchors(f):
    d = {}
    for g in f.glyphs:
        for li, layer in enumerate(g.layers):
            for a in layer.anchors:
                d["%s/%d/%s" % (g.name, li, a.name)] = (round(a.position.x), round(a.position.y))
    return d


def glyph_names(f):
    return {g.name: ",".join(g.unicodes or []) for g in f.glyphs}


def outlines(f):
    d = {}
    for g in f.glyphs:
        for li, layer in enumerate(g.layers):
            if not layer.associatedMasterId or layer.layerId != layer.associatedMasterId:
                continue
            pts = [(n.position.x, n.position.y, n.type) for p in layer.paths for n in p.nodes]
            comps = [(c.name, tuple(c.transform)) for c in layer.components]
            d["%s/%d" % (g.name, li)] = (len(pts), hash(tuple(pts)), tuple(comps), layer.width)
    return d


def features(f):
    d = {}
    for fe in f.features:
        d["fea:" + fe.name] = fe.code
    for c in f.classes:
        d["class:" + c.name] = c.code
    for p in f.featurePrefixes:
        d["prefix:" + p.name] = p.code
    return d


TOPICS = {"font_info": font_info, "font_params": custom_params, "masters": master_info,
          "instances": instances, "kerning": kerning, "groups": groups, "anchors": anchors,
          "glyph_names": glyph_names, "outlines": outlines, "features": features}


def diff(a, b):
    keys = sorted(set(a) | set(b))
    return [(k, a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)]


def main():
    out, la, lb = sys.argv[1:4]
    detail = sys.argv[sys.argv.index("--detail") + 1] if "--detail" in sys.argv else None
    rows = [l.rstrip("\n").split("\t") for l in open("%s/convert-ab.tsv" % out)]
    counts = {t: 0 for t in TOPICS}
    lines = []
    for r in rows:
        h, path = r[0], r[1]
        try:
            fa = glyphsLib.GSFont("%s/%s.%s.glyphs" % (out, h, la))
            fb = glyphsLib.GSFont("%s/%s.%s.glyphs" % (out, h, lb))
        except Exception as e:
            lines.append("%s  LOAD ERROR %s" % (path, str(e)[:100]))
            continue
        bad = []
        for t, fn in TOPICS.items():
            dd = diff(fn(fa), fn(fb))
            if dd:
                counts[t] += 1
                bad.append("%s(%d)" % (t, len(dd)))
                if detail == t:
                    print("== %s" % path)
                    for k, x, y in dd[:12]:
                        print("   %-40s %s: %s | %s: %s" % (str(k)[:40], la, str(x)[:70], lb, str(y)[:70]))
        lines.append("%s  %s" % (path, " ".join(bad) or "same"))
    if detail:
        return
    print("files: %d" % len(rows))
    for t, n in counts.items():
        print("  %-12s %d differ" % (t, n))
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
