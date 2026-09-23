#!/usr/bin/env python3
"""Question answered: which cmap-related converter options make each style map
EXACTLY the codepoints its release maps?

The table gate accepts a codepoint the build GAINS (sfd-batch5/tools/table_gate.py,
cmap_blocking: "the accepted duplicate-cmap class"), so a gate-clean build can still
map codepoints the release does not. This measures the codepoint set directly, from
the converted .glyphs, for the four combinations of
  --add-legacy-duplicate-cmap   (makeotf's duplicate set, added where unmapped)
  --drop-alternate-unicodes     (drop the .sfd's AltUni2 alternates)
Conversion only, no compile: the built cmap is the union of the glyphs' codepoints.

Usage: gftools/venv/bin/python3 tools/probes/cmap_recipe/run.py > tools/probes/cmap_recipe/RESULT.tsv
"""
import itertools, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import recipe  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

BF = "/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont"
OPTS = [("dup", "--add-legacy-duplicate-cmap"), ("dropalt", "--drop-alternate-unicodes")]


def codepoints(glyphs_path):
    out = set()
    for m in re.finditer(r"^unicode = \(?([^;]*?)\)?;$", open(glyphs_path).read(), re.M):
        out |= {int(v) for v in re.split(r"[,\s]+", m.group(1).strip()) if v}
    return out


def main():
    print("style\trelease_dups\t" + "\t".join(
        "+".join(n for (n, _), on in zip(OPTS, combo) if on) or "none"
        for combo in itertools.product([0, 1], repeat=len(OPTS))) + "\tmatching")
    with tempfile.TemporaryDirectory() as tmp:
        for row in recipe.rows():
            src = os.path.join(tmp, "s.sfd")
            open(src, "w", encoding="utf-8", errors="replace").write(recipe.source_text(row))
            rel = set(TTFont(row["shipped"]).getBestCmap() or {})
            cells, match = [], []
            for combo in itertools.product([0, 1], repeat=len(OPTS)):
                flags = [f for (_, f), on in zip(OPTS, combo) if on]
                g = os.path.join(tmp, "o.glyphs")
                subprocess.run([BF, src, g] + flags, capture_output=True, check=True)
                ours = codepoints(g)
                gained, lost = sorted(ours - rel), sorted(rel - ours)
                label = "+".join(n for (n, _), on in zip(OPTS, combo) if on) or "none"
                cells.append("=" if not gained and not lost else
                             "+%s-%s" % (",".join("%04X" % c for c in gained),
                                         ",".join("%04X" % c for c in lost)))
                if not gained and not lost:
                    match.append(label)
            print("%s\t%s\t%s\t%s" % (row["style"], recipe.legacy_duplicate_cmap(row["shipped"]),
                                      "\t".join(cells), ",".join(match) or "NONE"))


if __name__ == "__main__":
    main()
