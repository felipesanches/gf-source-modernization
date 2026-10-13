#!/usr/bin/env python3
"""Question answered: for each family the library census could not give a buildable source
(verdicts NO-SOURCES, NO-SOURCE-BLOCK, NOT-MIRRORED), does any source file exist in the
repository METADATA.pb records -- at the recorded commit or anywhere in its history?

upstream_info.md is not evidence for this: on 2026-10-13 eight of them said "legacy formats
only (.vfb/.sfd)" for families whose repository never held such a file. This reads the repo
archive (bare mirrors) instead. For the googlefontdirectory-hg monorepo only the family's own
directory counts.

A source file is one of: .glyphs .glyphspackage .ufo .designspace .sfd .sfdir .vfb .vfc .vfj
.fontra .babelfont .pfa .pfb .bdf .mf (.fea alone is no source); .ttx is reported separately
(a dump of a binary). Archives at the commit (.zip, .7z, ...) are listed, and a .zip's members
count as files at the commit.

  python3 screen.py <census tsv> <google/fonts clone> <rev> <repo archive> > screen.tsv

Columns: family, census verdict, repository_url, commit, archive (yes/no), shipped (number of
.ttf/.otf in google/fonts), sources_at_commit, sources_in_history, ttx_files, screen:
  BINARY-ONLY   no source file at the commit or in the history
  HAS-SOURCES   some source file somewhere (read before converting)
  NO-REPO       no source block, or the repository is not in the archive
"""
import collections
import os
import re
import subprocess
import sys

CENSUS, GF, REV, ARCHIVE = sys.argv[1:5]
SOURCE_EXT = re.compile(r"\.(glyphs|glyphspackage|ufo|designspace|sfd|sfdir|vfb|vfc|vfj|fontra|"
                        r"babelfont|pfa|pfb|bdf|mf)(/|$)", re.I)
MONOREPO = "googlefonts/googlefontdirectory-hg"


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       errors="replace")
    return r.stdout if r.returncode == 0 else None


def archive_path(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)/(.+?)(?:\.git)?/?$", url.strip())
    if not m:
        return None
    host, path = m.groups()
    parts = path.split("/")
    owner, repo = parts[0], parts[-1]
    for p in (os.path.join(ARCHIVE, owner, repo + ".git"),
              os.path.join(ARCHIVE, host, path + ".git"),
              os.path.join(ARCHIVE, "sr.ht-" + owner.lstrip("~"), repo + ".git")):
        if os.path.isdir(p):
            return p
    od = next((d for d in os.listdir(ARCHIVE) if d.lower() == owner.lower()), None)
    if od:
        rd = next((d for d in os.listdir(os.path.join(ARCHIVE, od))
                   if d.lower() == (repo + ".git").lower()), None)
        if rd:
            return os.path.join(ARCHIVE, od, rd)
    return None


_HISTORY = {}


def history(repo):
    """Every path any commit of the repository touched (read once per repository)."""
    if repo not in _HISTORY:
        out = git(repo, "log", "--all", "--format=", "--name-only") or ""
        _HISTORY[repo] = sorted(set(out.split("\n")) - {""})
    return _HISTORY[repo]


def kinds(paths):
    c = collections.Counter()
    for p in paths:
        m = SOURCE_EXT.search(p)
        if m:
            # count a .ufo directory once, not per file in it
            key = m.group(1).lower()
            c[(key, p[:m.end(1)] if m.group(2) == "/" else p)] += 1
    return ",".join("%s:%d" % (k, n) for k, n in sorted(
        collections.Counter(k for k, _ in c).items()))


ARCHIVE_EXT = re.compile(r"\.(zip|7z|rar|tar|tgz|tar\.gz|tar\.bz2|tar\.xz)$", re.I)


def archive_members(repo, rev, path):
    """Names inside a .zip in the repository (other archive kinds: just the archive name)."""
    if not path.lower().endswith(".zip"):
        return ["(%s)" % os.path.basename(path)]
    import io
    import zipfile
    blob = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (rev, path)],
                          capture_output=True).stdout
    try:
        return [path + "!" + n for n in zipfile.ZipFile(io.BytesIO(blob)).namelist()]
    except zipfile.BadZipFile:
        return ["(%s: unreadable)" % os.path.basename(path)]


def family_dir(fam):
    for lic in ("ofl", "apache", "ufl"):
        if git(GF, "cat-file", "-e", "%s:%s/%s/METADATA.pb" % (REV, lic, fam)) is not None:
            return "%s/%s" % (lic, fam)
    return None


def main():
    rows = [l.split("\t") for l in open(CENSUS).read().splitlines()[1:]]
    wanted = [r[0] for r in rows if len(r) > 2 and r[2] in
              ("NO-SOURCES", "NO-SOURCE-BLOCK", "NOT-MIRRORED")]
    verdict = {r[0]: r[2] for r in rows if len(r) > 2}
    print("\t".join(["family", "census", "repository_url", "commit", "archive", "shipped",
                     "sources_at_commit", "sources_in_history", "ttx_files", "screen", "archives"]))
    for fam in sorted(wanted):
        d = family_dir(fam)
        meta = git(GF, "show", "%s:%s/METADATA.pb" % (REV, d)) if d else ""
        url = (re.search(r'repository_url:\s*"([^"]*)"', meta or "") or [None, ""])[1]
        commit = (re.search(r'commit:\s*"([^"]*)"', meta or "") or [None, ""])[1]
        tree = git(GF, "ls-tree", "--name-only", "%s:%s" % (REV, d)) if d else ""
        shipped = sum(1 for n in (tree or "").split() if n.lower().endswith((".ttf", ".otf")))
        repo = archive_path(url) if url else None
        if not repo:
            print("\t".join([fam, verdict[fam], url, commit[:12], "no", str(shipped),
                             "", "", "", "NO-REPO"]))
            continue
        def in_scope(p):
            return MONOREPO not in url or p.startswith(fam + "/") or ("/%s/" % fam) in p
        at = git(repo, "ls-tree", "-r", "--name-only", commit) if commit else ""
        at_paths = [p for p in (at or "").split("\n") if p and in_scope(p)]
        hist_paths = [p for p in history(repo) if in_scope(p)]
        ttx = sum(1 for p in set(at_paths) | set(hist_paths) if p.lower().endswith(".ttx"))
        # sources can hide in an archive (Dongle: sources/Dongle.zip holds Dongle.glyphs)
        packed = [m for p in at_paths if ARCHIVE_EXT.search(p)
                  for m in archive_members(repo, commit, p)]
        s_at, s_hist = kinds(at_paths + packed), kinds(hist_paths)
        screen = "HAS-SOURCES" if (s_at or s_hist) else "BINARY-ONLY"
        print("\t".join([fam, verdict[fam], url, commit[:12], "yes", str(shipped), s_at,
                         s_hist, str(ttx), screen,
                         ";".join(p for p in at_paths if ARCHIVE_EXT.search(p))]))


main()
