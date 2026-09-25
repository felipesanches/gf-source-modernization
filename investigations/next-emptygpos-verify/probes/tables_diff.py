#!/usr/bin/env python3
"""Which tables differ between two fonts, and is a GPOS shell the release's shell?

Question 1 (control): is a build made with a candidate builder3/fontc and the new
flag OFF identical to the pinned build, table by table? Tables are compared as
decompiled XML (ttx), so a difference is a content difference; head is compared
with `modified` masked, name with nameID 5 masked (both carry build stamps).
Question 2 (shell): does each font's GPOS/GSUB have the same ScriptList
(script -> [(langsys, [feature tags])]), the same number of features and lookups?

Signal read: fontTools ttx XML per table; ScriptList/FeatureList/LookupList.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 tables_diff.py <a.ttf> <b.ttf>
"""
import io
import sys

from fontTools.ttLib import TTFont


def xml(font, tag):
    t = font[tag]
    saved = None
    if tag == "head":
        saved = t.modified
        t.modified = 0
    if tag == "name":
        keep = [r for r in t.names if r.nameID != 5]
        saved, t.names = t.names, keep
    w = io.StringIO()
    from fontTools.misc.xmlWriter import XMLWriter
    xw = XMLWriter(w)
    t.toXML(xw, font)
    if tag == "head":
        t.modified = saved
    if tag == "name":
        t.names = saved
    return w.getvalue()


def layout(font, tag):
    if tag not in font:
        return None
    t = font[tag].table
    feats = t.FeatureList.FeatureRecord if t.FeatureList else []
    scripts = []
    for sr in (t.ScriptList.ScriptRecord if t.ScriptList else []):
        langs = []
        if sr.Script.DefaultLangSys:
            d = sr.Script.DefaultLangSys
            langs.append(("dflt", d.ReqFeatureIndex, [feats[i].FeatureTag for i in d.FeatureIndex]))
        for l in sr.Script.LangSysRecord:
            langs.append((l.LangSysTag, l.LangSys.ReqFeatureIndex, [feats[i].FeatureTag for i in l.LangSys.FeatureIndex]))
        scripts.append((sr.ScriptTag, langs))
    return {"version": hex(t.Version), "scripts": scripts, "features": len(feats),
            "lookups": t.LookupList.LookupCount if t.LookupList else 0}


def main():
    a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
    ta, tb = set(a.keys()) - {"GlyphOrder"}, set(b.keys()) - {"GlyphOrder"}
    print("only in a:", sorted(ta - tb), " only in b:", sorted(tb - ta))
    diff = [t for t in sorted(ta & tb) if xml(a, t) != xml(b, t)]
    print("tables differing (head.modified, name ID 5 masked):", diff or "none")
    for tag in ("GPOS", "GSUB"):
        la, lb = layout(a, tag), layout(b, tag)
        print("%s a: %s" % (tag, la if tag == "GPOS" or la is None else {k: la[k] for k in ("version", "features", "lookups")}))
        print("%s b: %s" % (tag, lb if tag == "GPOS" or lb is None else {k: lb[k] for k in ("version", "features", "lookups")}))
        if la and lb:
            print("%s script lists equal: %s" % (tag, la["scripts"] == lb["scripts"]))


if __name__ == "__main__":
    main()
