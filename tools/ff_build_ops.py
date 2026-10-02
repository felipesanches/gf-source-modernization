#!/usr/bin/env python3
"""FontForge build-script steps, reproduced as edits to an .sfd (Thabit's build.py).

Promoted 2026-10-02 from investigations/next-provenance/probes/ff_build_ops.py (unchanged
below this note) for tools/sfd_edit.py's mergefea, mergepsfont, afmligatures, obliqize and
pastepsglyphs ops; the probe stays where its measurements cite it.

Question answered: Thabit's release is not a TTF export of src/Thabit.sfd alone. Its build
script (hg 52f780b ofl/thabit/src/build.py; the 0.02 release's ChangeLog calls it
helper.py) runs, with FontForge's Python module:

    font = fontforge.open("Thabit.sfd")
    font.mergeFeature("Thabit.fea")        # the whole GSUB
    font.mergeFonts("cour/cour.pfa")       # IBM Courier: the Latin, and (from the AFM
                                           #  FontForge reads beside it) the f-ligatures
    font.copyright += "\\nLatin glyphs are Copyright (c) IBM Corporation 1990,1991."
    font.generate("Thabit.ttf", flags=("opentype",))

and, for the two obliques, `obliqize` (psMat.skew(-16) -- RADIANS -- on every glyph but the
U+200C..U+202E controls, after unlinking references), `deobliqize` (upright Courier
parentheses, brackets, braces and exclam pasted over), then the same `generate` with the
Courier Italic / Bold Italic PFA.

If each step is written into the .sfd as a documented edit, does the converted source build
what Google Fonts ships? This module performs each step on the .sfd TEXT, following the
FontForge of the release's FFTM stamp (2008-08-08 01:38:58 UTC, so git eb711fd7 of
fontforge/fontforge, 2008-08-08 00:28:07Z): fvfonts.c _MergeFont / __MergeFont,
splinesaveafm.c SCWorthOutputting / LoadKerningDataFromAfm, psread.c seac, featurefile.c.
No FontForge is run; no value is taken from the release.

Operations (each FATAL when it cannot apply as FontForge would):
  mergefea <file.fea>        GSUB single and ligature lookups only; one subtable per
                             lookup, named "<lookup> subtable" as FontForge names it
  mergepsfont <file.pfa> [<file.afm>] <prefix>
                             copy every glyph that draws something and that the font
                             does not already have (by Unicode or by name) -- outlines
                             unscaled (_MergeFont does not scale the em), seac as two
                             references, Unicode from the glyph name (FontForge's
                             UniFromName, probes/ff_namelist.py); AFM "L"
                             ligatures become one 'liga' lookup for script latn, named
                             "<prefix>-'liga' Standard Ligatures in Latin lookup 0"
  appendcopyright <text>     Copyright: <old> + <text> (build.py's font.copyright += ...)
  ffnotdef                   the .notdef FontForge's TTF exporter synthesises when the
                             font has none (tottf.c dumpmissingglyph; the formula is
                             investigations/tuffy's): a converter-side rule, emulated here
                             only to measure it
  obliqize <angle> <first> <last> [sse|x87|double]
                             build.py obliqize(): unlink references, then skew every glyph
                             worth outputting by psMat.skew(angle) = (1,0,tan(angle),1,0,0),
                             except the Unicode range first..last; anchors are moved too
  pastepsglyphs <file.pfa> <name>...
                             build.py deobliqize(): replace (or create) these glyphs with
                             the PFA's, outlines only, keeping the target's encoding slot

Usage:
  ff_build_ops.py <in.sfd> <out.sfd> <op> [args...] [-- <op> [args...]]...
"""
import math
import re
import sys

from fontTools import agl
from fontTools.encodings.StandardEncoding import StandardEncoding
from fontTools.feaLib import ast as fea
from fontTools.feaLib.parser import Parser
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.t1Lib import T1Font


class OpError(Exception):
    pass


# --------------------------------------------------------------------------- sfd text

