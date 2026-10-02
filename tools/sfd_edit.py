#!/usr/bin/env python3
"""Documented edits to a FontForge .sfd, one operation at a time.

Each edit a repository's history makes to its legacy source is one of these
operations, applied by tools/land.py and committed on its own with the plan's
subject and justification. The first five keep the semantics of
sfd-batch5/tools/source_corrections.py, where they were introduced, so a plan
written for either tool means the same thing:

  setfield <Field> <value...>     replace the existing "Field: ..." line
  addfield <Field> <value...>     insert "Field: value" after FontName:; error if present
  ensurefield <Field> <value...>  insert if absent; keep an existing value
  nbspwidth                       set the U+00A0 glyph's Width to the space's
  renameglyph <old> <new>         rename a StartChar and every standalone reference

and four this workspace adds, each from an investigation's reference
implementation (investigations/<unit>/):

  addprivate <Key> <value...>     add a PostScript private dictionary holding one
                                  entry, where FontForge's SFD writer puts it (after
                                  the display/WinInfo lines, before Grid, TeXData,
                                  AnchorClass2 and BeginChars); FATAL if the source
                                  already has one (next-heights: the -TTF.sfd files
                                  re-imported from a TTF lost the BlueValues their
                                  release was exported with)

  scaleem <em>                    change the em as FontForge 20100501's `f.em = <em>`
                                  did (tools/ff_scale_em.py, puritan: its port
                                  reproduces a released glyf point for point)
  droplookup <name>               delete a Lookup: line with this exact name and every
                                  glyph line filling its subtables; FATAL if anything
                                  still names the lookup or a subtable (nosifer)
  setname <id> <value...>         state US English name ID <id> in the LangName: 1033
                                  record (created after FontName: if absent); FontForge
                                  exports it in preference to FullName/FamilyName/FontName
                                  (names: a release renamed after export)
  renameglyphgid <gid> <old> <new>  rename only the StartChar whose Encoding: line
                                  carries <gid>, when <old> is duplicated; by-name
                                  references keep binding to the other glyph, as
                                  FontForge bound them (corben-bold)

Glyph-level edits, each changing one stated value of one glyph (investigations/tuffy,
probes/apply_edits.py, where they were measured):

  setencoding <glyph> <slot> <uni>  rewrite the glyph's "Encoding: slot uni gid", keeping
                                  its gid; FATAL if another glyph has that slot or Unicode
  setwidth <glyph> <w>            the glyph's advance
  setrefer <glyph> <n> <dx> <dy>  the translation of the glyph's n-th (1-based) Refer:
  translateglyph <glyph> <dx> <dy>  move the glyph's outline; FATAL if it has references,
                                  anchors or hints (they would have to move too)
  dropglyph <glyph>               delete an empty, unreferenced glyph; only the last one
                                  (references go by gid, so no other glyph may move)
  setglyphclass <glyph> <class>   GlyphClass: as FontForge stores it (OpenType class + 1:
                                  2 base, 3 ligature, 4 mark, 5 component)
  setlangname <lang> <id> <value...>  a name in the LangName record of Windows language
                                  <lang> (decimal); non-ASCII is written UTF-7, as
                                  FontForge stores it
  movelangname <lang> <from> <to>  move a LangName string from one name ID to another
  droplangname <lang>             delete the LangName record of a language

What the tool that made a release did that the source does not state, done to the
source instead (each one replaced a babelfont filter Simon declined, #107 and #115):

  truncateanchors                 write every AnchorPoint coordinate truncated toward
                                  zero (129.5 -> 129, -46.7 -> -46), as FontForge's GPOS
                                  export does (C conversion of a real to a short in
                                  tottf.c/dumpgpos); a compiler rounds them instead.
                                  FATAL if no anchor has a fractional coordinate
  sfdlibinterpolated              state the outline sfdLib 2.0.0 read from a quadratic
                                  Fore layer (parser.py _drawContours): every on-curve
                                  point of a `c` segment flagged 0x80
                                  (SFD_PTFLAG_INTERPOLATE) becomes a control point at the
                                  same place; a flagged closing segment makes the
                                  contour's first point one, and the contour then starts
                                  at its first stated on-curve point, as the release's
                                  does. The on-curve points TrueType implies between two
                                  adjacent control points are written out at their exact
                                  midpoints, flagged 0x80 with TrueType number -1, as
                                  FontForge stores implied points. Unchanged points keep
                                  their TrueType numbers; a point made a control point
                                  gets an unused one. FATAL on a glyph with TrueType
                                  instructions, a cubic Fore layer, an open contour with
                                  a flagged point, or when no point is flagged

Edits whose values are copied from a released binary. <release> names it exactly, as
google/fonts@<commit>:<path>, read from the google/fonts clone (GF=, default
/home/fsanches/compartilhado/google/fonts); a plan using one says so in its body:

  importoutlines <release> U+XXXX...  replace these glyphs' Fore-layer outlines and advances
                                  with the release's exact quadratic points (contours and
                                  point flags from sfd-batch5/tools/drift/import_outlines.py;
                                  written into the Fore layer, which that tool does not do
                                  when a glyph also has a Back layer); simple glyphs only
  renameglyphs <release>          rename every encoded glyph to the name the release's
                                  post table gives its codepoint (StartChar and the
                                  glyph-name lists of substitution lines; references and
                                  kerning go by gid); FATAL on constructs it does not model
  importgsub <release>            replace every GSUB lookup with the release's: single,
                                  ligature, alternate, multiple and coverage-format
                                  chaining lookups, in the release's lookup order and
                                  with its script/language/feature registration; glyphs
                                  matched by codepoint, else by name

Steps of a FontForge build script, done to the source text (tools/ff_build_ops.py,
promoted from investigations/next-provenance/probes, which follows the FontForge of
2008-08-08, git eb711fd7). File arguments are relative to the .sfd's directory, as the
build script, run in src/, names them:

  generatefrom <file.sfd>         create this style's .sfd as a copy of another source
                                  (a build script's generated intermediate); FATAL if
                                  the file already exists
  mergefea <file.fea>             font.mergeFeature(): GSUB single and ligature lookups
  mergepsfont <file.pfa> <prefix>  font.mergeFonts() of a Type 1 font: every drawing glyph
                                  the font lacks, unscaled, named and encoded as FontForge
                                  2008 did; the outlines are converted to quadratics by
                                  cu2qu (max error 1 unit), NOT by FontForge's
                                  SplineSetsTTFApprox, so points differ within a unit
  afmligatures <lookup> <lig>=<a>+<b>...  the 'liga' lookup (script latn) FontForge's AFM
                                  reader makes from an AFM's "L" lines, under its name
  obliqize <angle> <first> <last>  build.py obliqize(): unlink references and skew every
                                  glyph by psMat.skew(<angle>) (radians), except the
                                  Unicode range first..last (hex)
  pastepsglyphs <file.pfa> <glyph>...  copy these glyphs' outlines and advances from a Type 1
                                  font over the font's own (build.py deobliqize())

An operation that cannot apply is FATAL: a silently skipped correction is how a
defect ships. Every edit reports what the field said before, so a plan cannot
overwrite a value the designer stated without the commit saying so.

Usage (for testing a plan by hand):
  sfd_edit.py <file.sfd> <op> [args...]
"""
import os
import re
import shlex
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GF = os.environ.get("GF", "/home/fsanches/compartilhado/google/fonts")
IMPORT_OUTLINES = "/home/fsanches/compartilhado/sfd-batch5/tools/drift/import_outlines.py"


