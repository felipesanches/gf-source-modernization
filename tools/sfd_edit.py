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

An operation that cannot apply is FATAL: a silently skipped correction is how a
defect ships. Every edit reports what the field said before, so a plan cannot
overwrite a value the designer stated without the commit saying so.

Usage (for testing a plan by hand):
  sfd_edit.py <file.sfd> <op> [args...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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


def apply(text, op, args):
    """Apply one operation; return (new_text, before) where `before` describes
    what the source stated beforehand (for the commit body)."""
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


def apply_file(path, op, args):
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        text = fh.read()
    new, before = apply(text, op, args)
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