def glyph_blocks(text):
    """(name, match) for every StartChar..EndChar block, in file order."""
    return [(m.group(1).strip(), m) for m in
            re.finditer(r"^StartChar: ([^\n]*)\n.*?^EndChar\n", text, re.M | re.S)]


def glyph_info(text):
    info = []
    for name, m in glyph_blocks(text):
        body = m.group(0)
        enc = re.search(r"^Encoding: (-?\d+) (-?\d+) (-?\d+)", body, re.M)
        draws = bool(re.search(r"^SplineSet\n(?!EndSplineSet)", body, re.M)) or \
            bool(re.search(r"^\s*-?[\d.]+ -?[\d.e-]+ m ", body, re.M)) or \
            bool(re.search(r"^Refer: ", body, re.M))
        info.append(dict(name=name, slot=int(enc.group(1)), uni=int(enc.group(2)),
                         gid=int(enc.group(3)), draws=draws, match=m))
    return info


def insert_before_endchars(text, blocks):
    e = list(re.finditer(r"^EndChars$", text, re.M))
    if len(e) != 1:
        raise OpError("%d EndChars lines" % len(e))
    return text[:e[0].start()] + blocks + text[e[0].start():]


def bump_beginchars(text, nslots, nglyphs):
    m = re.search(r"^BeginChars: (\d+) (\d+)$", text, re.M)
    if not m:
        raise OpError("no BeginChars line")
    return text[:m.start()] + "BeginChars: %d %d" % (max(int(m.group(1)), nslots), nglyphs) + text[m.end():]


def add_lookup_lines(text, lines, gsub=True):
    """Insert Lookup: lines after the last existing GSUB lookup (FontForge keeps GSUB
    lookups before GPOS ones in an .sfd), or before the first Lookup/BeginChars line."""
    existing = list(re.finditer(r"^Lookup: (\d+) .*\n", text, re.M))
    gsub_l = [m for m in existing if int(m.group(1)) < 0x100]
    if gsub_l:
        pos = gsub_l[-1].end()
    elif existing:
        pos = existing[0].start()
    else:
        m = re.search(r"^(?:MarkAttachClasses|DEI|LangName|GaspTable|Encoding|BeginChars):", text, re.M)
        pos = m.start()
    return text[:pos] + "".join(l + "\n" for l in lines) + text[pos:]


def add_glyph_lines(text, glyph, lines):
    """Append lines to a glyph block just before its EndChar (PST lines)."""
    for name, m in glyph_blocks(text):
        if name == glyph:
            body = m.group(0)
            new = body[:-len("EndChar\n")] + "".join(l + "\n" for l in lines) + "EndChar\n"
            return text[:m.start()] + new + text[m.end():]
    raise OpError("no glyph %s" % glyph)


# --------------------------------------------------------------------------- mergefea

FLAG_BITS = {"RightToLeft": 1, "IgnoreBaseGlyphs": 2, "IgnoreLigatures": 4, "IgnoreMarks": 8}


