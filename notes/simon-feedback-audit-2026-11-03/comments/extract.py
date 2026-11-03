#!/usr/bin/env python3
"""Every comment by simoncozens in the JSON fetch.sh downloads, oldest first, verbatim, with its URL.
Usage: python3 -I extract.py <scratch dir> > simon-<from>-to-<to>.txt"""
import glob, json, os, sys
os.chdir(sys.argv[1])
seen, out = set(), []
def add(f, repo):
    try:
        d = json.load(open(f))
    except Exception:
        return
    for c in d if isinstance(d, list) else []:
        if c.get("user", {}).get("login") != "simoncozens" or c["id"] in seen:
            continue
        seen.add(c["id"])
        out.append((c["created_at"][:10], c["html_url"], repo, c["body"].replace("\r", "")))
for f in sorted(glob.glob("bf-all-*.json")):
    add(f, "simoncozens/babelfont-rs")
for f in sorted(glob.glob("c-*.json")):
    add(f, f[2:-5])
for f in sorted(glob.glob("gfrust-*.json")):
    add(f, "simoncozens/gftools-rust")
add("glyphslib-rs.json", "simoncozens/glyphslib-rs")
for f in sorted(glob.glob("gfonts-10490-*.json")):
    add(f, "google/fonts")
for d, u, r, b in sorted(out):
    print("== %s %s %s\n%s\n" % (d, r, u, b))
