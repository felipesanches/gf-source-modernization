#!/usr/bin/env python3
"""Question answered: does tools/workarounds.py's weight_class behave exactly as before the
FEA writer was split out of it (the commit "workarounds: weight_class_fea writes a given
usWeightClass as FEA")?

Runs the version before that commit and the current one on every .glyphs given (and three
synthetic sources: no features, an OS/2 block without WeightClass, one with WeightClass 300),
each with no TTFWeight and TTFWeight 400, 300, 500 and 700, and asserts identical results.

Usage: check_weight_class_refactor.py /home/fsanches/compartilhado/sfd-reland-repos/*/sources/*.glyphs
Measured 2026-10-08: 243 real .glyphs + 3 synthetic, 1230 cases identical, 692 changed the text.
"""
import importlib.util
import itertools
import os
import subprocess
import sys
import tempfile

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    split = subprocess.run(["git", "-C", W, "log", "-1", "--format=%H", "--fixed-strings",
                            "--grep=workarounds: weight_class_fea writes a given usWeightClass"],
                           capture_output=True, text=True, check=True).stdout.strip()
    before = subprocess.run(["git", "-C", W, "show", split + "^:tools/workarounds.py"],
                            capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "workarounds_before.py")
        open(p, "w").write(before)
        old = module(p, "workarounds_before")
    new = module(os.path.join(W, "tools", "workarounds.py"), "workarounds_now")
    texts = [open(p, encoding="utf-8").read() for p in sys.argv[1:]]
    texts += ['{\n.formatVersion = 3;\nfamilyName = X;\n}\n',
              '{\n.formatVersion = 3;\nfeaturePrefixes = (\n{\ncode = "table OS/2 {\n    TypoAscender 800;\n'
              '} OS/2;";\nname = x;\n}\n);\n}\n',
              '{\n.formatVersion = 3;\nfeaturePrefixes = (\n{\ncode = "table OS/2 {\n    WeightClass 300;\n'
              '} OS/2;";\nname = x;\n}\n);\n}\n']
    n = changed = 0
    for t, w in itertools.product(texts, (None, 400, 300, 500, 700)):
        sfd = "" if w is None else "TTFWeight: %d\nStartChar: a\n" % w
        a, b = old.weight_class(t, sfd), new.weight_class(t, sfd)
        assert a == b, (w, a[1], b[1])
        n += 1
        changed += a[1] is not None
    print("%d real .glyphs + 3 synthetic; %d cases identical, %d of them changed the text"
          % (len(sys.argv) - 1, n, changed))


if __name__ == "__main__":
    main()
