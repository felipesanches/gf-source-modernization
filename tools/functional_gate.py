#!/usr/bin/env python3
"""Question answered: does a font built from the modernised sources BEHAVE like the binary
Google Fonts ships?

Felipe's rule (2026-09-24): the commit METADATA.pb records must build fonts FUNCTIONALLY
equivalent to the release -- same cmap, shaping, positioning, metrics and line spacing,
names and rendering; not byte-identical. Defects of the release are reproduced, not fixed.
The table gate (sfd-batch5/tools/table_gate.py, diffenator3's `tables` section) is
structural and accepts whole classes of rows (OS/2.fs_selection, GPOS reorganisation,
GDEF, names are not gated), so it passed fonts that behave differently: Italiana kerning
pairs twice, Salsa without its GDEF, Lohit-Bengali with 284 Bengali words drawn
differently, wrong name ID 6, USE_TYPO_METRICS gained. This gate measures behaviour.

Checks (each PASS or FAIL; the verdict is PASS only if all seven pass):

  cmap          every Unicode cmap subtable (and (3,0) symbol, format 14 variation
                sequences): each codepoint maps in both fonts, to the same glyph NAME
                (post names; a font without names is matched by outline identity).
  shaping       HarfBuzz (uharfbuzz) shapes the same text in both fonts; glyphs compared
                by name (glyph ids mapped through the correspondence), each glyph's
                absolute ink position (pen + offset) and the final pen compared exactly.
                Corpora: every shared codepoint alone; every ordered pair of letters and
                layout-active characters within a script (kerning); pairs the release
                kerns with a combining mark between (IgnoreMarks); base+mark for every
                base and mark of a compatible script; base+mark+mark on representative
                bases; every sequence a GSUB/GPOS contextual or ligature rule describes;
                and the words of the diffenator word lists (the lists diffenator3 uses)
                for each script the font covers. Default features first; then each
                GSUB/GPOS feature either font has, toggled from its default, over the
                corpus that feature reaches; then every language system either font
                registers.
  rendering     diffenator3's glyph and word rendering diffs (read from its JSON, as
                investigations/next-provenance/probes/d3_render.py does), confirmed, plus
                an outline-geometry test of every reachable glyph. diffenator3 1.1.4 draws
                UNHINTED (skrifa DrawSettings::unhinted, ab_glyph_rasterizer): words at 16
                ppem, glyphs at 32 ppem, reported above 8 / 16 differing pixels after a
                gray fuzz of 8/255. Its count does not measure displacement: the fuzz is
                one font unit of edge movement at 1000 units/em, and a 1-unit lsb
                difference on identical points scores 179 px (Kristi 'a', lsb -1 vs -2;
                FreeType at the same size and fuzz: 0 px), while a 4-unit shift scores 17
                (NixieOne comma). So its reports count only when CONFIRMED: the glyph fails
                the geometry test, or HarfBuzz shapes the string differently (for a word:
                or one of its glyphs fails the geometry test). Unconfirmed reports are
                listed as notes.
                The geometry test renders every reachable glyph whose normalised outline
                (as drawn: TrueType rasterizers place the outline by the phantom point
                xMin - lsb, so a stale lsb moves ink) differs, with FreeType unhinted at
                1 px = 8 font units, and fails when more than 4 pixels differ in coverage
                by more than 64/255 (2 units of edge displacement). Calibrated on the 92
                landed styles (tools/probes/functional_gate/CALIBRATION.txt): every
                conversion-made outline difference (point structure, 1-unit rounding,
                start point) scores 0 px; one point moved 60 units scores 40 px, where
                diffenator3's glyph test gives 7 of the 16 it needs. It covers unencoded
                glyphs (alternates, ligatures, small caps), which diffenator3 never draws.
                Hinting is reported apart (release vs build fpgm/prep/cvt, glyph programs,
                gasp) and does not enter the verdict: rendering is compared unhinted, so
                hinting-only effects (small sizes under a TrueType interpreter) are not
                measured.
  names         Windows name records 1, 2, 4, 6 equal, and the typographic names 16, 17,
                21, 22 as an application reads them (16 falls back to 1, 17 to 2, 21 to
                16, 22 to 17), for every language the release carries; usWeightClass and
                usWidthClass equal. Every other record is reported, not failed.
  line_spacing  the ascender / descender / line gap each platform uses: hhea (CoreText);
                OS/2 typo when USE_TYPO_METRICS else usWin + GDI's external leading
                (DirectWrite, GDI); OS/2 typo when USE_TYPO_METRICS else hhea (FreeType
                engines: Chrome/Skia, Firefox). Plus the raw hhea / typo / win fields,
                fsSelection (every bit but 7, which counts through its effect above),
                head.macStyle bold/italic, unitsPerEm, underline and strikeout metrics,
                and the x-height / cap height a layout engine reads (OS/2 v2+ sxHeight /
                sCapHeight, else the 'x' / 'H' outline top). OS/2 version, caret and
                other head/hhea/post values are reported.
  advances      every hmtx advance of every glyph either font can reach, compared by
                correspondence and never hidden; vhea/vmtx if either font has them;
                post.isFixedPitch. A reachable glyph missing from either font fails.
                Left side bearings are reported here; where one moves ink (a TrueType
                rasterizer draws the outline shifted by lsb - xMin) the rendering check
                measures it.
  gdef          GDEF presence, and each reachable glyph's class as HarfBuzz uses it (the
                GDEF class, or without a GDEF the class HarfBuzz synthesises: a
                nonspacing mark's codepoint is a mark, anything else a base). A class
                difference fails when a mark is involved (zero-width marks, IgnoreMarks,
                attachment) or when some lookup's flags filter the other class (1 under
                IgnoreBaseGlyphs, 2 under IgnoreLigatures). Mark attachment classes and
                mark glyph sets fail only when a lookup uses them.

Run (Python: /home/fsanches/compartilhado/gftools/venv/bin/python3):
    functional_gate.py <shipped.ttf> <built.ttf> [--style NAME] [--d3-json FILE]
                       [--json OUT.json] [--examples N] [--wordlists DIR] [--workdir DIR]
    functional_gate.py --fetch-wordlists       (once: the pinned diffenator word lists)
--d3-json reuses a diffenator3 JSON of the same pair (land.py's table gate writes one);
without it diffenator3 is run here. Prints a short human summary; --json writes the
machine-readable verdict. Exit status 0 PASS, 1 FAIL, 2 could not run.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import unicodedata2 as unicodedata
except ImportError:          # pragma: no cover
    import unicodedata

import freetype
import uharfbuzz as hb
from fontTools import subset
from fontTools import unicodedata as ftud
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otBase

D3 = "/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3"
SCRATCH = os.environ.get("FG_SCRATCH", "/home/fsanches/compartilhado/sfd-reland-scratch/functional-gate")
# The word lists diffenator3 1.1.4 embeds come from googlefonts/fontheight
# static-lang-word-lists/data/diffenator (fetched from `main` when diffenator3 is built);
# this gate pins one commit of them. --fetch-wordlists recreates the directory.
WORDLISTS_REPO = "https://github.com/googlefonts/fontheight"
WORDLISTS_COMMIT = "b23cef0f8712c218173893cd8934ba44ba3cd760"
WORDLISTS_SUBDIR = "static-lang-word-lists/data/diffenator"
WORDLISTS = os.environ.get("FG_WORDLISTS", os.path.join(SCRATCH, "fontheight", WORDLISTS_SUBDIR))

# diffenator3 1.1.4 diffenator3-lib/src/render/mod.rs
D3_WORDS_PPEM, D3_GLYPHS_PPEM = 16, 32
D3_WORDS_THRESHOLD, D3_GLYPHS_THRESHOLD, D3_GRAY_FUZZ = 8, 16, 8
# the outline-geometry test (calibrated in tools/probes/functional_gate/CALIBRATION.txt:
# every conversion-made outline difference in the 92 landed styles scores 0 px)
GEOMETRY_UNITS_PER_PX, GEOMETRY_FUZZ, GEOMETRY_THRESHOLD = 8, 64, 4

CORE_NAMES = (1, 2, 4, 6)
TYPO_NAMES = {16: 1, 17: 2, 21: 16, 22: 17}          # id -> the id it falls back to
# Features HarfBuzz applies without being asked (horizontal text, all shapers); a
# toggle turns these OFF and every other feature ON.
DEFAULT_ON = set("""abvf abvm abvs akhn blwf blwm blws calt ccmp cfar cjct clig curs dist
fin2 fin3 fina half haln init isol kern liga ljmo locl ltra ltrm mark med2 medi mkmk mset
nukt pref pres pstf psts rclt rkrf rlig rphf rtla rtlm rvrn stch tjmo vatu vjmo""".split())

PAIRS_CAP = 3_000_000       # ordered pairs shaped under default features
FEATURE_PAIRS_CAP = 250_000  # ordered pairs per toggled feature / language system
FEATURE_WORDS = 3000        # words per script per toggled feature / language system
RULE_EXPANSION_CAP = 400    # sequences per contextual/ligature rule
MARK_PAIR_BASES = 4         # representative bases for base+mark+mark, per script
MARKS_FOR_STACKS = 60       # marks per script used in base+mark+mark


# ---------------------------------------------------------------------------------
# fonts and glyph correspondence
# ---------------------------------------------------------------------------------
class Font:
    def __init__(self, path):
        self.path = path
        self.tt = TTFont(path)
        self.order = self.tt.getGlyphOrder()
        self.gid = {n: i for i, n in enumerate(self.order)}
        self.cmap = self.tt.getBestCmap() or {}
        self.rev = {}
        for cp, n in sorted(self.cmap.items()):
            self.rev.setdefault(n, cp)
        post = self.tt["post"].formatType if "post" in self.tt else 3.0
        self.has_names = post in (1.0, 2.0)
        self.upem = self.tt["head"].unitsPerEm
        self._reach = None
        self._outlines = {}

    def unicode_subtables(self):
        out = {}
        for st in self.tt["cmap"].tables:
            if st.isUnicode() or (st.platformID == 3 and st.platEncID in (0, 1, 10)):
                if st.format == 14:
                    continue
                for cp, n in st.cmap.items():
                    out.setdefault(cp, n)
        return out

    def reachable(self):
        """Glyphs a text engine can reach: the Unicode cmap, closed over GSUB (all
        features, scripts, languages) and composite components, plus .notdef."""
        if self._reach is None:
            tt = TTFont(self.path)
            opts = subset.Options()
            opts.layout_features = ["*"]
            opts.layout_scripts = ["*"]
            opts.notdef_glyph = True
            opts.notdef_outline = True
            s = subset.Subsetter(opts)
            s.populate(unicodes=set(self.unicode_subtables()))
            s._closure_glyphs(tt)
            self._reach = set(s.glyphs_retained)
        return self._reach

    def outline(self, name):
        """Normalised outline AS DRAWN: composites flattened, a FontForge closing
        duplicate and implied on-curve points (the exact midpoint of two off-curves)
        dropped, each contour rotated to a canonical start; as a sorted tuple of
        contours. TrueType rasterizers (FreeType, skrifa, CoreText) place the outline by
        the phantom point pp1 = xMin - lsb, so a release whose hmtx lsb is not its glyf
        xMin draws the outline shifted by lsb - xMin (NixieOne's comma: lsb 75, xMin 71,
        drawn 4 units right); that shift is applied here. Two glyphs with equal
        signatures draw the same ink whatever their point bookkeeping."""
        if name in self._outlines:
            return self._outlines[name]
        sig = ()
        if "glyf" in self.tt:
            g = self.tt["glyf"][name]
            if g.numberOfContours:
                coords, ends, flags = g.getCoordinates(self.tt["glyf"])
                dx = self.tt["hmtx"][name][1] - g.xMin
                contours, s = [], 0
                for e in ends:
                    pts = [(round(x) + dx, round(y), f & 1) for (x, y), f in
                           zip(coords[s:e + 1], flags[s:e + 1])]
                    s = e + 1
                    contours.append(canonical_contour(pts))
                sig = tuple(sorted(contours))
        elif "CFF " in self.tt:
            from fontTools.pens.recordingPen import DecomposingRecordingPen
            gs = self.tt.getGlyphSet()
            pen = DecomposingRecordingPen(gs)
            gs[name].draw(pen)
            sig = tuple((op, tuple(tuple(round(v) for v in pt) for pt in args)) for op, args in pen.value)
        self._outlines[name] = sig
        return sig


def canonical_contour(pts):
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    n = len(pts)
    keep = []
    for i, p in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        if p[2] and not a[2] and not b[2] and n > 2 and \
                2 * p[0] == a[0] + b[0] and 2 * p[1] == a[1] + b[1]:
            continue
        keep.append(p)
    if not keep:
        return ()
    best = min(tuple(keep[k:] + keep[:k]) for k in range(len(keep)))
    return best


def correspondence(A, B):
    """key_a[gid], key_b[gid]: a common key for glyphs that are the same glyph.

    Glyph names when both fonts carry them (post 1/2): identical names correspond. What
    is left pairs by codepoint (a glyph both cmaps assign to the same codepoint), then
    by outline identity (a unique normalised outline + advance). A glyph with no
    counterpart keys as "<release name>" or "+<build name>"."""
    ka, kb = {}, {}
    if A.has_names and B.has_names:
        for n in A.order:
            if n in B.gid:
                ka[n] = kb[n] = n
    left_a = [n for n in A.order if n not in ka]
    left_b = set(n for n in B.order if n not in kb)
    for cp, na in sorted(A.cmap.items()):
        nb = B.cmap.get(cp)
        if na in ka or nb is None or nb not in left_b:
            continue
        ka[na] = kb[nb] = na
        left_b.discard(nb)
    left_a = [n for n in A.order if n not in ka]

    def sig(F, n):
        return (F.outline(n), F.tt["hmtx"][n][0])
    by_sig_b = {}
    for n in left_b:
        by_sig_b.setdefault(sig(B, n), []).append(n)
    by_sig_a = {}
    for n in left_a:
        by_sig_a.setdefault(sig(A, n), []).append(n)
    for s, names_a in by_sig_a.items():
        names_b = by_sig_b.get(s, [])
        if len(names_a) == 1 and len(names_b) == 1 and s[0]:
            ka[names_a[0]] = kb[names_b[0]] = names_a[0]
    for n in A.order:
        ka.setdefault(n, n)
    for n in B.order:
        kb.setdefault(n, "+" + n)
    return [ka[n] for n in A.order], [kb[n] for n in B.order], ka, kb


# ---------------------------------------------------------------------------------
# layout traversal helpers
# ---------------------------------------------------------------------------------
def lookups_of(tt, tag):
    if tag not in tt or not tt[tag].table.LookupList:
        return []
    return tt[tag].table.LookupList.Lookup


def real_subtables(lk):
    """(lookup type, subtables) with Extension lookups (GSUB 7, GPOS 9) unwrapped."""
    sts = list(lk.SubTable)
    typ = lk.LookupType
    if sts and hasattr(sts[0], "ExtSubTable"):
        typ = sts[0].ExtensionLookupType
        sts = [s.ExtSubTable for s in sts]
    return typ, sts


def walk_glyphs(obj, glyphset, out, nested, seen=None):
    """Every glyph name an otTables object mentions (coverage, classes, mappings,
    ligature components, pair second glyphs, rule sequences) into `out`; nested lookup
    indices into `nested`."""
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return
    seen.add(id(obj))
    if isinstance(obj, str):
        if obj in glyphset:
            out.add(obj)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk_glyphs(k, glyphset, out, nested, seen)
            walk_glyphs(v, glyphset, out, nested, seen)
        return
    if isinstance(obj, (list, tuple, set)):
        for v in obj:
            walk_glyphs(v, glyphset, out, nested, seen)
        return
    if isinstance(obj, otBase.BaseTable):
        if type(obj).__name__ in ("SubstLookupRecord", "PosLookupRecord"):
            nested.add(obj.LookupListIndex)
        for k, v in vars(obj).items():
            if k.startswith("_") or k in ("Format", "LookupType", "ExtensionLookupType"):
                continue
            walk_glyphs(v, glyphset, out, nested, seen)


def feature_map(tt, tag):
    """{feature tag: set of lookup indices} over every language system, and
    {(script, lang): set of lookup indices} (lang 'dflt' for the default)."""
    feats, systems = {}, {}
    if tag not in tt or not tt[tag].table.FeatureList:
        return feats, systems
    t = tt[tag].table
    fl = t.FeatureList.FeatureRecord
    for fr in fl:
        feats.setdefault(str(fr.FeatureTag), set()).update(fr.Feature.LookupListIndex)
    for sr in (t.ScriptList.ScriptRecord if t.ScriptList else []):
        langs = [("dflt", sr.Script.DefaultLangSys)] if sr.Script.DefaultLangSys else []
        langs += [(str(lr.LangSysTag).strip(), lr.LangSys) for lr in sr.Script.LangSysRecord]
        for lang, ls in langs:
            idx = set()
            for fi in ls.FeatureIndex:
                idx.update(fl[fi].Feature.LookupListIndex)
            if ls.ReqFeatureIndex != 0xFFFF and ls.ReqFeatureIndex < len(fl):
                idx.update(fl[ls.ReqFeatureIndex].Feature.LookupListIndex)
            systems[(str(sr.ScriptTag), lang)] = idx     # uharfbuzz takes str, not Tag
    return feats, systems


def lookup_closure(tt, tag, indices):
    """Glyphs mentioned by these lookups and every lookup they call."""
    lks = lookups_of(tt, tag)
    glyphset = set(tt.getGlyphOrder())
    todo, done, glyphs = list(indices), set(), set()
    while todo:
        i = todo.pop()
        if i in done or i >= len(lks):
            continue
        done.add(i)
        nested = set()
        _, sts = real_subtables(lks[i])
        walk_glyphs(sts, glyphset, glyphs, nested)
        todo.extend(nested - done)
    return glyphs, done


def rule_sequences(tt, tag, indices=None):
    """Sequences of glyph-name alternatives a ligature or contextual rule describes:
    [[names at position 0], [names at position 1], ...]."""
    seqs = []
    lks = lookups_of(tt, tag)
    for li, lk in enumerate(lks):
        if indices is not None and li not in indices:
            continue
        typ, sts = real_subtables(lk)
        for st in sts:
            fmt = getattr(st, "Format", None)
            if tag == "GSUB" and typ == 4:
                for a, ligs in st.ligatures.items():
                    for lg in ligs:
                        seqs.append([[a]] + [[c] for c in lg.Component])
                continue
            ctx = (tag == "GSUB" and typ in (5, 6)) or (tag == "GPOS" and typ in (7, 8))
            if not ctx:
                continue
            if fmt == 3:
                pos = []
                for attr in ("BacktrackCoverage", "InputCoverage", "LookAheadCoverage", "Coverage"):
                    cs = getattr(st, attr, None)
                    if cs is None:
                        continue
                    cs = cs if isinstance(cs, list) else [cs]
                    glist = [list(c.glyphs) for c in cs]
                    if attr == "BacktrackCoverage":
                        glist = glist[::-1]
                    pos += glist
                seqs.append(pos)
            elif fmt == 1:
                cov = list(st.Coverage.glyphs)
                for attr in ("ChainSubRuleSet", "SubRuleSet", "ChainPosRuleSet", "PosRuleSet"):
                    for gi, rs in enumerate(getattr(st, attr, None) or []):
                        if rs is None or gi >= len(cov):
                            continue
                        rules = (getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None)
                                 or getattr(rs, "ChainPosRule", None) or getattr(rs, "PosRule", None) or [])
                        for r in rules:
                            seqs.append([[g] for g in reversed(getattr(r, "Backtrack", None) or [])] +
                                        [[cov[gi]]] + [[g] for g in r.Input] +
                                        [[g] for g in getattr(r, "LookAhead", None) or []])
            elif fmt == 2:
                cov = list(st.Coverage.glyphs)
                bc = getattr(st, "BacktrackClassDef", None)
                ic = getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None)
                lc = getattr(st, "LookAheadClassDef", None)

                def members(cd, c, restrict=None, glyphs=tt.getGlyphOrder()):
                    if cd is None:
                        return []
                    if c == 0:
                        m = [g for g in glyphs if g not in cd.classDefs]
                    else:
                        m = [g for g, k in cd.classDefs.items() if k == c]
                    return [g for g in m if restrict is None or g in restrict]
                for attr in ("ChainSubClassSet", "SubClassSet", "ChainPosClassSet", "PosClassSet"):
                    for ci, cs in enumerate(getattr(st, attr, None) or []):
                        if cs is None:
                            continue
                        first = members(ic, ci, set(cov)) if ic is not None else cov
                        rules = (getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None)
                                 or getattr(cs, "ChainPosClassRule", None) or getattr(cs, "PosClassRule", None) or [])
                        for r in rules:
                            inp = list(getattr(r, "Input", None) or getattr(r, "Class", None) or [])
                            seqs.append([members(bc, c) for c in reversed(getattr(r, "Backtrack", None) or [])] +
                                        [first] + [members(ic, c) for c in inp] +
                                        [members(lc, c) for c in getattr(r, "LookAhead", None) or []])
    return seqs


def expand(seqs, rev, cap=RULE_EXPANSION_CAP):
    out = set()
    for seq in seqs:
        opts = [[chr(rev[g]) for g in pos if g in rev] for pos in seq]
        if not opts or any(not o for o in opts):
            continue
        for n, combo in enumerate(itertools.product(*opts)):
            if n >= cap:
                break
            out.add("".join(combo))
    return out


def markbase_bases(tt):
    out = set()
    for lk in lookups_of(tt, "GPOS"):
        typ, sts = real_subtables(lk)
        if typ in (4, 5):
            for st in sts:
                cov = getattr(st, "BaseCoverage", None) or getattr(st, "LigatureCoverage", None)
                if cov is not None:
                    out.update(cov.glyphs)
    return out


def kern_table_glyphs(tt):
    out = set()
    if "kern" in tt:
        for st in tt["kern"].kernTables:
            for (l, r) in getattr(st, "kernTable", {}) or {}:
                out.update((l, r))
    return out


def script_of(cp):
    try:
        return ftud.script(chr(cp))
    except Exception:
        return "Zzzz"


def category(cp):
    return unicodedata.category(chr(cp))


# ---------------------------------------------------------------------------------
# check helpers
# ---------------------------------------------------------------------------------
def result(status, summary, failures=(), notes=(), **data):
    out = {"status": status, "summary": summary, "failures": list(failures), "notes": list(notes)}
    if data:
        out["data"] = data
    return out


def u(cp):
    return "U+%04X" % cp


# 1 ------------------------------------------------------------------ cmap
def check_cmap(A, B, ka, kb):
    fails, notes = [], []
    ua, ub = A.unicode_subtables(), B.unicode_subtables()
    lost = sorted(set(ua) - set(ub))
    gained = sorted(set(ub) - set(ua))
    if lost:
        fails.append("build loses %d codepoint(s): %s" % (len(lost), " ".join(u(c) for c in lost[:20])))
    if gained:
        fails.append("build gains %d codepoint(s): %s" % (len(gained), " ".join(u(c) for c in gained[:20])))
    renamed, other = [], []
    for cp in sorted(set(ua) & set(ub)):
        na, nb = ua[cp], ub[cp]
        if A.has_names and B.has_names:
            if na != nb:
                same = A.outline(na) == B.outline(nb) and A.tt["hmtx"][na][0] == B.tt["hmtx"][nb][0]
                (renamed if same else other).append("%s %s/%s" % (u(cp), na, nb))
        elif ka[na] != kb[nb]:
            other.append("%s %s/%s" % (u(cp), na, nb))
    if renamed:
        fails.append("%d codepoint(s) map to a glyph of another name (same outline and advance): %s"
                     % (len(renamed), "; ".join(renamed[:10])))
    if other:
        fails.append("%d codepoint(s) map to a different glyph: %s" % (len(other), "; ".join(other[:10])))

    def subtables(F):
        return {(st.platformID, st.platEncID): st for st in F.tt["cmap"].tables}
    sa, sb = subtables(A), subtables(B)
    for key in ((3, 0),):
        if key in sa or key in sb:
            ca = dict(sa[key].cmap) if key in sa else {}
            cb = dict(sb[key].cmap) if key in sb else {}
            if ca != cb:
                fails.append("cmap (3,0) symbol subtable differs (%d vs %d entries)" % (len(ca), len(cb)))
    uvs_a = {k: v for st in A.tt["cmap"].tables if st.format == 14 for k, v in st.uvsDict.items()}
    uvs_b = {k: v for st in B.tt["cmap"].tables if st.format == 14 for k, v in st.uvsDict.items()}
    if uvs_a != uvs_b:
        fails.append("format 14 variation sequences differ")
    mac_a = sorted(k for k in sa if k[0] == 1)
    mac_b = sorted(k for k in sb if k[0] == 1)
    if mac_a != mac_b:
        notes.append("Macintosh cmap subtables %s in the release, %s in the build (read only by "
                     "pre-Unicode Mac software)" % (mac_a or "none", mac_b or "none"))
    return result("FAIL" if fails else "PASS",
                  "%d codepoints, %s" % (len(ua), "exact" if not fails else "%d problem(s)" % len(fails)),
                  fails, notes)


# 2 ------------------------------------------------------------------ shaping
class Shaper:
    def __init__(self, F, keys):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(F.path)))
        self.buf = hb.Buffer()
        self.keys = keys

    def run(self, text, features=None, script=None, lang=None):
        b = self.buf
        b.clear_contents()
        b.add_str(text)
        b.guess_segment_properties()
        if script and script != "DFLT":
            b.set_script_from_ot_tag(script)
        if lang and lang != "dflt":
            b.set_language_from_ot_tag(lang)
        else:
            # not the process locale (HarfBuzz's default): no language system at all
            b.language = "und"
        hb.shape(self.font, b, features or {})
        keys = self.keys
        out, x, y = [], 0, 0
        for i, p in zip(b.glyph_infos, b.glyph_positions):
            out.append((keys[i.codepoint], x + p.x_offset, y + p.y_offset))
            x += p.x_advance
            y += p.y_advance
        out.append(("END", x, y))
        return out


def fmt_run(run):
    return " ".join("%s@%d,%d" % r for r in run)


def load_wordlists(path, scripts, shared):
    """{list name: [words]} for each diffenator list whose script the font covers,
    keeping the words every character of which both fonts map."""
    out = {}
    if not os.path.isdir(path):
        return None
    for fn in sorted(os.listdir(path)):
        if not fn.endswith(".toml"):
            continue
        meta = open(os.path.join(path, fn), encoding="utf-8").read()
        sc = None
        for line in meta.splitlines():
            if line.strip().startswith("script"):
                sc = line.split("=", 1)[1].strip().strip('"')
        if sc not in scripts:
            continue
        txt = os.path.join(path, fn[:-5] + ".txt")
        words = set()
        with open(txt, encoding="utf-8") as fh:
            for w in fh:
                w = w.strip()
                if w and all(ord(c) in shared for c in w):
                    words.add(w)
        out[fn[:-5]] = sorted(words)
    return out


def wordlists_digest(path):
    h = hashlib.sha256()
    for fn in sorted(os.listdir(path)):
        h.update(fn.encode())
        with open(os.path.join(path, fn), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def check_shaping(A, B, key_a, key_b, examples, wordlists_dir, extra_words=()):
    SA, SB = Shaper(A, key_a), Shaper(B, key_b)
    shared = set(A.cmap) & set(B.cmap)
    rev = {}
    for cp in sorted(shared):
        rev.setdefault(A.cmap[cp], cp)
        rev.setdefault(B.cmap[cp], cp)
    cps = sorted(shared)
    cat = {cp: category(cp) for cp in cps}
    scr = {cp: script_of(cp) for cp in cps}

    # layout-active characters: their glyph appears in some lookup (or the legacy kern
    # table) of either font; a pair of inactive characters shapes as its two singles
    active_glyphs = set()
    for F in (A, B):
        for tag in ("GSUB", "GPOS"):
            g, _ = lookup_closure(F.tt, tag, range(len(lookups_of(F.tt, tag))))
            active_glyphs |= g
        active_glyphs |= kern_table_glyphs(F.tt)
    active = {cp for cp in cps if A.cmap[cp] in active_glyphs or B.cmap[cp] in active_glyphs}

    letters_by_script = {}
    for cp in cps:
        if cat[cp][0] in "LN" and scr[cp] not in ("Zyyy", "Zinh", "Zzzz"):
            letters_by_script.setdefault(scr[cp], []).append(cp)
    common = [cp for cp in cps if scr[cp] in ("Zyyy", "Zinh", "Zzzz") and cat[cp][0] != "M"
              and cat[cp] not in ("Cc", "Cf", "Zl", "Zp")]
    common_letters = [cp for cp in common if cat[cp][0] in "LN" or cp in active]
    marks = [cp for cp in cps if cat[cp] in ("Mn", "Mc", "Me")]

    corpora = {}
    corpora["singles"] = [chr(c) for c in cps]
    pairs = set()
    groups = list(letters_by_script.values()) or [[cp for cp in cps if cat[cp][0] != "M"]]
    for grp in groups:
        uni = sorted(set(grp) | set(common_letters))
        for a in uni:
            for b in uni:
                pairs.add(chr(a) + chr(b))
    notes = []
    if len(pairs) > PAIRS_CAP:
        # keep every pair touching a layout-active character; drop inactive x inactive,
        # which shape as the concatenation of two singles
        pairs = {p for p in pairs if ord(p[0]) in active or ord(p[1]) in active}
        notes.append("pairs: %d characters; inactive x inactive pairs skipped (they shape as two singles)"
                     % len(set(itertools.chain(*groups)) | set(common_letters)))
    corpora["pairs"] = sorted(pairs)

    def compatible(base, mark):
        ms = scr[mark]
        if ms in ("Zinh", "Zyyy"):
            return True
        try:
            ext = ftud.script_extension(chr(mark))
        except Exception:
            ext = {ms}
        return scr[base] in ext or scr[base] in ("Zyyy",)
    bases = [cp for cp in cps if cat[cp][0] in "LN" or cp == 0x25CC]
    corpora["base+mark"] = [chr(b) + chr(m) for b in bases for m in marks if compatible(b, m)]
    stacks = []
    mb = markbase_bases(A.tt) | markbase_bases(B.tt)
    for sc, grp in sorted(letters_by_script.items()):
        ms = [m for m in marks if compatible(grp[0], m)]
        if not ms:
            continue
        if len(ms) > MARKS_FOR_STACKS:
            notes.append("base+mark+mark (%s): the first %d of %d marks" % (sc, MARKS_FOR_STACKS, len(ms)))
            ms = ms[:MARKS_FOR_STACKS]
        with_anchor = [b for b in grp if A.cmap[b] in mb or B.cmap[b] in mb][:MARK_PAIR_BASES - 1]
        reps = with_anchor + [b for b in grp if b not in with_anchor][:MARK_PAIR_BASES - len(with_anchor)]
        for b in reps:
            for m1, m2 in itertools.product(ms, repeat=2):
                stacks.append(chr(b) + chr(m1) + chr(m2))
    corpora["base+mark+mark"] = stacks

    seqs = []
    for F in (A, B):
        for tag in ("GSUB", "GPOS"):
            seqs += rule_sequences(F.tt, tag)
    corpora["rules"] = sorted(expand(seqs, rev))

    words, wl_meta = [], None
    scripts = {scr[c] for c in cps if cat[c][0] == "L"}
    wl = load_wordlists(wordlists_dir, scripts, shared)
    if wl is None:
        return result("FAIL", "the word lists are missing (%s); run functional_gate.py --fetch-wordlists"
                      % wordlists_dir, ["word lists missing: the words corpus could not be shaped"])
    for name, ws in sorted(wl.items()):
        words += ws
    words = sorted(set(words) | {w for w in extra_words if all(ord(c) in shared for c in w)})
    corpora["words"] = words
    wl_meta = {name: len(ws) for name, ws in wl.items()}

    diffs = {}
    fails = []
    counts = {}
    kerned = []
    adv_a = {n: w for n, (w, _) in A.tt["hmtx"].metrics.items()}
    for name, texts in corpora.items():
        d, ex = 0, []
        for t in texts:
            a = SA.run(t)
            b = SB.run(t)
            if name == "pairs" and a[-1][1] != sum(adv_a[A.cmap[ord(c)]] for c in t):
                kerned.append(t)
            if a != b:
                d += 1
                if len(ex) < examples:
                    ex.append({"text": t, "codepoints": " ".join(u(ord(c)) for c in t),
                               "release": fmt_run(a), "build": fmt_run(b)})
        counts[name] = [len(texts), d]
        if d:
            diffs[name] = ex
    # kern + mark: a kerned pair with a combining mark between (lookup mark flags)
    between = [m for m in (0x0301, 0x0308, 0x0323) if m in shared]
    kmt = [t[0] + chr(m) + t[1] for t in kerned for m in between]
    d, ex = 0, []
    for t in kmt:
        a, b = SA.run(t), SB.run(t)
        if a != b:
            d += 1
            if len(ex) < examples:
                ex.append({"text": t, "codepoints": " ".join(u(ord(c)) for c in t),
                           "release": fmt_run(a), "build": fmt_run(b)})
    counts["kern+mark"] = [len(kmt), d]
    if d:
        diffs["kern+mark"] = ex
    for name, (n, d) in counts.items():
        if d:
            fails.append("default features, %s: %d of %d runs differ" % (name, d, n))

    # each feature, toggled from its default, over the corpus it reaches
    feat_counts = {}
    fa = {tag: feature_map(A.tt, tag) for tag in ("GSUB", "GPOS")}
    fb = {tag: feature_map(B.tt, tag) for tag in ("GSUB", "GPOS")}
    words_by_char = {}
    for w in words:
        for c in set(w):
            words_by_char.setdefault(ord(c), []).append(w)

    def reach_corpus(glyphs_a, glyphs_b, seq_a, seq_b):
        chars = sorted(cp for cp in cps if A.cmap[cp] in glyphs_a or B.cmap[cp] in glyphs_b)
        texts = set(chr(c) for c in chars)
        pr = [chr(a) + chr(b) for a in chars for b in chars]
        if len(pr) > FEATURE_PAIRS_CAP:
            pr = pr[:FEATURE_PAIRS_CAP]
        texts.update(pr)
        texts.update(expand(seq_a, rev))
        texts.update(expand(seq_b, rev))
        # words containing the characters the feature reaches, spread over them: at
        # most FEATURE_WORDS per call, the same few for every character
        ws, quota = set(), max(10, FEATURE_WORDS // max(1, len(chars)))
        for c in chars:
            ws.update(words_by_char.get(c, ())[:quota])
            if len(ws) >= FEATURE_WORDS:
                break
        texts.update(ws)
        return sorted(texts)

    for tag in ("GSUB", "GPOS"):
        for feat in sorted(set(fa[tag][0]) | set(fb[tag][0])):
            la, lb = fa[tag][0].get(feat, set()), fb[tag][0].get(feat, set())
            ga, la_all = lookup_closure(A.tt, tag, la)
            gb, lb_all = lookup_closure(B.tt, tag, lb)
            texts = reach_corpus(ga, gb, rule_sequences(A.tt, tag, la_all), rule_sequences(B.tt, tag, lb_all))
            on = feat not in DEFAULT_ON
            fdict = {feat: on}
            d, ex = 0, []
            for t in texts:
                a, b = SA.run(t, fdict), SB.run(t, fdict)
                if a != b:
                    d += 1
                    if len(ex) < examples:
                        ex.append({"text": t, "codepoints": " ".join(u(ord(c)) for c in t),
                                   "release": fmt_run(a), "build": fmt_run(b)})
            key = "%s %s %s" % (tag, feat, "on" if on else "off")
            feat_counts[key] = [len(texts), d]
            if d:
                diffs[key] = ex
                fails.append("%s: %d of %d runs differ" % (key, d, len(texts)))

    # every language system either font registers, default features
    lang_counts = {}
    systems = set()
    for tag in ("GSUB", "GPOS"):
        systems |= set(fa[tag][1]) | set(fb[tag][1])
    for script, lang in sorted(systems):
        if lang == "dflt":
            continue
        ga = gb = set()
        sa, sb = [], []
        for tag in ("GSUB", "GPOS"):
            ia = fa[tag][1].get((script, lang), set())
            ib = fb[tag][1].get((script, lang), set())
            g1, ia_all = lookup_closure(A.tt, tag, ia)
            g2, ib_all = lookup_closure(B.tt, tag, ib)
            ga, gb = ga | g1, gb | g2
            sa += rule_sequences(A.tt, tag, ia_all)
            sb += rule_sequences(B.tt, tag, ib_all)
        texts = reach_corpus(ga, gb, sa, sb)
        d, ex = 0, []
        for t in texts:
            a, b = SA.run(t, None, script, lang), SB.run(t, None, script, lang)
            if a != b:
                d += 1
                if len(ex) < examples:
                    ex.append({"text": t, "codepoints": " ".join(u(ord(c)) for c in t),
                               "release": fmt_run(a), "build": fmt_run(b)})
        key = "%s/%s" % (script, lang)
        lang_counts[key] = [len(texts), d]
        if d:
            diffs["langsys " + key] = ex
            bcp47 = hb.ot_tag_to_language(lang) or ""
            fails.append("language system %s: %d of %d runs differ%s" % (
                key, d, len(texts), "" if "x-hbot" not in bcp47 else
                " (%s is not a registered OpenType language tag: no BCP 47 language selects it; "
                "only a request for the tag itself does, e.g. CSS font-language-override)" % lang))

    total = sum(n for n, _ in counts.values()) + sum(n for n, _ in feat_counts.values()) + \
        sum(n for n, _ in lang_counts.values())
    bad = sum(d for _, d in counts.values()) + sum(d for _, d in feat_counts.values()) + \
        sum(d for _, d in lang_counts.values())
    if "kern" in A.tt and "GPOS" not in A.tt and "kern" not in B.tt:
        notes.append("the release kerns through a legacy 'kern' table, the build through GPOS "
                     "(compared as HarfBuzz shapes; engines that read only 'kern' see no kerning)")
    return result("FAIL" if fails else "PASS",
                  "%d runs shaped, %d differ" % (total, bad), fails, notes,
                  corpora=counts, features=feat_counts, language_systems=lang_counts,
                  wordlists=wl_meta, examples=diffs)


# 3 ------------------------------------------------------------------ rendering
def hinting_state(F):
    tt = F.tt
    progs = 0
    if "glyf" in tt:
        for n in F.order:
            g = tt["glyf"][n]
            if hasattr(g, "program") and g.program is not None and len(g.program.getBytecode()):
                progs += 1
    return {"fpgm": "fpgm" in tt, "prep": "prep" in tt, "cvt": "cvt " in tt,
            "glyph_programs": progs, "gasp": dict(tt["gasp"].gaspRange) if "gasp" in tt else None}


def ft_bitmap(face, gid):
    """(left, top, width, rows) of FreeType's unhinted 8-bit anti-aliased rendering."""
    face.load_glyph(gid, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_RENDER)
    s = face.glyph
    bm = s.bitmap
    buf = bytes(bm.buffer)
    rows = [buf[r * bm.pitch:r * bm.pitch + bm.width] for r in range(bm.rows)]
    return s.bitmap_left, s.bitmap_top, bm.width, rows


