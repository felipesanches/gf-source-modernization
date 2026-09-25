#!/usr/bin/env python3
"""Question answered: is "the release was exported by FontForge from the sibling
src/<X>.otf, whose CFF Private BlueValues snapped the OS/2 heights" CONSISTENT across
EVERY style of both batches that has such an .otf -- not only across the 20 styles the
investigator chose? A style whose release matches the rule WITHOUT the .otf's blues but
NOT with them would contradict the mechanism (the exporter would have had the blues).

For every row of families.tsv and families-next.tsv whose paired source is a -TTF.sfd
with a sibling src/<X>.otf (same base tree) carrying CFF BlueValues:
  - vintage from the release's FFTM stamp (tools/recipe.py rule: < 1337023489 -> 2011);
  - the rule on the paired .sfd (committed ../../heights/ff_heights_probe.py, which
    looks glyphs up by primary OR AltUni codepoint, lowest gid, as SFFindGID does),
    once with no blues and once with the .otf's BlueValues (read here with fontTools);
  - tie: does the .otf's head.created equal the release FFTM sourceCreated?
Prints one line per style and height with the verdict:
  both / blues-only / noblues-only (CONTRADICTION) / neither.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 blues_theory_all.py > ../runs/blues_theory_all.txt
"""
import io
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, "/home/fsanches/compartilhado/sfd-reland/investigations/heights")
import ff_heights_probe as P  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
W = "/home/fsanches/compartilhado/sfd-reland"
E1904 = 2082844800
FIX = 1337023489


def rows(path):
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]


def show(r, rel):
    p = f"{r['lic']}/{r['family']}/{rel}" if r["kind"] == "hg" else rel
    q = subprocess.run(["git", "-C", f"{ARC}/{r['base']}.git", "show", f"{r['commit']}:{p}"],
                       capture_output=True)
    return q.stdout if q.returncode == 0 else None


def main():
    tally = {}
    for tsv in ("families.tsv", "families-next.tsv"):
        for r in rows(os.path.join(W, tsv)):
            if not r["source"].endswith("-TTF.sfd") or not os.path.exists(r["shipped"]):
                continue
            otf_rel = r["source"][: -len("-TTF.sfd")] + ".otf"
            data = show(r, otf_rel)
            if data is None:
                continue
            otf = TTFont(io.BytesIO(data))
            if "CFF " not in otf:
                continue
            bv = getattr(otf["CFF "].cff.topDictIndex[0].Private, "BlueValues", None)
            if not bv:
                continue
            rel = TTFont(r["shipped"])
            if "FFTM" not in rel:
                print(f"{tsv}\t{r['style']}\tno FFTM in release; skipped")
                continue
            ff = rel["FFTM"]
            year = 2011 if ff.FFTimeStamp - E1904 < FIX else 2012
            tie = otf["head"].created == ff.sourceCreated
            sfd_text = show(r, r["source"]).decode("utf-8", "replace")
            font = P.parse(sfd_text)
            has_priv = font["blues"] is not None
            o = rel["OS/2"]
            if o.version < 2:
                print(f"{tsv}\t{r['style']}\trelease OS/2 v{o.version}: no heights; skipped")
                continue
            blues = "[" + " ".join(str(v) for v in bv) + "]"
            for label, lst, want in (("x", P.XH, o.sxHeight), ("cap", P.CAP, o.sCapHeight)):
                vals = {}
                for bname, b in (("none", None), ("otf", blues)):
                    f = dict(font)
                    f["blues"] = b if not has_priv else font["blues"]
                    res = P.standard_height(P.V(year), f, lst)[0]
                    vals[bname] = (P.exported(res), None if res is None else round(res[0], 3))
                mn = vals["none"][0] == want
                mo = vals["otf"][0] == want
                verdict = ("both" if mn and mo else "blues-only" if mo else
                           "noblues-only CONTRADICTION" if mn else "neither")
                tally[verdict] = tally.get(verdict, 0) + 1
                print(f"{tsv}\t{r['style']}\t{label}\trelease {want}\tFFTM {year}\t"
                      f"noblues {vals['none'][0]} (raw {vals['none'][1]})\totf-blues {vals['otf'][0]}\t"
                      f"{verdict}\totf-head-created==FFTM {tie}\tsfd-has-private {has_priv}\tBV {blues}")
    print("TALLY", tally)


if __name__ == "__main__":
    main()
