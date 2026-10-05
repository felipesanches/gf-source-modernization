#!/usr/bin/env python3
"""Question answered: for the three styles the investigator attributes to the AltUni
lookup gap (KottaOne-Regular, Macondo-Regular, Rosarivo-Italic), which x-height glyphs
does FontForge's SFFindGID find (primary OR AltUni codepoint, lowest gid) versus a
primary-codepoint-only lookup (babelfont #91 as written), what are their tops, and what
does the FFTM-selected (2011, glyph-count) mean give under each lookup?

Also lists, for EVERY style of both batches, each x/cap codepoint that is reachable ONLY
through an AltUni2 entry (the population the proposed #91 follow-up can affect).

Uses the committed rule implementation ../../heights/ff_heights_probe.py (SPLMaxHeight
etc.), with its lookup swapped for the primary-only variant for the comparison.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 altuni_arith.py > ../runs/altuni_arith.txt
"""
import os
import subprocess
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/investigations/heights")
import ff_heights_probe as P  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
W = "/home/fsanches/compartilhado/gf-source-modernization"


def rows(path):
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]


def text(r):
    p = f"{r['lic']}/{r['family']}/{r['source']}" if r["kind"] == "hg" else r["source"]
    q = subprocess.run(["git", "-C", f"{ARC}/{r['base']}.git", "show", f"{r['commit']}:{p}"],
                       capture_output=True)
    return q.stdout.decode("utf-8", "replace") if q.returncode == 0 else None


def primary_only(font, u):
    for gid in sorted(font["glyphs"]):
        g = font["glyphs"][gid]
        if g["unis"] and g["unis"][0] == u:
            return g
    return None


def run(font, lst, year, find):
    old = P.find
    P.find = find
    try:
        tr = []
        res, flats, curves = P.standard_height(P.V(year), dict(font, blues=None), lst, tr)
    finally:
        P.find = old
    return res, flats, curves, tr


def main():
    nxt = {r["style"]: r for r in rows(os.path.join(W, "families-next.tsv"))}
    for s in ("KottaOne-Regular", "Macondo-Regular", "Rosarivo-Italic"):
        font = P.parse(text(nxt[s]))
        print("=" * 70)
        for label, find in (("SFFindGID (primary or AltUni)", P.find), ("primary only", primary_only)):
            res, flats, curves, tr = run(font, P.XH, 2011, find)
            n = sum(c for _, c in curves)
            tot = sum(p for p, _ in curves)
            print(f"{s} x-height, 2011 rule, lookup = {label}: {len(tr)} glyphs, flats={flats}, "
                  f"distinct curve tops={sorted(round(p, 3) for p, _ in curves)} sum={tot:.3f} "
                  f"/ {n} glyphs = {tot / n:.3f} -> {int(tot / n)}")
            if label.startswith("SFF"):
                for ch, name, t, f in tr:
                    print(f"    U+{ch:04X} {name:12s} {f:7s} {t:.3f}")
    print("=" * 70)
    print("codepoints of the x/cap lists reachable only via AltUni2, all styles of both batches:")
    for tsv in ("families.tsv", "families-next.tsv"):
        for r in rows(os.path.join(W, tsv)):
            t = text(r)
            if t is None:
                continue
            font = P.parse(t)
            hits = []
            for label, lst in (("x", P.XH), ("cap", P.CAP)):
                for u in P.walk(lst):
                    a = P.find(font, u)
                    b = primary_only(font, u)
                    if a is not None and (b is None or b["gid"] != a["gid"]):
                        hits.append(f"{label}:U+{u:04X}->{a['name']}"
                                    + ("" if b is None else f" (primary-only finds {b['name']})"))
            if hits:
                print(f"  {tsv}\t{r['style']}\t{' '.join(hits)}")


if __name__ == "__main__":
    main()
