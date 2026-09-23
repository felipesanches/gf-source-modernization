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

and one this workspace adds:

  scaleem <em>                    change the em as FontForge 20100501's `f.em = <em>`
                                  did (tools/ff_scale_em.py, from the puritan
                                  investigation: its port reproduces a released glyf
                                  point for point)

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
    if op == "renameglyph":
        old, new = args.split()
        if not re.search(r"^StartChar: %s$" % re.escape(old), text, re.M):
            raise EditError("no StartChar: %s to rename" % old)
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
