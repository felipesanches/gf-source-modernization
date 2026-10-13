#!/usr/bin/env python3
"""Question answered: what does a binary-only family's landing need to disclose, and where did
its earlier material live? Writes plans/<family>.json (earlier_sources, disclose) and prints
its families-binary.tsv rows, from measurements -- not from upstream_info.md:

  - kerning: a legacy `kern` table (pairs per style) with no GPOS kern feature is rebuilt as a
    GPOS kern feature; beside a GPOS kern feature it is not carried;
  - hinting: glyph instructions per style; a font program with no glyph calling it (and a
    control value program that only sets dropout control) is said so;
  - earlier sources: what the repository METADATA.pb records holds at the recorded commit
    (googlefontdirectory-hg: the family's directory).

The texts are the ones the hand-written plans of 2026-10-13 use. Anything unusual (a residual
the gates report, a provenance question) is not covered: read the probe log and edit the plan.

  python3 make_plan.py <google/fonts> <rev> <repo archive> <family> [<commit for rows>]
"""
import json
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont

GF, REV, ARCHIVE, FAM = sys.argv[1:5]
ROW_COMMIT = sys.argv[5] if len(sys.argv) > 5 else "2eb0b48d5f760f62e286216f0859a8c540dbc1bd"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_EXT = (".ttf", ".otf", ".woff", ".woff2", ".eot", ".ttc")


def git(repo, *args):
    r = subprocess.run(["git", "-c", "core.quotePath=off", "-C", repo, *args], capture_output=True, text=True,
                       errors="replace")
    return r.stdout if r.returncode == 0 else None


def archive_path(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)/(.+?)(?:\.git)?/?$", url.strip())
    if not m:
        return None
    host, path = m.groups()
    parts = path.split("/")
    for p in (os.path.join(ARCHIVE, parts[0], parts[-1] + ".git"),
              os.path.join(ARCHIVE, host, path + ".git")):
        if os.path.isdir(p):
            return p
    od = next((d for d in os.listdir(ARCHIVE) if d.lower() == parts[0].lower()), None)
    if od:
        rd = next((d for d in os.listdir(os.path.join(ARCHIVE, od))
                   if d.lower() == (parts[-1] + ".git").lower()), None)
        if rd:
            return os.path.join(ARCHIVE, od, rd)
    return None


def facts(path):
    f = TTFont(path)
    kern = sum(len(t.kernTable) for t in f["kern"].kernTables
               if hasattr(t, "kernTable")) if "kern" in f else 0
    gpos_kern = "GPOS" in f and f["GPOS"].table.FeatureList is not None and any(
        r.FeatureTag == "kern" for r in f["GPOS"].table.FeatureList.FeatureRecord)
    instructed = 0
    if "glyf" in f:
        g = f["glyf"]
        instructed = sum(1 for n in f.getGlyphOrder()
                         if getattr(g[n], "program", None) and len(g[n].program.getBytecode()))
    prep = ""
    if "prep" in f:
        prep = " ".join(x.split("\t")[0].split("[")[0] if not x.lstrip("-").isdigit() else x
                        for x in f["prep"].program.getAssembly())
    return {"kern": kern, "gpos_kern": gpos_kern, "fpgm": "fpgm" in f,
            "instructed": instructed, "glyphs": len(f.getGlyphOrder()), "prep": prep}


def span(values):
    lo, hi = min(values), max(values)
    return str(lo) if lo == hi else "%d to %d" % (lo, hi)