def mergefea(text, fea_path):
    names = {n for n, _ in glyph_blocks(text)}
    import io
    src = open(fea_path, encoding="utf-8").read()
    # FontForge's feature-file parser (featurefile.c) accepts the old comma-separated
    # "lookupflag RightToLeft, IgnoreMarks;"; feaLib wants the flags space-separated.
    src = re.sub(r"^(\s*lookupflag\b[^;]*);", lambda m: m.group(1).replace(",", " ") + ";", src, flags=re.M)
    buf = io.StringIO(src)
    buf.name = fea_path
    doc = Parser(buf, glyphNames=names).parse()
    lookups = {}       # name -> dict(kind, flags, rules)
    order = []
    feats = {}         # lookup name -> [(feature, script, lang)]
    for st in doc.statements:
        if isinstance(st, fea.LookupBlock):
            flags, rules, kind = 0, [], None
            for s in st.statements:
                if isinstance(s, fea.LookupFlagStatement):
                    flags = s.value
                    if s.markAttachment is not None or s.markFilteringSet is not None:
                        raise OpError("mark attachment/filtering flags not modelled")
                elif isinstance(s, fea.SingleSubstStatement):
                    if s.prefix or s.suffix:
                        raise OpError("contextual single substitution not modelled")
                    k = 1
                    for g_in, g_out in zip(s.glyphs[0].glyphSet(), s.replacements[0].glyphSet()):
                        rules.append((g_in, [g_out]))
                    kind = kind or k
                elif isinstance(s, fea.LigatureSubstStatement):
                    if s.prefix or s.suffix:
                        raise OpError("contextual ligature not modelled")
                    comps = [g.glyphSet() for g in s.glyphs]
                    if any(len(c) != 1 for c in comps):
                        raise OpError("class ligature components not modelled")
                    rules.append((s.replacement, [c[0] for c in comps]))
                    kind = kind or 4
                elif isinstance(s, fea.Comment):
                    continue
                else:
                    raise OpError("statement not modelled: %s" % type(s).__name__)
            if kind not in (1, 4):
                raise OpError("only single and ligature substitution are modelled")
            lookups[st.name] = dict(kind=kind, flags=flags, rules=rules)
            order.append(st.name)
        elif isinstance(st, fea.FeatureBlock):
            script, lang = "DFLT", "dflt"
            for s in st.statements:
                if isinstance(s, fea.ScriptStatement):
                    script, lang = s.script, "dflt"
                elif isinstance(s, fea.LanguageStatement):
                    lang = s.language
                elif isinstance(s, fea.LookupReferenceStatement):
                    feats.setdefault(s.lookup.name, []).append((st.name, script, lang.strip()))
                elif isinstance(s, fea.Comment):
                    continue
                else:
                    raise OpError("feature statement not modelled: %s" % type(s).__name__)
        elif isinstance(st, (fea.Comment, fea.LanguageSystemStatement)):
            continue
        else:
            raise OpError("top-level statement not modelled: %s" % type(st).__name__)
    lines = []
    for name in order:
        lk = lookups[name]
        fl = []
        for feat, script, lang in feats.get(name, []):
            fl.append("'%s' ('%s' <'%s' > )" % (feat, script, lang))
        lines.append('Lookup: %d %d 0 "%s" {"%s subtable"  } [%s ]' % (
            lk["kind"], lk["flags"], name, name, " ".join(fl)))
    text = add_lookup_lines(text, lines)
    n = 0
    for name in order:
        lk = lookups[name]
        for target, comps in lk["rules"]:
            if lk["kind"] == 1:
                # FontForge stores a single substitution on the SOURCE glyph
                text = add_glyph_lines(text, target, ['Substitution2: "%s subtable" %s' % (name, comps[0])])
            else:
                # and a ligature on the LIGATURE glyph
                text = add_glyph_lines(text, target, ['Ligature2: "%s subtable" %s' % (name, " ".join(comps))])
            n += 1
    return text, "%d lookups (%s), %d rules" % (len(order), ", ".join(order), n)


# --------------------------------------------------------------------------- mergepsfont

def fmt(v):
    if float(v).is_integer():
        return "%d" % v
    return ("%.12g" % v)