class EditError(Exception):
    pass


def field_value(text, field):
    """The value a header field states, or None."""
    head = text.split("\nStartChar:", 1)[0]
    m = re.search(r"^%s: (.*)$" % re.escape(field), head, re.M)
    return m.group(1) if m else None


def _glyph_block(text, codepoint):
    for m in re.finditer(r"StartChar: [^\n]*\n(.*?)EndChar", text, re.S):
        enc = re.search(r"^Encoding: \S+ (-?\d+) ", m.group(1), re.M)
        if enc and int(enc.group(1)) == codepoint:
            return m
    return None


def apply(text, op, args, base=None):
    """Apply one operation; return (new_text, before) where `before` describes
    what the source stated beforehand (for the commit body). `base` is the .sfd's
    directory, against which file arguments are resolved."""
    if op in MORE_OPS:
        return MORE_OPS[op](text, args, base or ".")
    if op in ("setfield", "addfield", "ensurefield"):
        field, value = args.split(" ", 1)
        before = field_value(text, field)
        if op == "setfield":
            if before is None:
                raise EditError("no %s: line to replace" % field)
            text = re.sub(r"^%s: .*$" % re.escape(field), "%s: %s" % (field, value), text,
                          count=1, flags=re.M)
        else:
            if before is not None:
                if op == "addfield":
                    raise EditError("%s: already present (%s); use setfield" % (field, before))
                return text, before          # ensurefield keeps what is there
            if not re.search(r"^FontName: .*$", text, re.M):
                raise EditError("no FontName: line to insert after")
            text = re.sub(r"^(FontName: .*)$", lambda m: "%s\n%s: %s" % (m.group(1), field, value),
                          text, count=1, flags=re.M)
        return text, before
    if op == "nbspwidth":
        space = _glyph_block(text, 0x20)
        nbsp = _glyph_block(text, 0xA0)
        if space is None or nbsp is None:
            raise EditError("space or nbsp glyph not found")
        sw = re.search(r"^Width: (-?\d+)", space.group(1), re.M)
        nw = re.search(r"^Width: (-?\d+)", nbsp.group(1), re.M)
        if not sw or not nw:
            raise EditError("space or nbsp has no Width:")
        block = nbsp.group(0)
        text = text.replace(block, re.sub(r"^Width: -?\d+", "Width: %s" % sw.group(1), block,
                                          count=1, flags=re.M), 1)
        return text, "nbsp Width %s, space Width %s" % (nw.group(1), sw.group(1))
    if op == "addprivate":
        key, value = args.split(" ", 1)
        head = text.split("\nStartChar:", 1)[0]
        if re.search(r"^BeginPrivate:", head, re.M):
            raise EditError("the source already has a private dictionary")
        # SFD_Dump writes the private dictionary after DisplaySize/AntiAlias/FitToEm/
        # WinInfo/OnlyBitmaps and before these (fontforge/sfd.c, SFDDumpPrivate)
        m = re.search(r"^(?:GridOrder2:|Grid$|TeXData:|AnchorClass2:|BeginSubFonts:|BeginChars:)",
                      text, re.M)
        if not m:
            raise EditError("no BeginChars: line to insert before")
        block = "BeginPrivate: 1\n%s %d %s\nEndPrivate\n" % (key, len(value), value)
        return text[:m.start()] + block + text[m.start():], "no private dictionary"
    if op == "setname":
        name_id, value = args.split(" ", 1)
        name_id = int(name_id)
        if not value.isascii() or '"' in value:
            raise EditError("setname takes plain ASCII without quotes (FontForge stores UTF-7)")
        m = re.search(r'^LangName: 1033 (.*)$', text.split("\nStartChar:", 1)[0], re.M)
        strings = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)) if m else []
        before = strings[name_id] if name_id < len(strings) and strings[name_id] else None
        strings += [""] * (name_id + 1 - len(strings))
        strings[name_id] = value
        line = "LangName: 1033 " + " ".join('"%s"' % t for t in strings)
        if m:
            text = text.replace(m.group(0), line, 1)
        else:
            if not re.search(r"^FontName: .*$", text, re.M):
                raise EditError("no FontName: line to insert after")
            text = re.sub(r"^(FontName: .*)$", lambda mm: "%s\n%s" % (mm.group(1), line),
                          text, count=1, flags=re.M)
        return text, before
    if op == "renameglyph":
        old, new = args.split()
        n_old = len(re.findall(r"^StartChar: %s$" % re.escape(old), text, re.M))
        if not n_old:
            raise EditError("no StartChar: %s to rename" % old)
        if n_old > 1:
            # the reference rewrite below would rename every copy, leaving the name
            # duplicated under its new spelling (Corben-Bold's two dcroat)
            raise EditError("%d glyphs are named %s; use renameglyphgid" % (n_old, old))
        if re.search(r"^StartChar: %s$" % re.escape(new), text, re.M):
            raise EditError("StartChar: %s already exists" % new)
        text = re.sub(r"^StartChar: %s$" % re.escape(old), "StartChar: %s" % new, text,
                      count=1, flags=re.M)
        text = re.sub(r"(?<![\w.])%s(?![\w.])" % re.escape(old), new, text)
        if re.search(r"(?<![\w.])%s(?![\w.])" % re.escape(old), text):
            raise EditError("%s still referenced after rename" % old)
        return text, "glyph %s" % old
    if op == "scaleem":
        import ff_scale_em
        # The port scales outlines, references, widths and the header metrics -- all
        # a source like Puritan's holds. Anything else FontForge would also scale is
        # refused rather than left at the old em.
        unsupported = [k for k, pat in (
            ("kerning", r"^(KernClass2?|VKernClass2?|KP|VKP|Kerns):"),
            ("anchors", r"^(AnchorPoint|AnchorClass2?):"),
            ("PostScript hints", r"^(HStem|VStem|DStem2?):"),
            ("BASE", r"^BaseHoriz|^BaseVert"),
            ("MATH", r"^MATH:"),
        ) if re.search(pat, text, re.M)]
        if unsupported:
            raise EditError("scaleem does not model: %s" % ", ".join(unsupported))
        before = "Ascent %s, Descent %s" % (field_value(text, "Ascent"), field_value(text, "Descent"))
        # integer underline values: babelfont parses metrics as i32 and drops a real
        # (FontForge's own export gives the same bytes either way)
        scaled, (asc, desc, _scale, _stats) = ff_scale_em.scale_sfd(text, int(args), int_underline=True)
        return scaled, before + " -> Ascent %d, Descent %d" % (asc, desc)
    if op == "droplookup":
        name = args
        m = re.search(r'^Lookup: \d+ \d+ \d+ "%s"\s+\{(.*?)\}.*\n' % re.escape(name), text, re.M)
        if not m:
            raise EditError("no Lookup: line named %r" % name)
        subtables = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
        text = text[:m.start()] + text[m.end():]
        n = 0
        for st in subtables:
            text, k = re.subn(r'^(?:Ligature2|Substitution2|AlternateSubs2|MultipleSubs2): "%s" .*\n'
                              % re.escape(st), "", text, flags=re.M)
            n += k
        if n == 0:
            raise EditError("lookup %r had no glyph entries" % name)
        for token in [name] + subtables:
            if '"%s"' % token in text:
                raise EditError("%r is still referenced after the drop" % token)
        return text, "lookup %r with %d glyph entr%s" % (name, n, "y" if n == 1 else "ies")
    if op == "renameglyphgid":
        gid_s, old, new = args.split()
        gid = int(gid_s)
        starts = list(re.finditer(r"^StartChar: (.*)\n", text, re.M))
        same = [s for s in starts if s.group(1) == old]
        if len(same) < 2:
            raise EditError("%s is not duplicated; use renameglyph" % old)
        if any(s.group(1) == new for s in starts):
            raise EditError("StartChar: %s already exists" % new)
        hit = [s for s in same
               if (lambda e: e and int(e.group(3)) == gid)(
                   re.match(r"Encoding: (-?\d+) (-?\d+) (\d+)", text[s.end():s.end() + 80]))]
        if len(hit) != 1:
            raise EditError("%d StartChar: %s with gid %d" % (len(hit), old, gid))
        s = hit[0]
        return text[:s.start()] + "StartChar: %s\n" % new + text[s.end():], "glyph %s (gid %d)" % (old, gid)
    raise EditError("unknown op %s" % op)


