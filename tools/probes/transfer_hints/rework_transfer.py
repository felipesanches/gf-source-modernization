#!/usr/bin/env python3
"""Question answered: does the reworked `gftools transfer-hints` (gftools#1248, font to font:
take the release's glyph when the built one draws the same outline) give each built font the
release's hinting, under tools/functional_gate.py's hinting check?

Usage: rework_transfer.py <gftools checkout> <release.ttf> <built.ttf> <out.ttf> [<hint source>]
(the hint source defaults to the release; a .ttx dump of it is the format a source repository keeps)
Imports Lib/gftools/scripts/transfer_hints.py from the checkout; prints refused glyphs, or the
hinting check's verdict on the result.
"""
import importlib.util
import os
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import functional_gate as fg  # noqa: E402

checkout, rel, built, out = sys.argv[1:5]
hint_src = sys.argv[5] if len(sys.argv) > 5 else rel
spec = importlib.util.spec_from_file_location(
    "transfer_hints", os.path.join(checkout, "Lib/gftools/scripts/transfer_hints.py"))
th = importlib.util.module_from_spec(spec)
spec.loader.exec_module(th)
src, dst = th.load(hint_src), TTFont(built, recalcBBoxes=False)
refused = th.transfer(src, dst)
if refused:
    print("  refused %d: %s" % (len(refused), "; ".join("%s (%s)" % kv for kv in sorted(refused.items())[:6])))
    sys.exit(0)
dst.save(out)
A, B = fg.Font(rel), fg.Font(out)
_, _, ka, kb = fg.correspondence(A, B)
res = fg.check_hinting(A, B, ka, kb, 3)
print("  hinting check: %s %s" % (res["status"], res["summary"][:150]))
for f in res["failures"][:3]:
    print("    - " + f[:170])