class SFDPen(BasePen):
    """Type 1 outlines as FontForge SplineSet lines, as FontForge 2008 holds them after
    loading a PostScript font: every contour REVERSED to the TrueType direction (psread.c:
    "PS and TT disagree on which direction to use ... we must reverse postscript"), and a
    contour returning to its start explicitly, as FontForge writes it.

    quadratic=True: the target layer is TrueType (Thabit.sfd's "Fore" is order2), and
    FontForge's merge converts every copied glyph to the target's order
    (fvfonts.c SplineCharCopy -> SCConvertOrder -> splineorder2.c SplineSetsTTFApprox).
    That algorithm is NOT ported here: cu2qu (max_err 1 unit, FontForge's "within an
    emunit or so") stands in for it, so points differ from FontForge's while the drawing
    stays within a unit. Each quadratic segment is written as one "c" line whose two
    control points are the single off-curve point, as FontForge writes order2 splines;
    implied on-curve points are written explicitly."""

    def __init__(self, quadratic=False, max_err=1.0, reverse=True):
        super().__init__(None)
        self.lines, self.start, self.segs = [], None, []
        self.quadratic, self.max_err, self.reverse = quadratic, max_err, reverse

    def _moveTo(self, p):
        self._flush()
        self.start, self.segs = p, []

    def _lineTo(self, p):
        self.segs.append(("l", [], p))

    def _curveToOne(self, p1, p2, p3):
        if not self.quadratic:
            self.segs.append(("c", [p1, p2], p3))
            return
        from fontTools.cu2qu import curve_to_quadratic
        p0 = self._getCurrentPoint()
        q = curve_to_quadratic([p0, p1, p2, p3], self.max_err)
        offs, end = q[1:-1], q[-1]
        for i, off in enumerate(offs):
            on = end if i == len(offs) - 1 else ((off[0] + offs[i + 1][0]) / 2, (off[1] + offs[i + 1][1]) / 2)
            self.segs.append(("q", [off], on))

    def _closePath(self):
        cur = self._getCurrentPoint()
        if cur is not None and self.start is not None and tuple(cur) != tuple(self.start):
            self.segs.append(("l", [], self.start))
        self._flush()

    _endPath = _closePath

    def _flush(self):
        if self.start is None or not self.segs:
            self.start, self.segs = None, []
            return
        start, segs = self.start, self.segs
        if self.reverse:
            pts = [start] + [e for _, _, e in segs]          # pts[-1] == start
            rsegs = []
            for i in range(len(segs) - 1, -1, -1):
                kind, ctrl, _ = segs[i]
                rsegs.append((kind, list(reversed(ctrl)), pts[i]))
            segs = rsegs
        self.lines.append("%s %s m 1" % (fmt(round(start[0], 4)), fmt(round(start[1], 4))))
        for kind, ctrl, e in segs:
            if kind == "l":
                self.lines.append(" %s %s l 1" % (fmt(round(e[0], 4)), fmt(round(e[1], 4))))
            elif kind == "c":
                self.lines.append(" %s %s %s %s %s %s c 0" % tuple(fmt(round(v, 4)) for v in (*ctrl[0], *ctrl[1], *e)))
            else:
                self.lines.append(" %s %s %s %s %s %s c 0" % tuple(fmt(round(v, 4)) for v in (*ctrl[0], *ctrl[0], *e)))
        self.start, self.segs = None, []


def ps_glyphs(pfa, quadratic=False):
    t1 = T1Font(pfa)
    t1.parse()
    cs = t1.font["CharStrings"]
    out = []
    for name in cs.keys():
        rec = RecordingPen()
        cs[name].draw(rec)
        comps = [(v[0], v[1]) for op, v in rec.value if op == "addComponent"]
        pen = SFDPen(quadratic)
        for op, args in rec.value:
            if op != "addComponent":
                getattr(pen, op)(*args)
        out.append(dict(name=name, splines=pen.lines, comps=comps))
    return t1, out


def t1_width(t1, name):
    """hsbw's wx for a glyph (fontTools records it while drawing)."""
    cs = t1.font["CharStrings"][name]
    cs.draw(RecordingPen())
    return cs.width


def afm_ligatures(afm):
    ligs = []   # (ligature, [components])
    for line in open(afm, encoding="latin-1"):
        if not line.startswith("C "):
            continue
        n = re.search(r"; N (\S+) ;", line)
        for second, lig in re.findall(r"; L (\S+) (\S+)", line):
            ligs.append((lig, [n.group(1), second]))
    return ligs


def uni_from_name(name):
    """FontForge 2008's UniFromName (probes/ff_namelist.py), not fontTools' AGL: the two
    disagree on Omega/ohm, mu/micro and the IBM box-drawing names."""
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ff_namelist
    return ff_namelist.uni_from_name(name)