# --- glyph-level edits --------------------------------------------------------
def _fmt(v):
    v = float(v)
    return "%d" % v if v.is_integer() else "%.12g" % v


def _blocks(text):
    return list(re.finditer(r"^StartChar: ([^\n]*)\n.*?^EndChar\n", text, re.M | re.S))


def _one_block(text, name):
    hits = [m for m in _blocks(text) if m.group(1) == name]
    if len(hits) != 1:
        raise EditError("%d glyphs named %s" % (len(hits), name))
    return hits[0]


def _replace_block(text, m, new):
    return text[:m.start()] + new + text[m.end():]


def op_setencoding(text, args, base):
    name, slot, uni = args.split()
    m = _one_block(text, name)
    for o in _blocks(text):
        if o.group(1) == name:
            continue
        e = re.search(r"^Encoding: (-?\d+) (-?\d+) ", o.group(0), re.M)
        if e and (e.group(1) == slot or (int(uni) >= 0 and e.group(2) == uni)):
            raise EditError("slot %s / Unicode %s already belongs to %s" % (slot, uni, o.group(1)))
    old = re.search(r"^Encoding: (-?\d+) (-?\d+) (\d+)$", m.group(0), re.M)
    if not old:
        raise EditError("%s has no Encoding: line" % name)
    new = m.group(0).replace(old.group(0), "Encoding: %s %s %s" % (slot, uni, old.group(3)), 1)
    return _replace_block(text, m, new), "%s Encoding: %s %s %s" % (name, *old.groups())


def op_setwidth(text, args, base):
    name, w = args.split()
    m = _one_block(text, name)
    old = re.search(r"^Width: (-?\d+)$", m.group(0), re.M)
    if not old:
        raise EditError("%s has no Width: line" % name)
    new = m.group(0).replace(old.group(0), "Width: %s" % w, 1)
    return _replace_block(text, m, new), "%s Width: %s" % (name, old.group(1))


def op_setrefer(text, args, base):
    name, idx, dx, dy = args.split()
    m = _one_block(text, name)
    refs = list(re.finditer(r"^Refer: ((?:\S+ ){7})(\S+) (\S+)( .*)?$", m.group(0), re.M))
    i = int(idx)
    if not 1 <= i <= len(refs):
        raise EditError("%s has %d Refer: lines, not %d" % (name, len(refs), i))
    r = refs[i - 1]
    body = m.group(0)
    new = body[:r.start()] + "Refer: %s%s %s%s" % (r.group(1), dx, dy, r.group(4) or "") + body[r.end():]
    return _replace_block(text, m, new), "%s Refer %d at %s %s" % (name, i, r.group(2), r.group(3))


