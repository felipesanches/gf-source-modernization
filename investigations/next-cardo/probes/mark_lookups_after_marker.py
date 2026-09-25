#!/usr/bin/env python3
"""Would defining a feature's own lookups AFTER its "# Automatic Code" marker give
fontc's generated mark lookups the release's precedence? (emulates a converter change)

Question answered: fea-rs 1.0.0 inserts the lookups fontc generates for a feature at
the lookup-list position current when it meets that feature's "# Automatic Code"
comment (compile_ctx.rs: InsertionPoint { lookup_id: next_gpos_id() }). babelfont
defines every FontForge lookup as a top-level block in featurePrefixes, before any
feature, so the generated mark-to-base lookups land AFTER all of them. The release
(FontForge's .sfd order) interleaves them; probes/lookup_order_test.py showed that
moving every MarkBasePos lookup of the release FIRST shapes identically to the
release on 241128 base+mark strings and the 17 strings where our build differs.

This rewrites a converted .glyphs the way the proposed babelfont change would write
it: every featurePrefixes lookup referenced by exactly one feature that carries the
marker, and by nothing else (no other feature, no contextual lookup), is moved from
featurePrefixes to its first `lookup NAME;` reference inside that feature, after the
marker, as a full `lookup NAME { ... } NAME;` block (later references stay references).
The file TEXT is edited, so nothing else changes (re-serialising it with
openstep_plist produced a file fontc refused: "Expected string value"); --control
copies it unchanged.

Usage:
  mark_lookups_after_marker.py <in.glyphs> <out.glyphs> [--control]
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import re
import sys


def main():
    """Edits the file TEXT (openstep_plist.dump re-serialises values fontc then refuses:
    "Expected string value"), so nothing but the moved blocks changes."""
    src, dst = sys.argv[1], sys.argv[2]
    control = "--control" in sys.argv
    text = open(src, encoding="utf-8").read()
    moved = []
    if not control:
        entry = re.compile(r'\{\ncode = "(lookup (\S+) \{.*?\} \2;)";\nname = \2;\n\},?\n', re.S)
        blocks = {m.group(2): m for m in entry.finditer(text)}
        feat = re.compile(r'code = "(# Automatic Code.*?)";\ntag = (\w+);', re.S)
        for fm in list(feat.finditer(text)):
            code = fm.group(1)
            for name in re.findall(r"^lookup (\S+);$", code, re.M):
                if name not in blocks:
                    continue
                pat = re.compile(r"\blookup %s\b" % re.escape(name))
                # referenced anywhere but its own definition and this feature?
                rest = text.replace(blocks[name].group(0), "").replace(fm.group(0), "")
                if pat.search(rest):
                    continue
                code = re.sub(r"^lookup %s;$" % re.escape(name),
                              lambda m, b=blocks[name].group(1): b, code, count=1, flags=re.M)
                moved.append(name)
            new_feature = fm.group(0).replace(fm.group(1), code, 1)
            text = text.replace(fm.group(0), new_feature, 1)
        for name in moved:
            text = text.replace(blocks[name].group(0), "", 1)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("moved %d lookup definition(s) after the marker: %s" % (len(moved), moved))


if __name__ == "__main__":
    main()
