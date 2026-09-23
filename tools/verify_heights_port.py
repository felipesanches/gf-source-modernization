#!/usr/bin/env python3
"""Question answered: does babelfont's Rust port of FontForge's height rule
(--fontforge-os2-defaults, filters/fontforge_standard_height.rs) produce exactly
what the Python oracle (tools/ff_heights_oracle.py) computes, on every real
source in families.tsv?

Two independent implementations of the same C code agreeing on 42 real fonts is
the evidence that the port is faithful; the oracle's agreement with the releases
is separate evidence that the rule is the right one.

Conversion only -- no compilation -- so it is cheap: each source is converted
with just --fontforge-os2-defaults, and the master's x-height and cap height are
read back out of the .glyphs.

Usage: gftools/venv/bin/python3 tools/verify_heights_port.py <babelfont binary>
Exit 1 on any disagreement between the two implementations.
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_heights_oracle as oracle  # noqa: E402

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def glyphs_heights(path):
    """x-height and cap height of the first master of a Glyphs 3 file."""
    text = open(path, encoding="utf-8").read()
    block = re.search(r"^metrics = \((.*?)^\);", text, re.S | re.M).group(1)
    types = re.findall(r"\{\n(?:filter = [^;]*;\n)?(?:name = [^;]*;|type = \"?([^\";]+)\"?;)", block)
    master = re.search(r"metricValues = \((.*?)\n\);", text, re.S).group(1)
    values = re.findall(r"\{\n?(?:over = -?[\d.]+;\n?)?(?:pos = (-?[\d.]+);)?\n?\}", master)
    got = {}
    for kind, value in zip(types, values):
        if kind in ("x-height", "cap height"):
            got[kind] = int(float(value)) if value else 0
    return got.get("x-height"), got.get("cap height")


def main():
    bf = sys.argv[1]
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(W, "families.tsv"))][1:]
    disagree = 0
    with tempfile.TemporaryDirectory() as tmp:
        for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
            path = f"{lic}/{fam}/{src}" if kind == "hg" else src
            data = subprocess.run(["git", "-C", f"{oracle.ARC}/{base}.git", "show", f"{commit}:{path}"],
                                  capture_output=True, check=True).stdout
            sfd = os.path.join(tmp, style + ".sfd")
            open(sfd, "wb").write(data)
            out = os.path.join(tmp, style + ".glyphs")
            subprocess.run([bf, sfd, out, "--fontforge-os2-defaults"], capture_output=True, check=True)
            rx, rc = glyphs_heights(out)
            text = data.decode("utf-8", "replace")
            s = oracle.Sfd(text)
            hdr = text.split("\nStartChar:", 1)[0]
            sx = re.search(r"^OS2XHeight: (-?\d+)", hdr, re.M)
            sc = re.search(r"^OS2CapHeight: (-?\d+)", hdr, re.M)
            ox = int(sx.group(1)) if sx and int(sx.group(1)) else oracle.exported(oracle.standard_height(s, oracle.XH))
            oc = int(sc.group(1)) if sc and int(sc.group(1)) else oracle.exported(oracle.standard_height(s, oracle.CAP))
            same = (rx, rc) == (ox, oc)
            disagree += not same
            print("%-26s rust %5s %5s   oracle %5s %5s   %s" % (style, rx, rc, ox, oc, "same" if same else "DISAGREE"))
    print()
    print("Rust port agrees with the oracle on %d of %d styles" % (len(rows) - disagree, len(rows)))
    return 1 if disagree else 0


if __name__ == "__main__":
    sys.exit(main())
