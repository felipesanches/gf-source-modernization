#!/usr/bin/env python3
"""Place the FontForge-related filter registrations in babelfont/src/filters/mod.rs
under the help headings they have in gf-sfd-conversion 8b59bc3, keeping only the
entries whose module file exists in the tree. Run from the repository root."""
import os
import sys

MODRS = "babelfont/src/filters/mod.rs"
FILTERS = "babelfont/src/filters/"

LEGACY_HEADER = '    group "Filters for reproducing a legacy FontForge export" {'
KEEP_HEADER = '    group "Filters for keeping what the source states" {'

LEGACY = [
    ("DropAlternateUnicodes", "dropalternateunicodes"),
    ("SnapComponentTransforms", "snapcomponenttransforms"),
    ("FontForgeUnderlinePosition", "fontforgeunderlineposition"),
    ("FontForgeHeightGlyphCountMean", "fontforgeheightglyphcountmean"),
    ("FontForgeOs2Defaults", "fontforgeos2defaults"),
]
KEEP = [
    ("KeepSourceGlyphNames", "keepsourceglyphnames"),
    ("KeepSourceAdvances", "keepsourceadvances"),
]
REVERSE = ("ReversePathDirection", "reversepathdirection")


def entry(t, m):
    return f'        {t}({m}) => "{m}",'


def exists(m):
    return os.path.exists(os.path.join(FILTERS, m + ".rs"))


def normalize(text):
    managed = {entry(t, m) for t, m in LEGACY + KEEP + [REVERSE]}
    out = []
    skipping = False
    for line in text.split("\n"):
        if line in (LEGACY_HEADER, KEEP_HEADER):
            skipping = True
            continue
        if skipping:
            if line == "    }":
                skipping = False
            continue
        if line in managed:
            continue
        if line == "mod fontforge_standard_height;":
            continue
        out.append(line)
    text = "\n".join(out)

    if exists("fontforge_standard_height"):
        text = text.replace(
            "mod curve_filter_common;\n",
            "mod curve_filter_common;\nmod fontforge_standard_height;\n",
            1,
        )

    blocks = []
    legacy = [entry(t, m) for t, m in LEGACY if exists(m)]
    keep = [entry(t, m) for t, m in KEEP if exists(m)]
    if legacy:
        blocks.append("\n".join([LEGACY_HEADER] + legacy + ["    }"]))
    if keep:
        blocks.append("\n".join([KEEP_HEADER] + keep + ["    }"]))
    anchor = '        RetainGlyphs(retainglyphs) => "retainglyphs",\n    }\n'
    assert text.count(anchor) == 1, "anchor not found"
    if blocks:
        text = text.replace(anchor, anchor + "\n".join(blocks) + "\n", 1)

    if exists(REVERSE[1]):
        cpd = '        CorrectPathDirection(correctpathdirection) => "correctpathdirection",\n'
        assert text.count(cpd) == 1
        text = text.replace(cpd, cpd + entry(*REVERSE) + "\n", 1)
    return text


if __name__ == "__main__":
    with open(MODRS) as f:
        before = f.read()
    after = normalize(before)
    if after != before:
        with open(MODRS, "w") as f:
            f.write(after)
        print("normalized", MODRS, file=sys.stderr)
