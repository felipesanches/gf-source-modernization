#!/usr/bin/env python3
"""Did FontForge register each GSUB lookup for EXACTLY the (script, language, feature)
triples the .sfd names -- no inheritance from the default language, no extra language
systems for aalt -- and write the lookups in the .sfd's order?

Question: the converted builds differ from the releases in two registration ways
(Varela: `liga` lookup 24, which the .sfd does not register for AZE/CRT/TRK, runs
there in our build; Poly-Italic / Varela: `aalt` runs under latn/ROM / latn/SRB, which
the .sfd does not name). If FontForge wrote precisely what the .sfd says, the release
is the .sfd's own statement and the difference is the converter's (feature-file
`language X;` includes the default language's lookups unless `exclude_dflt`; fea-rs
registers `aalt` for every `languagesystem`).

Signal read: the .sfd header's `Lookup: <type> <flags> <store> "<name>" {subtables}
[<feature> (<script> <langs...>) ...]` lines, GSUB ones (type < 256) in file order;
the release's GSUB LookupList (index i <-> i-th GSUB Lookup line, checked by type) and
its ScriptList/FeatureList. A blank script tag is FontForge's DFLT.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 sfd_vs_release_registration.py \
        <file.sfd> <release.ttf>
Prints, per lookup whose registration differs, both sets; then the verdict line
    ORDER: <n> lookups, types match in file order: True/False
    REGISTRATION: <n> lookups, identical: <k>
"""
import re
import sys

from fontTools.ttLib import TTFont

TYPES = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8}


def sfd_lookups(path):
    head = open(path, encoding="utf-8", errors="replace").read().split("\nBeginChars:")[0]
    out = []
    for m in re.finditer(r'^Lookup: (\d+) (\d+) (\d+) "([^"]*)"\s+\{.*?\} \[(.*)\]\s*$', head, re.M):
        typ = int(m.group(1))
        if typ >= 256:
            continue
        regs = set()
        for fm in re.finditer(r"'(.{4})' \((.*?)\)", m.group(5)):
            feat = fm.group(1)
            for sm in re.finditer(r"'(.{4})' <(.*?)>", fm.group(2)):
                script = sm.group(1).strip() or "DFLT"
                for lang in re.findall(r"'(.{4})'", sm.group(2)):
                    regs.add((script, lang.strip(), feat))
        out.append((m.group(4), typ, regs))
    return out


def release_regs(path):
    f = TTFont(path)
    g = f["GSUB"].table
    feats = g.FeatureList.FeatureRecord
    regs = [set() for _ in g.LookupList.Lookup]
    for sr in g.ScriptList.ScriptRecord:
        systems = []
        if sr.Script.DefaultLangSys is not None:
            systems.append(("dflt", sr.Script.DefaultLangSys))
        systems += [(lr.LangSysTag.strip(), lr.LangSys) for lr in sr.Script.LangSysRecord]
        for lang, ls in systems:
            for fi in ls.FeatureIndex:
                for li in feats[fi].Feature.LookupListIndex:
                    regs[li].add((sr.ScriptTag, lang, feats[fi].FeatureTag))
    types = [lk.LookupType for lk in g.LookupList.Lookup]
    return types, regs


def main():
    sfd, rel = sys.argv[1], sys.argv[2]
    sl = sfd_lookups(sfd)
    types, regs = release_regs(rel)
    order_ok = len(sl) == len(types) and all(t == s[1] for t, s in zip(types, sl))
    same = 0
    for i, (name, typ, want) in enumerate(sl):
        got = regs[i] if i < len(regs) else None
        if got == want:
            same += 1
            continue
        print("L%d %r\n   .sfd    %s\n   release %s" % (i, name, sorted(want), sorted(got or [])))
    print("ORDER: %d .sfd GSUB lookups, %d release lookups, types match in file order: %s"
          % (len(sl), len(types), order_ok))
    print("REGISTRATION: %d lookups, identical: %d" % (len(sl), same))


if __name__ == "__main__":
    main()
