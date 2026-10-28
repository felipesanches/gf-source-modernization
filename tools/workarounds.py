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
                 block, because fea-rs keeps only the last one. A converted binary
                 (tools/land.py, kind binary) states it in OS/2, and its usWidthClass,
                 lost the same way, travels as `WidthClass N` (width_class_fea).
  italic-angle   babelfont stores metrics as integers and loses a fractional
                 ItalicAngle (-9.3 becomes 9; ../../sfd-batch6/issues/
                 babelfont-italic-angle-rounded.md). The .sfd's own value is
                 written back into the master's italic angle metric.

  fixed-pitch    babelfont's TTF reader (as published on 2026-10-24) does not read
                 post.isFixedPitch, so a monospaced binary's build loses the flag
                 (Nanum Gothic Coding). The value is written as the font-level
                 `isFixedPitch` custom parameter, which fontc reads (glyphs-reader
                 font.rs: "postscriptIsFixedPitch" | "isFixedPitch"); the reader change
                 waits for babelfont #119 (fixed_pitch_custom_parameter).
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
    t = weight_class_fea(glyphs_text, wc)
    if t == glyphs_text:
        return glyphs_text, None     # already carried; report only a real change
    return t, ("usWeightClass %d (TTFWeight) as FEA; fontc 1.0.0 drops a single "
               "master's instance weightClass" % wc)


def weight_class_fea(glyphs_text, wc):
    """The .glyphs text with `table OS/2 { WeightClass wc; }` in its features, merged
    into an existing OS/2 block (fea-rs keeps only the last one)."""
    return os2_statement_fea(glyphs_text, "WeightClass", wc)


def width_class_fea(glyphs_text, wc):
    """The same for `WidthClass`: fontc 1.0.0 drops a single master's instance
    widthClass as it does its weightClass (../issues/fontc-static-weight-class.md)."""
    return os2_statement_fea(glyphs_text, "WidthClass", wc)


def os2_statement_fea(glyphs_text, keyword, value):
    t = glyphs_text
    m = re.search(r'code = "table OS/2 \{\n', t)
    if m:
        end = t.index("} OS/2;", m.end())
        if re.search(r"^\s*%s\s+\d+;\s*$" % keyword, t[m.end():end], re.M):
            t = t[:m.end()] + re.sub(r"(?m)^(\s*)%s\s+\d+;$" % keyword,
                                     r"\g<1>%s %d;" % (keyword, value), t[m.end():end], count=1) + t[end:]
        else:
            t = t[:m.end()] + "    %s %d;\n" % (keyword, value) + t[m.end():]
    else:
        t = add_feature_prefix(t, "%sOverride" % keyword,
                               "table OS/2 {\n    %s %d;\n} OS/2;" % (keyword, value))
    return t


def add_feature_prefix(glyphs_text, name, code):
    """The .glyphs text with a feature prefix `name` holding `code`, first in its
    featurePrefixes list (created before the format version's next key when absent)."""
    t = glyphs_text
    entry = '{\ncode = "%s";\nname = %s;\n},\n' % (code.replace("\\", "\\\\").replace('"', '\\"'), name)
    key = "featurePrefixes = (\n"
    if key in t:
        i = t.index(key) + len(key)
        return t[:i] + entry + t[i:]
    anchor = ".formatVersion = 3;\n"
    i = t.index(anchor) + len(anchor)
    return t[:i] + "featurePrefixes = (\n" + entry + ");\n" + t[i:]


# fea-rs-ast's FEA_KEYWORDS: a glyph so named is written with a backslash
FEA_KEYWORDS = {
    "anchor", "anchordef", "anon", "anonymous", "by", "contour", "cursive", "device", "enum",
    "enumerate", "excludedflt", "exclude_dflt", "feature", "from", "ignore", "ignorebaseglyphs",
    "ignoreligatures", "ignoremarks", "include", "includedflt", "include_dflt", "language",
    "languagesystem", "lookup", "lookupflag", "mark", "markattachmenttype", "markclass", "nameid",
    "null", "parameters", "pos", "position", "required", "righttoleft", "reversesub", "rsub",
    "script", "sub", "substitute", "subtable", "table", "usemarkfilteringset", "useextension",
    "valuerecorddef", "base", "gdef", "head", "hhea", "name", "vhea", "vmtx",
}


def gdef_classes_fea(glyphs_text, ttfont):
    """The .glyphs text with the release's GDEF glyph classes stated as
    `table GDEF { GlyphClassDef ...; } GDEF;` in a feature prefix, glyph by glyph id, so
    the compiler keeps them. A compiler classes a glyph base or ligature only for an
    attaching anchor and mark only by category, so a release whose GDEF classes glyphs
    otherwise cannot keep its classes through the source's categories; a plan asks for
    this (`gdef_classes_fea`) when the gate shows the lost classes matter."""
    gdef = ttfont["GDEF"].table if "GDEF" in ttfont else None
    if gdef is None or gdef.GlyphClassDef is None:
        return glyphs_text
    names = re.findall(r'^glyphname = "?([^";]+)"?;$', glyphs_text, re.M)
    order = ttfont.getGlyphOrder()
    if len(names) != len(order):
        raise ValueError("%d glyphs in the source, %d in the release" % (len(names), len(order)))
    classes = [[] for _ in range(4)]
    for gid, glyph in enumerate(order):
        c = gdef.GlyphClassDef.classDefs.get(glyph, 0)
        if 1 <= c <= 4:
            n = names[gid]
            classes[c - 1].append("\\" + n if n in FEA_KEYWORDS else n)
    statement = ", ".join("[%s]" % " ".join(m) if m else "" for m in classes)
    return add_feature_prefix(glyphs_text, "GDEF",
                              "table GDEF {\n    GlyphClassDef %s;\n} GDEF;" % statement)


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


def fixed_pitch_custom_parameter(glyphs_text):
    """The .glyphs text with the font-level custom parameter `isFixedPitch = 1`, added to
    the font's customParameters list or as that list before the `date` key."""
    t = glyphs_text
    if re.search(r"^name = isFixedPitch;$", t, re.M):
        return t
    entry = "{\nname = isFixedPitch;\nvalue = 1;\n},\n"
    m = re.search(r"^customParameters = \(\n", t, re.M)
    if m and m.start() < t.index("\nfontMaster = (") if "\nfontMaster = (" in t else bool(m):
        return t[:m.end()] + entry + t[m.end():]
    key = re.search(r"^date = ", t, re.M)
    block = "customParameters = (\n" + entry.rstrip(",\n") + "\n);\n"
    return t[:key.start()] + block + t[key.start():]


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
