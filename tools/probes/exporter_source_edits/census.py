#!/usr/bin/env python3
"""Question answered: which styles depend on the three exporter-reproducing babelfont flags
that pending/recipe-combined.patch passes and that move into documented .sfd edits instead
(--fontforge-truncate-anchors, --fontforge-legacy-offset-metrics,
--fontforge-underline-position=20190317), and what does each release show?

For every style of families.tsv and families-next.tsv (the .sfd as tools/land.py converts
it, sources.py, BEFORE any truncateanchors op of its plan):

anchors    the AnchorPoint coordinates that are not integers, and how many of them a
           compiler's rounding (otRound, floor(v + 0.5), what fontc does with a fractional
           anchor) puts somewhere else than FontForge's truncation toward zero
           (tottf.c/dumpgpos: putshort of a real). For each of those, the release's GPOS
           anchors of that glyph (every Anchor record of MarkBase/MarkLig/MarkMark/Cursive
           subtables, glyph matched by name, else by codepoint) say which value shipped:
           TRUNC (the truncated pair is there, the rounded one is not), ROUND, BOTH or
           NEITHER. FFTM = the release was exported by FontForge (the patch passed the
           flag only then).
underline  the patch passed =20190317 (position + width/2) for a SplineFontDB 3.2 source or
           a release built from 2018-12-28 on; listed with the source's UnderlinePosition/
           UnderlineWidth, what each rule gives (truncated toward zero) and the release's
           post.underlinePosition.
offset     the patch passed --fontforge-legacy-offset-metrics when the release's FFTM stamp
           is before 2014-09-16; listed with the source's offset-mode win/hhea fields. Which
           of those the flag changes is measured by convert_check.py, not here.

Run from the gf-source-modernization checkout (writes nothing outside $TMPDIR); <rev> takes the plans as
they were at that commit (e2430fa: before these edits; default: the working tree's):
  /home/fsanches/compartilhado/gftools/venv/bin/python3 tools/probes/exporter_source_edits/census.py [<rev>]
"""
import math
import os
import re
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import convert_check  # noqa: E402
import sources  # noqa: E402

UNIX_FROM_1904 = 2082844800
UNDERLINE_TOP = 1545955200          # 2018-12-28, pending/recipe-combined.patch
ONCURVE_BBOX_FIXED = 1410896146     # 2014-09-16, pending/recipe-combined.patch
ANCHOR = re.compile(r'^AnchorPoint: "(?:[^"\\]|\\.)*" (\S+) (\S+) ', re.M)


def ot_round(v):
    return math.floor(v + 0.5)


def glyph_anchors(text):
    """[(glyph name, codepoint, x, y)] for every AnchorPoint of every glyph."""
    out = []
    for m in re.finditer(r"^StartChar: ([^\n]*)\n(.*?)^EndChar", text, re.M | re.S):
        enc = re.search(r"^Encoding: \S+ (-?\d+) ", m.group(2), re.M)
        for a in ANCHOR.finditer(m.group(2)):
            out.append((m.group(1), int(enc.group(1)) if enc else -1, float(a.group(1)), float(a.group(2))))
    return out


