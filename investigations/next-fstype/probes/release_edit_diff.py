#!/usr/bin/env python3
"""release_edit_diff.py -- what exactly did a google/fonts commit change inside a binary?

Question answered: between two google/fonts revisions of the same shipped file
(the FontForge export and the later edited release), which tables differ, and for
the header-like tables (head, hhea, OS/2, post, name, gasp, maxp) which fields?
Glyph-bearing tables are compared by compiled bytes only.

Used for:
  Titillium Web  90abd17b4 (v1.000, FontForge 2012-09-06 export)  ->  93550bd32 (#931 "hotfix v1.002")
  Wallpoet       90abd17b4 (FontForge 2011-02-22 export)         ->  8ccda7bf7 ("Fix fsType for 40 font files")

Every field listed is a value the release has that the .sfd's own export did not:
each needs either a documented .sfd edit citing the commit, or a statement that the
gate does not see it.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY investigations/next-fstype/probes/release_edit_diff.py > investigations/next-fstype/runs/release_edit_diff.txt
"""
import io
import subprocess

from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts"
PAIRS = [("ofl/titilliumweb/TitilliumWeb-%s.ttf" % s, "90abd17b4", "93550bd32")
         for s in ("Black", "Bold", "BoldItalic", "ExtraLight", "ExtraLightItalic", "Italic",
                   "Light", "LightItalic", "Regular", "SemiBold", "SemiBoldItalic")]
PAIRS.append(("ofl/wallpoet/Wallpoet-Regular.ttf", "90abd17b4", "8ccda7bf7"))
FIELDS = ("head", "hhea", "OS/2", "post", "maxp", "gasp")


def load(rev, path):
    blob = subprocess.run(["git", "-C", GF, "show", "%s:%s" % (rev, path)],
                          capture_output=True, check=True).stdout
    return TTFont(io.BytesIO(blob))


def attrs(table):
    out = {}
    for k, v in vars(table).items():
        if k.startswith("_") or k in ("tableTag", "glyphOrder", "extraNames", "mapping"):
            continue
        if k == "panose":
            v = tuple(vars(v).values())
        out[k] = v
    return out


def main():
    for path, a, b in PAIRS:
        fa, fb = load(a, path), load(b, path)
        print("=" * 90)
        print("%s  %s -> %s" % (path, a, b))
        ta, tb = set(fa.keys()) - {"GlyphOrder"}, set(fb.keys()) - {"GlyphOrder"}
        if ta - tb:
            print("  tables removed: %s" % sorted(ta - tb))
        if tb - ta:
            print("  tables added:   %s" % sorted(tb - ta))
        for t in sorted(ta & tb):
            if t in FIELDS:
                da, db = attrs(fa[t]), attrs(fb[t])
                diffs = [(k, da.get(k), db.get(k)) for k in sorted(set(da) | set(db))
                         if repr(da.get(k)) != repr(db.get(k))
                         and k not in ("checkSumAdjustment", "modified")]
                for k, x, y in diffs:
                    print("  %s.%s: %r -> %r" % (t, k, x, y))
            elif t == "name":
                na = {(r.nameID, r.platformID, r.platEncID, r.langID): r.toUnicode() for r in fa["name"].names}
                nb = {(r.nameID, r.platformID, r.platEncID, r.langID): r.toUnicode() for r in fb["name"].names}
                for k in sorted(set(na) | set(nb)):
                    if na.get(k) != nb.get(k):
                        print("  name %s: %r -> %r" % (k, (na.get(k) or "")[:90], (nb.get(k) or "")[:90]))
            else:
                if fa.getTableData(t) != fb.getTableData(t):
                    print("  %s: bytes differ" % t)
        # head.modified is reported separately (a re-save, not a font change)
        print("  head.modified: %s -> %s" % (fa["head"].modified, fb["head"].modified))


if __name__ == "__main__":
    main()
