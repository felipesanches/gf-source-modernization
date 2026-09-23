#!/usr/bin/env python3
"""Converter and compiler gaps closed after babelfont runs, inside the convert commit.

Question answered: which values does the toolchain lose between a FontForge
source and the compiled font, and how are they carried across without taking
anything from the released binary?

Each workaround here reads its value FROM THE .sfd, and each exists only because
of a named, reproduced defect in a tool -- it is not a change to the font:

  weight-class   fontc 1.0.0 ignores a single-master Glyphs source's instance
                 weightClass and builds usWeightClass 400 (glyphs2fontir never sets
                 it; ../issues/fontc-static-weight-class.md,
                 probes/fontc_static_weight_class/). The .sfd states the value as
                 TTFWeight, so it is written into the source's features as
                 `table OS/2 { WeightClass N; }` -- merged into an existing OS/2
                 block, because fea-rs keeps only the last one.
  italic-angle   babelfont stores metrics as integers and loses a fractional
                 ItalicAngle (-9.3 becomes 9; ../../sfd-batch6/issues/
                 babelfont-italic-angle-rounded.md). The .sfd's own value is
                 written back into the master's italic angle metric.

When the defect is fixed upstream the workaround becomes a no-op and should be
removed; tools/land.py records in the convert commit which ones fired and why.

Usage: workarounds.py <file.glyphs> <file.sfd>     (applies both; prints what fired)
"""
import re
import sys


def sfd_header_value(sfd_text, field):
    head = sfd_text.split("\nStartChar:", 1)[0]
    m = re.search(r"^%s: (.*)$" % re.escape(field), head, re.M)
    return m.group(1).strip() if m else None


def weight_class(glyphs_text, sfd_text):
    """Return (new_text, note or None)."""
    stated = sfd_header_value(sfd_text, "TTFWeight")
    if stated is None or int(stated) == 400:
        return glyphs_text, None
    wc = int(stated)
    t = glyphs_text
    m = re.search(r'code = "table OS/2 \{\n', t)
    if m:
        end = t.index("} OS/2;", m.end())
        if re.search(r"^\s*WeightClass\s+\d+;\s*$", t[m.end():end], re.M):
            t = t[:m.end()] + re.sub(r"(?m)^(\s*)WeightClass\s+\d+;$",
                                     r"\g<1>WeightClass %d;" % wc, t[m.end():end], count=1) + t[end:]
        else:
            t = t[:m.end()] + "    WeightClass %d;\n" % wc + t[m.end():]
    else:
        entry = ('{\ncode = "table OS/2 {\n    WeightClass %d;\n} OS/2;";\n'
                 'name = WeightClassOverride;\n},\n' % wc)
        key = "featurePrefixes = (\n"
        if key in t:
            i = t.index(key) + len(key)
            t = t[:i] + entry + t[i:]
        else:
            anchor = ".formatVersion = 3;\n"
            i = t.index(anchor) + len(anchor)
            t = t[:i] + "featurePrefixes = (\n" + entry + ");\n" + t[i:]
    if t == glyphs_text:
        return glyphs_text, None     # already carried; report only a real change
    return t, ("usWeightClass %d (TTFWeight) as FEA; fontc 1.0.0 drops a single "
               "master's instance weightClass" % wc)


def italic_angle(glyphs_text, sfd_text):
    """Return (new_text, note or None)."""
    stated = sfd_header_value(sfd_text, "ItalicAngle")
    if stated is None:
        return glyphs_text, None
    angle = float(stated)
    if angle.is_integer():
        return glyphs_text, None
    want = -angle          # babelfont's sense is the opposite of post's and the .sfd's
    t = glyphs_text
    m = re.search(r"^metrics = \(\n(.*?)\n\);$", t, re.S | re.M)
    if not m:
        return t, None
    entries = re.findall(r"\{\n(.*?)\n\}", m.group(1), re.S)
    idx = next((i for i, e in enumerate(entries) if 'type = "italic angle";' in e), None)
    if idx is None:
        return t, None
    changed = []

    def fix_block(mv):
        parts = re.split(r"(\{\n(?:[^{}]*\n)?\})", mv.group(1))
        seen, out = -1, []
        for part in parts:
            if part.startswith("{"):
                seen += 1
                if seen == idx:
                    pm = re.search(r"pos = (-?[\d.]+);", part)
                    if pm and float(pm.group(1)) != want:
                        changed.append(pm.group(1))
                        part = part.replace(pm.group(0), "pos = %s;" % want)
            out.append(part)
        return "metricValues = (\n" + "".join(out) + "\n);"

    t = re.sub(r"metricValues = \(\n(.*?)\n\);", fix_block, t, flags=re.S)
    if not changed:
        return glyphs_text, None
    return t, ("italic angle %s (ItalicAngle %s); babelfont stores metrics as "
               "integers and gave %s" % (want, stated, ", ".join(changed)))


ALL = (weight_class, italic_angle)


def apply_all(glyphs_path, sfd_path):
    t = open(glyphs_path, encoding="utf-8").read()
    s = open(sfd_path, encoding="utf-8", errors="replace").read()
    notes = []
    for fn in ALL:
        t, note = fn(t, s)
        if note:
            notes.append(note)
    open(glyphs_path, "w", encoding="utf-8").write(t)
    return notes


if __name__ == "__main__":
    for n in apply_all(sys.argv[1], sys.argv[2]):
        print(n)