def target_is_quadratic(text):
    """Layer: 1 <quadratic> "Fore" ... -- the foreground layer's order."""
    m = re.search(r'^Layer: 1 (\d) ', text, re.M)
    return bool(m and m.group(1) == "1")


def mergepsfont(text, pfa, afm, prefix):
    t1, glyphs = ps_glyphs(pfa, target_is_quadratic(text))
    have = glyph_info(text)
    have_names = {g["name"]: g for g in have}
    have_unis = {g["uni"]: g for g in have if g["uni"] >= 0}
    next_gid = max(g["gid"] for g in have) + 1
    next_slot = max(max(g["slot"] for g in have) + 1, 0x10000)
    by_name = {g["name"]: g for g in glyphs}
    # SCWorthOutputting (splinesaveafm.c): draws something, or is referenced
    referenced = {c for g in glyphs for c, _ in g["comps"]}
    added, gid_of = [], {}
    for g in glyphs:
        draws = bool(g["splines"]) or bool(g["comps"])
        if not (draws or g["name"] in referenced):
            continue
        uni = uni_from_name(g["name"])
        exists = have_names.get(g["name"]) or (have_unis.get(uni) if uni >= 0 else None)
        if exists is not None and (exists["draws"] or exists["name"] in referenced):
            continue      # SFHasChar: the font already has it
        g["uni"] = uni
        g["gid"] = next_gid
        if 0 <= uni < 0x10000:
            g["slot"] = uni
        else:
            g["slot"] = next_slot
            next_slot += 1
        gid_of[g["name"]] = next_gid
        next_gid += 1
        added.append(g)
    # existing glyphs keep their gids; a reference to a glyph the font already had
    # binds to the font's glyph (MergeFixupRefChars works by name)
    for g in have:
        gid_of.setdefault(g["name"], g["gid"])
    # babelfont resolves Refer: by the glyph's POSITION in the file; appended glyphs
    # are written in gid order after every existing glyph, so position == gid holds
    # when it held before
    positions = {g["name"]: i for i, g in enumerate(have)}
    if any(positions[g["name"]] != g["gid"] for g in have):
        raise OpError("existing glyph positions differ from gids; Refer resolution would break")
    ligs = afm_ligatures(afm) if afm else []
    lig_of = {}
    for lig, comps in ligs:
        if lig in gid_of and all(c in gid_of for c in comps):
            lig_of.setdefault(lig, []).append(comps)
    lookup = "%s-'liga' Standard Ligatures in Latin lookup 0" % prefix
    blocks = []
    for g in added:
        width = t1_width(t1, g["name"])
        lines = ["StartChar: %s" % g["name"], "Encoding: %d %d %d" % (g["slot"], g["uni"], g["gid"]),
                 "Width: %s" % fmt(width), "Flags: W", "LayerCount: 2", "Fore"]
        if g["splines"]:
            lines += ["SplineSet"] + g["splines"] + ["EndSplineSet"]
        for comp, tr in g["comps"]:
            if comp not in gid_of:
                raise OpError("%s refers to %s, which is not in the font" % (g["name"], comp))
            cu = uni_from_name(comp)
            lines.append("Refer: %d %d N %s %s %s %s %s %s 2" % (
                gid_of[comp], cu, *(fmt(v) for v in tr)))
        for comps in lig_of.get(g["name"], []):
            lines.append('Ligature2: "%s subtable" %s' % (lookup, " ".join(comps)))
        lines.append("EndChar")
        blocks.append("\n".join(lines) + "\n\n")
    text = insert_before_endchars(text, "".join(blocks))
    text = bump_beginchars(text, next_slot, next_gid)
    if lig_of:
        text = add_lookup_lines(text, ['Lookup: 4 0 1 "%s" {"%s subtable"  } [\'liga\' (\'latn\' <\'dflt\' > ) ]'
                                       % (lookup, lookup)])
    unmapped = [g["name"] for g in added if g["uni"] < 0]
    return text, "%d glyphs added (%d unencoded: %s), %d AFM ligatures" % (
        len(added), len(unmapped), " ".join(unmapped[:12]), sum(len(v) for v in lig_of.values()))