def bitmap_diff(ba, bb, fuzz=D3_GRAY_FUZZ):
    """Pixels whose gray differs by more than `fuzz`, both bitmaps placed on one canvas by
    their own origin offsets (so a shifted outline counts)."""
    la, ta, wa, ra = ba
    lb, tb, wb, rb = bb
    x0, x1 = min(la, lb), max(la + wa, lb + wb)
    top, bottom = max(ta, tb), min(ta - len(ra), tb - len(rb))
    blank = bytes(x1 - x0)

    def row(l, t, w, rows, y):
        r = t - y
        if 0 <= r < len(rows):
            return bytes(l - x0) + rows[r] + bytes(x1 - l - w)
        return blank
    n = 0
    for y in range(top, bottom, -1):
        a, b = row(la, ta, wa, ra, y), row(lb, tb, wb, rb, y)
        if a != b:
            n += sum(1 for p, q in zip(a, b) if p - q > fuzz or q - p > fuzz)
    return n


def run_d3(shipped, built, workdir):
    j = os.path.join(workdir, os.path.basename(built) + ".fg-d3.json")
    with open(j, "w") as fh:
        subprocess.run([D3, "-J", "2", "--no-tables", "--no-kerns", "--no-languages", "--no-match",
                        "--json", shipped, built], stdout=fh, stderr=subprocess.DEVNULL)
    return j


