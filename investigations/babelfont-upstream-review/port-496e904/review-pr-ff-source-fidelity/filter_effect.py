#!/usr/bin/env python3
"""Review harness (disposable): does each of the five filters change a real SFD's
conversion the same way before the port (a089e9a) as after it (24671e6)?

For every SFD in the list and every filter F, it runs the pre-port and the ported CLI
twice, `babelfont in.sfd out.babelfont` and `babelfont in.sfd out.babelfont --F`, and
computes the set of JSON leaf changes the filter causes (path, before, after). The
upstream reader changed between the two bases (da97d82 refactor, #85 metrics), so the
unfiltered outputs may differ; the filter's own delta should not.

Usage: filter_effect.py <pre-bin> <post-bin> <sfd-list> <outdir>
Prints one line per (file, filter): SAME/DIFF plus change counts; DIFF details in
<outdir>/diff-<n>-<filter>.txt.
"""
import json
import subprocess
import sys
from pathlib import Path

FILTERS = [
    "drop-alternate-unicodes",
    "reverse-path-direction",
    "keep-source-glyph-names",
    "keep-source-advances",
    "snap-component-transforms",
]


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, json.dumps(obj, sort_keys=True)


def convert(binary, sfd, out, flag):
    cmd = [binary, str(sfd), str(out)] + ([f"--{flag}"] if flag else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        return None, r.stderr[-500:]
    return dict(leaves(json.loads(Path(out).read_text()))), None


def delta(a, b):
    keys = set(a) | set(b)
    return {(k, a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}


def main():
    pre, post, lst, outdir = sys.argv[1:5]
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    files = [l.strip() for l in open(lst) if l.strip()]
    same = diff = err = 0
    for n, f in enumerate(files):
        base = {}
        for tag, binary in (("pre", pre), ("post", post)):
            base[tag], e = convert(binary, f, outdir / f"{tag}.babelfont", None)
            if e:
                print(f"ERR {n} {tag} nofilter {f}: {e!r}", flush=True)
        for flag in FILTERS:
            d = {}
            for tag, binary in (("pre", pre), ("post", post)):
                if base[tag] is None:
                    d[tag] = None
                    continue
                filtered, e = convert(binary, f, outdir / f"{tag}.babelfont", flag)
                if e:
                    print(f"ERR {n} {tag} {flag} {f}: {e!r}", flush=True)
                    d[tag] = None
                    continue
                d[tag] = delta(base[tag], filtered)
            if d["pre"] is None or d["post"] is None:
                err += 1
                status = "ERR" if (d["pre"] is None) != (d["post"] is None) else "BOTHERR"
            elif d["pre"] == d["post"]:
                same += 1
                status = "SAME"
            else:
                diff += 1
                status = "DIFF"
                with open(outdir / f"diff-{n}-{flag}.txt", "w") as fh:
                    fh.write(f"{f}\nonly pre:\n")
                    for x in sorted(d["pre"] - d["post"], key=str)[:200]:
                        fh.write(f"  {x}\n")
                    fh.write("only post:\n")
                    for x in sorted(d["post"] - d["pre"], key=str)[:200]:
                        fh.write(f"  {x}\n")
            npre = len(d["pre"]) if d["pre"] is not None else -1
            npost = len(d["post"]) if d["post"] is not None else -1
            print(f"{status} {n} {flag} pre={npre} post={npost} {f}", flush=True)
    print(f"TOTAL same={same} diff={diff} err={err}")


if __name__ == "__main__":
    main()