def op_translateglyph(text, args, base):
    name, dx, dy = args.split()
    dx, dy = float(dx), float(dy)
    m = _one_block(text, name)
    body = m.group(0)
    if re.search(r"^(Refer|AnchorPoint|HStem|VStem|DStem2|TtInstrs):", body, re.M):
        raise EditError("%s has references, anchors or hints that would have to move too" % name)
    ss = re.search(r"^SplineSet\n(.*?)^EndSplineSet$", body, re.M | re.S)
    if not ss:
        raise EditError("%s has no outline" % name)

    def mv(line):
        t = line.split()
        k = next(i for i, x in enumerate(t) if x in ("m", "l", "c"))
        nums = [float(x) + (dx if i % 2 == 0 else dy) for i, x in enumerate(t[:k])]
        lead = line[:len(line) - len(line.lstrip())]
        return lead + " ".join(_fmt(v) for v in nums) + " " + " ".join(t[k:])
    moved = "\n".join(mv(l) for l in ss.group(1).rstrip("\n").split("\n")) + "\n"
    new = body[:ss.start(1)] + moved + body[ss.end(1):]
    return _replace_block(text, m, new), "%s outline as drawn" % name


def op_setglyphclass(text, args, base):
    name, cls = args.split()
    if cls not in ("0", "1", "2", "3", "4", "5"):
        raise EditError("GlyphClass %s is not one FontForge writes" % cls)
    m = _one_block(text, name)
    body = m.group(0)
    old = re.search(r"^GlyphClass: (\d)$", body, re.M)
    if old:
        new = body.replace(old.group(0), "GlyphClass: %s" % cls, 1)
    else:
        # FontForge writes GlyphClass: after Flags: (sfd.c SFDDumpChar)
        f = re.search(r"^Flags: .*\n", body, re.M)
        if not f:
            raise EditError("%s has no Flags: line to place GlyphClass: after" % name)
        new = body[:f.end()] + "GlyphClass: %s\n" % cls + body[f.end():]
    return _replace_block(text, m, new), "%s GlyphClass: %s" % (name, old.group(1) if old else "none (automatic)")


def op_dropglyph(text, args, base):
    name = args.strip()
    m = _one_block(text, name)
    enc = re.search(r"^Encoding: (-?\d+) (-?\d+) (\d+)$", m.group(0), re.M)
    gid = int(enc.group(3))
    if re.search(r"^(SplineSet|Refer:)", m.group(0), re.M):
        raise EditError("%s draws something; dropglyph removes only empty glyphs" % name)
    gids = [int(g) for g in re.findall(r"^Encoding: -?\d+ -?\d+ (\d+)$", text, re.M)]
    # references go by gid (and babelfont resolves them by file position): only the
    # last glyph can go without renumbering every glyph after it
    if gid != max(gids) or m.end() != _blocks(text)[-1].end():
        raise EditError("%s (gid %d) is not the last glyph; renumbering is not modelled" % (name, gid))
    if re.search(r"^Refer: %d " % gid, text, re.M):
        raise EditError("%s is referenced" % name)
    if re.search(r"(?<![\w.])%s(?![\w.])" % re.escape(name), text[:m.start()] + text[m.end():]):
        raise EditError("%s is named elsewhere in the file" % name)
    text = text[:m.start()] + text[m.end():].lstrip("\n")
    bc = re.search(r"^BeginChars: (\d+) (\d+)$", text, re.M)
    text = text[:bc.start()] + "BeginChars: %s %d" % (bc.group(1), int(bc.group(2)) - 1) + text[bc.end():]
    return text, "%s (Encoding: %s %s %d)" % (name, enc.group(1), enc.group(2), gid)


_LANG = re.compile(r'^LangName: (\d+) (.*)$', re.M)


def _langname(text, lang):
    head = text.split("\nStartChar:", 1)[0]
    for m in _LANG.finditer(head):
        if m.group(1) == lang:
            return m, re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
    return None, []


def _langline(lang, strings):
    while strings and not strings[-1]:
        strings = strings[:-1]
    return "LangName: %s %s " % (lang, " ".join('"%s"' % s for s in strings))


def op_setlangname(text, args, base):
    lang, nid, value = args.split(" ", 2)
    nid = int(nid)
    if '"' in value:
        raise EditError("setlangname takes a value without double quotes")
    if not value.isascii():
        value = value.encode("utf-7").decode("ascii")
    m, strings = _langname(text, lang)
    strings = strings + [""] * (nid + 1 - len(strings))
    before = strings[nid] or None
    strings[nid] = value
    line = _langline(lang, strings)
    if m:
        return text[:m.start()] + line + text[m.end():], before
    last = list(_LANG.finditer(text.split("\nStartChar:", 1)[0]))
    if not last:
        raise EditError("no LangName: record to insert beside")
    pos = last[-1].end()
    return text[:pos] + "\n" + line + text[pos:], None


def op_movelangname(text, args, base):
    lang, a, b = args.split()
    a, b = int(a), int(b)
    m, strings = _langname(text, lang)
    if not m or a >= len(strings) or not strings[a]:
        raise EditError("LangName %s has no name ID %d" % (lang, a))
    strings = strings + [""] * (b + 1 - len(strings))
    if strings[b]:
        raise EditError("LangName %s already has name ID %d (%s)" % (lang, b, strings[b]))
    strings[b], strings[a] = strings[a], ""
    return text[:m.start()] + _langline(lang, strings) + text[m.end():], \
        "LangName %s ID %d %r" % (lang, a, strings[b])


def op_droplangname(text, args, base):
    lang = args.strip()
    m, strings = _langname(text, lang)
    if not m:
        raise EditError("no LangName %s" % lang)
    return text[:m.start()] + text[m.end() + 1:], m.group(0)


# --- what an exporter did that the source does not state ---------------------------
_ANCHOR = re.compile(r'^(AnchorPoint: "(?:[^"\\]|\\.)*" )(\S+) (\S+)( .*)?$', re.M)


def op_truncateanchors(text, args, base):
    if args.strip():
        raise EditError("truncateanchors takes no arguments")
    changed, example = 0, None

    def trunc(m):
        nonlocal changed, example
        x, y = float(m.group(2)), float(m.group(3))
        if x.is_integer() and y.is_integer():
            return m.group(0)
        changed += 1
        if example is None:
            glyph = re.findall(r"^StartChar: (.*)$", text[:m.start()], re.M)
            example = "%s %s,%s" % (glyph[-1] if glyph else "?", m.group(2), m.group(3))
        # int() of a float truncates toward zero, as C's conversion to short does
        return "%s%d %d%s" % (m.group(1), int(x), int(y), m.group(4) or "")
    new = _ANCHOR.sub(trunc, text)
    if not changed:
        raise EditError("no anchor has a fractional coordinate")
    return new, "%d anchor(s) with fractional coordinates, e.g. %s" % (changed, example)


