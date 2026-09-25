#!/usr/bin/env python3
"""Was each release exported by FontForge with its OpenType layout output ON or OFF?

Question: a release that lacks a GSUB its source declares (Megrim; Nosifer before it)
was either exported in FontForge's non-OpenType mode, or edited afterwards. FontForge
20110222 tottf.c initATTables writes GSUB/GPOS/GDEF (and, with ttf_flag_dummyDSIG, a
dummy DSIG) only when `at->opentypemode`; a legacy `kern` only when neither OpenType
nor Apple mode is on (or with ttf_flag_oldkern). This prints, per release, the signals
that decide it, next to what the paired source declares:

  * table set: GSUB / GPOS / GDEF / DSIG / kern / morx present?
  * OS/2.usMaxContext (FontForge sets it from the GSUB/GPOS it wrote; 1 = none)
  * FFTM: FontForge build stamp, source created/modified; head.created (time of export)
  * source: number of GSUB/GPOS lookups that carry a feature ('Lookup:' lines with a
    non-empty feature list), kerning present (KernClass2/Kerns2)

It also lists every TTF in the googlefontdirectory-hg monorepo whose head.created lies
within +-120 s of a non-OpenType release, to show export batches (--batch).

Pairing: families-next.tsv (the pipeline's own), sources read from the repo archive at
the pinned hg commit, releases from google/fonts (byte-identical to the monorepo copies).

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 release_export_mode.py \
        Megrim Poly-Italic RibeyeMarrow-Regular Varela-Regular [--batch]
"""
import datetime
import io
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/sfd-reland"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
EPOCH = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)


def t1904(s):
    return (EPOCH + datetime.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M:%S")


def rows():
    out = {}
    for line in open(W + "/families-next.tsv"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 9 and p[0] != "repo":
            out[p[6]] = p
    return out


def source_text(p):
    repo, fam, lic, kind, base, commit, style, src, shipped = p[:9]
    path = "%s/%s/%s" % (lic, fam, src) if kind == "hg" else src
    return subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show", "%s:%s" % (commit, path)],
                          capture_output=True, check=True).stdout.decode("utf-8", "replace")


def main():
    styles = [a for a in sys.argv[1:] if not a.startswith("--")]
    table = rows()
    non_ot = []
    for s in styles:
        p = table[s]
        f = TTFont(p[8])
        src = source_text(p)
        head = src.split("\nBeginChars:")[0]
        lk = re.findall(r"^Lookup: (\d+) \d+ \d+ \"[^\"]*\"\s+\{.*\} \[(.*)\]\s*$", head, re.M)
        gsub = sum(1 for t, feats in lk if int(t) < 256 and feats.strip())
        gpos = sum(1 for t, feats in lk if int(t) >= 256 and feats.strip())
        kern = len(re.findall(r"^(KernClass2|Kerns2|KernPairs):", src, re.M))
        tabs = {t: (t in f) for t in ("GSUB", "GPOS", "GDEF", "DSIG", "kern", "morx")}
        fftm = f["FFTM"] if "FFTM" in f else None
        print("%s  release %s" % (s, p[8].split("/google/fonts/")[-1]))
        print("   tables   %s" % " ".join("%s=%s" % (k, "yes" if v else "no") for k, v in tabs.items()))
        print("   usMaxContext %d; head.created %s UTC" % (f["OS/2"].usMaxContext, t1904(f["head"].created)))
        if fftm:
            print("   FFTM build %s; source created %s; modified %s" % (
                t1904(fftm.FFTimeStamp), t1904(fftm.sourceCreated), t1904(fftm.sourceModified)))
        print("   source %s: %d GSUB and %d GPOS lookups with a feature; %d kerning records"
              % (p[7], gsub, gpos, kern))
        mode = "OpenType ON" if (tabs["GSUB"] or tabs["GPOS"] or tabs["GDEF"]) else (
            "OpenType OFF (no layout tables although the source declares %d lookups)" % (gsub + gpos)
            if gsub + gpos else "undecidable (source declares no lookups)")
        print("   => %s" % mode)
        if mode.startswith("OpenType OFF"):
            non_ot.append((s, f["head"].created))
    if "--batch" in sys.argv and non_ot:
        base = "googlefonts/googlefontdirectory-hg"
        commit = "52f780bc9d197280a9f430574e179a5f233c56b6"
        ls = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "ls-tree", "-r", commit],
                            capture_output=True, check=True, text=True).stdout
        ttfs = [l.split("\t")[1] for l in ls.splitlines() if l.endswith(".ttf")]
        print("== export batches (monorepo %s, %d TTFs)" % (commit[:12], len(ttfs)))
        created = {}
        for path in ttfs:
            blob = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show", "%s:%s" % (commit, path)],
                                  capture_output=True).stdout
            try:
                t = TTFont(io.BytesIO(blob), lazy=True)
                created[path] = (t["head"].created, "GSUB" in t, "GPOS" in t, "kern" in t)
            except Exception:
                continue
        for s, c in non_ot:
            near = sorted((abs(v[0] - c), k, v) for k, v in created.items() if abs(v[0] - c) <= 120)
            print("   %s (%s): %d TTF(s) within 120 s" % (s, t1904(c), len(near)))
            for d, k, v in near:
                print("      %+4ds %s GSUB=%s GPOS=%s kern=%s" % (v[0] - c, k, v[1], v[2], v[3]))


if __name__ == "__main__":
    main()
