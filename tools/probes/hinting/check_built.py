#!/usr/bin/env python3
"""functional_gate's hinting check alone, over built fonts, beside predict.py's verdict.

Usage: check_built.py <prediction.tsv> <shipped.ttf> <built.ttf> [<shipped.ttf> <built.ttf>...]
Prints font, predicted verdict, gate verdict, MATCH or MISMATCH, and the gate's failures
(or, for a pass, its notes: what it accepted).
"""
import csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import functional_gate as fg

pred = {r["font"]: r["prediction"] for r in csv.DictReader(open(sys.argv[1]), delimiter="\t")}
args = sys.argv[2:]
bad = 0
for shipped, built in zip(args[::2], args[1::2]):
    A, B = fg.Font(shipped), fg.Font(built)
    _, _, ka, kb = fg.correspondence(A, B)
    c = fg.check_hinting(A, B, ka, kb, 3)
    name = os.path.basename(shipped)
    p = pred.get(name, "?")
    ok = p == c["status"]
    bad += not ok
    print("%-36s predicted %-4s gate %-4s %s  %s" % (name, p, c["status"], "MATCH" if ok else "MISMATCH",
                                                   " | ".join(f[:90] for f in (c["failures"] or c["notes"])[:3])))
sys.exit(1 if bad else 0)