def check_rendering(A, B, ka_map, kb_map, key_a, key_b, d3_json, examples):
    fails, notes = [], []
    data = {}
    if d3_json is None or not os.path.exists(d3_json):
        return result("FAIL", "diffenator3 produced no JSON", ["diffenator3 did not run"])
    try:
        d = json.load(open(d3_json))
    except ValueError as e:
        return result("FAIL", "diffenator3 JSON unreadable: %s" % e, ["diffenator3 JSON unreadable"])
    glyphs, words = [], []
    for loc in d.get("locations") or []:
        if isinstance(loc.get("glyphs"), dict) and "error" in loc["glyphs"]:
            fails.append("diffenator3 glyphs: %s" % loc["glyphs"]["error"])
        for g in loc.get("glyphs") or []:
            if isinstance(g, dict):
                glyphs.append(g)
        w = loc.get("words") or {}
        for lst_name, lst in (w.items() if isinstance(w, dict) else []):
            for x in lst:
                words.append((lst_name, x))

    # The geometry test: a glyph's drawn ink, FreeType unhinted at 1 px = 8 font units,
    # both fonts on one canvas; a pixel counts when its coverage differs by more than
    # 64/255 (a quarter pixel = 2 units of edge displacement).
    ga, gb = freetype.Face(A.path), freetype.Face(B.path)
    geo_ppem = max(8, round(A.upem / GEOMETRY_UNITS_PER_PX))
    ga.set_pixel_sizes(0, geo_ppem)
    gb.set_pixel_sizes(0, geo_ppem)
    inv_b = {k: n for n, k in kb_map.items()}
    geo_cache = {}

    def geo(n):
        """Differing pixels for release glyph n and its counterpart (None: no counterpart)."""
        if n not in geo_cache:
            nb = inv_b.get(ka_map[n])
            if nb is None:
                geo_cache[n] = None
            elif A.outline(n) == B.outline(nb):
                geo_cache[n] = 0
            else:
                geo_cache[n] = bitmap_diff(ft_bitmap(ga, A.gid[n]), ft_bitmap(gb, B.gid[nb]), GEOMETRY_FUZZ)
        return geo_cache[n]

    changed, geo_bad = 0, []
    for n in sorted(A.reachable()):
        px = geo(n)
        if px is None:
            continue
        nb = inv_b[ka_map[n]]
        if A.outline(n) != B.outline(nb):
            changed += 1
        if px > GEOMETRY_THRESHOLD:
            geo_bad.append((px, n))
    geo_bad.sort(reverse=True)
    bad_names = {n for _, n in geo_bad}

    # diffenator3's reports, each confirmed or not. Its gray fuzz (8/255 at 32 ppem) is one
    # font unit of edge displacement at 1000 units/em, and a 1-unit lsb difference on
    # identical points scores 179 px (Kristi 'a', lsb -1 vs -2; FreeType at the same size
    # and fuzz: 0) while a 4-unit shift scores 17 (NixieOne comma). A report
    # counts when the glyph fails the geometry test or HarfBuzz shapes the string
    # differently; otherwise it is rounding-level and reported, not failed.
    SA, SB = Shaper(A, key_a), Shaper(B, key_b)
    conf_g, unconf_g = [], []
    for g in glyphs:
        s = g.get("string") or ""
        cp = ord(s[0]) if s else None
        n = A.cmap.get(cp) if cp is not None else None
        px = g.get("differing_pixels") or 0
        label = "%s %dpx" % (g.get("unicode") or s, px)
        if n is None or (geo(n) or 0) > GEOMETRY_THRESHOLD or SA.run(s) != SB.run(s):
            conf_g.append(label)
        else:
            unconf_g.append(label)
    conf_w, unconf_w = [], []
    for lst, x in words:
        wd = x.get("word", "")
        label = "%r %dpx" % (wd, x.get("differing_pixels") or 0)
        ra, rb = SA.run(wd), SB.run(wd)
        if ra != rb or {k for k, _, _ in ra[:-1]} & bad_names:
            conf_w.append(label)
        else:
            unconf_w.append(label)
    data.update(d3_glyph_diffs=len(glyphs), d3_word_diffs=len(words), d3_glyph_confirmed=len(conf_g),
                d3_word_confirmed=len(conf_w), outline_changed=changed, geometry_diffs=len(geo_bad))
    if conf_g:
        fails.append("diffenator3: %d encoded glyph(s) render differently (>%d px at %d ppem), confirmed: %s"
                     % (len(conf_g), D3_GLYPHS_THRESHOLD, D3_GLYPHS_PPEM, ", ".join(conf_g[:examples])))
    if conf_w:
        fails.append("diffenator3: %d word(s) render differently (>%d px at %d ppem), confirmed: %s"
                     % (len(conf_w), D3_WORDS_THRESHOLD, D3_WORDS_PPEM, ", ".join(conf_w[:examples])))
    if geo_bad:
        fails.append("%d glyph outline(s) draw ink more than rounding apart (FreeType unhinted, %d ppem = %d "
                     "units/px, > %d px at coverage fuzz %d): %s" % (
                         len(geo_bad), geo_ppem, GEOMETRY_UNITS_PER_PX, GEOMETRY_THRESHOLD, GEOMETRY_FUZZ,
                         ", ".join("%s %dpx" % (n, px) for px, n in geo_bad[:examples])))
    if unconf_g or unconf_w:
        notes.append("diffenator3 reports %d glyph(s) and %d word(s) that neither the geometry test nor "
                     "HarfBuzz confirms (1-unit rounding or lsb): %s" % (
                         len(unconf_g), len(unconf_w), ", ".join((unconf_g + unconf_w)[:examples])))
    if changed and not geo_bad:
        notes.append("%d glyph(s) store their outline differently (point structure, 1-unit rounding) "
                     "and draw the same ink" % changed)
    ha, hb_ = hinting_state(A), hinting_state(B)
    data["hinting"] = {"release": ha, "build": hb_}

    def hinted(h):
        return h["fpgm"] or h["glyph_programs"] > 0
    if (hinted(ha), ha["gasp"]) != (hinted(hb_), hb_["gasp"]):
        notes.append("HINTING (reported, not gated; rendering above is unhinted): release %s, build %s" % (
            "hinted (fpgm %s, %d glyph programs)" % (ha["fpgm"], ha["glyph_programs"]) if hinted(ha)
            else "unhinted (prep %s)" % ha["prep"],
            "hinted (fpgm %s, %d glyph programs)" % (hb_["fpgm"], hb_["glyph_programs"]) if hinted(hb_)
            else "unhinted (prep %s)" % hb_["prep"]) + "; gasp %s / %s" % (ha["gasp"], hb_["gasp"]))
    summary = "diffenator3 %d glyph / %d word diffs (%d / %d confirmed); %d of %d changed outlines draw different ink" % (
        len(glyphs), len(words), len(conf_g), len(conf_w), len(geo_bad), changed)
    return result("FAIL" if fails else "PASS", summary, fails, notes, **data)