_SEG = re.compile(r"^ ?((?:-?[\d.]+(?:[eE][-+]?\d+)? )+)([mlc]) (\d+)(?:x[0-9a-fA-F]+)?(?:,(-?\d+)(?:,(-?\d+))?)?$")


def _sfdlib_contour(lines, glyph):
    """sfdLib 2.0.0's point list for one closed quadratic contour (parser.py
    _drawContours): [x, y, on, flags, number, text]. `flags` is the SFD flag number of an
    on-curve point; `number` its TrueType number (-1 implied) or, for a control point,
    the number its predecessor's line gives it as nextcpindex; None when a flagged point
    becomes a control point (it gets a number of its own). `text` is the coordinates as
    the file writes them (kept byte for byte, "-0" included)."""
    pts, force_open, nextcp, ends = [], False, None, []
    for line in lines:
        m = _SEG.match(line)
        if not m:
            raise EditError("%s: spline line not modelled: %r" % (glyph, line))
        toks = m.group(1).split()
        nums = [float(v) for v in toks]
        kind, flag = m.group(2), int(m.group(3))
        ttf = int(m.group(4)) if m.group(4) is not None else None
        force_open |= bool(flag & 0x400)
        ends.append(tuple(nums[-2:]))
        if kind == "c":
            if len(nums) != 6 or nums[0:2] != nums[2:4]:
                raise EditError("%s: a quadratic c line names one control point twice: %r" % (glyph, line))
            pts.append([nums[0], nums[1], False, None, nextcp, " ".join(toks[0:2])])
            # SFD_PTFLAG_INTERPOLATE: sfdLib emits the end point as an off-curve point
            on = not flag & 0x80
            pts.append([nums[4], nums[5], on, flag if on else None, ttf if on else None,
                        " ".join(toks[4:6])])
        else:
            pts.append([nums[0], nums[1], True, flag, ttf, " ".join(toks[0:2])])
        nextcp = int(m.group(5)) if m.group(5) is not None else None
    if force_open or len(pts) < 2 or ends[0] != ends[-1]:
        raise EditError("%s: an open contour with an interpolated point is not modelled" % glyph)
    # a closed contour: the closing segment's end point replaces the first one
    return [pts[-1]] + pts[1:-1]


def _sfd_quadratic_lines(pts, fresh, numbered):
    """FontForge quadratic spline lines for a cyclic [x, y, on, flags, number, text] in which
    two off-curve points are never adjacent, starting at pts[0] (on-curve). A point
    without a number gets fresh(); `numbered` False writes no TrueType numbers at all."""
    order = pts + [pts[0]]

    def suffix(k):
        if not numbered:
            return ""
        nxt = order[k + 1] if k + 1 < len(order) else order[1]
        if not nxt[2] and nxt[4] is None:
            nxt[4] = fresh()
        return ",%d,%d" % (order[k][4], -1 if nxt[2] else nxt[4])
    def xy(p):
        # a new point is written as the shortest decimal that reads back as exactly the
        # midpoint (FontForge's %.12g may not), so a reader can tell it is implied
        return p[5] if p[5] is not None else " ".join("%d" % v if v.is_integer() else repr(v) for v in p[:2])
    out = ["%s m %d%s" % (xy(order[0]), order[0][3], suffix(0))]
    k = 1
    while k < len(order):
        p = order[k]
        if p[2]:
            out.append(" %s l %d%s" % (xy(p), p[3], suffix(k)))
            k += 1
        else:
            e = order[k + 1]
            out.append(" %s %s %s c %d%s" % (xy(p), xy(p), xy(e), e[3], suffix(k + 1)))
            k += 2
    return out


def op_sfdlibinterpolated(text, args, base):
    if args.strip():
        raise EditError("sfdlibinterpolated takes no arguments")
    if not re.search(r"^Layer: 1 1 ", text, re.M):
        raise EditError("the Fore layer is not quadratic")

    def is_flagged(line):
        m = _SEG.match(line)
        return bool(m) and m.group(2) == "c" and bool(int(m.group(3)) & 0x80)
    total, glyphs, out, prev = 0, [], [], 0
    for b in _blocks(text):
        body = b.group(0)
        fore = re.search(r"^Fore\nSplineSet\n(.*?)^EndSplineSet\n", body, re.M | re.S)
        if not fore:
            continue
        lines = fore.group(1).rstrip("\n").split("\n")
        if not any(is_flagged(l) for l in lines):
            continue
        if re.search(r"^TtInstrs:", body, re.M):
            raise EditError("%s has TrueType instructions, which name points by number" % b.group(1))
        # the TrueType numbers FontForge keeps per point (sfd.c SFDDumpSplineSet): the
        # glyph's points keep theirs; a point this makes a control point gets an unused one
        matches = [_SEG.match(l) for l in lines]
        numbered = all(m and m.group(4) is not None for m in matches)
        used = [int(v) for m in matches if m for v in m.groups()[3:5] if v is not None]
        counter = iter(range(max(used + [-1]) + 1, 1 << 16))
        contours, cur = [], []
        for l in lines:
            if re.search(r" m \d", l) and cur:
                contours.append(cur)
                cur = []
            cur.append(l)
        contours.append(cur)
        new = []
        for c in contours:
            if not any(is_flagged(l) for l in c):
                new += c
                continue
            pts = _sfdlib_contour(c, b.group(1))
            # TrueType implies an on-curve point midway between two off-curve points;
            # FontForge stores it, flagged 0x80 (exported implied) with TrueType number -1
            expanded = []
            for i, p in enumerate(pts):
                expanded.append(p)
                q = pts[(i + 1) % len(pts)]
                if not p[2] and not q[2]:
                    expanded.append([(p[0] + q[0]) / 2, (p[1] + q[1]) / 2, True, 0x80, -1, None])
            if not expanded[0][2]:
                # sfdLib's contour starts on an off-curve point; the release's starts at
                # its first on-curve point (fontTools' BasePointToSegmentPen, which ufo2ft
                # draws through, moves to it), or, with none, at the implied point before
                k = next((i for i, p in enumerate(expanded) if p[2] and not p[3] & 0x80), len(expanded) - 1)
                expanded = expanded[k:] + expanded[:k]
            new += _sfd_quadratic_lines(expanded, lambda: next(counter), numbered)
            total += sum(1 for l in c[1:] if is_flagged(l))
        out.append(text[prev:b.start()])
        out.append(body[:fore.start(1)] + "\n".join(new) + "\n" + body[fore.end(1):])
        prev = b.end()
        glyphs.append(b.group(1))
    if not glyphs:
        raise EditError("no quadratic on-curve point is flagged 0x80")
    out.append(text[prev:])
    return "".join(out), "%d on-curve point(s) flagged 0x80 in %d glyph(s): %s" % (
        total, len(glyphs), " ".join(glyphs))


