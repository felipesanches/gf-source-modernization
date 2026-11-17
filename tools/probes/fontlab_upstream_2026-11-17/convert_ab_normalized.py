#!/usr/bin/env python3
"""Question: apart from the run's date and random master ids, do the builds of convert_ab.sh write the same .glyphs?
Usage: convert_ab_normalized.py <convert-ab dir> <label a> <label b>   (prints counts and the first differing lines)"""
import collections, difflib, glob, os, re, sys
d, a, b = sys.argv[1:4]
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
def norm(p):
    ids = {}
    out = []
    for l in open(p, encoding="utf-8"):
        if l.startswith("date = "):
            continue
        out.append(UUID.sub(lambda m: ids.setdefault(m.group(0).lower(), "ID%d" % len(ids)), l))
    return out
names = dict(l.split("\t")[:2] for l in open(os.path.join(d, "convert-ab.tsv")))
same = diff = missing = 0
kinds = collections.Counter()
for pa in sorted(glob.glob(os.path.join(d, "*.%s.glyphs" % a))):
    h = os.path.basename(pa).split(".")[0]
    pb = os.path.join(d, "%s.%s.glyphs" % (h, b))
    if not os.path.exists(pb):
        missing += 1; continue
    na, nb = norm(pa), norm(pb)
    if na == nb:
        same += 1; continue
    diff += 1
    for l in difflib.unified_diff(na, nb, n=0, lineterm=""):
        if l[:1] in "+-" and l[:3] not in ("+++", "---"):
            kinds[l[0] + " " + re.sub(r"[-0-9.]+", "N", l[1:].strip())[:60]] += 1
print("%s vs %s: same %d, different %d, only in %s %d" % (a, b, same, diff, a, missing))
for k, n in kinds.most_common(12):
    print("  %6d  %s" % (n, k))