# --------------------------------------------------------------------------- the rest

def appendcopyright(text, extra):
    m = re.search(r"^Copyright: (.*)$", text, re.M)
    if not m:
        raise OpError("no Copyright line")
    return text[:m.start()] + "Copyright: %s%s" % (m.group(1), extra) + text[m.end():], m.group(1)


def ffnotdef(text):
    """tottf.c dumpmissingglyph(), as investigations/tuffy/probes/apply_edits.py ffnotdef."""
    if re.search(r"^StartChar: \.notdef$", text, re.M):
        raise OpError("font already has a .notdef")
    asc = int(re.search(r"^Ascent: (\d+)", text, re.M).group(1))
    dsc = int(re.search(r"^Descent: (\d+)", text, re.M).group(1))
    em = asc + dsc

    def ps(key):
        m = re.search(r"^%s \d+ (.*)$" % key, text, re.M)
        if not m:
            return None
        try:
            return float(m.group(1).strip())
        except ValueError:
            return 0.0
    v = ps("StdVW")
    stem = int(v if v is not None else (ps("StdHW") or 0))
    if stem <= 0:
        stem = em // 30
    ymax = min(2 * em // 3, asc)
    xmax = 5 * stem + em // 10 + stem
    width = xmax + 2 * stem
    outer = [(stem, 0), (stem, ymax), (xmax, ymax), (xmax, 0)]
    inner = [(2 * stem, stem), (xmax - stem, stem), (xmax - stem, ymax - stem), (2 * stem, ymax - stem)]
    lines = []
    for c in (outer, inner):
        lines.append("%d %d m 1" % c[0])
        for p in c[1:] + [c[0]]:
            lines.append(" %d %d l 1" % p)
    have = glyph_info(text)
    gid = max(g["gid"] for g in have) + 1
    slot = max(max(g["slot"] for g in have) + 1, 0x10000)
    block = ("StartChar: .notdef\nEncoding: %d -1 %d\nWidth: %d\nFlags: HMW\nLayerCount: 2\n"
             "Fore\nSplineSet\n%s\nEndSplineSet\nEndChar\n\n" % (slot, gid, width, "\n".join(lines)))
    text = insert_before_endchars(text, block)
    text = bump_beginchars(text, slot + 1, gid + 1)
    return text, "stem %d, advance %d, box %s" % (stem, width, outer)


def _refer_targets(text):
    names = [n for n, _ in glyph_blocks(text)]
    return names


def unlink_and_skew(text, angle, first, last):
    """build.py obliqize(): select every glyph worth outputting, deselect the encoding
    range first..last, unlinkReferences(), transform(skew)."""
    c = math.tan(angle)
    names = _refer_targets(text)
    blocks = glyph_blocks(text)
    info = glyph_info(text)
    # outlines of every glyph, for unlinking
    outlines = {}
    for (name, m) in blocks:
        body = m.group(0)
        ss = re.search(r"^SplineSet\n(.*?)^EndSplineSet\n", body, re.M | re.S)
        outlines[name] = ss.group(1) if ss else ""

    def refs(body):
        return re.findall(r"^Refer: (-?\d+) (-?\d+) \S+ (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) \d+\n", body, re.M)

    def flat(name, depth=0):
        """The glyph's outline with every reference unlinked (recursively)."""
        if depth > 20:
            raise OpError("reference loop at %s" % name)
        body = dict(blocks)[name].group(0)
        out = parse_splines(outlines[name])
        for gid, _u, a, b, cc, d, e, f in refs(body):
            target = names[int(gid)]
            for contour in flat(target, depth + 1):
                out.append(transform_contour(contour, [float(v) for v in (a, b, cc, d, e, f)]))
        return out

    skip = set()
    for g in info:
        if first <= g["uni"] <= last:
            skip.add(g["name"])
    new_text = text
    changed = 0
    for (name, m) in reversed(blocks):
        g = next(x for x in info if x["name"] == name)
        body = m.group(0)
        if name in skip or not (g["draws"]):
            continue
        contours = flat(name)
        contours = [transform_contour(ct, (1, 0, c, 1, 0, 0)) for ct in contours]
        body2 = re.sub(r"^Refer: .*\n", "", body, flags=re.M)
        ss_new = "SplineSet\n" + write_splines(contours) + "EndSplineSet\n"
        if re.search(r"^SplineSet\n.*?^EndSplineSet\n", body2, re.M | re.S):
            body2 = re.sub(r"^SplineSet\n.*?^EndSplineSet\n", lambda _m: ss_new, body2, count=1, flags=re.M | re.S)
        else:
            body2 = re.sub(r"^(Fore\n)", lambda _m: "Fore\n" + ss_new, body2, count=1, flags=re.M)
        # anchors move with the outline
        # splineutil.c ApTransform: the same arithmetic and 1/1024 quantization as points
        body2 = re.sub(r'^(AnchorPoint: "[^"]*" )(-?[\d.e-]+) (-?[\d.e-]+)',
                       lambda a: "%s%s %s" % ((a.group(1),) + tuple(fmt(v) for v in _ff_point(
                           (1, 0, c, 1, 0, 0), float(a.group(2)), float(a.group(3))))), body2, flags=re.M)
        # TrueType instructions no longer fit the outline; FontForge drops them
        body2 = re.sub(r"^TtInstrs:\n.*?^EndTTInstrs\n", "", body2, flags=re.M | re.S)
        new_text = new_text[:m.start()] + body2 + new_text[m.end():]
        changed += 1
    return new_text, "skewed %d glyphs by tan(%g) = %.6f; kept upright: %s" % (
        changed, angle, c, " ".join(sorted(skip)))


def parse_splines(s):
    """SplineSet text -> list of contours; a contour is a list of (op, [points])."""
    contours, cur = [], None
    for line in s.splitlines():
        parts = line.split()
        if not parts:
            continue
        op_i = next((i for i, p in enumerate(parts) if p in ("m", "l", "c")), None)
        if op_i is None:
            continue
        nums = [float(x) for x in parts[:op_i]]
        op = parts[op_i]
        flags = parts[op_i + 1] if len(parts) > op_i + 1 else ("1" if op != "c" else "0")
        pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]
        if op == "m":
            cur = [("m", pts, flags)]
            contours.append(cur)
        else:
            cur.append((op, pts, flags))
    return contours