# 4 ------------------------------------------------------------------ names
def name_table(F):
    out = {}
    for r in F.tt["name"].names:
        try:
            s = r.toUnicode()
        except Exception:
            s = repr(r.string)
        out[(r.platformID, r.platEncID, r.langID, r.nameID)] = s
    return out


def effective(recs, plat, enc, lang, nid):
    v = recs.get((plat, enc, lang, nid))
    if v is None and nid in TYPO_NAMES:
        return effective(recs, plat, enc, lang, TYPO_NAMES[nid])
    return v


def check_names(A, B):
    ra, rb = name_table(A), name_table(B)
    fails, notes = [], []
    win_keys = sorted({k[:3] for k in list(ra) + list(rb) if k[0] == 3})
    for plat, enc, lang in win_keys:
        for nid in CORE_NAMES + tuple(TYPO_NAMES):
            a = effective(ra, plat, enc, lang, nid) if nid in TYPO_NAMES else ra.get((plat, enc, lang, nid))
            b = effective(rb, plat, enc, lang, nid) if nid in TYPO_NAMES else rb.get((plat, enc, lang, nid))
            if a != b:
                fails.append("name ID %d (%d,%d,0x%X)%s: release %r, build %r" % (
                    nid, plat, enc, lang, " as read" if nid in TYPO_NAMES else "", a, b))
        for nid in TYPO_NAMES:
            a, b = ra.get((plat, enc, lang, nid)), rb.get((plat, enc, lang, nid))
            if (a is None) != (b is None) and effective(ra, plat, enc, lang, nid) == effective(rb, plat, enc, lang, nid):
                notes.append("name ID %d (%d,%d,0x%X) %s but reads the same (%r)" % (
                    nid, plat, enc, lang, "added by the build" if a is None else "dropped by the build",
                    effective(ra, plat, enc, lang, nid)))
    for nid in sorted({k[3] for k in list(ra) + list(rb)} - set(CORE_NAMES) - set(TYPO_NAMES)):
        for k in sorted({k[:3] for k in list(ra) + list(rb) if k[3] == nid and k[0] == 3}):
            a, b = ra.get(k + (nid,)), rb.get(k + (nid,))
            if a != b:
                notes.append("name ID %d (%d,%d,0x%X): release %r, build %r" % (
                    nid, k[0], k[1], k[2], (a or "")[:80] or None, (b or "")[:80] or None))
    mac_a = {k for k in ra if k[0] == 1}
    mac_b = {k for k in rb if k[0] == 1}
    if mac_a != mac_b or any(ra[k] != rb[k] for k in mac_a & mac_b):
        notes.append("Macintosh name records: %d in the release (IDs %s), %d in the build; modern systems "
                     "read the Windows records" % (len(mac_a), sorted({k[3] for k in mac_a}), len(mac_b)))
    oa, ob = A.tt["OS/2"], B.tt["OS/2"]
    for f in ("usWeightClass", "usWidthClass"):
        if getattr(oa, f) != getattr(ob, f):
            fails.append("OS/2.%s: release %d, build %d" % (f, getattr(oa, f), getattr(ob, f)))
    for f in ("fsType", "achVendID", "ulCodePageRange1", "ulCodePageRange2"):
        a, b = getattr(oa, f, None), getattr(ob, f, None)
        if a != b:
            notes.append("OS/2.%s: release %r, build %r" % (f, a, b))
    return result("FAIL" if fails else "PASS",
                  "IDs 1 2 4 6 16 17 21 22 %s" % ("equal" if not fails else "differ (%d)" % len(fails)),
                  fails, notes)