# --- edits from the release binary ---------------------------------------------
def release_file(spec):
    """google/fonts@<commit>:<path> -> a local copy of that blob (in TMPDIR)."""
    m = re.match(r"google/fonts@([0-9a-f]{7,40}):(\S+)$", spec)
    if not m:
        raise EditError("a release is named google/fonts@<commit>:<path>, not %r" % spec)
    r = subprocess.run(["git", "-C", GF, "show", "%s:%s" % m.groups()], capture_output=True)
    if r.returncode != 0:
        raise EditError("cannot read %s from %s: %s" % (spec, GF, r.stderr.decode(errors="replace").strip()))
    fd, path = tempfile.mkstemp(suffix=os.path.splitext(m.group(2))[1], prefix="release-")
    with os.fdopen(fd, "wb") as fh:
        fh.write(r.stdout)
    return path


def _fore_replace(body, spline, width):
    """Put `spline` in the glyph's Fore layer (removing its outline, references and
    hints there) and set its Width. A glyph block may carry a Back layer first, so the
    first SplineSet of the block is not necessarily the drawn one."""
    body = re.sub(r"^Width: -?\d+$", "Width: %d" % width, body, count=1, flags=re.M)
    body = re.sub(r"^TtInstrs:\n.*?^EndTTInstrs\n", "", body, flags=re.M | re.S)
    for f in ("HStem", "VStem", "DStem2", "DStem", "CounterMasks"):
        body = re.sub(r"^%s: .*\n" % f, "", body, flags=re.M)
    fore = re.search(r"^Fore\n", body, re.M)
    if fore:
        # the Fore layer runs to the next layer marker or the glyph's other records
        end = re.compile(r"^(?:Back|Layer: \d+|EndChar|Kerns2|KernsSLIF|Substitution2|AlternateSubs2|"
                         r"MultipleSubs2|Ligature2|Position2|PairPos2|AnchorPoint|Colour|Comment)\b", re.M)
        e = end.search(body, fore.end())
        layer = body[fore.end():e.start()]
        layer = re.sub(r"^SplineSet\n.*?^EndSplineSet\n", "", layer, flags=re.M | re.S)
        layer = re.sub(r"^Refer: .*\n", "", layer, flags=re.M)
        return body[:fore.end()] + spline + layer + body[e.start():]
    if re.search(r"^(Back|Layer: )", body, re.M):
        raise EditError("glyph has other layers but no Fore line")
    e = re.search(r"^EndChar", body, re.M)
    return body[:e.start()] + "Fore\n" + spline + body[e.start():]


def op_importoutlines(text, args, base):
    spec, *cps = args.split()
    if not cps or not all(re.match(r"U\+[0-9A-F]{4,6}$", c) for c in cps):
        raise EditError("importoutlines takes U+XXXX codepoints")
    from fontTools.ttLib import TTFont
    sys.path.insert(0, os.path.dirname(IMPORT_OUTLINES))
    import import_outlines as io_
    rel = release_file(spec)
    try:
        f = TTFont(rel)
        cmap = f.getBestCmap()
        quad = re.search(r"^Layer: 1 1 ", text, re.M)
        if not quad:
            raise EditError("the Fore layer is not quadratic")
        done, seen = [], set()
        for c in cps:
            u = int(c[2:], 16)
            g = cmap.get(u)
            if g is None:
                raise EditError("%s is not in the release" % c)
            if f["glyf"][g].isComposite():
                raise EditError("%s is a composite in the release; not modelled" % c)
            m = [b for b in _blocks(text)
                 if re.search(r"^Encoding: -?\d+ %d " % u, b.group(0), re.M)]
            if len(m) != 1:
                raise EditError("%d source glyphs encoded %s" % (len(m), c))
            m = m[0]
            if m.group(1) in seen:
                continue
            seen.add(m.group(1))
            spline = io_.splineset(io_.ttf_contours(f, g), cubic=False)
            text = _replace_block(text, m, _fore_replace(m.group(0), spline, f["hmtx"][g][0]))
            done.append(m.group(1))
    finally:
        os.remove(rel)
    return text, "%d glyphs as this source drew them: %s" % (len(done), " ".join(done))


_PST = re.compile(r'^((?:Substitution2|AlternateSubs2|MultipleSubs2|Ligature2): "(?:[^"\\]|\\.)*" )(.*)$', re.M)


def op_renameglyphs(text, args, base):
    from fontTools.ttLib import TTFont
    rel = release_file(args.strip())
    try:
        f = TTFont(rel)
        cmap = f.getBestCmap()
    finally:
        os.remove(rel)
    # glyph names also appear in class definitions and contextual rules; this op
    # renames only StartChar and substitution lines, so it refuses a source with those
    # ("MarkAttachClasses: 1" is FontForge's count for none)
    if re.search(r"^(KernClass|VKernClass|ContextSub2|ChainSub2|ContextPos2|ChainPos2|"
                 r"ReverseChain2|MarkAttachSets|MarkAttachClasses: ([2-9]|\d\d))", text, re.M):
        raise EditError("the source has glyph-name classes or contextual lookups; not modelled")
    names = [m.group(1) for m in _blocks(text)]
    if len(set(names)) != len(names):
        raise EditError("duplicated glyph names; rename those first")
    ren = {}
    for m in _blocks(text):
        e = re.search(r"^Encoding: -?\d+ (-?\d+) ", m.group(0), re.M)
        u = int(e.group(1)) if e else -1
        if u >= 0 and u in cmap and cmap[u] != m.group(1):
            ren[m.group(1)] = cmap[u]
    final = [ren.get(n, n) for n in names]
    if len(set(final)) != len(final):
        dup = sorted({n for n in final if final.count(n) > 1})
        raise EditError("renaming would duplicate %s" % " ".join(dup[:10]))
    if not ren:
        raise EditError("every encoded glyph already has the release's name")

    def sub_start(m):
        return "StartChar: %s" % ren.get(m.group(1), m.group(1))
    text = re.sub(r"^StartChar: (.*)$", sub_start, text, flags=re.M)

    def sub_pst(m):
        return m.group(1) + " ".join(ren.get(g, g) for g in m.group(2).split())
    text = _PST.sub(sub_pst, text)
    return text, "%d glyph names, e.g. %s" % (len(ren), ", ".join(
        "%s->%s" % kv for kv in sorted(ren.items())[:8]))


