#!/bin/sh
# Question answered: what have others said on the open PRs of felipesanches in a repository?
# Usage: sh comments.sh <owner/repo> <since ISO date> <out dir>
# Unauthenticated GitHub API (60 calls/hour): repository-wide issue and inline comments,
# then the reviews of each open PR by felipesanches. Writes JSON into <out dir>; prints a digest.
set -u
R=${1:?owner/repo}; S=${2:?since}; O=${3:?out dir}
mkdir -p "$O"; A=https://api.github.com/repos/$R
curl -s -o "$O/open.json" "$A/pulls?state=open&per_page=100"
curl -s -o "$O/icomments.json" "$A/issues/comments?since=${S}T00:00:00Z&per_page=100"
curl -s -o "$O/rcomments.json" "$A/pulls/comments?since=${S}T00:00:00Z&per_page=100"
R="$R" python3 -I - "$O" <<'PY'
import json, sys, os, subprocess
o = sys.argv[1]
ours = [p["number"] for p in json.load(open(os.path.join(o, "open.json"))) if p["user"]["login"] == "felipesanches"]
ev = []
for c in json.load(open(os.path.join(o, "icomments.json"))):
    ev.append((int(c["issue_url"].rsplit("/", 1)[1]), c["created_at"], c["user"]["login"], "comment", c["body"]))
for c in json.load(open(os.path.join(o, "rcomments.json"))):
    ev.append((int(c["pull_request_url"].rsplit("/", 1)[1]), c["created_at"], c["user"]["login"], "inline", c["body"]))
for n in ours:
    out = os.path.join(o, "reviews-%d.json" % n)
    subprocess.run(["curl", "-s", "-o", out, "https://api.github.com/repos/%s/pulls/%d/reviews" % (os.environ.get("R", ""), n)])
for n in sorted(ours):
    es = sorted(e for e in ev if e[0] == n and e[2] != "felipesanches")
    print("#%d: %d comment(s) by others" % (n, len(es)))
    for e in es:
        print("  %s %s %s: %s" % (e[1][:10], e[2], e[3], e[4].replace("\n", " ")[:300]))
PY
