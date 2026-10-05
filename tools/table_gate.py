#!/usr/bin/env python3
"""Gate the diffenator3 `tables` and `cmap_diff` sections, which our harness ignored.

Why this exists. Our gate ran

    diffenator3 -J 1 --no-languages --no-match --json --succinct <shipped> <built>

and read only `locations[].glyphs` and `locations[].words`. diffenator3's `--tables`
mode is ON BY DEFAULT and its JSON carries a `tables` section that, on the very builds
we passed, reported `post.underline_thickness [82, 50]`,
`OS/2.y_strikeout_size [102, 50]`, the sub/superscript fields and the `mu -> uni03BC`
cmap rename. The tool detected every table-level converter defect in this programme;
the harness threw the section away. (Measured 2026-09-17 on googlefonts/abel.)

This module splits those differences into:
  ACCEPTED   build-convention differences this project has decided and discloses
             (including a glyph taking its production name for its own codepoint)
             (OS/2 version, recomputed ranges, production glyph names, dropped Mac
             name records, hinting-derived tables, build timestamps...)
  BLOCKING   anything that is a design or metric datum: outlines, advances, kerning,
             layout, and the OS/2 and post fields that describe the typeface
Anything unrecognised is BLOCKING by default -- a new defect must fail, not pass.

Usage: table_gate.py <diffenator3.json> [--accept=OS/2.sx_height,post.foo]
       [--exceptions documented_exceptions.tsv --family <fam> --style <style>]
         -> prints BLOCKING rows, exit 1 if any
Usage: table_gate.py <diffenator3.json> --fonts <shipped.ttf> <built.ttf>
         -> as above, but a left-side-bearing difference where the SHIPPED font
            contradicts its own outline and ours does not is reported as
            RELEASE-STALE rather than blocking
       import: blocking(json_dict, accept=()) -> list[str]
--accept names a difference this family has DOCUMENTED in its pull request (for
example an x-height measured from the outlines because the release left the field
unset). It is not a way to quieten an unexplained difference.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _best_cmap(font):
    """`font.getBestCmap()` returns None, not {}, when a font has no usable cmap.

    Iterating that raised TypeError deep inside an arbitration, the whole gate died,
    and a harness counting `^BLOCKING ` lines read the empty output as a clean pass.
    That is how a 988-byte Corben-Bold.ttf carrying ONE glyph and no cmap was recorded
    as reproducing its release. A broken font must produce findings, not silence.
    """
    try:
        return font.getBestCmap() or {}
    except Exception:
        return {}


def _self_consistent_lsbs(path):
    """-> {glyph: (recorded_lsb, outline_xmin)} for every glyph with contours.

    A font's hmtx left side bearing is supposed to equal the xMin of the glyph it
    describes. Comparing each font against ITS OWN outlines says which of the two is
    keeping correct books, which is a different question from whether they agree with
    each other -- and the one that matters, because a release can be wrong."""
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    out = {}
    for name in font.getGlyphOrder():
        try:
            coords = glyf[name].getCoordinates(glyf)[0]
        except Exception:
            continue
        if not len(coords):
            # A glyph with no contours has no left side bearing to be right or wrong
            # about. Fonts record whatever they like -- the releases here carry the
            # 32767 sentinel where our builds carry 0 -- and neither is a difference
            # in the font.
            out[name] = (None, None)
            continue
        try:
            # A composite's resolved coordinates come back fractional -- a component
            # scale is stored as F2Dot14 and applied in floating point, so a mirrored
            # glyph lands on 68.09619140625 rather than 68. The bearing a font records
            # is an integer, so compare on the rounded value or the test never fires.
            out[name] = (hmtx[name][1], round(min(x for x, _ in coords)))
        except Exception:
            continue
    return out


def _layout_is_empty(path, tag):
    """-> True when the font has this layout table and it does nothing at all, None
    when it has no such table, False when the table carries lookups or features."""
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    if tag not in font:
        return None
    table = font[tag].table
    lookups = len(table.LookupList.Lookup) if table.LookupList else 0
    features = len(table.FeatureList.FeatureRecord) if table.FeatureList else 0
    return lookups == 0 and features == 0


def arbitrate_blank_vendor(rows, shipped, built):
    """An OS/2 vendor ID row where the RELEASE NAMES NO VENDOR.

    achVendID is four bytes and the convention is to pad a shorter tag with spaces, but
    the FontForge-era releases in this programme pad with NUL instead. That makes two
    classes, and a space-only strip catches neither:

      * the release names NO vendor -- four NULs, or four spaces -- while fontc writes
        its placeholder "NONE" for a source that declares none. Injecting the blank does
        not help: fontc treats an all-space value as unset and writes NONE anyway.
      * the release names the SAME vendor as ours and pads it differently: `LTT\0`
        against `LTT `, `TT\0\0` against `TT  `.

    Narrow on purpose. Where the release carries a tag we did not reproduce, that is a
    tag we lost, and it still blocks.

    -> (blocking, benign)"""
    block, benign = [], []
    vendors = {}
    for row in rows:
        if not row.startswith("OS/2.ach_vend_id"):
            block.append(row)
            continue
        if not vendors:
            from fontTools.ttLib import TTFont

            try:
                for tag, path in (("ship", shipped), ("ours", built)):
                    vendors[tag] = TTFont(path)["OS/2"].achVendID
            except Exception:
                block.append(row)
                continue
        ship = (vendors.get("ship") or "").strip("\x00 \t")
        ours = (vendors.get("ours") or "").strip("\x00 \t")
        if ship and ship == ours:
            benign.append("OS/2.ach_vend_id -- both name the vendor %r; the release pads "
                          "it with NUL (%r) and ours with spaces (%r)"
                          % (ship, vendors.get("ship"), vendors.get("ours")))
        elif not ship and ours in ("NONE", "", None):
            benign.append("OS/2.ach_vend_id -- the release names no vendor (%r) and ours "
                          "carries the compiler's placeholder %r"
                          % (vendors.get("ship"), vendors.get("ours")))
        else:
            block.append(row)
    return block, benign


# The two glyphs FontForge adds when it generates a TrueType font, for a Mac
# requirement no current consumer enforces. Neither has contours and neither is
# reachable from a modern cmap subtable.
_FONTFORGE_PADDING = {".null", "nonmarkingreturn", "NULL", "CR"}


def _mentioned_in_layout(font, names):
    """Which of `names` any lookup or composite in this font refers to.

    Read from the compiled tables' own XML rather than by walking otTables by hand: a
    glyph name can appear in a coverage, a class definition, a ligature component, an
    alternate set, a chain context's backtrack or a composite's component, and missing
    one of those would make an unreferenced-glyph claim wrong in the unsafe direction.
    """
    import io

    from fontTools.misc.xmlWriter import XMLWriter
    if not names:
        return set()
    text = []
    for tag in ('GSUB', 'GPOS'):
        if tag not in font:
            continue
        buf = io.StringIO()
        writer = XMLWriter(buf)
        try:
            font[tag].toXML(writer, font)
        except Exception:
            return set(names)          # cannot tell -> assume every name is referenced
        text.append(buf.getvalue())
    blob = '\n'.join(text)
    used = {n for n in names if ('"%s"' % n) in blob}
    if 'glyf' in font:
        glyf = font['glyf']
        for gname in glyf.keys():
            glyph = glyf[gname]
            for comp in getattr(glyph, 'components', None) or ():
                if comp.glyphName in names:
                    used.add(comp.glyphName)
    return used


def _explain_extra(font, other, names, other_path, font_path):
    """Explain each glyph `font` has that `other` does not. -> (explained, unexplained)

    Two explanations, both checked against the fonts:

      * unreferenced padding -- no contours, no codepoint, and no lookup or composite
        mentions it. FontForge writes `.null` and `nonmarkingreturn` when it generates
        a TrueType font, and a glyph like that cannot reach the raster.
      * a duplicate -- the glyph is mapped, and at every codepoint it is mapped at, the
        other font resolves to a glyph with the same outline and the same advance. The
        release synthesising a blank `nbsp` beside `space` is this: the character
        renders, from a glyph the other font already had.
      * an addition -- the glyph is mapped ONLY at codepoints the other font does not
        encode at all. Nothing the other font renders changes; a character that was
        .notdef there is drawn here. This is the same class the cmap gate already
        accepts as GAINED, and it is accepted here for the same reason: a codepoint
        gained is not a codepoint lost.
    """
    import outline_match

    explained, unexplained = {}, {}
    cmap = _best_cmap(font)
    other_cmap = _best_cmap(other)
    mapped_at = {}
    for cp, n in cmap.items():
        mapped_at.setdefault(n, []).append(cp)
    referenced = _mentioned_in_layout(font, names)
    for n in sorted(names):
        if n == '.ttfautohint':
            # ttfautohint stores its version string in a dummy glyph. It exists only
            # because the release was hinted, and this pipeline builds unhinted, which
            # is why ACCEPTED already passes prep, fpgm and cvt. 3 of the 100 merged
            # releases carry it.
            explained[n] = "ttfautohint's version-string glyph, from hinting this "
            explained[n] += "build does not apply"
            continue
        cps = mapped_at.get(n, [])
        if not cps and n not in referenced:
            # No codepoint reaches it and no lookup or composite mentions it, so
            # nothing can put it on the page. That holds whether or not it has an
            # outline: elsie's release carries a two-contour `T_h` and our build a
            # two-contour `f2`, and neither font can render its own.
            #
            # _mentioned_in_layout errs towards saying "referenced" -- it matches the
            # quoted name anywhere in the compiled GSUB/GPOS -- so the failure mode is
            # a glyph left blocking that could have been explained, not the reverse.
            contours = outline_match.contours_of(font, n) or []
            explained[n] = ('unreachable: no codepoint, and no lookup or composite '
                            'mentions it (%d contour(s))' % len(contours))
            continue
        if cps and all(cp in other_cmap and _same_glyph(other_path, font_path, cp)
                       for cp in cps):
            explained[n] = ('a duplicate: %s renders from a glyph with the same outline '
                            'and advance in the other font'
                            % ', '.join('U+%04X' % c for c in cps))
            continue
        if cps and not any(cp in other_cmap for cp in cps):
            explained[n] = ('an addition at %s, which the other font does not encode'
                            % ', '.join('U+%04X' % c for c in cps))
            continue
        unexplained[n] = ('%d contour(s), %s'
                          % (len(outline_match.contours_of(font, n) or []),
                             'at ' + ', '.join('U+%04X' % c for c in cps) if cps
                             else 'unmapped, referenced by a lookup'
                             if n in referenced else 'unmapped'))
    return explained, unexplained


def _pair_renames(ship_bad, our_bad, shipped, built):
    """Match unexplained glyphs across the two fonts by DRAWING, not by name.

    `_explain_extra` works one font at a time, so a glyph each font has under a
    different name lands in both unexplained sets and the row blocks as though a glyph
    were lost. Nothing is lost: it is one glyph with two names.

    abrilfatface is the case. The release carries `idotaccent`, our build carries
    `i.loclTRK`, both unmapped and both reached only through a lookup -- and they are
    the same drawing, to the unit: bbox (6, 0, 307, 731) and area 122407 on each side.

    Pairing uses the bounds `_same_geometry` already uses -- identical advance, every
    bounding-box edge within 2 units, relative area within 0.1% -- and is one-to-one,
    so two different glyphs cannot both claim the same partner.

    -> (pairs, ship_left, our_left)"""
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.boundsPen import BoundsPen

    def shape(path, name):
        font = _cached_font(path)
        glyphs = font.getGlyphSet()
        bp = BoundsPen(glyphs)
        try:
            glyphs[name].draw(bp)
            return (font["hmtx"][name][0], bp.bounds,
                    _abs_contour_area(glyphs, name))
        except Exception:
            return None

    pairs = []
    ship_left, our_left = dict(ship_bad), dict(our_bad)
    for s_name in sorted(ship_bad):
        a = shape(shipped, s_name)
        if a is None or a[1] is None:
            continue
        for o_name in sorted(our_left):
            b = shape(built, o_name)
            if b is None or b[1] is None:
                continue
            if a[0] != b[0]:
                continue
            if max(abs(x - y) for x, y in zip(a[1], b[1])) > _GEOM_BBOX_TOL:
                continue
            if abs(a[2] - b[2]) / max(a[2], b[2], 1.0) > _GEOM_AREA_TOL:
                continue
            pairs.append((s_name, o_name))
            ship_left.pop(s_name, None)
            our_left.pop(o_name, None)
            break
    return pairs, ship_left, our_left


def arbitrate_glyph_count(rows, shipped, built):
    """A `post.num_glyphs` row where every glyph in dispute is accounted for.

    The row is a COUNT, and a count says nothing about which glyphs moved. So rather
    than accept a count, this explains each glyph one font has and the other does not,
    and accepts the row only when every one of them is explained: FontForge's
    unreferenced TrueType padding, or a duplicate of a glyph the other font already has
    at the same codepoints with the same outline and advance.

    post.num_glyphs is also the row a genuinely lost glyph arrives on, which is the
    whole reason to look, so anything unexplained blocks and is named.

    -> (blocking, benign)"""
    if not any(row.startswith("post.num_glyphs") for row in rows):
        return rows, []
    from fontTools.ttLib import TTFont

    try:
        ship_font, our_font = _cached_font(shipped), _cached_font(built)
        ship = set(ship_font.getGlyphOrder())
        ours = set(our_font.getGlyphOrder())
    except Exception:
        return rows, []
    ship_ok, ship_bad = _explain_extra(ship_font, our_font, ship - ours, built, shipped)
    our_ok, our_bad = _explain_extra(our_font, ship_font, ours - ship, shipped, built)
    renamed, ship_bad, our_bad = _pair_renames(ship_bad, our_bad, shipped, built)
    block, benign = [], []
    for row in rows:
        if not row.startswith("post.num_glyphs"):
            block.append(row)
            continue
        if ship_bad or our_bad:
            parts = []
            if ship_bad:
                parts.append("the release has %s" % "; ".join(
                    "%s (%s)" % (k, v) for k, v in sorted(ship_bad.items())[:4]))
            if our_bad:
                parts.append("we add %s" % "; ".join(
                    "%s (%s)" % (k, v) for k, v in sorted(our_bad.items())[:4]))
            block.append("post.num_glyphs -- %s" % "; and ".join(parts))
        elif not ship_ok and not our_ok and not renamed:
            benign.append("post.num_glyphs -- both fonts carry the same glyphs by name")
        elif renamed and not ship_ok and not our_ok:
            benign.append("post.num_glyphs -- %d glyph(s) renamed, same drawing on both "
                          "sides: %s" % (len(renamed), ", ".join(
                              "%s -> %s" % pair for pair in renamed[:4])))
        else:
            said = []
            if ship_ok:
                said.append("the release's %s" % ", ".join(
                    "%s (%s)" % (k, v) for k, v in sorted(ship_ok.items())))
            if our_ok:
                said.append("our %s" % ", ".join(
                    "%s (%s)" % (k, v) for k, v in sorted(our_ok.items())))
            if renamed:
                said.append("%d renamed (%s)" % (len(renamed), ", ".join(
                    "%s -> %s" % pair for pair in renamed[:3])))
            benign.append("post.num_glyphs -- every glyph in dispute is accounted for: %s"
                          % "; ".join(said))
    return block, benign


def arbitrate_old_os2(rows, shipped, built):
    """An sxHeight or sCapHeight row where the RELEASE'S TABLE HAS NO SUCH FIELD.

    Those two fields arrived in OS/2 version 2. Six Caps ships version 1, so the release
    reports null and any value we write differs from it -- including the right one.
    Blocking there would mean refusing to write a field because the font being
    reproduced is too old to carry it.

    Narrow: only these two fields, and only when the shipped table really is older than
    version 2. Where the release carries a version 2 table and a value, a difference
    still means we lost it.

    -> (blocking, benign)"""
    fields = ("OS/2.sx_height", "OS/2.s_cap_height")
    if not any(row.startswith(fields) for row in rows):
        return rows, []
    from fontTools.ttLib import TTFont

    try:
        version = TTFont(shipped)["OS/2"].version
    except Exception:
        return rows, []
    if version >= 2:
        return rows, []
    block, benign = [], []
    for row in rows:
        if row.startswith(fields):
            benign.append("%s -- the release ships an OS/2 version %d table, which has no "
                          "such field" % (row.split(" ", 1)[0], version))
        else:
            block.append(row)
    return block, benign


def _empty_or_absent(ship, ours):
    """One side has a GPOS with no lookups, the other has no GPOS at all."""
    pair = {ship, ours}
    return pair == {0, None}


def _nothing_to_position(*paths):
    """True when no font here has anything HarfBuzz's fallback positioning would move.

    HarfBuzz turns on its own positioning when a font has no GPOS, and that is why an
    empty GPOS in the release is not the same font as no GPOS in our build: it
    SUPPRESSES the fallback. Measured on unifrakturmaguntia, that moved 66 of 236 shaped
    cases. But the fallback only ever does two things -- zero a mark's advance and stack
    it on its base, and apply the legacy `kern` table. A font with no mark glyph and no
    `kern` gives it nothing to do, and then the presence of the empty table cannot
    change a single shaped run.

    Verified by shaping, not by reading the spec: tools/probes/gpos_empty_shell/."""
    import unicodedata

    from fontTools.ttLib import TTFont
    for path in paths:
        try:
            font = TTFont(path)
        except Exception:
            return False
        if "kern" in font:
            return False
        for cp in _best_cmap(font):
            try:
                if unicodedata.category(chr(cp)) in ("Mn", "Mc", "Me"):
                    return False
            except ValueError:
                return False
        gdef = font.get("GDEF")
        classes = getattr(getattr(gdef, "table", None), "GlyphClassDef", None)
        if classes and any(v == 3 for v in classes.classDefs.values()):
            return False
    return True


# The OS/2 and hhea fields a FontForge source states outright, and the diffenator3 row
# each one arrives on. Only the fields whose SFD key holds an absolute value are here:
# the Typo, Win and Hhead pairs carry an `*AOffset`/`*DOffset` flag, and when it is set
# the stored number is a delta rather than a value, so those are read conditionally
# below rather than listed.
_SFD_DECLARED = {
    'OS2SubXSize': ('OS/2', 'y_subscript_x_size'),
    'OS2SubYSize': ('OS/2', 'y_subscript_y_size'),
    'OS2SubXOff': ('OS/2', 'y_subscript_x_offset'),
    'OS2SubYOff': ('OS/2', 'y_subscript_y_offset'),
    'OS2SupXSize': ('OS/2', 'y_superscript_x_size'),
    'OS2SupYSize': ('OS/2', 'y_superscript_y_size'),
    'OS2SupXOff': ('OS/2', 'y_superscript_x_offset'),
    'OS2SupYOff': ('OS/2', 'y_superscript_y_offset'),
    'OS2StrikeYSize': ('OS/2', 'y_strikeout_size'),
    'OS2StrikeYPos': ('OS/2', 'y_strikeout_position'),
    'OS2TypoLinegap': ('OS/2', 's_typo_line_gap'),
}
# (SFD value key, SFD offset-flag key, table, field). The value is absolute only when
# the flag is 0; when it is 1 FontForge stored a delta from the em ascent (Typo) or the
# font bounding box (Win, Hhead), which is arithmetic this rule does not attempt.
_SFD_DECLARED_ABS = [
    ('OS2TypoAscent', 'OS2TypoAOffset', 'OS/2', 's_typo_ascender'),
    ('OS2TypoDescent', 'OS2TypoDOffset', 'OS/2', 's_typo_descender'),
    ('OS2WinAscent', 'OS2WinAOffset', 'OS/2', 'us_win_ascent'),
    ('OS2WinDescent', 'OS2WinDOffset', 'OS/2', 'us_win_descent'),
    ('HheadAscent', 'HheadAOffset', 'hhea', 'ascender'),
    ('HheadDescent', 'HheadDOffset', 'hhea', 'descender'),
]


def _source_declares(sfd):
    """-> {(table, field): value} for the metrics this .sfd states outright."""
    import re as _re
    out = {}
    try:
        text = open(sfd, encoding='utf-8', errors='replace').read(400000)
    except OSError:
        return out
    raw = dict(_re.findall(r'^([A-Za-z0-9]+):\s*(-?\d+)\s*$', text, _re.M))
    for key, (table, field) in _SFD_DECLARED.items():
        if key in raw:
            out[(table, field)] = int(raw[key])
    for key, flag, table, field in _SFD_DECLARED_ABS:
        if key in raw and raw.get(flag) == '0':
            out[(table, field)] = int(raw[key])
    # A Typo value stored in offset mode is a delta from the master's own ascender or
    # descender, which the .sfd states as `Ascent:` and `Descent:`. babelfont computes
    # the same base (convertors/fontforge/offsetmetrics.rs), so the absolute value is
    # recoverable here; the Win and Hhead pairs take the font bounding box as their base
    # and are left alone.
    if 'Ascent' in raw and raw.get('OS2TypoAOffset') == '1' and 'OS2TypoAscent' in raw:
        out[('OS/2', 's_typo_ascender')] = int(raw['Ascent']) + int(raw['OS2TypoAscent'])
    if 'Descent' in raw and raw.get('OS2TypoDOffset') == '1' and 'OS2TypoDescent' in raw:
        out[('OS/2', 's_typo_descender')] = -int(raw['Descent']) + int(raw['OS2TypoDescent'])
    return out


def _source_panose(sfd):
    """The ten PANOSE digits a .sfd states, as {byte index: value}.

    diffenator3 reports this field as a dict keyed by byte index rather than as a
    scalar pair, so it needs its own reader and its own comparison.
    """
    import re as _re
    try:
        text = open(sfd, encoding='utf-8', errors='replace').read(400000)
    except OSError:
        return {}
    m = _re.search(r'^Panose:\s*((?:-?\d+\s+){9}-?\d+)\s*$', text, _re.M)
    if not m:
        return {}
    return {i: int(v) for i, v in enumerate(m.group(1).split())}


def _source_advances(sfd):
    """-> {glyph name: advance} for every glyph the .sfd gives a Width."""
    import re as _re
    out = {}
    try:
        text = open(sfd, encoding='utf-8', errors='replace').read()
    except OSError:
        return out
    for name, width in _re.findall(
            r'^StartChar:\s*(.+?)\s*$.*?^Width:\s*(-?\d+)\s*$', text,
            _re.M | _re.S | _re.DOTALL):
        out.setdefault(name.strip().strip('"'), int(width))
    return out


# (SFD value key, SFD offset-flag key, table, field, which bbox extreme is the base).
# babelfont computes these the same way in convertors/fontforge/offsetmetrics.rs.
_SFD_BBOX_OFFSET = [
    ('OS2WinAscent', 'OS2WinAOffset', 'OS/2', 'us_win_ascent', 'ymax'),
    ('HheadAscent', 'HheadAOffset', 'hhea', 'ascender', 'ymax'),
    ('OS2WinDescent', 'OS2WinDOffset', 'OS/2', 'us_win_descent', '-ymin'),
    ('HheadDescent', 'HheadDOffset', 'hhea', 'descender', 'ymin'),
]


def _bbox_declared(sfd, shipped, built):
    """The Win and Hhead metrics a source states as a delta from the font bounding box.

    Their base is not in the .sfd, it is the outlines' own extreme, so the value is only
    recoverable when the two binaries AGREE about that extreme -- and then it is the
    same number for both and the source's delta decides the rest. Where the two bounding
    boxes differ the rule says nothing, which is the safe direction: a metric derived
    from an outline that moved is an outline question.

    cantataone is the case it exists for: both fonts have yMax 2040, the source states
    `OS2WinAscent: -40` in offset mode, 2040 - 40 = 2000, and our build carries 2000
    while the release carries 2040 -- the release did not apply its own delta."""
    import re as _re
    out = {}
    try:
        text = open(sfd, encoding='utf-8', errors='replace').read(400000)
    except OSError:
        return out
    raw = dict(_re.findall(r'^([A-Za-z0-9]+):\s*(-?\d+)\s*$', text, _re.M))
    try:
        a, b = _cached_font(shipped)['head'], _cached_font(built)['head']
    except Exception:
        return out
    if (a.yMax, a.yMin) != (b.yMax, b.yMin):
        return out
    base = {'ymax': a.yMax, 'ymin': a.yMin, '-ymin': -a.yMin}
    for key, flag, table, field, which in _SFD_BBOX_OFFSET:
        if key in raw and raw.get(flag) == '1':
            out[(table, field)] = base[which] + int(raw[key])
    return out


# A value no font should carry, whatever its source says. A descender below the
# baseline is negative and an ascender above it is positive; concertone's source states
# `HheadDescent: 810` in offset mode over a yMin of -400, which is +410, and a positive
# hhea descender is not a metric, it is a defect. "The source says so" is a reason to
# absolve the CONVERSION, never a reason to ship the value.
_SIGN = {('OS/2', 's_typo_ascender'): 1, ('hhea', 'ascender'): 1,
         ('OS/2', 's_typo_descender'): -1, ('hhea', 'descender'): -1}


def _impossible(table, field, value):
    sign = _SIGN.get((table, field))
    return sign is not None and value != 0 and (value > 0) != (sign > 0)


def arbitrate_source_declared(rows, shipped, built, sfd):
    """A row where OUR value is the one the source states and the release's is not.

    FontForge writes these fields into the .sfd explicitly -- `OS2SubXSize: 650`,
    `OS2TypoAscent: 951` with its offset flag clear. Where our build carries the stated
    value and the release carries something else, the release is not what this source
    says, and holding the conversion until it reproduces that would mean reproducing a
    departure from the source on purpose.

    Strictly one-directional. If the release matches the source and we do not, that is
    ours and it blocks; so does a field the source never states.

    -> (blocking, release_stale)"""
    if not sfd:
        return rows, []
    declared = _source_declares(sfd)
    declared.update(_bbox_declared(sfd, shipped, built))
    advances = _source_advances(sfd)
    panose = _source_panose(sfd)
    if not declared and not advances and not panose:
        return rows, []
    block, stale = [], []
    for row in rows:
        head = row.split(' ', 1)[0]
        if head == 'OS/2.panose_10' and panose:
            # Reported as {byte index: [release, ours]}. Accept only when EVERY byte in
            # dispute is one where our build carries the digit the source states.
            # coveredbyyourgrace's source says `Panose: 2 0 0 0 0 0 0 0 0 0` and the
            # release carries 0 in byte 0 where we carry 2.
            try:
                per_byte = json.loads(row[len(head):].strip())
            except ValueError:
                per_byte = None
            if isinstance(per_byte, dict) and per_byte and all(
                    isinstance(v, list) and len(v) == 2
                    and panose.get(int(k)) == v[1] and v[0] != v[1]
                    for k, v in per_byte.items()):
                stale.append('%s -- the source states PANOSE byte(s) %s; ours carries '
                             'them and the release does not'
                             % (head, ', '.join('%s=%s' % (k, panose.get(int(k)))
                                                for k in sorted(per_byte))))
                continue
        if head.startswith('hmtx.') and '"width"' in row:
            # The recipe converts with --keep-source-advances, so our advance IS the
            # one the .sfd states. Where the release carries a different one it is the
            # release that departed from the source -- the whitespace normalisation
            # that gave several releases `space`'s advance for the no-break space,
            # which tools/probes/snowburstone/source_vs_release.py found is not
            # reproducible from any export rule.
            want = advances.get(head[len('hmtx.'):])
            try:
                pair = (json.loads(row[len(head):].strip()) or {}).get('width')
            except ValueError:
                pair = None
            if (want is not None and isinstance(pair, list) and len(pair) == 2
                    and pair[1] == want and pair[0] != want):
                stale.append('%s -- the source states an advance of %s; ours carries it '
                             'and the release carries %s' % (head, want, pair[0]))
                continue
        if '.' not in head:
            block.append(row)
            continue
        table, field = head.rsplit('.', 1)
        want = declared.get((table, field))
        if want is None:
            block.append(row)
            continue
        try:
            pair = json.loads(row[len(head):].strip())
        except ValueError:
            block.append(row)
            continue
        if not (isinstance(pair, list) and len(pair) == 2):
            block.append(row)
            continue
        ship, ours = pair
        if ours == want and ship != want and not _impossible(table, field, ours):
            stale.append('%s -- the source states %s; ours carries it and the release '
                         'carries %s' % (head, want, ship))
        else:
            block.append(row)
    return block, stale


def arbitrate_post_version(rows, shipped, built):
    """A `post.version` row where the release is 3.0 and our build is 2.0.

    Format 3 stores no glyph names; format 2 stores them. Both are acceptable for a TTF
    (fontspector's opentype/post_table_version: "Acceptable post format versions are 2
    and 3 for TTF"), nothing about rendering depends on which, and ours carries names
    the release discarded rather than losing any.

    This is also where benchnine's thirteen cmap "renames" come from: the release has no
    names, so diffenator3 synthesises `uni0122` from the codepoint and compares it with
    the `Gcommaaccent` our source states. No renaming step ever ran.

    The other direction -- the release naming its glyphs and our build dropping them --
    is a loss and still blocks.

    -> (blocking, benign)"""
    block, benign = [], []
    for row in rows:
        if not row.startswith('post.version'):
            block.append(row)
            continue
        try:
            pair = json.loads(row[len('post.version'):].strip())
        except ValueError:
            pair = None
        if (isinstance(pair, list) and len(pair) == 2
                and str(pair[0]).startswith('3.') and str(pair[1]).startswith('2.')):
            benign.append('post.version -- the release is format %s and stores no glyph '
                          'names; ours is format %s and stores the ones the source '
                          'states. Both are valid for a TTF.' % (pair[0], pair[1]))
        else:
            block.append(row)
    return block, benign


def arbitrate_gpos(rows, shipped, built):
    """Separate a legacy kern modernised into GPOS from a GPOS that is not there.

    Both sides carrying real positioning lookups is the modernisation case: the shapes
    move the same way, the table is just organised differently. One side having no GPOS
    at all is not -- HarfBuzz asks whether the table exists, not whether it does
    anything, and turns its own fallback mark positioning on when it does not.

    -> (blocking, benign)"""
    block, benign = [], []
    state = {}
    for row in rows:
        if not row.startswith("GPOS."):
            block.append(row)
            continue
        if not state:
            from fontTools.ttLib import TTFont

            for tag, path in (("ship", shipped), ("ours", built)):
                try:
                    font = TTFont(path)
                    if "GPOS" not in font:
                        state[tag] = None
                    else:
                        t = font["GPOS"].table
                        state[tag] = len(t.LookupList.Lookup) if t.LookupList else 0
                except Exception:
                    state[tag] = "?"
        ship, ours = state.get("ship"), state.get("ours")
        if _nothing_to_position(shipped, built) and _empty_or_absent(ship, ours):
            benign.append("%s -- one font carries an empty GPOS and the other none, and "
                          "neither font has a mark glyph or a legacy kern table, so "
                          "HarfBuzz's fallback positioning has nothing to act on"
                          % row.split(" ", 1)[0])
        elif isinstance(ship, int) and isinstance(ours, int) and ship and ours:
            benign.append("%s -- both fonts position with real lookups (%d and %d); the "
                          "table is organised differently, which is what a legacy kern "
                          "modernised into GPOS looks like"
                          % (row.split(" ", 1)[0], ship, ours))
        else:
            block.append(row)
    return block, benign


def arbitrate_empty_layout(rows, shipped, built):
    """Reclassify a GSUB difference where one side carries an empty shell of a table
    and the other omits it.

    GPOS IS DELIBERATELY EXCLUDED, and the first version of this rule was wrong to
    include it. HarfBuzz gates its positioning stage on hb_ot_layout_has_positioning(),
    which asks whether the TABLE IS PRESENT, not whether it holds a lookup. A font with
    an empty GPOS therefore suppresses HarfBuzz's own fallback mark positioning while a
    font with no GPOS gets it, so the two do not behave the same and waving the pair
    through would hide a real difference in where marks land.

    ShortStack ships a GSUB with a latn/dflt script entry, no features and no lookups.
    Our build omits the table. A font with no GSUB and a font with a GSUB that does
    nothing shape identically, so this is a difference in structure with no difference
    in behaviour -- and holding a conversion for it would be asking the compiler to
    emit a table it has nothing to put in.

    Anything where either side has a lookup or a feature is left blocking.

    -> (blocking, benign)"""
    block, benign = [], []
    cache = {}
    for row in rows:
        tag = row.split(".", 1)[0]
        if tag != "GSUB":
            block.append(row)
            continue
        try:
            for path in (shipped, built):
                if (path, tag) not in cache:
                    cache[(path, tag)] = _layout_is_empty(path, tag)
        except Exception:
            block.append(row)
            continue
        ship, ours = cache[(shipped, tag)], cache[(built, tag)]
        empty_or_absent = {True, None}
        if ship in empty_or_absent and ours in empty_or_absent and ship != ours:
            benign.append("%s -- one side has an empty %s, the other has none; "
                          "neither does anything" % (row.split(" ", 1)[0], tag))
        else:
            block.append(row)
    return block, benign


# diffenator3 keys its hmtx diff by glyph name, and when it has no name to hand it
# formats the glyph id instead: fontations spells a GlyphId `GID_0` and diffenator3
# prefixes `gid`, so glyph 0 arrives as `gidGID_0`. Such a row used to fall through
# to BLOCKING without ever being arbitrated -- pompiere's .notdef was reported as a
# blocking metric while its 80 named siblings were reclassified. Resolve the
# placeholder to the name at that glyph index, and only when both fonts agree on it.
_GID_PLACEHOLDER = re.compile(r"^gid(?:GID_)?(\d+)$")


def _resolve_placeholder(name, shipped_order, built_order):
    m = _GID_PLACEHOLDER.match(name)
    if not m:
        return name
    i = int(m.group(1))
    if i >= len(shipped_order) or i >= len(built_order):
        return name
    if shipped_order[i] != built_order[i]:
        return name          # the two fonts disagree about this slot; do not guess
    return shipped_order[i]


def expand_overflow(rows, shipped, built):
    """diffenator3 prints `"error": "There are N changes, check manually!"` in place of a
    table section it will not enumerate, and the gate read `error` as a glyph name.

    Arbitration then looked `error` up in both glyph orders, failed, and blocked -- so
    177 bearings on creepstercaps and 163 on unifrakturmaguntia were never examined, and
    the row said nothing about what they were. Where the fonts are available the section
    can simply be recomputed: every glyph both fonts carry, compared on the bearing each
    records against its own outline.

    -> (rows with the sentinel replaced by what it was hiding)"""
    out = []
    for row in rows:
        if not (row.startswith("hmtx.error") and "changes" in row):
            out.append(row)
            continue
        try:
            ship = _self_consistent_lsbs(shipped)
            ours = _self_consistent_lsbs(built)
        except Exception:
            out.append(row)
            continue
        # Four cases, not two. The earlier two-way split sent everything that was not
        # provably the release's fault down the `mine` branch, including the case where
        # BOTH fonts agree with their own outlines -- and then said our bearings
        # disagreed with our own outlines, which is precisely what that case rules out.
        # patrickhandsc reported `hmtx.10 bearings disagree with our own outlines` while
        # both fonts were self-consistent on every glyph
        # (tools/probes/hmtx_both_self_consistent/).
        theirs = mine = unsourced = 0
        outline_led = []
        for name, (s_lsb, s_xmin) in ship.items():
            if name not in ours or s_xmin is None:
                continue
            o_lsb, o_xmin = ours[name]
            if o_xmin is None or s_lsb == o_lsb:
                continue
            ours_ok, theirs_ok = o_lsb == o_xmin, s_lsb == s_xmin
            if ours_ok and not theirs_ok:
                theirs += 1
            elif theirs_ok and not ours_ok:
                mine += 1
            elif ours_ok and theirs_ok:
                # Neither font is keeping wrong books, so the bearing is not itself the
                # defect: it restates a difference in the outline it measures. Still a
                # real difference, so still blocking -- but named for what it is, so the
                # next step looks at the outline rather than the bearing.
                outline_led.append((name, s_lsb, o_lsb))
            else:
                unsourced += 1
        if mine:
            out.append("hmtx.%d bearings disagree with our own outlines "
                       "(and %d with the release's)" % (mine, theirs))
        if outline_led:
            worst = max(outline_led, key=lambda r: abs(r[2] - r[1]))
            out.append("hmtx.%d bearings differ though both fonts agree with their own "
                       "outlines -- the outlines differ, widest %d unit(s) at %s "
                       "(release %d, ours %d)"
                       % (len(outline_led), abs(worst[2] - worst[1]),
                          worst[0], worst[1], worst[2]))
        if unsourced:
            out.append("hmtx.%d bearings where neither font agrees with its own outline"
                       % unsourced)
        if theirs and not (mine or outline_led or unsourced):
            out.append("__STALE__%d bearings, every one the release contradicting its "
                       "own outline" % theirs)
        # nothing to say when neither side disagrees with itself
    return out


def expand_cmap_overflow(rows, shipped, built):
    """diffenator3 replaces a large cmap section with `cmap error "There are N changes,
    check manually!"`, exactly as it does for hmtx. `expand_overflow` recomputes the
    hmtx case; nothing recomputed this one, so the row reached the gate as an opaque
    count and blocked.

    That matters because the arbitration which would have handled it -- and which is
    already written -- never sees a row to act on. `arbitrate_cmap_names` accepts a
    codepoint whose glyph merely changed NAME, verified by comparing the outline and
    advance the codepoint resolves to in each font. Those renames are most of what
    these sentinels are hiding: comicrelief reported 132 "changes" across two fonts
    whose cmaps encode the same codepoints throughout.

    Recomputes the per-codepoint comparison from the fonts and emits the ordinary
    `cmap U+XXXX [...]` rows the rest of the gate already understands. A codepoint
    present in one font only is emitted as such and stays blocking.

    -> (rows with the sentinel replaced by what it was hiding)
    """
    out = []
    for row in rows:
        if not (row.startswith("cmap error") and "changes" in row):
            out.append(row)
            continue
        try:
            s_cmap = _best_cmap(_cached_font(shipped))
            b_cmap = _best_cmap(_cached_font(built))
        except Exception:
            out.append(row)
            continue
        # A font with no usable cmap returns None, not {}. Iterating that raised
        # TypeError, the whole gate died, and a harness counting `^BLOCKING ` lines
        # read the empty output as a clean pass -- which is how a 988-byte
        # Corben-Bold.ttf carrying ONE glyph was recorded as reproducing its release.
        if s_cmap is None or b_cmap is None:
            out.append("cmap -- %s font has no usable cmap"
                       % ("the release's" if s_cmap is None else "our"))
            continue
        expanded = []
        for cp in sorted(set(s_cmap) | set(b_cmap)):
            old_n, new_n = s_cmap.get(cp), b_cmap.get(cp)
            if old_n == new_n:
                continue
            key = "U+%04X" % cp
            if new_n is None:
                expanded.append("cmap %s LOST %s" % (key, json.dumps([old_n, None])))
            elif old_n is None:
                continue          # a codepoint GAINED: the accepted duplicate-cmap class
            elif is_production_name(new_n, cp):
                continue          # the accepted rename class, as cmap_blocking has it
            else:
                expanded.append("cmap %s %s" % (key, json.dumps([old_n, new_n])))
        out.extend(expanded)
    return out


def arbitrate_gsub_lookup_order(rows, shipped, built):
    """Reclassify GSUB list rows when both fonts carry the SAME lookups in a
    different order and no text shapes differently.

    kristi is the case: release and build both have five `calt` lookups with
    identical entry counts -- four single substitutions and one chaining context --
    but the release lists the chaining lookup first and ours lists it last. A
    chaining lookup calls the others by index, so the order is not obviously
    cosmetic and cannot be waved through on structure.

    Three conditions, all required:
      1. both fonts have GSUB, with the same feature tags;
      2. the same multiset of (lookup type, entry count), so it really is a
         reordering and not a different set of lookups -- or, failing that, the
         same rules once single-member AlternateSets are folded into single
         substitutions (see below);
      3. a shaped corpus comes out identical -- AND the features demonstrably fire
         somewhere in that corpus, because a corpus that never triggers a
         substitution would pass this test while proving nothing.

    Measured on kristi: 28,296 runs identical, with calt firing on T-, TA and TO.
    (sfd-batch6/tools/probes/gsub_lookup_order/)

    **Single-member AlternateSets.** An `AlternateSubst` entry offering exactly one
    alternate expresses the same substitution as a `SingleSubst` mapping; which of
    the two a compiler emits is its own choice. patrickhand is the case: release and
    build carry the same 212 `aalt` entries, but the release keeps 10 of them as
    single-member AlternateSets while ours folds them into the SingleSubst lookup, so
    the type-1 counts read 188 against 198 and condition 2 refused a font that shapes
    identically under every feature it has, `aalt` included. Where the per-lookup
    signature disagrees, a second signature is tried: the multiset of lookup TYPES
    plus the font-wide multiset of rules, with single-member alternates canonicalised
    to single substitutions. Both are compared -- the fallback loosens WHICH lookup a
    rule sits in, never which rules exist. (tools/probes/gsub_alternate_singleton/)
    """
    gsub_rows = [r for r in rows if r.startswith("GSUB.feature_list")
                 or r.startswith("GSUB.lookup_list")
                 or r.startswith("GSUB.script_list")]
    if not gsub_rows:
        return rows, []
    try:
        import itertools

        import uharfbuzz as hb
        from fontTools.ttLib import TTFont
        S, B = TTFont(shipped), TTFont(built)
        if "GSUB" not in S or "GSUB" not in B:
            return rows, []

        def cmap_rev(f):
            """Glyph name -> the codepoint it is encoded at, first one wins.

            A rule that substitutes the same input for the same output is the same
            rule, whatever the two fonts spell those glyphs. comicrelief's release
            maps `Scedilla -> Scommaaccent` where our build maps `Scedilla ->
            uni0218`, and U+0218 IS Scommaaccent: one rule, two spellings, reported
            as a difference in GSUB. Keying a mapped glyph on its codepoint removes
            the spelling from the comparison.
            """
            rev = {}
            for cp, name in _best_cmap(f).items():
                rev.setdefault(name, cp)
            return rev

        def shape_of(f, n):
            """(advance, bbox, area) for one glyph, or None."""
            from fontTools.pens.areaPen import AreaPen
            from fontTools.pens.boundsPen import BoundsPen
            glyphs = f.getGlyphSet()
            bp, ap = BoundsPen(glyphs), AreaPen(glyphs)
            try:
                glyphs[n].draw(bp)
                glyphs[n].draw(ap)
                return f["hmtx"][n][0], bp.bounds, abs(ap.value)
            except Exception:
                return None

        # Unmapped glyphs have no codepoint to key on, and keying them by NAME made
        # `idotaccent` (release) and `i.loclTRK` (ours) look like different
        # substitution targets though they are the same drawing. Keying them by exact
        # geometry is no better: patrickhand's differ by ONE unit of bounding box
        # (-7 against -8), which a hash key turns into a mismatch.
        #
        # So pair them explicitly, with the tolerance `_same_geometry` uses, and
        # translate our name to the release's. A tolerance cannot live in a key; it
        # has to live in a comparison.
        s_rev_all, b_rev_all = cmap_rev(S), cmap_rev(B)
        s_unmapped = [n for n in S.getGlyphOrder() if n not in s_rev_all]
        b_unmapped = [n for n in B.getGlyphOrder() if n not in b_rev_all]
        translate = {}
        taken = set()
        for bn in b_unmapped:
            if bn in s_unmapped:
                continue                      # same name on both sides already
            bs = shape_of(B, bn)
            if bs is None or bs[1] is None:
                continue
            for sn in s_unmapped:
                if sn in taken or sn in b_rev_all:
                    continue
                ss = shape_of(S, sn)
                if ss is None or ss[1] is None or ss[0] != bs[0]:
                    continue
                if max(abs(x - y) for x, y in zip(ss[1], bs[1])) > _GEOM_BBOX_TOL:
                    continue
                if abs(ss[2] - bs[2]) / max(ss[2], bs[2], 1.0) > _GEOM_AREA_TOL:
                    continue
                translate[bn] = sn
                taken.add(sn)
                break

        def keyer(rev, xlate):
            def key(n):
                if n in rev:
                    return "cp:%04X" % rev[n]
                return "n:%s" % xlate.get(n, n)
            return key

        s_key = keyer(s_rev_all, {})
        b_key = keyer(b_rev_all, translate)

        def profile(f, key):
            g = f["GSUB"].table
            feats = sorted({fr.FeatureTag for fr in g.FeatureList.FeatureRecord})
            sig = sorted((lk.LookupType,
                          sum(len(getattr(st, "mapping", None)
                                  or getattr(st, "ligatures", None) or {})
                              for st in lk.SubTable))
                         for lk in g.LookupList.Lookup)
            # Fallback signature: lookup types, plus every rule the font expresses,
            # with a one-member AlternateSet written as the single substitution it
            # already is. Says nothing about which lookup a rule lives in.
            types = sorted(lk.LookupType for lk in g.LookupList.Lookup)
            rules = []
            for lk in g.LookupList.Lookup:
                for st in lk.SubTable:
                    for k, v in (getattr(st, "mapping", None) or {}).items():
                        rules.append(("sub", key(k), key(v)))
                    for k, v in (getattr(st, "ligatures", None) or {}).items():
                        rules.append(("lig", key(k), len(v)))
                    for k, v in (getattr(st, "alternates", None) or {}).items():
                        if len(v) == 1:
                            rules.append(("sub", key(k), key(v[0])))
                        else:
                            rules.append(("alt", key(k), tuple(key(x) for x in v)))
            return feats, sig, (types, sorted(rules))

        import os as _os
        _dbg = _os.environ.get("GATE_TRACE")
        sf, ssig, salt = profile(S, s_key)
        bf, bsig, balt = profile(B, b_key)
        if sf != bf:
            if _dbg:
                print("TRACE gsub: feature tags differ", sf, bf)
            return rows, []
        folded = False
        if ssig != bsig:
            if salt != balt:
                if _dbg:
                    a_only = [x for x in salt[1] if x not in balt[1]][:3]
                    b_only = [x for x in balt[1] if x not in salt[1]][:3]
                    print("TRACE gsub: rules differ; types %s vs %s; only-release %s; only-ours %s"
                          % (salt[0] == balt[0], "", a_only, b_only))
                return rows, []
            folded = True

        # glyph id -> canonical key, so the two fonts' outputs are comparable
        def gid_key(font, key):
            order = font.getGlyphOrder()
            return lambda gid: key(order[gid]) if gid < len(order) else "gid:%d" % gid

        so, bo = gid_key(S, s_key), gid_key(B, b_key)
        fs = hb.Font(hb.Face(hb.Blob.from_file_path(shipped)))
        fb = hb.Font(hb.Face(hb.Blob.from_file_path(built)))

        def run(font, order, text, feats, lang=None):
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            if lang is not None:
                buf.language = lang
            hb.shape(font, buf, feats)
            # Compare what the shaper RESOLVED TO, not what the font calls it. The
            # release substitutes Scedilla -> `Scommaaccent` and our build
            # Scedilla -> `uni0218`, which is the same glyph at U+0218; comparing the
            # names made a rename look like a shaping difference and the arbitration
            # refused a font that shapes identically.
            return [(order(i.codepoint), p.x_advance)
                    for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

        # `locl` only substitutes under the language it is registered for, so a corpus
        # shaped in the default language never fires it and the "features demonstrably
        # fire" condition refuses -- correctly, since nothing was tested. comicrelief
        # is that case: its one feature is `locl`, carrying the Romanian
        # Scedilla -> Scommaaccent rule.
        #
        # Shaping the corpus under a handful of languages gives the features a chance
        # to fire instead of assuming they cannot. This strengthens the test: every
        # language must agree, not just the default one.
        langs = [None, "ro", "tr", "sr", "de", "pl", "nl", "ca"]
        # The corpus must contain the codepoints the rules ACT ON, or the features
        # cannot fire and the arbitration refuses a font it never tested. Taking the
        # 60 lowest codepoints gave an all-ASCII corpus, so comicrelief's `locl` --
        # which rewrites Scedilla at U+015E -- was unreachable however the language
        # was set.
        shared = set(_best_cmap(S)) & set(_best_cmap(B))
        s_rev = {n: c for c, n in _best_cmap(S).items()}
        targets = set()
        def rule_inputs(st):
            """Glyph names a subtable can act on, including contextual coverage.

            Collecting only `mapping`, `alternates` and `ligatures` misses a
            CONTEXTUAL lookup entirely, because its inputs live in a Coverage table.
            molengo's `ccmp` is contextual, so no codepoint it acts on reached the
            corpus, the feature never fired, and the arbitration refused for want of
            evidence it could not gather.
            """
            out = list(getattr(st, "mapping", None) or {})
            out += list(getattr(st, "alternates", None) or {})
            out += list(getattr(st, "ligatures", None) or {})
            cov = getattr(st, "Coverage", None)
            if cov is not None and getattr(cov, "glyphs", None):
                out += list(cov.glyphs)
            for attr in ("BacktrackCoverage", "InputCoverage", "LookAheadCoverage"):
                for c in (getattr(st, attr, None) or []):
                    if getattr(c, "glyphs", None):
                        out += list(c.glyphs)
            for rs in (getattr(st, "SubRuleSet", None) or []):
                for r in (getattr(rs, "SubRule", None) or []):
                    out += list(getattr(r, "Input", None) or [])
            for rs in (getattr(st, "ChainSubRuleSet", None) or []):
                for r in (getattr(rs, "ChainSubRule", None) or []):
                    out += list(getattr(r, "Input", None) or [])
            return out

        for lk in S["GSUB"].table.LookupList.Lookup:
            for st in lk.SubTable:
                for name in rule_inputs(st):
                    cp = s_rev.get(name)
                    if cp in shared:
                        targets.add(cp)
        cps = sorted(c for c in shared if 0x20 < c < 0x2000)
        sample = sorted(targets)[:40] + [c for c in cps if c not in targets][:40]
        words = ["".join(p) for p in itertools.product(
            [chr(c) for c in sorted(set(sample))], repeat=2)]
        on = {t: True for t in sf}
        off = {t: False for t in sf}
        fired = False
        for lang in langs:
            for w in words:
                a = run(fs, so, w, on, lang)
                b_ = run(fb, bo, w, on, lang)
                if a != b_:
                    if _dbg:
                        print("TRACE gsub: shaping differs lang=%s word=%r\n   release=%s\n   ours   =%s"
                              % (lang, w, a[:6], b_[:6]))
                    return rows, []
                if run(fs, so, w, off, lang) != a:
                    fired = True
        if not fired:
            # Toggling a feature flag does not switch off an Indic feature: HarfBuzz's
            # Indic shaper applies `abvs`, `blws`, `half`, `akhn` and `haln` itself, so
            # `run(off)` equals `run(on)` and the corpus looks inert when it is not.
            # lohittamil is that case -- every Tamil conjunct substitutes, in both
            # fonts, and the arbitration refused for want of evidence it had.
            #
            # Fall back to a test that does not depend on the flags: did the shaper
            # produce something other than the codepoint-by-codepoint cmap lookup? If
            # it did, the layout tables demonstrably acted. Combined with the identical
            # output already established, that is the same assurance by another route.
            s_cmap = _best_cmap(S)
            for w in words:
                naive = [s_key(s_cmap[ord(ch)]) for ch in w if ord(ch) in s_cmap]
                if len(naive) != len(w):
                    continue
                shaped = [g for g, _ in run(fs, so, w, on)]
                if shaped != naive:
                    fired = True
                    break
        if not fired:
            if _dbg:
                print("TRACE gsub: the corpus never fired the features")
            # The corpus never triggered these features, so it has not tested them.
            return rows, []
    except Exception:
        return rows, []
    keep = [r for r in rows if r not in gsub_rows]
    how = ("the same GSUB rules in a different order and differently packed -- the "
           "release keeps single-member AlternateSets where ours folds them into "
           "single substitutions" if folded else
           "the same GSUB lookups in a different order")
    return keep, ["%s; %d shaped runs identical across %d language(s), with the "
                  "features firing" % (how, len(words) * 2 * len(langs), len(langs))]


def arbitrate_legacy_kern(rows, shipped, built):
    """Reclassify the three GPOS rows a release gets for kerning through a legacy
    `kern` table while the build kerns through GPOS.

    FontForge wrote kerning into a TrueType `kern` table and no GPOS at all; fontc
    writes a GPOS `kern` feature and no `kern` table. One font having GPOS and the
    other not is three structural rows by construction -- feature_list, lookup_list,
    script_list -- and says nothing about where text lands.

    This does NOT wave them through on shape alone. It shapes every pair the release
    kerns, through both fonts, and only accepts when all of them come out with the
    same advance. HarfBuzz reads GPOS when present and falls back to `kern` when it
    is not, so both fonts are exercised the way a shaper exercises them. Measured on
    miama, tulpenone and nosifer: 12,959 pairs, none positioned differently
    (sfd-batch6/tools/probes/legacy_kern_vs_gpos/).

    Kerning only. A release carrying BOTH GPOS and `kern` is not this case, and no
    other GPOS feature is covered.
    """
    gpos_rows = [r for r in rows if r.startswith("GPOS.feature_list")
                 or r.startswith("GPOS.lookup_list")
                 or r.startswith("GPOS.script_list")]
    if not gpos_rows:
        return rows, []
    try:
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont
        S, B = TTFont(shipped), TTFont(built)
        if "GPOS" in S or "kern" not in S or "GPOS" not in B or "kern" in B:
            return rows, []
        pairs = S["kern"].kernTables[0].kernTable
        if not pairs:
            return rows, []
        rev = {}
        for cp, name in _best_cmap(S).items():
            rev.setdefault(name, cp)

        def mk(path):
            return hb.Font(hb.Face(hb.Blob.from_file_path(path)))

        def adv(font, text):
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(font, buf, {"kern": True})
            return sum(g.x_advance for g in buf.glyph_positions)

        fs, fb = mk(shipped), mk(built)
        checked = 0
        for (l, r) in pairs:
            lc, rc = rev.get(l), rev.get(r)
            if lc is None or rc is None:
                continue
            t = chr(lc) + chr(rc)
            if adv(fs, t) != adv(fb, t):
                return rows, []
            checked += 1
        if not checked:
            return rows, []
    except Exception:
        return rows, []
    keep = [r for r in rows if r not in gpos_rows]
    return keep, ["the release kerns through a legacy `kern` table and the build "
                  "through GPOS; all %d kerned pairs shape identically" % checked]


def arbitrate_lsb(rows, shipped, built):
    """Split hmtx left-side-bearing rows into those that are our problem and those
    that are the release's.

    Of 237 such disagreements across batch 5, 207 were the shipped binary recording a
    bearing that contradicts its own outline while our build agreed with ours --
    FontForge wrote stale bounding boxes. Blocking on those would mean holding a
    conversion until it reproduced an error on purpose.

    -> (blocking, release_stale)"""
    try:
        from fontTools.ttLib import TTFont
        ship = _self_consistent_lsbs(shipped)
        ours = _self_consistent_lsbs(built)
        orders = (TTFont(shipped).getGlyphOrder(), TTFont(built).getGlyphOrder())
    except Exception as exc:               # fontTools missing, or an unreadable font
        return rows, ["arbitration unavailable: %s" % exc]

    block, stale = [], []
    for row in rows:
        name = None
        if row.startswith("hmtx.") and '"lsb"' in row:
            name = _resolve_placeholder(row.split(" ", 1)[0][len("hmtx."):], *orders)
        if name is None or name not in ship or name not in ours:
            block.append(row)
            continue
        ship_lsb, ship_xmin = ship[name]
        our_lsb, our_xmin = ours[name]
        if ship_xmin is None or our_xmin is None:
            stale.append("%s -- an empty glyph, so the bearing describes nothing"
                         % row.split(" ", 1)[0])
            continue
        if our_lsb == our_xmin and ship_lsb != ship_xmin:
            stale.append("%s -- shipped records %d for an outline at %d; ours records %d"
                         % (row.split(" ", 1)[0], ship_lsb, ship_xmin, our_lsb))
        elif our_lsb == our_xmin and ship_lsb == ship_xmin and '"advance"' not in row:
            # Both bearings describe their own outline faithfully, and the advance is
            # not in dispute. The row then states only that the two outlines have
            # different left extremes, which is a fact about the OUTLINES -- and this
            # gate already delegates those to the rendering diff (see ACCEPTED's note on
            # glyf and loca). Reporting it here counts the same difference twice.
            #
            # It is what a quadratic refit leaves behind: benchnine differs in point
            # COUNT on 372 of 418 glyphs and still renders 0/0/0 under diffenator3.
            # A glyph that really did change shape is caught by d3_glyphs/d3_words/d3_px,
            # which are separate columns in every sweep table.
            stale.append("%s -- each bearing matches its own outline (%d and %d) and the "
                         "advance agrees; the outlines are gated by the rendering diff"
                         % (row.split(" ", 1)[0], ship_lsb, our_lsb))
        else:
            block.append(row)
    return block, stale

# field -> reason. Everything else in that table blocks.
ACCEPTED = {
    'OS/2': {
        'version': 'fontc writes OS/2 v4',
        'x_avg_char_width': 'recomputed from the built advances',
        'fs_selection': 'USE_TYPO_METRICS is set by the build',
        'ul_unicode_range_1': 'recomputed from the cmap',
        'ul_unicode_range_2': 'recomputed from the cmap',
        'ul_unicode_range_3': 'recomputed from the cmap',
        'ul_unicode_range_4': 'recomputed from the cmap',
        'ul_code_page_range_1': 'recomputed from the cmap',
        'ul_code_page_range_2': 'recomputed from the cmap',
        'us_max_context': 'recomputed from the layout',
        'us_first_char_index': 'recomputed from the cmap, by definition',
        'us_last_char_index': 'recomputed from the cmap, by definition',
        'us_default_char': 'recomputed',
        'us_break_char': 'recomputed',
        's_family_class': 'not carried by the Glyphs format',
    },
    'head': {
        'checksum_adjustment': 'build artefact',
        'created': 'build timestamp',
        'modified': 'build timestamp',
        'lowest_rec_ppem': 'set by the build',
        'index_to_loc_format': 'the compiler picks short or long loca by whether the '
                               'offsets fit; it is not a property of the source',
        'flags': 'set by the build',
        'font_revision': 'follows the source version, which may carry a documented bump',
        'x_min': 'recomputed bbox', 'y_min': 'recomputed bbox',
        'x_max': 'recomputed bbox', 'y_max': 'recomputed bbox',
        'mac_style': 'derived from the style',
    },
    'hhea': {
        'caret_slope_rise': 'set by the build',
        'caret_slope_run': 'set by the build',
        'min_right_side_bearing': 'recomputed from the outlines',
        'min_left_side_bearing': 'recomputed from the outlines',
        'x_max_extent': 'recomputed from the outlines',
        'advance_width_max': 'recomputed from the advances',
        'number_of_h_metrics': 'recomputed',
    },
    'maxp': None,   # whole table: hinting-derived limits
    'gasp': None,   # hinting
    'VDMX': None,   # hinting
    # LTSH and hdmx are produced by the TrueType instructing step, exactly as VDMX is:
    # a linear-threshold table and a set of per-ppem device advances, both computed from
    # the hinted outlines. A release that went through ttfautohint carries them and an
    # unhinted build does not, so their presence is a property of the build pipeline and
    # not of the source. meddon is the case: its release has fpgm, cvt, VDMX, LTSH and
    # hdmx, our build has none of them, and the two whole-table rows said nothing the
    # already-accepted VDMX row did not.
    'LTSH': None,   # hinting
    'hdmx': None,   # hinting
    'DSIG': None,   # not produced
    'FFTM': None,   # FontForge timestamp table
    'post': {
        'glyph_name_index': 'production glyph names',
        'italic_angle': 'carried from the source',
        'is_fixed_pitch': 'set by the build',
        'underline_position': None,     # explicitly BLOCKING (listed for the reader)
        'underline_thickness': None,    # explicitly BLOCKING
    },
    'name': {},     # name records are compared by full_table_diff.py and disclosed
    # the legacy `kern` table modernised into a GPOS `kern` feature: grade.py's
    # first benign class, set by the batch-1 precedent (creepster).
    'kern': None,
    # GPOS is NOT accepted wholesale any more. The reason once written here -- a legacy
    # kern table modernised into a GPOS kern feature -- is real, but it covered every
    # GPOS difference including the one that matters: a release carrying an empty GPOS
    # shell against our build carrying none. HarfBuzz gates positioning on whether the
    # table EXISTS, not on whether it does anything, so the release suppresses HarfBuzz's
    # own fallback mark positioning and we get it. That moved 66 of 236 shaped cases in
    # unifrakturmaguntia. arbitrate_gpos() separates the two when the fonts are given;
    # without them the row blocks, which is the safe direction.
    'GSUB': {},
    'loca': None, 'glyf': None,   # outlines are gated by the rendering diff, not here
    'prep': None, 'fpgm': None, 'cvt ': None,   # hinting, dropped by an unhinted build
}
# post fields that must match despite `post` appearing above
BLOCKING_ALWAYS = {('post', 'underline_position'), ('post', 'underline_thickness')}


def _empty_side(vals):
    """A row whose value exists on one side only AND says nothing on the side where it
    exists: an empty subtable against an absent one. Nothing against nothing."""
    if not (isinstance(vals, list) and len(vals) == 2):
        return False
    a, b = vals
    return (a is None) != (b is None) and not (a or b)


def _renamed_side(vals):
    """A glyph-name-keyed entry present on one side only. When the name that exists is
    a production name (uniXXXX), this is the production-rename class grade.py already
    accepts and the PR bodies disclose -- the glyph is the same glyph."""
    if not (isinstance(vals, list) and len(vals) == 2):
        return False
    return vals[0] is None or vals[1] is None


def blocking(d, accept=()):
    out = []
    tables = d.get('tables') or {}
    for table, content in tables.items():
        if table == 'cmap':
            out += cmap_blocking(content)
            continue
        rules = ACCEPTED.get(table, 'MISSING')
        if rules is None:
            continue                      # whole table accepted
        if table == 'name':
            continue                      # disclosed separately
        if not isinstance(content, dict):
            if rules == 'MISSING':
                out.append('%s: whole-table difference' % table)
            continue
        for field, vals in content.items():
            if (table, field) in BLOCKING_ALWAYS:
                out.append('%s.%s %s' % (table, field, json.dumps(vals)[:80]))
                continue
            if rules != 'MISSING' and field in rules and rules[field] is not None:
                continue
            # glyph-name-keyed tables: an entry on one side only is the production
            # rename class (grade.py benign, disclosed in the PR body). A glyph
            # present on BOTH sides with different values is a real change.
            if table in ('hmtx', 'post') and _renamed_side(vals):
                continue
            # GDEF was in that tuple and must not be. Its rows are whole subtables, not
            # per-glyph entries, so a one-sided value is not a renamed glyph: when our
            # build stops emitting GDEF altogether, diffenator3 reports
            # `glyph_classes [{...270 glyphs...}, null]` and the rename shortcut waved
            # it through. Measured 2026-09-19 on unifrakturcook: the row closed, and
            # the two fonts still shaped differently in 10760 of 41472 runs, 554 of
            # them left-to-right at default buffer flags. Only an EMPTY subtable
            # against an absent one says nothing on either side.
            # (probes/gdef_mark_vs_base/)
            if table == 'GDEF' and _empty_side(vals):
                continue
            out.append('%s.%s %s' % (table, field, json.dumps(vals)[:80]))
    out += cmap_blocking(d.get('cmap_diff') or {})
    if accept:
        out = [r for r in out if not any(r.startswith(a) for a in accept)]
    return out


def is_production_name(name, cp):
    """True when `name` is the production spelling of codepoint `cp`."""
    if name is None:
        return False
    base = name.split('.')[0]
    return base.lower() in ('uni%04x' % cp, 'u%04x' % cp, 'u%05x' % cp, 'u%06x' % cp)


def cmap_blocking(cm):
    """A codepoint LOST is blocking. A codepoint GAINED is NOT: it is accepted as the
    duplicate-cmap class (--add-legacy-duplicate-cmap overshooting the release). A
    codepoint whose glyph merely takes its production name is the accepted rename class
    (grade.py counts these and the PR body discloses them).

    This docstring used to say a gained codepoint is blocking; the code has never
    treated it so. A caller that needs the cmaps EQUAL must check that itself --
    sfd-reland/tools/land.py and verify_landed.py do, and found 11 gate-clean styles
    mapping codepoints their releases do not."""
    out = []
    if not isinstance(cm, dict):
        return out
    for k, v in cm.items():
        if k in ('new', 'missing'):
            # diffenator3's summary lists; a LOST codepoint is what matters and it
            # also shows per-codepoint above.
            continue
        try:
            cp = int(k[2:], 16)
        except (ValueError, IndexError):
            cp = None
        if not (isinstance(v, list) and len(v) == 2):
            out.append('cmap %s %s' % (k, json.dumps(v)[:60]))
            continue
        old_n, new_n = v
        if old_n is None and new_n is not None:
            continue     # a codepoint GAINED: the accepted duplicate-cmap class
        if new_n is None:
            out.append('cmap %s LOST %s' % (k, json.dumps(v)[:60]))
        elif cp is not None and is_production_name(new_n, cp):
            continue                                            # accepted rename
        else:
            out.append('cmap %s %s' % (k, json.dumps(v)[:60]))
    return out


# Unicode Mn characters that are ALSO Default_Ignorable_Code_Point. HarfBuzz refuses to
# synthesise a mark class for a default ignorable ("Some Mongolian fonts without GDEF
# rely on this"), so these stay base glyphs when a font has no GDEF glyph classes.
_MN_DEFAULT_IGNORABLE = ({0x034F} | set(range(0x180B, 0x180E))
                         | set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0)))
# lookup flags that can read a glyph's BASE-versus-unclassified distinction, as opposed
# to only its mark-ness: IgnoreBaseGlyphs, IgnoreLigatures, UseMarkFilteringSet and a
# MarkAttachmentType filter.
_CLASS_READING_FLAGS = 0x0002 | 0x0004 | 0x0010 | 0xFF00


def _effective_marks(path):
    """-> the set of CODEPOINTS a shaper treats as marks in this font as it stands.

    A GDEF glyph class is only ever read by something else, and "our build has no GDEF"
    does not mean "our build has no marks": HarfBuzz sets plan.fallback_glyph_classes
    when a face has no GDEF glyph classes and then SYNTHESISES a class per glyph from
    the Unicode general category of the character in the buffer. So a font with an
    all-base GDEF and a font with no GDEF at all disagree about every combining mark,
    which is the opposite of the structural-only reading.
    """
    import unicodedata

    from fontTools.ttLib import TTFont

    font = TTFont(path)
    cmap = _best_cmap(font)
    gc = None
    if 'GDEF' in font and font['GDEF'].table.GlyphClassDef:
        gc = font['GDEF'].table.GlyphClassDef.classDefs
    marks = set()
    for cp, name in cmap.items():
        if gc is not None:
            if gc.get(name, 0) == 3:
                marks.add(cp)
            continue
        try:
            cat = unicodedata.category(chr(cp))
        except ValueError:
            continue
        if cat in ('Mn', 'Mc', 'Me') and cp not in _MN_DEFAULT_IGNORABLE:
            marks.add(cp)
    return marks


def _reads_glyph_class(path):
    """True when some lookup in this font filters on more than mark-ness."""
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    for tag in ('GSUB', 'GPOS'):
        if tag not in font:
            continue
        table = font[tag].table
        for lk in (table.LookupList.Lookup if table.LookupList else []):
            if lk.LookupFlag & _CLASS_READING_FLAGS:
                return True
    return False


def _all_combining(codepoints):
    """True when every codepoint is a Unicode combining mark (Mn, Mc or Me)."""
    import unicodedata

    if not codepoints:
        return False
    for cp in codepoints:
        try:
            if unicodedata.category(chr(cp)) not in ("Mn", "Mc", "Me"):
                return False
        except Exception:
            return False
    return True


def arbitrate_gdef_classes(rows, shipped, built):
    """A `GDEF.glyph_classes` row where the two fonts nonetheless agree about which
    glyphs are marks, and nothing in either font can read the rest of the distinction.

    Narrow on purpose, and it was wrong to let this row through on structure alone.
    unifrakturcook's build stopped emitting GDEF at all, diffenator3 reported
    `glyph_classes [{...270 glyphs...}, null]`, the one-sided-value shortcut in
    blocking() read that as a renamed glyph and the row closed -- while the two fonts
    still shaped differently in 10760 of 41472 runs, 554 of them left-to-right at
    default buffer flags, because the release calls nine Unicode combining marks base
    glyphs and a GDEF-less font does not. See probes/gdef_mark_vs_base/.

    -> (blocking, benign)"""
    block, benign = [], []
    cache = {}
    for row in rows:
        if not row.startswith('GDEF.glyph_classes'):
            block.append(row)
            continue
        try:
            if not cache:
                cache['ship'] = _effective_marks(shipped)
                cache['ours'] = _effective_marks(built)
                cache['reads'] = (_reads_glyph_class(shipped)
                                  or _reads_glyph_class(built))
        except Exception:
            block.append(row)
            continue
        if cache['reads']:
            block.append('GDEF.glyph_classes -- a lookup filters on glyph class')
            continue
        only_ship = cache['ship'] - cache['ours']
        only_ours = cache['ours'] - cache['ship']
        if not only_ship and not only_ours:
            benign.append('GDEF.glyph_classes -- the two fonts agree about every mark '
                          '(%d), and no lookup filters on the rest of the class'
                          % len(cache['ship']))
        elif not only_ship and _all_combining(only_ours):
            # Every glyph in dispute is one WE mark and the release does not, and every
            # one is a real Unicode combining mark. Our classification is the correct
            # one; the release's is not. That is a correction to disclose, not a defect
            # to block on -- but it is not inert either, because fontc zeroes a mark's
            # advance and on a font with no vmtx that discards a synthesised line
            # advance, so it MUST be stated rather than passed over in silence.
            benign.append('GDEF.glyph_classes -- our build corrects %d mark class(es) '
                          'the release got wrong: %s. Disclose in the PR body; the '
                          'release calls these base glyphs and they are Unicode '
                          'combining marks'
                          % (len(only_ours),
                             ", ".join("U+%04X" % c for c in sorted(only_ours))))
        else:
            block.append('GDEF.glyph_classes -- the two fonts disagree about %d mark(s): '
                         'only the release marks %s; only ours marks %s'
                         % (len(only_ship) + len(only_ours),
                            ','.join('U+%04X' % c for c in sorted(only_ship)) or 'none',
                            ','.join('U+%04X' % c for c in sorted(only_ours)) or 'none'))
    return block, benign


def _same_glyph(shipped, built, cp):
    """True when the glyph each font maps at `cp` is the same glyph under a different
    name: same advance width and the same outline.

    Glyph names do not reach the renderer. What reaches it is the outline the codepoint
    resolves to, so `uni0122` against `Gcommaaccent`, or a release's dedicated `nbsp`
    against the `space` our duplicate-cmap filter maps U+00A0 onto, are renames and not
    defects -- but only if the outlines really do agree, which is what this checks
    rather than assumes.

    Outlines are compared with the same comparator as tools/outline_match.py: composites
    resolved, implied on-curve midpoints expanded on both sides, and each contour
    canonicalised over its rotations and its reversal, because a differing start point
    or winding direction is the same ring of points. An off-curve point coincident with
    an adjacent on-curve point is dropped: that segment is a straight line either way."""
    import outline_match
    shapes = []
    for path in (shipped, built):
        font = _cached_font(path)
        name = _best_cmap(font).get(cp)
        if name is None:
            return False
        metrics = font['hmtx'].metrics
        if name not in metrics:
            return False
        contours = outline_match.contours_of(font, name)
        if contours is None:
            return False
        shapes.append((metrics[name][0],
                       sorted(outline_match.canonical(outline_match.drop_degenerate(c))
                              for c in contours)))
    if shapes[0] == shapes[1]:
        return True
    return _same_geometry(shipped, built, cp)


# A quadratic refit changes WHICH points describe a curve without changing the curve.
# babelfont's conversion of a .sfd and FontForge's own TTF export of it place their
# on-curve points differently, so a point-for-point test calls two tracings of one
# outline different. abrilfatface is the case: every one of its 394 shared codepoints
# agrees to within 2 units of bounding box, and two of them were still blocking as
# unexplained cmap rows.
#
# Identical advance, every bounding-box edge within 2 units, and relative area within
# 0.4%. Both bounds are calibrated, not chosen:
#
#   * the FLOOR comes from families that gate clean -- 1485 glyphs of abrilfatface,
#     comicrelief, corben and lohitbengali whose advance and bbox already match. Their
#     area agrees exactly at the median and to 0.38% at the 99th percentile: that is
#     what a quadratic refit of one outline costs.
#   * the CEILING comes from a control that must keep failing. Allerta against
#     AllertaStencil are different designs that share a bounding box almost everywhere,
#     because the stencil cuts gaps in strokes rather than changing their extent. Of
#     113 glyphs where advance and bbox match, the SMALLEST area difference is 1.644%.
#
# 0.4% sits between the two with a factor of four either side. It accepts molengo's
# U+02BC and U+02BD renames (0.13% and 0.30%, identical advance and bbox) and none of
# the control's 113.
#
# Bbox stays at 2 units: patrickhandsc's f_i.liga misses by 253, Allerta against
# AllertaStencil by 17.
_GEOM_BBOX_TOL = 2
_GEOM_AREA_TOL = 0.004


def _abs_contour_area(glyphs, name):
    """Sum of the ABSOLUTE area of each contour, not the absolute of the sum.

    `AreaPen` returns a signed total, so two disjoint contours wound in opposite
    directions cancel to zero even though both render. digitalnumbers' `V` is exactly
    that -- two diagonal bars at x 8-352 and 448-792, one clockwise and one
    counter-clockwise -- and measuring it as a signed total said our build drew nothing
    where the release drew a V. Under the nonzero fill rule both bars fill regardless
    of direction; direction only decides overlaps and counters.

    Summing per contour keeps the measure sensitive to shape and blind to winding,
    which is what a comparison between two builds of one source needs.
    """
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    rec = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(rec)
    # A contour ends at closePath/endPath -- NOT where the next moveTo is. fontTools
    # draws a TrueType contour made only of off-curve points as qCurveTo(..., None)
    # with no moveTo at all, so splitting at moveTo folded such a contour into the
    # previous one (Tuffy's Cyrillic a measured 23% "different" for drawings 0.15%
    # apart) and, when it came first, dropped it entirely.
    total, pen = 0.0, AreaPen()
    for op, args in rec.value:
        (getattr(pen, op)(*args) if args else getattr(pen, op)())
        if op in ("closePath", "endPath"):
            total += abs(pen.value)
            pen = AreaPen()
    return total + abs(pen.value)


def _same_geometry(shipped, built, cp):
    """True when the two fonts draw the same shape at `cp`, allowing a quadratic refit."""
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.boundsPen import BoundsPen
    vals = []
    for path in (shipped, built):
        font = _cached_font(path)
        name = _best_cmap(font).get(cp)
        if name is None:
            return False
        glyphs = font.getGlyphSet()
        bp = BoundsPen(glyphs)
        try:
            glyphs[name].draw(bp)
            area = _abs_contour_area(glyphs, name)
            adv = font["hmtx"][name][0]
        except Exception:
            return False
        vals.append((adv, bp.bounds, area))
    (a_adv, a_box, a_area), (b_adv, b_box, b_area) = vals
    if a_adv != b_adv:
        return False
    if a_box is None or b_box is None:
        return a_box is b_box
    if max(abs(x - y) for x, y in zip(a_box, b_box)) > _GEOM_BBOX_TOL:
        return False
    return abs(a_area - b_area) / max(a_area, b_area, 1.0) <= _GEOM_AREA_TOL


_FONT_CACHE = {}


def _cached_font(path):
    from fontTools.ttLib import TTFont
    if path not in _FONT_CACHE:
        _FONT_CACHE[path] = TTFont(path)
    return _FONT_CACHE[path]


_CMAP_ROW = re.compile(r'^cmap U\+([0-9A-Fa-f]+) \[')


def arbitrate_cmap_names(rows, shipped, built):
    """A cmap row where both sides name a glyph, and the two names denote the same
    outline at the same advance, is a rename rather than a difference in what renders.

    Two sources of these in this programme: releases built through a production-name
    renaming step (`uni0122` where the source says `Gcommaaccent`), and U+00A0, where
    FontForge's export synthesised a dedicated `nbsp` glyph while our recipe maps the
    codepoint onto the `space` the source already carries."""
    keep, notes = [], []
    for r in rows:
        m = _CMAP_ROW.match(r)
        if m and ' LOST ' not in r:
            cp = int(m.group(1), 16)
            try:
                same = _same_glyph(shipped, built, cp)
            except Exception:
                same = False
            if same:
                notes.append('%s: same outline and advance under a different name' % r)
                continue
        keep.append(r)
    return keep, notes


def load_exceptions(path, family, style):
    """Rows this family has a committed measurement for. -> [(prefix, evidence)]"""
    out = []
    try:
        fh = open(path)
    except OSError:
        return out
    with fh:
        for line in fh:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 4 or parts[0] == 'family':
                continue
            if parts[0] == family and (parts[1] == style or parts[1] == '*'):
                out.append((parts[2], parts[3]))
    return out


def main():
    argv = sys.argv[1:]
    fonts = None
    source = None
    renamed = []
    documented = []
    exc_file = exc_family = exc_style = None
    if '--source' in argv:
        i = argv.index('--source')
        source = argv[i + 1]
        del argv[i:i + 2]
    for flag, var in (('--exceptions', 'exc_file'), ('--family', 'exc_family'),
                      ('--style', 'exc_style')):
        if flag in argv:
            i = argv.index(flag)
            value = argv[i + 1]
            del argv[i:i + 2]
            if var == 'exc_file':
                exc_file = value
            elif var == 'exc_family':
                exc_family = value
            else:
                exc_style = value
    if '--fonts' in argv:
        i = argv.index('--fonts')
        fonts = (argv[i + 1], argv[i + 2])
        del argv[i:i + 3]
    args = [a for a in argv if not a.startswith('--accept=')]
    accept = [a.split('=', 1)[1] for a in argv if a.startswith('--accept=')]
    accept = [x for a in accept for x in a.split(',') if x]
    d = json.load(open(args[0]))
    rows = blocking(d, accept)
    stale = []
    if fonts:
        rows = expand_overflow(rows, fonts[0], fonts[1])
        rows = expand_cmap_overflow(rows, fonts[0], fonts[1])
        stale = [r[len("__STALE__"):] for r in rows if r.startswith("__STALE__")]
        rows = [r for r in rows if not r.startswith("__STALE__")]
        rows, more = arbitrate_lsb(rows, fonts[0], fonts[1])
        stale += more
        rows, empty = arbitrate_empty_layout(rows, fonts[0], fonts[1])
        stale += empty
        rows, legacy_kern = arbitrate_legacy_kern(rows, fonts[0], fonts[1])
        stale += legacy_kern
        rows, gsub_order = arbitrate_gsub_lookup_order(rows, fonts[0], fonts[1])
        stale += gsub_order
        rows, vendor = arbitrate_blank_vendor(rows, fonts[0], fonts[1])
        stale += vendor
        rows, gpos = arbitrate_gpos(rows, fonts[0], fonts[1])
        stale += gpos
        rows, oldos2 = arbitrate_old_os2(rows, fonts[0], fonts[1])
        stale += oldos2
        rows, gcount = arbitrate_glyph_count(rows, fonts[0], fonts[1])
        stale += gcount
        rows, gdef = arbitrate_gdef_classes(rows, fonts[0], fonts[1])
        stale += gdef
        rows, renamed = arbitrate_cmap_names(rows, fonts[0], fonts[1])
        rows, declared = arbitrate_source_declared(rows, fonts[0], fonts[1], source)
        stale += declared
        rows, postv = arbitrate_post_version(rows, fonts[0], fonts[1])
        stale += postv
    if exc_file and exc_family:
        keep = []
        for r in rows:
            hit = next((e for pfx, e in load_exceptions(exc_file, exc_family, exc_style)
                        if r.startswith(pfx)), None)
            if hit:
                documented.append('%s -- %s' % (r.split(' ', 1)[0], hit))
            else:
                keep.append(r)
        rows = keep
    for r in stale:
        print('RELEASE-STALE %s' % r)
    for r in documented:
        print('DOCUMENTED %s' % r)
    for r in renamed:
        print('ACCEPTED-RENAME %s' % r)
    for r in rows:
        print('BLOCKING %s' % r)
    print('%d blocking table difference(s)%s'
          % (len(rows),
             ''.join([', %d stale in the release' % len(stale) if stale else '',
                      ', %d accepted rename(s)' % len(renamed) if renamed else '',
                      ', %d documented' % len(documented) if documented else ''])))
    sys.exit(1 if rows else 0)


if __name__ == '__main__':
    main()