# 5 ------------------------------------------------------------------ line spacing
FS_BITS = {0: "ITALIC", 1: "UNDERSCORE", 2: "NEGATIVE", 3: "OUTLINED", 4: "STRIKEOUT", 5: "BOLD",
           6: "REGULAR", 7: "USE_TYPO_METRICS", 8: "WWS", 9: "OBLIQUE"}


def platform_metrics(F):
    o, h = F.tt["OS/2"], F.tt["hhea"]
    bit7 = bool(o.fsSelection & 0x80)
    typo = (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap)
    hh = (h.ascent, h.descent, h.lineGap)
    ext = max(0, h.lineGap - ((o.usWinAscent + o.usWinDescent) - (h.ascent - h.descent)))
    win = (o.usWinAscent, -o.usWinDescent, ext)
    return {"CoreText (hhea)": hh,
            "DirectWrite/GDI (%s)" % ("typo" if bit7 else "win"): typo if bit7 else win,
            "FreeType engines (%s)" % ("typo" if bit7 else "hhea"): typo if bit7 else hh}, bit7


def outline_top(F, cp):
    n = F.cmap.get(cp)
    if n is None or "glyf" not in F.tt:
        return None
    g = F.tt["glyf"][n]
    if not g.numberOfContours:
        return None
    coords, _, _ = g.getCoordinates(F.tt["glyf"])
    return max(y for _, y in coords) if len(coords) else None


