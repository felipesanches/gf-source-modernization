#!/usr/bin/env python3
"""Append the disclose texts of bottleneck items 9 and 11 to the plans of the 14 families landed
2026-10-24, from the values their accepted lists carry. Run from gf-source-modernization after
`land.py <family> --rebuild --write-accepted`; prints what it added. Idempotent.

Usage: python3 tools/probes/binary_to_source/disclose_texts.py <family>...
"""
import json
import re
import sys

HINT = ("The release's `head` table states fontDirectionHint {rel}; the build states 2, the only value "
        "the OpenType specification allows new fonts (the field is deprecated and no renderer reads "
        "it). A `.glyphs` source cannot state the field, so the difference is kept and disclosed.")
U0326 = ("The release kerns with a legacy `kern` table and has no GPOS, so HarfBuzz kerns every pair "
         "and positions combining marks itself. These sources kern through a GPOS kern feature, which "
         "is how fontc builds kerning, and fontc's kerning lookup skips marks; so a run that contains "
         "the combining comma below (U+0326) next to a kerned pair places it differently ({runs} of "
         "the gate's shaped runs per style, every one with U+0326), and U+0326 rendered on its own "
         "sits at a different position with the same ink; every other run shapes alike. Kept and "
         "disclosed.")
PCLT = ("The release carries a `PCLT` table (HP PCL 5 printer metrics; the OpenType specification "
        "says its use is strongly discouraged). fontc writes none, and no renderer reads it, so the "
        "build has no `PCLT`. Kept and disclosed.")

for family in sys.argv[1:]:
    p = "plans/%s.json" % family
    plan = json.load(open(p))
    accepted = plan.get("accepted", [])
    disclose = plan.setdefault("disclose", [])
    added = []
    rows = " ".join(a.get("row", "") for a in accepted)
    m = re.search(r"head\.font_direction_hint \[?(-?\d+)", rows)
    if m and not any("fontDirectionHint" in t for t in disclose):
        disclose.append(HINT.format(rel=m.group(1)))
        added.append("fontDirectionHint %s" % m.group(1))
    runs = sorted({a["summary"] for a in accepted if a["check"] == "shaping"})
    if runs and not any("U+0326" in t for t in disclose):
        counts = sorted({int(x) for s in runs for x in re.findall(r"(\d+) of \d+ runs differ", s)})
        text = "%d to %d" % (counts[0], counts[-1]) if len(counts) > 1 else str(counts[0]) if counts else "some"
        disclose.append(U0326.format(runs=text))
        added.append("U+0326 (%s runs)" % text)
    if "PCLT" in rows and not any("PCLT" in t for t in disclose):
        disclose.append(PCLT)
        added.append("PCLT")
    json.dump(plan, open(p, "w"), indent=2, ensure_ascii=False)
    open(p, "a").write("\n")
    print("%s: added %s" % (family, ", ".join(added) or "nothing"))
    for a in accepted:
        covered = (("font_direction_hint" in a.get("row", "")) or a["check"] == "shaping" and "U+0326" in " ".join(disclose)
                   or "PCLT" in a.get("row", "") or a["check"] in ("rendering", "gdef") and "U+0326" in " ".join(disclose))
        if not covered:
            print("   NOT EXPLAINED by a disclose text: %s %s | %s" % (a["style"], a["check"], (a.get("summary") or a.get("row"))[:120]))