def release_anchors(font):
    """{glyph name: set of (x, y)} over every anchor in the release's GPOS."""
    out = {}
    if "GPOS" not in font:
        return out

    def add(g, a):
        if a is not None:
            out.setdefault(g, set()).add((a.XCoordinate, a.YCoordinate))
    for lk in font["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            t = st.ExtSubTable if lk.LookupType == 9 else st
            typ = st.ExtensionLookupType if lk.LookupType == 9 else lk.LookupType
            if typ == 3:
                for g, r in zip(t.Coverage.glyphs, t.EntryExitRecord):
                    add(g, r.EntryAnchor)
                    add(g, r.ExitAnchor)
            elif typ in (4, 5, 6):
                marks = t.MarkCoverage.glyphs if typ in (4, 5) else t.Mark1Coverage.glyphs
                for g, r in zip(marks, (t.MarkArray if typ in (4, 5) else t.Mark1Array).MarkRecord):
                    add(g, r.MarkAnchor)
                if typ == 4:
                    for g, r in zip(t.BaseCoverage.glyphs, t.BaseArray.BaseRecord):
                        for a in r.BaseAnchor:
                            add(g, a)
                elif typ == 5:
                    for g, lig in zip(t.LigatureCoverage.glyphs, t.LigatureArray.LigatureAttach):
                        for comp in lig.ComponentRecord:
                            for a in comp.LigatureAnchor:
                                add(g, a)
                else:
                    for g, r in zip(t.Mark2Coverage.glyphs, t.Mark2Array.Mark2Record):
                        for a in r.Mark2Anchor:
                            add(g, a)
    return out


def fftm(font):
    return font["FFTM"].FFTimeStamp - UNIX_FROM_1904 if "FFTM" in font else None


def header(text, key):
    m = re.search(r"^%s: (\S+)" % key, text.split("\nStartChar:", 1)[0], re.M)
    return m.group(1) if m else None


def main():
    print("== anchors: style, FFTM?, fractional anchors, of which otRound != trunc, release says")
    by_repo = {}
    for r in sources.rows():
        by_repo.setdefault(r["repo"], []).append(r)
    under, offset = [], []
    for repo, rs in by_repo.items():
        override = convert_check.plan_at(sys.argv[1], repo) if len(sys.argv) > 1 else None
        paths = sources.edited(repo, stop_before=("truncateanchors",), tag="census", plan_override=override)
        for r in rs:
            if r["style"] not in paths:
                continue
            text = open(paths[r["style"]], encoding="utf-8", errors="surrogateescape").read()
            font = TTFont(r["shipped"])
            built = fftm(font)
            anchors = glyph_anchors(text)
            frac = [a for a in anchors if not (a[2].is_integer() and a[3].is_integer())]
            differ = [a for a in frac if (ot_round(a[2]), ot_round(a[3])) != (math.trunc(a[2]), math.trunc(a[3]))]
            if frac:
                rel = release_anchors(font)
                cmap = font.getBestCmap() or {}
                says = {"TRUNC": 0, "ROUND": 0, "BOTH": 0, "NEITHER": 0}
                for g, u, x, y in differ:
                    have = rel.get(g) or rel.get(cmap.get(u, None), set())
                    t = (math.trunc(x), math.trunc(y)) in have
                    o = (ot_round(x), ot_round(y)) in have
                    says["BOTH" if t and o else "TRUNC" if t else "ROUND" if o else "NEITHER"] += 1
                print("%-28s %-7s %5d %5d  %s" % (r["style"], "FFTM" if built else "no-FFTM", len(frac), len(differ),
                                                 " ".join("%s=%d" % kv for kv in says.items() if kv[1])))
            version = float((text.split("\n", 1)[0].split(":", 1) + ["0"])[1].strip() or 0)
            if version >= 3.2 or (built is not None and built >= UNDERLINE_TOP):
                pos, wid = header(text, "UnderlinePosition"), header(text, "UnderlineWidth")
                p, w = float(pos or 0), float(wid or 0)
                under.append("%-28s SFD %.1f FFTM %s UnderlinePosition %s UnderlineWidth %s -> "
                             "old rule %d, new rule %d; release %d" % (
                                 r["style"], version, built, pos, wid, math.trunc(p - w / 2),
                                 math.trunc(p + w / 2), font["post"].underlinePosition))
            if built is not None and built < ONCURVE_BBOX_FIXED:
                fields = [k for k in ("OS2WinAOffset", "OS2WinDOffset", "HheadAOffset", "HheadDOffset")
                          if header(text, k) not in (None, "0")]
                if fields:
                    offset.append("%-28s %s" % (r["style"], " ".join(fields)))
    print("\n== underline: styles the patch gave =20190317")
    print("\n".join(under) or "(none)")
    print("\n== offset: styles the patch gave --fontforge-legacy-offset-metrics with offset-mode fields")
    print("%d styles" % len(offset))
    print("\n".join(offset))


if __name__ == "__main__":
    main()