def disclosures(per_style):
    out = []
    styles = len(per_style)
    one = styles == 1
    the_release = "The release" if one else "The releases"
    legacy_only = [v for v in per_style.values() if v["kern"] and not v["gpos_kern"]]
    legacy_beside = [v for v in per_style.values() if v["kern"] and v["gpos_kern"]]
    if legacy_only:
        out.append("%s kern%s with a legacy `kern` table (%s pairs%s) and %s no GPOS; these "
                   "sources kern through a GPOS kern feature, which is how fontc builds kerning. "
                   "HarfBuzz shapes every kerned pair alike in both (the functional gate). "
                   "Decided 2026-10-01: releases with an old kern table are accepted and "
                   "disclosed." % (the_release, "s" if one else "", span([v["kern"] for v in legacy_only]),
                                   "" if one else " per style", "has" if one else "have"))
    if legacy_beside:
        out.append("%s kern%s through a GPOS kern feature and also carr%s a legacy `kern` table "
                   "(%s pairs%s). Shapers read the GPOS feature, which these sources keep; the "
                   "legacy table, read only by software without GPOS support, is not carried."
                   % (the_release, "s" if one else "", "ies" if one else "y",
                      span([v["kern"] for v in legacy_beside]), "" if one else " per style"))
    hinted = [v for v in per_style.values() if v["instructed"]]
    fpgm_only = [v for v in per_style.values() if v["fpgm"] and not v["instructed"]]
    if hinted:
        partial = [v for v in hinted if v["instructed"] < 0.5 * v["glyphs"]]
        what = "hinted (TrueType instructions)" if not partial else \
            "partly hinted (TrueType instructions in %s of %s glyphs%s)" % (
                span([v["instructed"] for v in hinted]), span([v["glyphs"] for v in hinted]),
                "" if one else " per style")
        out.append("The released font%s %s %s. These sources carry no TrueType instructions, "
                   "so the build is hinted by ttfautohint: the outlines, spacing and layout are "
                   "the release's, its rendering at small sizes under a TrueType interpreter is "
                   "not. Hinting is not compared by the gates."
                   % ("" if one else "s", "is" if one else "are", what))
    if fpgm_only and not hinted:
        dropout = all(v["prep"] == "PUSHW 511 SCANCTRL PUSHB 4 SCANTYPE" for v in fpgm_only)
        out.append("The release%s no glyph instructions: %s font program defines functions that "
                   "no glyph calls, and %s control value program %s. These sources carry no "
                   "TrueType instructions, and the build is hinted by ttfautohint, as for every "
                   "release that has a font program: the outlines, spacing and layout are the "
                   "release's, its rendering at small sizes under a TrueType interpreter is not. "
                   "Hinting is not compared by the gates."
                   % (" has" if one else "s have", "its" if one else "their",
                      "its" if one else "their",
                      "only turns on dropout control (SCANCTRL 511, SCANTYPE 4)" if dropout
                      else "sets up the rasterizer without hinting any glyph"))
    return out


def earlier_sources(fam_dir):
    meta = git(GF, "show", "%s:%s/METADATA.pb" % (REV, fam_dir)) or ""
    url = (re.search(r'repository_url:\s*"([^"]*)"', meta) or [None, ""])[1]
    commit = (re.search(r'commit:\s*"([^"]*)"', meta) or [None, ""])[1]
    repo = archive_path(url) if url else None
    if not repo or not commit:
        return []
    tree = (git(repo, "ls-tree", "-r", "--name-only", commit) or "").split("\n")
    if "googlefontdirectory-hg" in url:
        mine = [p for p in tree if p.startswith(fam_dir + "/")]
        src = [os.path.basename(p) for p in mine if p.startswith(fam_dir + "/src/")]
        tail = ("; src/ holds %s, no source." % ", ".join(sorted(src))) if src else "; no source."
        return ["%s at %s, %s/: the font as built and its metadata%s"
                % (url.replace("www.", ""), commit, fam_dir, tail)]
    fonts = [p for p in tree if p.lower().endswith(FONT_EXT)]
    ttx = [p for p in tree if p.lower().endswith(".ttx")]
    held = []
    if fonts:
        held.append("the font%s as built (%d font file%s)" % (
            "s" if len(fonts) > 1 else "", len(fonts), "s" if len(fonts) > 1 else ""))
    if ttx:
        held.append("TTX dumps of a build (%d files)" % len(ttx))
    if not held:
        held.append("no font file")
    return ["%s at %s: %s; no source." % (url.replace("www.", ""), commit, " and ".join(held))]


def main():
    fam_dir = next(d for d in ("ofl/" + FAM, "apache/" + FAM, "ufl/" + FAM)
                   if os.path.isdir(os.path.join(GF, d)))
    ttfs = sorted(p for p in os.listdir(os.path.join(GF, fam_dir)) if p.endswith(".ttf"))
    per_style = {t: facts(os.path.join(GF, fam_dir, t)) for t in ttfs}
    plan = {"repo": FAM, "commits": [], "earlier_sources": earlier_sources(fam_dir),
            "disclose": disclosures(per_style)}
    if not plan["earlier_sources"]:
        del plan["earlier_sources"]
    with open(os.path.join(HERE, "..", "..", "..", "plans", FAM + ".json"), "w") as out:
        json.dump(plan, out, indent=2, ensure_ascii=False)
        out.write("\n")
    lic = fam_dir.split("/")[0]
    for t in ttfs:
        print("\t".join([FAM, FAM, lic, "binary", "google/fonts", ROW_COMMIT, t[:-4], t,
                         "%s/%s" % (fam_dir, t)]))


main()