_GSUB_PST = ("Substitution2", "AlternateSubs2", "MultipleSubs2", "Ligature2")
_LOOKUP = re.compile(r'^Lookup: (\d+) (\d+) (\d+) "((?:[^"\\]|\\.)*)" *\{(.*?)\} *\[(.*)\] *\n', re.M)


def _drop_gsub(text):
    """Remove every GSUB lookup: its Lookup: line, its FPST sections and every glyph's
    lines filling its subtables."""
    head_end = text.index("\nBeginChars:")
    dropped, subtables = [], []
    for m in list(_LOOKUP.finditer(text[:head_end])):
        if int(m.group(1)) < 0x100:
            dropped.append(m.group(4))
            subtables += re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(5))
    text = _LOOKUP.sub(lambda m: "" if int(m.group(1)) < 0x100 else m.group(0), text[:head_end]) \
        + text[head_end:]
    for st in subtables:
        text = re.sub(r'^(?:ContextSub2|ChainSub2|ReverseChain2): \S+ "%s" .*?^EndFPST\n' % re.escape(st),
                      "", text, flags=re.M | re.S)
        text = re.sub(r'^(?:%s): "%s" .*\n' % ("|".join(_GSUB_PST), re.escape(st)), "", text, flags=re.M)
    for token in dropped + subtables:
        if '"%s"' % token in text:
            raise EditError("%r is still referenced after dropping the GSUB" % token)
    return text, dropped


def op_importgsub(text, args, base):
    from fontTools.ttLib import TTFont
    spec = args.strip()
    rel = release_file(spec)
    try:
        f = TTFont(rel)
        cmap = f.getBestCmap()
        if "GSUB" not in f:
            raise EditError("the release has no GSUB")
        t = f["GSUB"].table
    finally:
        os.remove(rel)
    have = [m.group(1) for m in _blocks(text)]
    by_uni = {}
    for m in _blocks(text):
        for e in re.findall(r"^Encoding: -?\d+ (-?\d+) ", m.group(0), re.M):
            if int(e) >= 0:
                by_uni.setdefault(int(e), m.group(1))
    rev = {}
    for u, g in sorted(cmap.items()):
        rev.setdefault(g, u)

    def src(g):
        if g in rev and rev[g] in by_uni:
            return by_uni[rev[g]]
        if g in have:
            return g
        raise EditError("release glyph %s has no counterpart in the source" % g)

    # registration: lookup index -> [(feature, script, [langs])]
    reg = {}
    for sr in t.ScriptList.ScriptRecord:
        langsys = [("dflt", sr.Script.DefaultLangSys)] + [(l.LangSysTag, l.LangSys) for l in sr.Script.LangSysRecord]
        for lang, ls in langsys:
            if ls is None:
                continue
            if ls.ReqFeatureIndex != 0xFFFF:
                raise EditError("required features are not modelled")
            for fi in ls.FeatureIndex:
                fr = t.FeatureList.FeatureRecord[fi]
                for li in fr.Feature.LookupListIndex:
                    ent = reg.setdefault(li, [])
                    hit = [x for x in ent if x[0] == fr.FeatureTag and x[1] == sr.ScriptTag]
                    if hit:
                        if lang not in hit[0][2]:
                            hit[0][2].append(lang)
                    else:
                        ent.append((fr.FeatureTag, sr.ScriptTag, [lang]))
    lookups = t.LookupList.Lookup
    names = []
    for i in range(len(lookups)):
        feats = sorted({x[0] for x in reg.get(i, [])})
        names.append("'%s' lookup %d" % ("+".join(feats), i) if feats else "contextual target lookup %d" % i)
    lookup_lines, fpst, pst = [], [], []      # pst: (glyph, line)
    kinds = {1: 1, 2: 2, 3: 3, 4: 4, 6: 6}
    for i, lk in enumerate(lookups):
        typ, subs = lk.LookupType, list(lk.SubTable)
        if typ == 7:
            typ = subs[0].ExtensionLookupType
            subs = [s.ExtSubTable for s in subs]
        if typ not in kinds:
            raise EditError("GSUB lookup type %d is not modelled" % typ)
        if lk.LookupFlag & ~0xF:
            raise EditError("lookup %d: mark attachment / filtering flags are not modelled" % i)
        stnames = ["%s subtable %d" % (names[i], j) for j in range(len(subs))]
        for st, sub in zip(stnames, subs):
            if typ == 1:
                for a, b in sub.mapping.items():
                    pst.append((src(a), 'Substitution2: "%s" %s' % (st, src(b))))
            elif typ == 2:
                for a, seq in sub.mapping.items():
                    pst.append((src(a), 'MultipleSubs2: "%s" %s' % (st, " ".join(src(g) for g in seq))))
            elif typ == 3:
                for a, alts in sub.alternates.items():
                    pst.append((src(a), 'AlternateSubs2: "%s" %s' % (st, " ".join(src(g) for g in alts))))
            elif typ == 4:
                for first, ligs in sub.ligatures.items():
                    for l in ligs:
                        pst.append((src(l.LigGlyph), 'Ligature2: "%s" %s' % (
                            st, " ".join(src(g) for g in [first] + list(l.Component)))))
            else:
                if sub.Format != 3:
                    raise EditError("lookup %d: chaining format %d is not modelled" % (i, sub.Format))

                def cov(tag, c):
                    gl = " ".join(src(g) for g in c.glyphs)
                    return "  %s: %d %s" % (tag, len(gl), gl)
                recs = sub.SubstLookupRecord
                lines = ['ChainSub2: coverage "%s"  0 0 0 1' % st,
                         " %d %d %d" % (len(sub.InputCoverage), len(sub.BacktrackCoverage),
                                        len(sub.LookAheadCoverage))]
                lines += [cov("Coverage", c) for c in sub.InputCoverage]
                lines += [cov("BCoverage", c) for c in sub.BacktrackCoverage]
                lines += [cov("FCoverage", c) for c in sub.LookAheadCoverage]
                lines.append(" %d" % len(recs))
                lines += ['  SeqLookup: %d "%s"' % (r.SequenceIndex, names[r.LookupListIndex]) for r in recs]
                lines.append("EndFPST")
                fpst.append("\n".join(lines) + "\n")
        # FontForge's form: each feature once, its scripts and their languages inside
        tags = []
        for tag, _s, _l in reg.get(i, []):
            if tag not in tags:
                tags.append(tag)
        feat = " ".join("'%s' (%s )" % (tag, " ".join(
            "'%s' <%s >" % (script, " ".join("'%s'" % l.ljust(4)[:4] for l in langs))
            for tg, script, langs in reg[i] if tg == tag)) for tag in tags)
        lookup_lines.append('Lookup: %d %d 0 "%s" {%s } [%s ]' % (
            kinds[typ], lk.LookupFlag, names[i], " ".join('"%s" ' % s for s in stnames), feat))
    text, dropped = _drop_gsub(text)
    # GSUB lookups come first in FontForge's list; the FPST sections follow the lookups
    existing = list(re.finditer(r"^Lookup: .*\n", text, re.M))
    pos = existing[0].start() if existing else re.search(
        r"^(?:MarkAttachClasses|DEI|LangName|GaspTable|Encoding|BeginChars):", text, re.M).start()
    text = text[:pos] + "".join(l + "\n" for l in lookup_lines) + text[pos:]
    last = list(re.finditer(r"^Lookup: .*\n", text, re.M))[-1]
    text = text[:last.end()] + "".join(fpst) + text[last.end():]
    by_glyph = {}
    for g, line in pst:
        by_glyph.setdefault(g, []).append(line)
    out, prev = [], 0
    for m in _blocks(text):
        lines = by_glyph.pop(m.group(1), None)
        if lines:
            out.append(text[prev:m.end() - len("EndChar\n")])
            out.append("".join(l + "\n" for l in lines) + "EndChar\n")
            prev = m.end()
    out.append(text[prev:])
    if by_glyph:
        raise EditError("glyphs not found for: %s" % " ".join(sorted(by_glyph)))
    return "".join(out), "%d GSUB lookup(s): %s" % (len(dropped), "; ".join(dropped))


