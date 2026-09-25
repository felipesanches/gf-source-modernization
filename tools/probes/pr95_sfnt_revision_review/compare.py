#!/usr/bin/env python3
"""Compare the two harness dumps; see README.md for what each line means."""
import json, re, sys

out = sys.argv[1]
def load(c):
    synth, corpus, tree = {}, [], None
    cur = None
    for line in open(f"{out}/dump-{c}.txt"):
        line = line.rstrip("\n")
        if line.startswith("TREE "): tree = line[5:]
        elif line.startswith("CORPUS "):
            corpus.append(re.sub(r" json=[0-9a-f]{16}", "", line))  # json embeds load time
        elif line.startswith("SYNTH "): cur = None
        elif line.startswith("=== "): cur = line[4:]; synth[cur] = []
        elif cur is not None: synth[cur].append(re.sub(r'"date":"[^"]*",', "", line))
    return tree, synth, corpus

def valid(l):
    v = l.split(":", 1)[1].strip()
    h = v[2:] if v.lower().startswith("0x") else v
    try: return int(h, 16) < 0x80000000
    except ValueError: return False

(ta, a, ca), (tb, b, cb) = load("b4dc853"), load("8042926")
print("trees:", ta, tb)
assert ta != tb, "both dumps came from the same build"
differ = [k for k in a if a[k] != b[k]]
print(f"synthetic headers: {len(a)}, differing: {len(differ)}")
unexplained = []
for k in differ:
    s = [l for l in json.loads(k) if l.startswith("sfntRevision")]
    if not (len(s) >= 2 and not valid(s[-1]) and any(valid(x) for x in s[:-1])):
        unexplained.append(k)
print(f"differing headers NOT of the form 'valid sfntRevision, then a later invalid one': {len(unexplained)}")
for name, d in (("b4dc853", a), ("8042926", b)):
    single = {k: v for k, v in d.items()
              if sum(l.startswith("sfntRevision") for l in json.loads(k)) <= 1
              and sum(l.startswith("Version") for l in json.loads(k)) <= 1}
    bad = [k for k, v in single.items()
           if any("same_version=false" in l or "emit_stable=false" in l or "error" in l for l in v)]
    print(f"{name}: headers with at most one Version and one sfntRevision line: {len(single)}, round-trip problems: {len(bad)}")
for name, d in (("b4dc853", a), ("8042926", b)):
    n = sum(any("same_version=false" in l for l in v) for v in d.values())
    print(f"{name}: all headers whose version changes over an SFD round trip: {n}")
print(f"corpus files: {len(ca)}, identical lines: {sum(x == y for x, y in zip(ca, cb))}, "
      f"load errors: {sum('load error' in x for x in cb)}")
