import json, subprocess, sys, os, itertools
W = sys.argv[1]; sfds = sys.argv[2:]
MODES = {
    "none": [],
    "os2": ["--fontforge-os2-defaults"],
    "ul": ["--fontforge-underline-position"],
    "hgcm+os2": ["--fontforge-height-glyph-count-mean", "--fontforge-os2-defaults"],
    "hgcm": ["--fontforge-height-glyph-count-mean"],
}
def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from flat(v, f"{p}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from flat(v, f"{p}[{i}]")
    else: yield p, json.dumps(o, sort_keys=True)
def run(rev, sfd, mode):
    out = os.path.join(W, "out", rev, os.path.basename(sfd) + "." + mode + ".babelfont")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([os.path.join(W, f"target-{rev}", "debug", "babelfont"), sfd, out] + MODES[mode],
                       capture_output=True, text=True)
    if r.returncode != 0: return ("ERR", r.stderr.strip().splitlines()[-1:] )
    with open(out) as f: return {k: v for k, v in flat(json.load(f)) if k != "/date"}  # write timestamp
def delta(a, b):
    if isinstance(a, tuple) or isinstance(b, tuple): return ("ERR", a if isinstance(a, tuple) else b)
    return sorted((k, a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k))
bad = 0; nonzero = {m: 0 for m in MODES if m != "none"}; basediff = []
for sfd in sfds:
    res = {rev: {m: run(rev, sfd, m) for m in MODES} for rev in ("4a293d4", "119f2be")}
    for m in MODES:
        if m == "none": continue
        d_pre = delta(res["4a293d4"]["none"], res["4a293d4"][m])
        d_post = delta(res["119f2be"]["none"], res["119f2be"][m])
        if d_pre and not (isinstance(d_pre, tuple)): nonzero[m] += 1
        if d_pre != d_post:
            bad += 1; print(f"FILTER-DELTA MISMATCH {os.path.basename(sfd)} {m}:\n  pre={d_pre}\n  post={d_post}")
    b = delta(res["4a293d4"]["none"], res["119f2be"]["none"])
    if b: basediff.append((os.path.basename(sfd), b if isinstance(b, tuple) else [k for k, _, _ in b][:8]))
print(f"{len(sfds)} SFDs x {len(MODES)-1} filter sets: {bad} filter-delta mismatch(es)")
print("files where the filter changed something (pre-port):", nonzero)
print(f"unfiltered pre-vs-post differences (upstream reader changes): {len(basediff)} file(s)")
for n, b in basediff: print("  ", n, b)
