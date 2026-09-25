#!/usr/bin/env python3
"""Question: does the release register each GSUB lookup for exactly the (feature,
script, language) triples the paired .sfd states -- i.e. did FontForge's exporter
write the .sfd's registrations verbatim, with no include-dflt inheritance and no
extra aalt registrations? (If so, any registration our build adds is a converter
or compiler artefact, not something the release took from elsewhere.)

Release GSUB lookup i is paired with the i-th GSUB Lookup: line of the .sfd (FontForge
writes lookups in file order); the lookup TYPE is checked for each pair, so a
mis-ordering shows up as a type mismatch rather than silently.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY sfd_registration_vs_release.py <file.sfd> <release.ttf>
"""
import re
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sfd_langsys_scan import parse  # noqa: E402


def main():
    sfd, rel = sys.argv[1], sys.argv[2]
    lookups = [l for l in parse(open(sfd, encoding="utf-8", errors="replace").read()) if l[0] < 256]
    g = TTFont(rel)["GSUB"].table
    rl = g.LookupList.Lookup
    print("sfd GSUB lookups %d, release lookups %d" % (len(lookups), len(rl)))
    type_ok = all(lookups[i][0] == rl[i].LookupType for i in range(min(len(lookups), len(rl))))
    print("types pair up in file order:", type_ok, [(lookups[i][0], rl[i].LookupType) for i in range(len(rl)) if lookups[i][0] != rl[i].LookupType][:5])
    rel_regs = {}
    for sr in g.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        systems += [(lr.LangSysTag.strip(), lr.LangSys) for lr in sr.Script.LangSysRecord]
        for lang, ls in systems:
            for fi in ls.FeatureIndex:
                fr = g.FeatureList.FeatureRecord[fi]
                for li in fr.Feature.LookupListIndex:
                    rel_regs.setdefault(li, set()).add((fr.FeatureTag, sr.ScriptTag.strip(), lang))
    ok = 0
    for i, (typ, name, regs) in enumerate(lookups):
        want = set(regs)
        got = rel_regs.get(i, set())
        if want == got:
            ok += 1
        else:
            print("  lookup %d %r: sfd-only %s release-only %s" % (i, name, sorted(want - got), sorted(got - want)))
    print("RESULT: %d/%d lookups registered exactly as the .sfd states" % (ok, len(lookups)))


if __name__ == "__main__":
    main()