def check_line_spacing(A, B):
    fails, notes = [], []
    ma, bit_a = platform_metrics(A)
    mb, bit_b = platform_metrics(B)
    changed = []
    for (pa, va), (pb, vb) in zip(ma.items(), mb.items()):
        if va != vb:
            plat = pa.split(" (")[0]
            changed.append(plat)
            fails.append("%s line spacing (ascender, descender, gap): release %s %s, build %s %s" % (
                plat, pa.split(" (")[1][:-1], va, pb.split(" (")[1][:-1], vb))
    if bit_a != bit_b:
        what = "USE_TYPO_METRICS %s by the build" % ("set" if bit_b else "cleared")
        bit_dependent = [p for p in changed if p != "CoreText"]
        if bit_dependent:
            fails.append("%s: it changes the line spacing on %s" % (what, ", ".join(bit_dependent)))
        else:
            notes.append("%s: no platform's line spacing changes (the typo values equal the ones it "
                         "replaces)" % what)
    oa, ob, ha, hb_ = A.tt["OS/2"], B.tt["OS/2"], A.tt["hhea"], B.tt["hhea"]
    for t, fields in ((("hhea", ha, hb_), ("ascent", "descent", "lineGap")),
                      (("OS/2", oa, ob), ("sTypoAscender", "sTypoDescender", "sTypoLineGap",
                                          "usWinAscent", "usWinDescent",
                                          "yStrikeoutSize", "yStrikeoutPosition"))):
        name, x, y = t
        for f in fields:
            if getattr(x, f) != getattr(y, f):
                fails.append("%s.%s: release %d, build %d" % (name, f, getattr(x, f), getattr(y, f)))
    pa, pb = A.tt["post"], B.tt["post"]
    for f in ("underlinePosition", "underlineThickness"):
        if getattr(pa, f) != getattr(pb, f):
            fails.append("post.%s: release %d, build %d" % (f, getattr(pa, f), getattr(pb, f)))
    fa, fb = oa.fsSelection & ~0x80, ob.fsSelection & ~0x80
    if fa != fb:
        diff = fa ^ fb
        fails.append("fsSelection: %s" % ", ".join("%s %s" % (FS_BITS.get(i, "bit%d" % i), "gained" if fb >> i & 1 else "lost")
                                                    for i in range(16) if diff >> i & 1))
    sa, sb = A.tt["head"].macStyle, B.tt["head"].macStyle
    for bit, nm in ((0, "bold"), (1, "italic")):
        if (sa >> bit & 1) != (sb >> bit & 1):
            fails.append("head.macStyle %s: release %d, build %d" % (nm, sa >> bit & 1, sb >> bit & 1))
    if (sa & ~3) != (sb & ~3):
        notes.append("head.macStyle other bits: release %d, build %d" % (sa, sb))
    if A.upem != B.upem:
        fails.append("head.unitsPerEm: release %d, build %d" % (A.upem, B.upem))

    def eff_height(F, o, field, cp):
        v = getattr(o, field, None) if o.version >= 2 else None
        return v if v else outline_top(F, cp)
    for field, cp, label in (("sxHeight", 0x78, "x-height"), ("sCapHeight", 0x48, "cap height")):
        a, b = eff_height(A, oa, field, cp), eff_height(B, ob, field, cp)
        if a != b:
            fails.append("%s as layout engines read it (CSS ex / cap units): release %s, build %s%s" % (
                label, a, b, " (the release's OS/2 v%d has no %s; engines measure the outline)" % (oa.version, field)
                if oa.version < 2 else ""))
    if oa.version != ob.version:
        notes.append("OS/2 version: release %d, build %d" % (oa.version, ob.version))
    slope_a = math.atan2(ha.caretSlopeRun, ha.caretSlopeRise)
    slope_b = math.atan2(hb_.caretSlopeRun, hb_.caretSlopeRise)
    if abs(slope_a - slope_b) > 1e-3:
        notes.append("caret slope: release %d/%d, build %d/%d (the caret's angle)" % (
            ha.caretSlopeRise, ha.caretSlopeRun, hb_.caretSlopeRise, hb_.caretSlopeRun))
    for t, fields in ((("hhea", ha, hb_), ("caretOffset",)),
                      (("head", A.tt["head"], B.tt["head"]), ("flags", "lowestRecPPEM")),
                      (("post", pa, pb), ("italicAngle",)),
                      (("OS/2", oa, ob), ("ySubscriptXSize", "ySubscriptYSize", "ySubscriptXOffset",
                                          "ySubscriptYOffset", "ySuperscriptXSize", "ySuperscriptYSize",
                                          "ySuperscriptXOffset", "ySuperscriptYOffset"))):
        name, x, y = t
        for f in fields:
            if getattr(x, f) != getattr(y, f):
                notes.append("%s.%s: release %s, build %s" % (name, f, getattr(x, f), getattr(y, f)))
    return result("FAIL" if fails else "PASS",
                  "per-platform ascender/descender/gap %s" % ("equal" if not any(
                      p in f for f in fails for p in ("CoreText", "DirectWrite", "FreeType")) else "DIFFER"),
                  fails, notes, platforms={"release": {k: list(v) for k, v in ma.items()},
                                           "build": {k: list(v) for k, v in mb.items()}})


