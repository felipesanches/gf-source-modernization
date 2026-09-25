#!/usr/bin/env python3
"""Which converted sources lose fontc's generated mark/kern lookups to babelfont's marker?

Question answered: babelfont's FontForge reader (convertors/fontforge.rs, upstream
commit 66334a7 "Skip empty lookups but add automatic code markers") prefixes the
abvm/blwm/kern/dist/mark/mkmk feature blocks it writes with the comment
"# Automatic code start". fea-rs 1.0.0 (token_tree/typed.rs, has_insert_marker) and
ufo2ft (baseFeatureWriter.py INSERT_FEATURE_MARKER) recognise only a comment starting
"# Automatic Code" -- case-sensitive. fontc therefore sees a manually written feature
with no insertion marker and SKIPS its feature writer for that tag
("Skipping generating feature 'mark', which is manually declared in FEA and has no
insertion comment", fontbe 1.0.0 features.rs feature_writer_todo_list).

EXCEPT kern: glyphs-reader 1.0.0 (font.rs insert_mark_if_manual_kern_feature, a port
of glyphsLib builder/features.py) appends "# Automatic Code" to every manual `kern`
feature of a Glyphs source, so fontc's kern writer still runs there (verified on
Italiana-Regular: its 1443 Glyphs kerning pairs are compiled, no "Skipping" warning).

For each .glyphs file given (or found under a directory), this prints every feature
carrying the lowercase marker and whether the source has what fontc's writer for that
feature would have generated from: anchors named X/_X (mark, mkmk, abvm, blwm) or
kerning (dist). "LOSES" means the writer had input and was skipped; "harmless" means
it had none, or the tag is kern (see above).

Usage:
  automatic_code_marker.py <file.glyphs | dir> ...
Prints: file, feature tag, LOSES|harmless, #base-anchor names, #kerning pairs.
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import glob
import os
import sys

import openstep_plist

MARK_TAGS = {"mark", "mkmk", "abvm", "blwm"}
KERN_TAGS = {"dist"}           # kern: see the docstring


def inputs(d):
    names = set()
    for g in d.get("glyphs", []):
        for layer in g.get("layers", []):
            for a in layer.get("anchors", []):
                names.add(a.get("name", ""))
    attach = {n for n in names if n.startswith("_") and n[1:] in names}
    kern = 0
    for master in (d.get("kerningLTR") or d.get("kerning") or {}).values():
        for right in master.values():
            kern += len(right)
    return attach, kern


def check(path):
    d = openstep_plist.load(open(path, encoding="utf-8"), use_numbers=True)
    attach, kern = inputs(d)
    out = []
    for f in d.get("features", []):
        code = f.get("code", "")
        if "# Automatic code start" not in code:
            continue
        tag = f.get("tag", "?")
        has_input = (tag in MARK_TAGS and attach) or (tag in KERN_TAGS and kern)
        out.append("%s\t%s\t%s\tattach-classes=%d\tkern-pairs=%d"
                   % (path, tag, "LOSES" if has_input else "harmless", len(attach), kern))
    return out


def main():
    paths = []
    for a in sys.argv[1:]:
        if os.path.isdir(a):
            paths += sorted(glob.glob(os.path.join(a, "**", "*.glyphs"), recursive=True))
        else:
            paths.append(a)
    for p in paths:
        try:
            for line in check(p):
                print(line)
        except Exception as exc:          # an unreadable file is reported, not skipped
            print("%s\tERROR\t%s" % (p, exc))


if __name__ == "__main__":
    main()
