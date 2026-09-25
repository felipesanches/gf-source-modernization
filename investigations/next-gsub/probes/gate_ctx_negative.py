#!/usr/bin/env python3
"""Does the proposed GSUB arbitration still REFUSE a build whose contextual rules
behave differently -- and does the shared gate?

Question: table_gate_gsub_proposed.py accepts RibeyeMarrow-Regular's `frac` (FontForge's
nine format-3 ChainContext subtables vs fontc's one type-5 subtable) and Varela's `ordn`
(four format-3 subtables vs two with merged input coverage) because it compares the
rules per first glyph instead of the lookup type and packing. A looser comparison would
pass a real difference too. This takes an accepted build, breaks one contextual lookup
(the first contextual lookup of <feature tag>), and runs BOTH gates' GSUB arbitration
on (release, broken build):

  swap-first-two   swap the first two rules that share a rule set (or, with one rule
                   per subtable, the first two subtables)
  drop-last        remove the last rule (or the last subtable)
  retarget         point the first rule's nested lookup at another single-substitution
                   lookup that maps the same input glyph to a different glyph

Whether a mutation CHANGES BEHAVIOUR is measured, not assumed: the broken build and the
accepted build are shaped (uharfbuzz, the feature on, languages none/ro/tr/sr/de) over
every sequence the build's GSUB rules spell (via the cmap, table_gate_gsub_proposed.
_rule_sequences), all pairs of their characters, and numeric text for the contextual
features these fonts carry (every "a/b" and "a\u2044b" for a, b in 0..99; "1a", "1.a",
"2o", "2.o", "10a", "10.o": frac and ordn rules act on glyphs an earlier lookup made, so
only such text reaches them). A behaviour-changing mutation must
be REFUSED (an ACCEPT is UNSOUND); the control refused is a FALSE BLOCK; for a neutral one (e.g. swapping two rules whose
contexts are disjoint) either verdict is sound and a refusal is reported as
conservative. The unmodified build, re-saved, must be ACCEPTED (control).

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 gate_ctx_negative.py \
        <release.ttf> <accepted-build.ttf> <scratch-dir> <feature tag>
Prints per case: behaviour changed?, shared-gate verdict, proposed-gate verdict, and
whether each verdict is sound; last line counts UNSOUND verdicts per gate.
"""
import importlib.util
import itertools
import os
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table_gate_gsub_proposed as P  # noqa: E402  (builds the patched gate on import)

spec = importlib.util.spec_from_file_location(
    "table_gate_shared", "/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py")
SHARED = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SHARED)

TAG = sys.argv[4] if len(sys.argv) > 4 else None


def target(font):
    g = font["GSUB"].table
    allowed = {li for fr in g.FeatureList.FeatureRecord if fr.FeatureTag == TAG
               for li in fr.Feature.LookupListIndex}
    for i, lk in enumerate(g.LookupList.Lookup):
        if lk.LookupType in (5, 6) and i in allowed:
            return i, lk
    raise SystemExit("no contextual lookup in %s" % TAG)


def rule_lists(lk):
    """Every rule list (format 1/2 rule sets), in application order."""
    out = []
    for st in lk.SubTable:
        for attr, rattr in (("SubClassSet", "SubClassRule"), ("ChainSubClassSet", "ChainSubClassRule"),
                            ("SubRuleSet", "SubRule"), ("ChainSubRuleSet", "ChainSubRule")):
            for s in (getattr(st, attr, None) or []):
                if s is not None:
                    out.append(getattr(s, rattr))
    return out


def first_rule(lk):
    """(glyphs the first rule can start with, its SubstLookupRecord list)."""
    st = lk.SubTable[0]
    if getattr(st, "Format", None) == 3:
        cov = st.InputCoverage[0] if lk.LookupType == 6 else st.Coverage[0]
        return set(cov.glyphs), st.SubstLookupRecord
    for rl in rule_lists(lk):
        if rl:
            return set(st.Coverage.glyphs), rl[0].SubstLookupRecord
    return set(), None


