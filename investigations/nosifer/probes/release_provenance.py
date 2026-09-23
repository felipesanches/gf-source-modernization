#!/usr/bin/env python3
"""Question answered: were the Nosifer / Nosifer Caps releases exported by
FontForge from the -TTF.sfd named in families.tsv, and with which export mode?

Prints, per release: layout tables present, FFTM (FontForge build stamp, source
CreationTime, source ModificationTime -- ttfspecial.c ttf_fftm_dump), head.created
(the moment of generation, tottf.c:2836-2839) and usMaxContext; then the named
sources' CreationTime/ModificationTime; then the other Typomondo fonts that
Dave Crossland committed on 2011-12-19 beside Nosifer.

Usage: /home/fsanches/compartilhado/gftools/venv/bin/python3 release_provenance.py
"""
import datetime
import re
import subprocess

from fontTools.misc.timeTools import timestampToString
from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts/ofl"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
C = "52f780bc9d197280a9f430574e179a5f233c56b6"
LAYOUT = ("GSUB", "GPOS", "GDEF", "DSIG", "kern", "morx", "feat")


def rel(path):
    f = TTFont(path)
    t = f["FFTM"] if "FFTM" in f else None
    print("%-44s layout=%-24s maxctx=%d head.created=%s" % (
        path.split("/ofl/")[1], ",".join(k for k in LAYOUT if k in f) or "-",
        f["OS/2"].usMaxContext, timestampToString(f["head"].created)))
    if t:
        print("%44s FFTM: FontForge build %s | source created %s | source modified %s" % (
            "", timestampToString(t.FFTimeStamp), timestampToString(t.sourceCreated),
            timestampToString(t.sourceModified)))


def src(path):
    text = subprocess.run(["git", "-C", ARC, "show", "%s:%s" % (C, path)], capture_output=True,
                          check=True).stdout.decode("utf-8", "replace")
    ct = int(re.search(r"^CreationTime: (\d+)", text, re.M).group(1))
    mt = int(re.search(r"^ModificationTime: (\d+)", text, re.M).group(1))
    fmt = lambda s: datetime.datetime.fromtimestamp(s, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print("%-60s CreationTime %s  ModificationTime %s  Lookups: %s" % (
        path, fmt(ct), fmt(mt), re.findall(r"^Lookup: \d+ \d+ \d+ \"([^\"]*)\"", text, re.M)))


print("== the two releases")
rel(GF + "/nosifer/Nosifer-Regular.ttf")
rel(GF + "/nosifercaps/NosiferCaps-Regular.ttf")
print("== the sources families.tsv names")
src("ofl/nosifer/src/Nosifer-Regular-TTF.sfd")
src("ofl/nosifercaps/src/NosiferCaps-Regular-TTF.sfd")
print("== the fonts committed with Nosifer on 2011-12-19 (same export session?)")
for p in ("butcherman/Butcherman-Regular.ttf", "creepster/Creepster-Regular.ttf", "eater/Eater-Regular.ttf"):
    rel(GF + "/" + p)
src("ofl/butcherman/src/Butcherman-Regular-TTF.sfd")
print("== monorepo commits")
print(subprocess.run(["git", "-C", ARC, "log", "--all", "--date=iso", "--format=%h %ad %an | %s",
                      "--since=2011-10-20", "--until=2011-12-20", "--",
                      "nosifer", "nosifercaps", "butcherman", "creepster", "eater"],
                     capture_output=True, text=True).stdout)