# 6 ------------------------------------------------------------------ advances
def check_advances(A, B, ka_map, kb_map, examples):
    fails, notes = [], []
    inv_b = {k: n for n, k in kb_map.items()}
    inv_a = {k: n for n, k in ka_map.items()}
    ra, rb = A.reachable(), B.reachable()
    missing = sorted(n for n in ra if inv_b.get(ka_map[n]) is None)
    extra = sorted(n for n in rb if inv_a.get(kb_map[n]) is None)
    if missing:
        fails.append("%d reachable release glyph(s) have no build counterpart: %s" % (len(missing), " ".join(missing[:15])))
    if extra:
        fails.append("%d reachable build glyph(s) have no release counterpart: %s" % (len(extra), " ".join(extra[:15])))
    dead_a = sorted(n for n in A.order if n not in ra and inv_b.get(ka_map[n]) is None)
    if dead_a:
        notes.append("%d release glyph(s) no text can reach are not in the build: %s" % (len(dead_a), " ".join(dead_a[:10])))
    adv, lsb = [], []
    compared = 0
    for n in sorted(ra | {inv_a[kb_map[m]] for m in rb if kb_map[m] in inv_a}):
        nb = inv_b.get(ka_map[n])
        if nb is None:
            continue
        compared += 1
        (wa, la), (wb, lb) = A.tt["hmtx"][n], B.tt["hmtx"][nb]
        if wa != wb:
            adv.append("%s %d/%d" % (n, wa, wb))
        if la != lb:
            lsb.append((n, la, lb))
    if adv:
        fails.append("%d advance width(s) differ (release/build): %s" % (len(adv), ", ".join(adv[:examples * 3])))
    if lsb:
        stale = 0
        for n, la, _ in lsb:
            g = A.tt["glyf"][n] if "glyf" in A.tt else None
            if g is not None and g.numberOfContours and g.xMin != la:
                stale += 1
        notes.append("%d left side bearing(s) differ (release/build), %d where the release's lsb is not "
                     "its glyf xMin, so rasterizers draw that outline shifted by lsb - xMin (the "
                     "rendering check measures the ink): %s" % (
                         len(lsb), stale, ", ".join("%s %d/%d" % x for x in lsb[:examples])))
    for tag in ("vhea", "vmtx", "VORG"):
        if (tag in A.tt) != (tag in B.tt):
            fails.append("%s: %s in the release, %s in the build" % (tag, tag in A.tt, tag in B.tt))
    if "vmtx" in A.tt and "vmtx" in B.tt:
        vd = []
        for n in sorted(ra):
            nb = inv_b.get(ka_map[n])
            if nb is not None and A.tt["vmtx"][n] != B.tt["vmtx"][nb]:
                vd.append("%s %s/%s" % (n, A.tt["vmtx"][n], B.tt["vmtx"][nb]))
        if vd:
            fails.append("%d vertical metric(s) differ: %s" % (len(vd), ", ".join(vd[:examples])))
        for f in ("ascent", "descent", "lineGap"):
            if getattr(A.tt["vhea"], f) != getattr(B.tt["vhea"], f):
                fails.append("vhea.%s differs" % f)
    if A.tt["post"].isFixedPitch != B.tt["post"].isFixedPitch:
        fails.append("post.isFixedPitch: release %d, build %d" % (A.tt["post"].isFixedPitch, B.tt["post"].isFixedPitch))
    return result("FAIL" if fails else "PASS",
                  "%d glyph advances compared, %d differ" % (compared, len(adv)), fails, notes)