# --- build-script steps ---------------------------------------------------------
def _ff(fn, *a):
    import ff_build_ops
    try:
        return fn(ff_build_ops, *a)
    except ff_build_ops.OpError as e:
        raise EditError(str(e))


def _file(base, rel):
    p = os.path.normpath(os.path.join(base, rel))
    if not os.path.isfile(p):
        raise EditError("no %s beside the .sfd" % rel)
    return p


def op_mergefea(text, args, base):
    new, what = _ff(lambda m: m.mergefea(text, _file(base, args.strip())))
    return new, "no GSUB from %s (%s)" % (args.strip(), what)


def op_mergepsfont(text, args, base):
    pfa, prefix = args.split()
    new, what = _ff(lambda m: m.mergepsfont(text, _file(base, pfa), None, prefix))
    return new, "%d glyphs; merged: %s" % (len(_blocks(text)), what)


def op_afmligatures(text, args, base):
    toks = shlex.split(args)
    if len(toks) < 2:
        raise EditError("afmligatures <lookup name> <lig>=<a>+<b>...")
    lookup, rules = toks[0], toks[1:]
    if re.search(r'^Lookup: \d+ \d+ \d+ "%s"' % re.escape(lookup), text, re.M):
        raise EditError("lookup %r already exists" % lookup)
    import ff_build_ops as fb
    try:
        for r in rules:
            lig, comps = r.split("=", 1)
            text = fb.add_glyph_lines(text, lig, ['Ligature2: "%s subtable" %s' % (lookup, " ".join(comps.split("+")))])
        text = fb.add_lookup_lines(text, ['Lookup: 4 0 1 "%s" {"%s subtable"  } [\'liga\' (\'latn\' <\'dflt\' > ) ]'
                                          % (lookup, lookup)])
    except (fb.OpError, ValueError) as e:
        raise EditError(str(e))
    return text, "no %r lookup" % lookup


def op_obliqize(text, args, base):
    angle, first, last = args.split()
    new, what = _ff(lambda m: m.unlink_and_skew(text, float(angle), int(first, 16), int(last, 16)))
    return new, "upright (%s)" % what


def op_pastepsglyphs(text, args, base):
    pfa, *glyphs = args.split()
    new, what = _ff(lambda m: m.pastepsglyphs(text, _file(base, pfa), glyphs))
    return new, "the font's own %s (%s)" % (" ".join(glyphs), what)


MORE_OPS = {
    "setencoding": op_setencoding, "setwidth": op_setwidth, "setrefer": op_setrefer,
    "translateglyph": op_translateglyph, "setglyphclass": op_setglyphclass, "dropglyph": op_dropglyph,
    "setlangname": op_setlangname, "movelangname": op_movelangname, "droplangname": op_droplangname,
    "importoutlines": op_importoutlines, "renameglyphs": op_renameglyphs, "importgsub": op_importgsub,
    "mergefea": op_mergefea, "mergepsfont": op_mergepsfont, "afmligatures": op_afmligatures,
    "obliqize": op_obliqize, "pastepsglyphs": op_pastepsglyphs,
    "truncateanchors": op_truncateanchors, "sfdlibinterpolated": op_sfdlibinterpolated,
}


def apply_file(path, op, args):
    base = os.path.dirname(os.path.abspath(path))
    if op == "generatefrom":
        # the one op that creates its file: a build script's generated intermediate
        if os.path.exists(path):
            raise EditError("%s already exists; generatefrom creates a new source" % path)
        src = os.path.join(base, args.strip())
        if not os.path.isfile(src):
            raise EditError("generatefrom: no %s" % src)
        with open(src, encoding="utf-8", errors="surrogateescape") as fh:
            new = fh.read()
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
            fh.write(new)
        return "absent (copied from %s)" % args.strip(), True
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        text = fh.read()
    new, before = apply(text, op, args, base)
    if new == text and op != "ensurefield":
        raise EditError("%s %s changed nothing in %s" % (op, args, path))
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write(new)
    return before, new != text


if __name__ == "__main__":
    try:
        before, changed = apply_file(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
    except EditError as e:
        sys.exit("FATAL: %s" % e)
    print("%s %s: before=%r changed=%s" % (sys.argv[2], " ".join(sys.argv[3:]), before, changed))