FF_ARITH = "sse"   # set by the obliqize op: sse | x87 | double


def _f32(v):
    import struct
    return struct.unpack("f", struct.pack("f", v))[0]


def _ff_point(t, x, y):
    """splineutil.c TransformPoint() of FontForge 2008, whose `real` is float unless
    built with --enable-double ("normally it uses floats", configure.in):
        p.x = t[0]*x + t[2]*y + t[4];  p.x = rint(1024*p.x)/1024;   (same for y)
    sse: every float operation rounds to float; x87: intermediates in extended
    precision, rounded to float when stored; double: a --enable-double build."""
    a, b, c, d, e, f = t
    if FF_ARITH == "double":
        px, py = a * x + c * y + e, b * x + d * y + f
    elif FF_ARITH == "x87":
        a, b, c, d, e, f, x, y = (_f32(v) for v in (a, b, c, d, e, f, x, y))
        px, py = _f32(a * x + c * y + e), _f32(b * x + d * y + f)
    else:
        a, b, c, d, e, f, x, y = (_f32(v) for v in (a, b, c, d, e, f, x, y))
        px = _f32(_f32(_f32(a * x) + _f32(c * y)) + e)
        py = _f32(_f32(_f32(b * x) + _f32(d * y)) + f)
    rx = round(1024 * px if FF_ARITH == "double" else _f32(1024 * px)) / 1024   # rint: ties to even
    ry = round(1024 * py if FF_ARITH == "double" else _f32(1024 * py)) / 1024
    return rx, ry


