#!/usr/bin/env python3
"""Which styles does the proposed "a mark that advances is Spacing Combining" rule touch?

Question answered: babelfont's SFD reader gives every `GlyphClass: 4` glyph the Glyphs
subCategory Nonspacing, and fontc exports a Nonspacing mark zero-width
(glyphs-reader 1.0.0 Glyph::is_nonspacing_mark; glyphs2fontir 1.0.0 source.rs "glyphs
non-spacing marks are 0-width"). FontForge's exporter writes every advance as the .sfd
states it. For each style of a pairing table, which GlyphClass-4 glyphs state a non-zero
Width, and what advance does the release give each (by the glyph's codepoint when it has
one, else by name)? A style listed here is one whose build the rule changes; a style not
listed cannot be changed by it.

Usage:
  FAMILIES=<pairing.tsv> advancing_marks.py            (default: gf-source-modernization/families-next.tsv)
Prints: style, glyph, sfd Width, release advance (or "absent").
"""
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/gf-source-modernization"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"


def rows(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh if l.strip()]


def source_text(r):
    path = "%s/%s/%s" % (r["lic"], r["family"], r["source"]) if r["kind"] == "hg" else r["source"]
    p = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, r["base"]), "show", "%s:%s" % (r["commit"], path)],
                       capture_output=True)
    return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else ""


def main():
    fam = os.environ.get("FAMILIES", os.path.join(W, "families-next.tsv"))
    for r in rows(fam):
        text = source_text(r)
        hits = []
        for m in re.finditer(r"^StartChar: ([^\n]*)\n(.*?)^EndChar", text, re.M | re.S):
            body = m.group(2)
            if not re.search(r"^GlyphClass: 4$", body, re.M):
                continue
            w = re.search(r"^Width: (-?\d+)", body, re.M)
            if w and int(w.group(1)) != 0:
                enc = re.search(r"^Encoding: \S+ (-?\d+) ", body, re.M)
                hits.append((m.group(1).strip(), int(w.group(1)), int(enc.group(1)) if enc else -1))
        if not hits:
            continue
        rel = TTFont(r["shipped"])
        cmap = rel.getBestCmap() or {}
        hmtx = rel["hmtx"].metrics
        for name, width, uni in hits:
            g = cmap.get(uni) if uni >= 0 else None
            g = g or (name if name in hmtx else None)
            print("%s\t%s\t%d\t%s" % (r["style"], name, width, hmtx[g][0] if g else "absent"))


if __name__ == "__main__":
    main()