# 7 ------------------------------------------------------------------ GDEF
def gdef_info(F):
    tt = F.tt
    info = {"present": "GDEF" in tt, "classes": None, "attach": {}, "sets": [], "carets": {}}
    if "GDEF" in tt:
        t = tt["GDEF"].table
        if t.GlyphClassDef is not None:
            info["classes"] = dict(t.GlyphClassDef.classDefs)
        if getattr(t, "MarkAttachClassDef", None) is not None:
            info["attach"] = dict(t.MarkAttachClassDef.classDefs)
        if getattr(t, "MarkGlyphSetsDef", None) is not None:
            info["sets"] = [set(c.glyphs) for c in t.MarkGlyphSetsDef.Coverage]
        if getattr(t, "LigCaretList", None) is not None:
            lc = t.LigCaretList
            for g, lg in zip(lc.Coverage.glyphs, lc.LigGlyph):
                info["carets"][g] = [getattr(c, "Coordinate", None) for c in lg.CaretValue]
    flags = 0
    attach_used, sets_used = set(), set()
    for tag in ("GSUB", "GPOS"):
        for lk in lookups_of(tt, tag):
            flags |= lk.LookupFlag
            if lk.LookupFlag & 0xFF00:
                attach_used.add(lk.LookupFlag >> 8)
            if lk.LookupFlag & 0x10:
                sets_used.add(getattr(lk, "MarkFilteringSet", None))
    info["flags"], info["attach_used"], info["sets_used"] = flags, attach_used, sets_used
    return info


def effective_class(F, info, name):
    if info["classes"] is not None:
        return info["classes"].get(name, 0)
    cp = F.rev.get(name)
    if cp is None:
        return None              # decided by the substitution that produces it
    ignorable = cp in (0x034F,) or 0xFE00 <= cp <= 0xFE0F or 0x180B <= cp <= 0x180F
    return 3 if category(cp) == "Mn" and not ignorable else 1


def check_gdef(A, B, ka_map, kb_map, examples):
    ia, ib = gdef_info(A), gdef_info(B)
    fails, notes = [], []
    inv_b = {k: n for n, k in kb_map.items()}
    ignore_base = bool((ia["flags"] | ib["flags"]) & 0x2)
    ignore_lig = bool((ia["flags"] | ib["flags"]) & 0x4)
    affecting, inert = [], []
    for n in sorted(A.reachable()):
        nb = inv_b.get(ka_map[n])
        if nb is None:
            continue
        a, b = effective_class(A, ia, n), effective_class(B, ib, nb)
        if a == b:
            continue
        label = "%s %s/%s" % (n, a if a is not None else "-", b if b is not None else "-")
        if None in (a, b):
            (affecting if 3 in (a, b) else inert).append(label)
        elif 3 in (a, b) or (ignore_base and 1 in (a, b)) or (ignore_lig and 2 in (a, b)):
            affecting.append(label)
        else:
            inert.append(label)
    if ia["present"] != ib["present"]:
        (fails if affecting else notes).append("GDEF %s in the build%s" % (
            "absent" if not ib["present"] else "present",
            "" if affecting else "; the classes HarfBuzz uses are the same"))
    if affecting:
        fails.append("%d glyph class(es) differ where shaping reads them (release/build; '-' = decided by "
                     "substitution, the build has no class table): %s" % (len(affecting), ", ".join(affecting[:examples * 3])))
    if inert:
        notes.append("%d glyph class(es) differ where no lookup reads them: %s" % (len(inert), ", ".join(inert[:examples])))

    def partition(info, kmap):
        groups = {}
        for g, c in info["attach"].items():
            groups.setdefault(c, set()).add(kmap.get(g, g))
        return {frozenset(s) for s in groups.values()}
    pa, pb = partition(ia, ka_map), partition(ib, kb_map)
    if pa != pb:
        used = ia["attach_used"] or ib["attach_used"]
        (fails if used else notes).append("mark attachment classes differ%s" % ("" if used else " (no lookup filters on them)"))
    sa = {frozenset(ka_map.get(g, g) for g in s) for s in ia["sets"]}
    sb = {frozenset(kb_map.get(g, g) for g in s) for s in ib["sets"]}
    if sa != sb:
        used = ia["sets_used"] or ib["sets_used"]
        (fails if used else notes).append("mark glyph sets differ%s" % ("" if used else " (no lookup filters on them)"))
    ca = {ka_map.get(g, g): v for g, v in ia["carets"].items()}
    cb = {kb_map.get(g, g): v for g, v in ib["carets"].items()}
    if ca != cb:
        notes.append("ligature carets differ (%d release, %d build glyphs): cursor placement inside ligatures"
                     % (len(ca), len(cb)))
    return result("FAIL" if fails else "PASS",
                  "GDEF %s/%s; %d class difference(s) shaping reads, %d it does not" % (
                      "present" if ia["present"] else "absent", "present" if ib["present"] else "absent",
                      len(affecting), len(inert)), fails, notes)


# ---------------------------------------------------------------------------------
def run(shipped, built, style=None, d3_json=None, workdir=None, examples=5, wordlists=WORDLISTS):
    """Compare a shipped font and a built font. Returns the verdict dict."""
    A, B = Font(shipped), Font(built)
    key_a, key_b, ka_map, kb_map = correspondence(A, B)
    own_tmp = None
    if d3_json is None:
        os.makedirs(SCRATCH, exist_ok=True)
        own_tmp = workdir or tempfile.mkdtemp(prefix="fg-", dir=SCRATCH)
        d3_json = run_d3(shipped, built, own_tmp)
    extra = []
    try:
        for loc in json.load(open(d3_json)).get("locations") or []:
            for lst in (loc.get("words") or {}).values() if isinstance(loc.get("words"), dict) else []:
                extra += [w["word"] for w in lst if "word" in w]
    except (OSError, ValueError):
        pass
    checks = {}
    checks["cmap"] = check_cmap(A, B, ka_map, kb_map)
    checks["shaping"] = check_shaping(A, B, key_a, key_b, examples, wordlists, extra)
    checks["rendering"] = check_rendering(A, B, ka_map, kb_map, key_a, key_b, d3_json, examples)
    checks["names"] = check_names(A, B)
    checks["line_spacing"] = check_line_spacing(A, B)
    checks["advances"] = check_advances(A, B, ka_map, kb_map, examples)
    checks["gdef"] = check_gdef(A, B, ka_map, kb_map, examples)
    if own_tmp and not workdir:
        shutil.rmtree(own_tmp, ignore_errors=True)
    env = {"harfbuzz": hb.version_string(), "uharfbuzz": getattr(hb, "__version__", "?"),
           "freetype": ".".join(map(str, freetype.version())),
           "diffenator3": subprocess.run([D3, "--version"], capture_output=True, text=True).stdout.strip(),
           "wordlists": {"repo": WORDLISTS_REPO, "commit": WORDLISTS_COMMIT, "dir": wordlists,
                         "digest": wordlists_digest(wordlists) if os.path.isdir(wordlists) else None}}
    try:
        import fontTools
        env["fonttools"] = fontTools.version
    except Exception:
        pass
    verdict = "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL"
    return {"tool": "tools/functional_gate.py", "style": style, "shipped": shipped, "built": built,
            "verdict": verdict, "checks": checks, "environment": env}


def summary_lines(res, per_check=3):
    lines = ["%s %s: functional %s" % (res.get("style") or os.path.basename(res["built"]),
                                       os.path.basename(res["built"]), res["verdict"])]
    for name, c in res["checks"].items():
        lines.append("  %-12s %-4s %s" % (name, c["status"], c["summary"]))
        for f in c["failures"][:per_check]:
            lines.append("      - " + f)
        if len(c["failures"]) > per_check:
            lines.append("      - ... %d more" % (len(c["failures"]) - per_check))
    return lines


def failed_checks(res):
    return [n for n, c in res["checks"].items() if c["status"] != "PASS"]


def fetch_wordlists():
    root = os.path.join(SCRATCH, "fontheight")
    if not os.path.isdir(os.path.join(root, ".git")):
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", WORDLISTS_REPO, root], check=True)
    subprocess.run(["git", "-C", root, "sparse-checkout", "set", WORDLISTS_SUBDIR], check=True)
    subprocess.run(["git", "-C", root, "fetch", "-q", "origin", WORDLISTS_COMMIT], check=True)
    subprocess.run(["git", "-C", root, "checkout", "-q", WORDLISTS_COMMIT], check=True)
    print("word lists at %s (fontheight %s), digest %s" % (WORDLISTS, WORDLISTS_COMMIT[:12], wordlists_digest(WORDLISTS)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("shipped", nargs="?")
    ap.add_argument("built", nargs="?")
    ap.add_argument("--style")
    ap.add_argument("--d3-json")
    ap.add_argument("--json")
    ap.add_argument("--examples", type=int, default=5)
    ap.add_argument("--wordlists", default=WORDLISTS)
    ap.add_argument("--workdir")
    ap.add_argument("--fetch-wordlists", action="store_true")
    a = ap.parse_args()
    if a.fetch_wordlists:
        fetch_wordlists()
        return 0
    if not (a.shipped and a.built):
        ap.error("need <shipped.ttf> <built.ttf>")
    try:
        res = run(a.shipped, a.built, a.style, a.d3_json, a.workdir, a.examples, a.wordlists)
    except Exception as e:                   # a gate that crashed has not passed
        print("functional gate could not run: %r" % e, file=sys.stderr)
        return 2
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False, default=list)
    print("\n".join(summary_lines(res)))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
