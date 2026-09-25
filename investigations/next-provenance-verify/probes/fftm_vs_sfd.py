#!/usr/bin/env python3
"""Independent re-check: does each release's FFTM sourceModified equal the .sfd
ModificationTime at the commit the pairing names, and at the commit the provenance
unit proposes instead?

Question answered: for Lohit-Bengali, Lohit-Tamil, Thabit and Thabit-Bold, print the
release's FFTM (FontForge build stamp, sourceCreated, sourceModified, in UTC) and, for
each candidate commit, the .sfd's CreationTime / ModificationTime / Version / Panose.
MATCH means ModificationTime == FFTM sourceModified.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 fftm_vs_sfd.py
"""
import datetime, re, subprocess
from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
GF = "/home/fsanches/compartilhado/google/fonts"
EPOCH = 2082844800
CASES = [
    ("ofl/lohitbengali/Lohit-Bengali.ttf", "pravins/lohit", "bengali/Lohit-Bengali.sfd",
     ["a403c9b", "0df83ad", "9d61e32", "e3b333b"]),
    ("ofl/lohittamil/Lohit-Tamil.ttf", "pravins/lohit", "tamil/Lohit-Tamil.sfd",
     ["a403c9b", "361b23b", "ffb56a5", "0df83ad"]),
    ("ofl/thabit/Thabit.ttf", "googlefonts/googlefontdirectory-hg", "ofl/thabit/src/Thabit.sfd", ["52f780b"]),
    ("ofl/thabit/Thabit-Bold.ttf", "googlefonts/googlefontdirectory-hg", "ofl/thabit/src/Thabit-Bold.sfd", ["52f780b"]),
]
u = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat()
for rel, repo, path, commits in CASES:
    f = TTFont(f"{GF}/{rel}")
    ff = f["FFTM"]
    sm = ff.sourceModified - EPOCH
    print(rel, "FFTM build", u(ff.FFTimeStamp - EPOCH), "sourceCreated", u(ff.sourceCreated - EPOCH),
          "sourceModified", sm, u(sm), "| name5", repr(f["name"].getDebugName(5)),
          "| panose", [getattr(f["OS/2"].panose, k) for k in ("bFamilyType", "bSerifStyle", "bWeight")])
    for c in commits:
        t = subprocess.run(["git", "-C", f"{ARC}/{repo}.git", "show", f"{c}:{path}"], capture_output=True).stdout.decode("utf-8", "replace")
        head = t.split("\nStartChar:", 1)[0]
        g = lambda k: (re.search(r"^%s: (.*)$" % k, head, re.M) or [None, "-"])[1]
        mt = g("ModificationTime")
        print("   %s %s Creation %s Modification %s Version %s Panose %s" % (
            "MATCH" if mt != "-" and int(mt) == sm else "     ", c, g("CreationTime"), mt, g("Version"), g("Panose")))