def transform_contour(contour, t):
    """A transform keeps each point's flags and TrueType numbering (",ttfindex,nextcp")."""
    return [(op, [_ff_point(t, x, y) for (x, y) in pts], fl) for op, pts, fl in contour]


def write_splines(contours):
    out = []
    for ct in contours:
        for op, pts, fl in ct:
            coords = " ".join("%s %s" % (fmt(x), fmt(y)) for x, y in pts)
            out.append(("%s %s %s" % (coords, op, fl)) if op == "m" else (" %s %s %s" % (coords, op, fl)))
    return "\n".join(out) + ("\n" if out else "")


def pastepsglyphs(text, pfa, names):
    """build.py deobliqize(): copy these glyphs from the PFA and paste them into the font
    (FontForge's paste replaces the outline and the width; the slot is the name's)."""
    t1, glyphs = ps_glyphs(pfa, target_is_quadratic(text))
    by = {g["name"]: g for g in glyphs}
    have = {g["name"]: g for g in glyph_info(text)}
    done = []
    for name in names:
        g = by.get(name)
        if g is None:
            raise OpError("%s not in %s" % (name, pfa))
        if g["comps"]:
            raise OpError("%s is a seac composite; not modelled" % name)
        width = t1_width(t1, name)
        ss = "SplineSet\n" + "\n".join(g["splines"]) + "\nEndSplineSet\n"
        if name in have:
            m = have[name]["match"]
            body = m.group(0)
            body = re.sub(r"^SplineSet\n.*?^EndSplineSet\n", lambda _m: ss, body, count=1, flags=re.M | re.S)
            body = re.sub(r"^Width: .*$", "Width: %s" % fmt(width), body, count=1, flags=re.M)
            body = re.sub(r"^Refer: .*\n", "", body, flags=re.M)
            text = text[:m.start()] + body + text[m.end():]
            have = {x["name"]: x for x in glyph_info(text)}
            done.append(name + "(replaced)")
        else:
            info = glyph_info(text)
            gid = max(x["gid"] for x in info) + 1
            uni = uni_from_name(name)
            block = ("StartChar: %s\nEncoding: %d %d %d\nWidth: %s\nFlags: W\nLayerCount: 2\nFore\n%sEndChar\n\n"
                     % (name, uni, uni, gid, fmt(width), ss))
            text = insert_before_endchars(text, block)
            text = bump_beginchars(text, max(x["slot"] for x in info) + 1, gid + 1)
            have = {x["name"]: x for x in glyph_info(text)}
            done.append(name + "(created)")
    return text, " ".join(done)


def run(text, op, args):
    if op == "mergefea":
        return mergefea(text, args[0])
    if op == "mergepsfont":
        if len(args) == 3:
            return mergepsfont(text, args[0], args[1], args[2])
        return mergepsfont(text, args[0], None, args[1])
    if op == "appendcopyright":
        return appendcopyright(text, " ".join(args).encode().decode("unicode_escape"))
    if op == "ffnotdef":
        return ffnotdef(text)
    if op == "obliqize":
        global FF_ARITH
        if len(args) > 3:
            FF_ARITH = args[3]
        return unlink_and_skew(text, float(args[0]), int(args[1], 16), int(args[2], 16))
    if op == "pastepsglyphs":
        return pastepsglyphs(text, args[0], args[1:])
    raise OpError("unknown op %s" % op)


def main(argv):
    src, dst = argv[0], argv[1]
    rest = argv[2:]
    ops, cur = [], []
    for a in rest:
        if a == "--":
            ops.append(cur)
            cur = []
        else:
            cur.append(a)
    if cur:
        ops.append(cur)
    text = open(src, encoding="utf-8", errors="surrogateescape").read()
    for op in ops:
        text, what = run(text, op[0], op[1:])
        print("%s: %s" % (op[0], what))
    open(dst, "w", encoding="utf-8", errors="surrogateescape").write(text)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except OpError as e:
        sys.exit("FATAL: %s" % e)
