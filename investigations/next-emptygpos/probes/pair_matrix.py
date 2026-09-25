#!/usr/bin/env python3
"""Which two-character sequences shape differently in plain left-to-right text?

Question: a release that kerns through a legacy `kern` table and a build that kerns
through GPOS -- do they kern the SAME pairs by the same amount in ordinary LTR text?
sweep.py and table_gate's legacy-kern arbitration only shape the pairs the RELEASE
kerns, so a pair that only the build kerns is invisible to them. This shapes every
ordered pair of the release's cmap'd characters (including a character with itself).

Signal read: HarfBuzz ink positions (glyph name, cluster, pen+offset; final pen), as
sfd-batch5 sweep.py computes them, direction ltr, script Latn, language en, default
buffer flags, default features. A differing pair is reported with both results,
grouped as: soft-hyphen (either member U+00AD), mark (either member a combining mark),
other.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 pair_matrix.py \
        <release.ttf> <candidate.ttf> [--show N]
"""
import collections
import importlib.util
import sys
import unicodedata

import uharfbuzz as hb
from fontTools.ttLib import TTFont

SWEEP = "/home/fsanches/compartilhado/sfd-batch5/tools/probes/gdef_mark_vs_base/sweep.py"
_spec = importlib.util.spec_from_file_location("sweep", SWEEP)
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show = 12
    if "--show" in sys.argv:
        show = int(sys.argv[sys.argv.index("--show") + 1])
        args = [a for a in args if a != str(show)]
    release, cand = args[:2]
    cps = [c for c in sorted(TTFont(release).getBestCmap()) if c >= 0x20]
    fa, fb = sweep.hbfont(release), sweep.hbfont(cand)
    na, nb = sweep.glyph_names(release), sweep.glyph_names(cand)
    diffs = []
    for a in cps:
        for b in cps:
            t = chr(a) + chr(b)
            ra = sweep.run(fa, t, "ltr", hb.BufferFlags.DEFAULT, None, na)
            rb = sweep.run(fb, t, "ltr", hb.BufferFlags.DEFAULT, None, nb)
            if ra != rb:
                diffs.append((t, ra, rb))

    def group(t):
        if "\xad" in t:
            return "soft-hyphen"
        if any(unicodedata.category(c) in ("Mn", "Mc", "Me") for c in t):
            return "mark"
        return "other"
    by = collections.Counter(group(t) for t, _, _ in diffs)
    print("%s vs %s: %d ordered pairs, %d differ %s" % (
        release.rsplit("/", 1)[-1], cand.rsplit("/", 1)[-1], len(cps) ** 2, len(diffs),
        dict(sorted(by.items()))))
    firsts = collections.Counter(t[0] for t, _, _ in diffs if group(t) == "other")
    if firsts:
        print("  'other' differences by first character: %s" % ", ".join(
            "%s(U+%04X)=%d" % (c, ord(c), n) for c, n in firsts.most_common(20)))
    for g in ("other", "soft-hyphen", "mark"):
        for t, ra, rb in [d for d in diffs if group(d[0]) == g][:show]:
            print("  %-11s %r\n     release %s\n     cand    %s" % (g, t, ra, rb))


if __name__ == "__main__":
    main()
