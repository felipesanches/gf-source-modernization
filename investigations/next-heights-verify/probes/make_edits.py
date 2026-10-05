#!/usr/bin/env python3
"""Question answered: applying the investigator's proposed documented .sfd edits, with
each VALUE re-derived here independently, what source copies result -- and does each
copy differ from its unmodified source ONLY by the intended lines?

  addprivate BlueValues <v>   v = the CFF Private BlueValues of the sibling
                              src/<X>.otf in the SAME base tree (families-next.tsv
                              pairing), read with fontTools and printed as FontForge's
                              CFF reader stores them (parsettf.c realarray2str: "%g"
                              per entry, trailing zeros dropped, "[...]").
  nbspwidth                   Ledger only: U+00A0 Width := the .sfd's own space Width
                              (reproduces google/fonts 0436d99c0).

The op itself is the investigator's uncommitted tools/sfd_edit.py `addprivate`
(imported, so its behaviour is what is exercised). Output: <scratch>/edits/<Style>.sfd
and a line-level diff count per file.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 make_edits.py > ../runs/make_edits.txt
"""
import difflib
import io
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
import sfd_edit  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/gf-source-modernization/families-next.tsv"
OUT = "/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify/edits"
BLUES = """Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular
OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular
Rambla-Bold Rambla-BoldItalic Sail-Regular TextMeOne-Regular""".split()


def show(r, rel):
    return subprocess.run(["git", "-C", ARC, "show", f"{r['commit']}:{r['lic']}/{r['family']}/{rel}"],
                          capture_output=True, check=True).stdout


def realarray2str(vals):
    i = len(vals)
    while i > 0 and vals[i - 1] == 0:
        i -= 1
    if i == 0:
        return None
    if i & 1 and i < len(vals):
        i += 1
    return "[" + " ".join("%g" % v for v in vals[:i]) + "]"


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        rows = {r["style"]: r for r in (dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh)}
    for s in BLUES:
        r = rows[s]
        text = show(r, r["source"]).decode("utf-8", "surrogateescape")
        otf = TTFont(io.BytesIO(show(r, r["source"].replace("-TTF.sfd", ".otf"))))
        bv = realarray2str(list(otf["CFF "].cff.topDictIndex[0].Private.BlueValues))
        new, before = sfd_edit.apply(text, "addprivate", f"BlueValues {bv}")
        notes = [f"addprivate BlueValues {bv} (before: {before})"]
        if s == "Ledger-Regular":
            new, b2 = sfd_edit.apply(new, "nbspwidth", "")
            notes.append(f"nbspwidth (before: {b2})")
        path = os.path.join(OUT, f"{s}.sfd")
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
            fh.write(new)
        d = [l for l in difflib.unified_diff(text.split("\n"), new.split("\n"), lineterm="", n=0)
             if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        print(f"{s}: {'; '.join(notes)}")
        for l in d:
            print(f"    {l}")


if __name__ == "__main__":
    main()
