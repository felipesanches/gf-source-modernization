#!/usr/bin/env python3
"""Census of the Google Fonts families that do not build from source yet.

Question answered: of the families gfonts_agents marks `missing_config` or `no_source`,
which need a source-FORMAT conversion (FontForge .sfd, FontLab .vfb/.vfj), which only
need a build config for sources that are already modern (.glyphs/.ufo/.designspace),
which have nothing but binaries -- and which of them this effort has already handled?

Reads data/gfonts_library_sources.json (gfonts_agents) for each family's repository_url
and commit, lists the files at that commit (HEAD when the commit is unknown or missing)
in the local bare mirror under upstream_repos/repo_archive/<owner>/<repo>.git, and
classifies by the source formats present. Offline; the mirrors are read-only.

Usage: census.py > census.tsv
Columns: family, gf_path, status, repo, commit_used, class, n_sfd, n_vfb, n_vfj,
         n_glyphs, n_ufo, n_designspace, n_binaries, already, shipped, fftm, fftm_build
shipped: font files google/fonts ships for the family (V = a variable font among them);
fftm: how many carry FontForge's FFTM table -- FontForge exported them, so where both
.sfd and .vfb exist the .sfd is the likely master; fftm_build: the earliest FFTM
FFTimeStamp, as the FontForge build date.
In a monorepo (googlefontdirectory-hg) only <license>/<family>/ is counted.
class: modern | sfd | vfb | sfd+vfb | binary-only | empty | no-repo | not-archived
already: which list of this effort already has the family (ledger bucket, reland, batch5)
"""
import json
import os
import re
import subprocess
import sys

GFA = "/home/fsanches/compartilhado/gfonts_agents/data/gfonts_library_sources.json"
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
HUB = "/home/fsanches/compartilhado/GoogleFonts"
RELAND = "/home/fsanches/compartilhado/sfd-reland/families.tsv"
GF = "/home/fsanches/compartilhado/google/fonts"
LEDGER = {"good": "GOOD_SHAPE_AFTER_REPO_MODERNIZATION.md", "ready": "PRS_READY_NOW.md",
          "pending": "PENDING_IMPROVEMENTS.md", "backlog": "FAMILIES_BACKLOG.md"}
BIN = (".ttf", ".otf", ".woff", ".woff2")
# repositories laid out <license>/<family>/ with many families in one tree
MONOREPOS = {"googlefonts/googlefontdirectory-hg", "google/fonts"}


def ledger():
    where = {}
    for bucket, f in LEDGER.items():
        text = open(os.path.join(HUB, f), encoding="utf-8").read()
        m = re.search(r"```ledger\n(.*?)```", text, re.S)
        for name in (m.group(1).split() if m else []):
            where[name] = "ledger:" + bucket
    return where


def reland():
    out = {}
    with open(RELAND, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            out[r["family"]] = "reland:" + r["repo"]
    return out


def files_at(mirror, commit):
    for rev in ([commit] if commit else []) + ["HEAD"]:
        r = subprocess.run(["git", "-C", mirror, "ls-tree", "-r", "--name-only", rev],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return rev, r.stdout.splitlines()
    return None, []


def classify(paths):
    low = [p.lower() for p in paths]
    n = {
        "sfd": sum(p.endswith(".sfd") or "/.sfdir/" in p or p.endswith(".sfdir") for p in low),
        "vfb": sum(p.endswith(".vfb") for p in low),
        "vfj": sum(p.endswith(".vfj") for p in low),
        "glyphs": sum(p.endswith(".glyphs") or ".glyphspackage/" in p for p in low),
        "ufo": len({p.split(".ufo/")[0] for p in low if ".ufo/" in p}),
        "designspace": sum(p.endswith(".designspace") for p in low),
        "bin": sum(p.endswith(BIN) for p in low),
    }
    if n["glyphs"] or n["ufo"] or n["designspace"]:
        cls = "modern"
    elif n["sfd"] and (n["vfb"] or n["vfj"]):
        cls = "sfd+vfb"
    elif n["sfd"]:
        cls = "sfd"
    elif n["vfb"] or n["vfj"]:
        cls = "vfb"
    elif n["bin"]:
        cls = "binary-only"
    else:
        cls = "empty"
    return cls, n


def shipped(gf_dir):
    """(files, n with FFTM, earliest FFTM build date) of the fonts google/fonts ships."""
    from datetime import datetime, timezone
    from fontTools.ttLib import TTFont
    d = os.path.join(GF, gf_dir)
    files = sorted(f for f in os.listdir(d) if f.endswith((".ttf", ".otf"))) if os.path.isdir(d) else []
    n, stamps = 0, []
    for f in files:
        t = TTFont(os.path.join(d, f), lazy=True)
        if "FFTM" in t:
            n += 1
            stamps.append(t["FFTM"].FFTimeStamp - 2082844800)
    label = "%d%s" % (len(files), "V" if any("[" in f for f in files) else "")
    when = datetime.fromtimestamp(min(stamps), timezone.utc).strftime("%Y-%m-%d") if stamps else "-"
    return label, str(n), when


def main():
    fams = json.load(open(GFA))["families"]
    items = fams.items() if isinstance(fams, dict) else [(f["family_name"], f) for f in fams]
    known = {**ledger(), **reland()}
    print("\t".join(["family", "gf_path", "status", "repo", "commit_used", "class", "n_sfd",
                     "n_vfb", "n_vfj", "n_glyphs", "n_ufo", "n_designspace", "n_binaries",
                     "already", "shipped", "fftm", "fftm_build"]))
    for _, v in sorted(items, key=lambda kv: kv[1]["path"]):
        if v.get("status") not in ("missing_config", "no_source"):
            continue
        gf_dir = os.path.dirname(v["path"])
        slug = gf_dir.split("/")[-1]
        url = (v.get("repository_url") or "").rstrip("/")
        m = re.match(r"https?://(?:www\.)?(?:github\.com|gitlab\.com)/([^/]+)/([^/]+?)(?:\.git)?$", url)
        already = known.get(slug, "")
        if not m:
            row = [v["family_name"], gf_dir, v["status"], url or "-", "-", "no-repo"] + ["0"] * 7
        else:
            mirror = os.path.join(ARC, m.group(1), m.group(2) + ".git")
            if not os.path.isdir(mirror):
                row = [v["family_name"], gf_dir, v["status"], url, "-", "not-archived"] + ["0"] * 7
            else:
                rev, paths = files_at(mirror, v.get("commit"))
                if "%s/%s" % m.groups() in MONOREPOS:
                    # a repository holding many families: only this family's directory
                    paths = [p for p in paths if p.startswith(gf_dir + "/")]
                cls, n = classify(paths)
                row = [v["family_name"], gf_dir, v["status"], "%s/%s" % m.groups(),
                       (rev or "-")[:12], cls] + [str(n[k]) for k in
                                                  ("sfd", "vfb", "vfj", "glyphs", "ufo",
                                                   "designspace", "bin")]
        print("\t".join(row + [already, *shipped(gf_dir)]))


if __name__ == "__main__":
    sys.exit(main())
