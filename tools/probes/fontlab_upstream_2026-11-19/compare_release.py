#!/usr/bin/env python3
"""Question answered: where two babelfont builds convert a library .vfb differently, which of
them states what the release Google Fonts ships has -- field by field?

For every corpus file that families-vfb.tsv or families-binary.tsv pairs with a shipped TTF
(repo + source path, else the repository's only shipped style),
reads both builds' .glyphs (convert_ab.sh output) and the release, and classifies each field
as same (both builds agree), A (only build a matches the release), B (only b), neither.
Fields: name IDs the .glyphs states (family, style, designer, manufacturer URL, designer URL,
trademark, license, license URL, description), version, OS/2 weight class, width class,
fsType, PANOSE, vendor ID, head.lowestRecPPEM, master ascender/descender against the release's
hhea and typo values, x-height and cap height.

Usage: compare_release.py <convert_ab outdir> <label a> <label b> [--show <field>]
"""
import os
import re
import sys

import glyphsLib
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GF = "/home/fsanches/compartilhado/google/fonts"     # the checkout families-binary.tsv paths are in


def load(path):
    f = glyphsLib.GSFont(path)
    f.filepath = path
    return f


def prop(f, key):
    for p in f.properties:
        if p.key == key:
            if p.value is not None:
                return p.value
            v = p.values
            if isinstance(v, dict):
                return v.get("dflt") or v.get("ENG") or next(iter(v.values()), None)
            return v
    return None


def param(obj, name):
    for p in obj.customParameters:
        if p.name == name:
            return p.value
    return None


def norm(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return tuple(int(x) for x in v)
    s = str(v).strip()
    try:
        return int(float(s))
    except ValueError:
        return " ".join(s.split())


def instance_class(f, key):
    """The first instance's `weightClass = N;` / `widthClass = N;`, from the file text."""
    text = open(f.filepath).read()
    start = text.find("\ninstances = (")
    m = re.search(r"^%s = (\d+);" % key, text[start:], re.M) if start >= 0 else None
    return int(m.group(1)) if m else None


def fields_glyphs(f):
    m = f.masters[0]
    inst = f.instances[0] if f.instances else None
    fs = param(f, "fsType")
    return {
        "name1 family": f.familyName,
        "name2/17 style": (inst.name if inst else None) or prop(f, "styleNames") or m.name,
        "name7 trademark": prop(f, "trademarks"),
        "name9 designer": prop(f, "designers") or getattr(f, "designer", None),
        "name10 description": prop(f, "descriptions"),
        "name11 manufacturerURL": prop(f, "manufacturerURL") or getattr(f, "manufacturerURL", None),
        "name12 designerURL": prop(f, "designerURL") or getattr(f, "designerURL", None),
        "name13 license": prop(f, "licenses"),
        "name14 licenseURL": prop(f, "licenseURL"),
        "version": "%d.%03d" % (f.versionMajor or 0, f.versionMinor or 0),
        # glyphsLib does not expose a Glyphs 3 instance's numeric classes: read the file
        "OS/2 weightClass": instance_class(f, "weightClass"),
        "OS/2 widthClass": instance_class(f, "widthClass"),
        "OS/2 fsType": sum(1 << b for b in fs) if isinstance(fs, (list, tuple)) else fs,
        "OS/2 panose": param(f, "panose") or param(m, "panose"),
        "OS/2 vendorID": param(f, "vendorID") or prop(f, "vendorID"),
        "head lowestRecPPEM": param(f, "openTypeHeadLowestRecPPEM"),
        "ascender": m.ascender,
        "descender": m.descender,
        "xHeight": m.xHeight,
        "capHeight": m.capHeight,
    }


def fields_release(t):
    n = t["name"]
    os2 = t["OS/2"]
    g = lambda i: n.getDebugName(i)
    return {
        "name1 family": g(16) or g(1),
        "name2/17 style": g(17) or g(2),
        "name7 trademark": g(7),
        "name9 designer": g(9),
        "name10 description": g(10),
        "name11 manufacturerURL": g(11),
        "name12 designerURL": g(12),
        "name13 license": g(13),
        "name14 licenseURL": g(14),
        "version": "%.3f" % round(t["head"].fontRevision, 3),
        "OS/2 weightClass": os2.usWeightClass,
        "OS/2 widthClass": os2.usWidthClass,
        "OS/2 fsType": os2.fsType,
        "OS/2 panose": tuple(getattr(os2.panose, k) for k in (
            "bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast", "bStrokeVariation",
            "bArmStyle", "bLetterForm", "bMidline", "bXHeight")),
        "OS/2 vendorID": os2.achVendID.strip(),
        "head lowestRecPPEM": t["head"].lowestRecPPEM,
        "ascender": (t["hhea"].ascent, os2.sTypoAscender),
        "descender": (t["hhea"].descent, os2.sTypoDescender),
        "xHeight": getattr(os2, "sxHeight", None),
        "capHeight": getattr(os2, "sCapHeight", None),
    }


def matches(field, ours, rel):
    if field in ("ascender", "descender"):
        return norm(ours) in rel
    if field == "version":
        return ours == rel
    return norm(ours) == norm(rel)


def main():
    out, la, lb = sys.argv[1:4]
    show = sys.argv[sys.argv.index("--show") + 1] if "--show" in sys.argv else None
    pairs, by_repo = {}, {}
    for table in ("families-vfb.tsv", "families-binary.tsv"):
        for l in open(os.path.join(W, table)):
            r = l.rstrip("\n").split("\t")
            if r[0] == "repo":
                continue
            shipped = r[8] if os.path.isabs(r[8]) else os.path.join(GF, r[8])
            pairs.setdefault((r[0], r[7]), shipped)
            by_repo.setdefault(r[0], set()).add(shipped)
    tally = {}
    for l in open(os.path.join(out, "convert-ab.tsv")):
        r = l.rstrip("\n").split("\t")
        h, path = r[0], r[1]
        repo, _, src = path.partition("/")
        repo = repo.replace(".prev", "")
        # the exact source, else the repository's only shipped style (its -OTF/-TTF siblings
        # are the same font)
        shipped = pairs.get((repo, src)) or (next(iter(by_repo[repo])) if len(by_repo.get(repo, ())) == 1 else None)
        if not shipped or not os.path.exists(shipped):
            continue
        fa = fields_glyphs(load(os.path.join(out, "%s.%s.glyphs" % (h, la))))
        fb = fields_glyphs(load(os.path.join(out, "%s.%s.glyphs" % (h, lb))))
        fr = fields_release(TTFont(shipped, lazy=True))
        for k in fr:
            a, b = matches(k, fa[k], fr[k]), matches(k, fb[k], fr[k])
            if norm(fa[k]) == norm(fb[k]):
                v = "same(ok)" if a else "same(neither)"
            else:
                v = {(True, True): "both", (True, False): la, (False, True): lb, (False, False): "neither"}[(a, b)]
            tally.setdefault(k, {}).setdefault(v, 0)
            tally[k][v] += 1
            if show == k and not v.startswith("same(ok)"):
                print("%-55s %-12s release=%r | %s=%r | %s=%r" % (path[:55], v, str(fr[k])[:40], la,
                      str(fa[k])[:40], lb, str(fb[k])[:40]))
    if show:
        return
    cols = ["same(ok)", "same(neither)", la, lb, "both", "neither"]
    print("%-24s %s" % ("field", " ".join("%-13s" % c for c in cols)))
    for k, d in tally.items():
        print("%-24s %s" % (k, " ".join("%-13s" % d.get(c, 0) for c in cols)))


if __name__ == "__main__":
    main()