def mutate(path, how, out):
    f = TTFont(path)
    i, lk = target(f)
    groups = [g for g in rule_lists(lk) if g]
    if how == "swap-first-two":
        g2 = next((g for g in groups if len(g) >= 2), None)
        if g2 is not None:
            g2[0], g2[1] = g2[1], g2[0]
        elif len(lk.SubTable) >= 2:
            lk.SubTable[0], lk.SubTable[1] = lk.SubTable[1], lk.SubTable[0]
        else:
            return None
    elif how == "drop-last":
        if groups and len(groups[-1]) >= 2:
            groups[-1].pop()
        elif len(lk.SubTable) >= 2:
            lk.SubTable.pop()
            lk.SubTableCount = len(lk.SubTable)
        else:
            return None
    elif how == "retarget":
        glyphs, recs = first_rule(lk)
        if not recs:
            return None
        lks = f["GSUB"].table.LookupList.Lookup
        cur = recs[0].LookupListIndex
        cur_map = {}
        for st in lks[cur].SubTable:
            cur_map.update(getattr(st, "mapping", None) or {})
        pick = None
        for j, other in enumerate(lks):
            if j in (cur, i) or other.LookupType != 1:
                continue
            m = {}
            for st in other.SubTable:
                m.update(st.mapping)
            if any(g in m and m[g] != cur_map.get(g) for g in glyphs):
                pick = j
                break
        if pick is None:
            return None
        recs[0].LookupListIndex = pick
    f.save(out)
    return out


def behaviour_changed(ref, mut):
    f = TTFont(ref)
    words = P._rule_sequences(f, f)
    chars = sorted({c for w in words for c in w})
    extra = {"%d%s%d" % (a, sep, b) for a in range(100) for b in range(100) for sep in "/\u2044"}
    extra |= {"1a", "1.a", "2o", "2.o", "10a", "10.o", "a1a"}
    words = sorted(set(words) | extra | {a + b for a, b in itertools.product(chars, repeat=2)})
    fa = hb.Font(hb.Face(hb.Blob.from_file_path(ref)))
    fb = hb.Font(hb.Face(hb.Blob.from_file_path(mut)))
    oa, ob = f.getGlyphOrder(), TTFont(mut).getGlyphOrder()
    for lang in (None, "ro", "tr", "sr", "de"):
        for w in words:
            res = []
            for font, order in ((fa, oa), (fb, ob)):
                buf = hb.Buffer()
                buf.add_str(w)
                buf.guess_segment_properties()
                if lang:
                    buf.language = lang
                hb.shape(font, buf, {TAG: True})
                res.append([order[x.codepoint] for x in buf.glyph_infos])
            if res[0] != res[1]:
                return "yes (%r: %s -> %s, lang %s)" % (w, res[0], res[1], lang)
    return "no (%d words x 5 languages identical)" % len(words)


def verdict(mod, release, build):
    keep, _ = mod.arbitrate_gsub_lookup_order(["GSUB.lookup_list probe"], release, build)
    return "REFUSE" if keep else "ACCEPT"


def main():
    rel, bld, scratch = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(scratch, exist_ok=True)
    ctrl = os.path.join(scratch, "control.ttf")
    TTFont(bld).save(ctrl)
    unsound = {"shared": 0, "proposed": 0}
    for case in ("control", "swap-first-two", "drop-last", "retarget"):
        path = ctrl if case == "control" else mutate(bld, case, os.path.join(scratch, case + ".ttf"))
        if path is None:
            print("%-15s not applicable to this lookup" % case)
            continue
        changed = "no (control)" if case == "control" else behaviour_changed(bld, path)
        line = ["%-15s behaviour changed: %s" % (case, changed)]
        for name, mod in (("shared", SHARED), ("proposed", P.tg)):
            v = verdict(mod, rel, path)
            if changed.startswith("yes"):
                ok = "sound" if v == "REFUSE" else "UNSOUND"
            elif case == "control":
                ok = "sound"
            else:
                ok = "sound" if v == "ACCEPT" else "conservative"
            if case == "control" and v == "REFUSE":
                ok = "FALSE BLOCK"
            unsound[name] += ok == "UNSOUND"
            line.append("%s gate %s (%s)" % (name, v, ok))
        print("; ".join(line))
    print("UNSOUND verdicts: shared %d, proposed %d" % (unsound["shared"], unsound["proposed"]))


if __name__ == "__main__":
    main()
