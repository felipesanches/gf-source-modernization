#!/usr/bin/env python3
"""Documented source edits to a converted .glyphs (Glyphs 3) file, as plain text, so that each
edit's commit shows exactly the lines it changes. tools/land.py applies them after the conversion
from a plan's `source_edits` (one "Source edit: ..." commit each); tools/sfd_edit.py is the
counterpart for .sfd files before the conversion.

Ops (args is one string):
  rename      "OLD NEW; OLD2 NEW2"   rename glyphs, all at once (so a swap works): the glyph,
                                     component references, kerning, feature and class code, and
                                     the glyphOrder parameter. Refuses an OLD that is not a glyph
                                     or a NEW that already is one (outside the renames).
  setparam    "NAME=JSON"            set a font-level custom parameter's value (JSON: a number,
                                     a string, or a list, e.g. fsType=[])
  setprop     "KEY=VALUE"            set a font-level singular property's value (e.g.
                                     postscriptFontName=IrishGrover-Regular)
  setnameentry "ID=VALUE"            set the font-level "Name Table Entry" parameter for name ID
                                     ID (value "ID; VALUE")

Usage: glyphs_edit.py <file.glyphs> <op> <args>      (edits the file in place)
"""
import json
import re
import sys

NAME_CHARS = r"A-Za-z0-9._\-"


def _plist(v):
    if isinstance(v, list):
        return "(" + ",".join(_plist(x) for x in v) + ")"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if re.fullmatch(r"[A-Za-z0-9._/]+", s) and not re.fullmatch(r"[0-9.]+", s):
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _top_block(lines, key):
    """(start, end) line indices of the font-level `key = (` ... `);` block."""
    depth, start = 0, None
    for i, line in enumerate(lines):
        if depth == 1 and start is None and line == "%s = (" % key:
            start = i
        depth += line.count("{") + line.count("(") - line.count("}") - line.count(")")
        if start is not None and i > start and depth == 1:
            return start, i
    return None


def rename(text, args):
    pairs = [p.split() for p in args.split(";") if p.strip()]
    mapping = {a: b for a, b in pairs}
    glyphs = set(re.findall(r'^glyphname = "?([^";]+)"?;$', text, re.M))
    for old, new in mapping.items():
        if old not in glyphs:
            raise ValueError("no glyph %r" % old)
        if new in glyphs and new not in mapping:
            raise ValueError("glyph %r already exists" % new)
    token = re.compile(r"(?<![%s])(%s)(?![%s])" % (NAME_CHARS, "|".join(map(re.escape, mapping)), NAME_CHARS))
    sub = lambda s: token.sub(lambda m: mapping[m.group(1)], s)
    out, in_code, kern_depth, in_order = [], False, 0, False
    for line in text.split("\n"):
        start_code = line.startswith("code = ") or in_code
        if line.startswith(("glyphname = ", "ref = ")) or start_code or kern_depth or in_order:
            line = sub(line)
        if line.startswith("code = "):
            in_code = not re.search(r'(?<!\\)";$', line)
        elif in_code and re.search(r'(?<!\\)";$', line):
            in_code = False
        if re.match(r"^kerning(LTR|RTL|Vertical) = \{$", line):
            kern_depth = 1
        elif kern_depth:
            kern_depth += line.count("{") - line.count("}")
        if line == "name = glyphOrder;":
            in_order = True
        elif in_order and line.endswith(");"):
            in_order = False
        out.append(line)
    return "\n".join(out)


def setparam(text, args, match=None):
    name, value = args.split("=", 1)
    lines = text.split("\n")
    block = _top_block(lines, "customParameters")
    if block is None:
        raise ValueError("no font-level customParameters")
    s, e = block
    for i in range(s, e):
        if lines[i] in ("name = %s;" % name, 'name = "%s";' % name):
            j = i + 1
            if not lines[j].startswith("value = "):
                raise ValueError("unexpected layout after %s" % lines[i])
            k = j
            while not lines[k].endswith(";"):
                k += 1
            if match is not None and not match("\n".join(lines[j:k + 1])):
                continue
            lines[j:k + 1] = ["value = %s;" % value]
            return "\n".join(lines)
    raise ValueError("no font-level custom parameter %r" % name)


def setnameentry(text, args):
    nid, value = args.split("=", 1)
    want = '"%s; ' % nid
    return setparam(text, 'Name Table Entry=%s' % _plist("%s; %s" % (nid, value)),
                    match=lambda v: want in v)


def setprop(text, args):
    key, value = args.split("=", 1)
    lines = text.split("\n")
    block = _top_block(lines, "properties")
    if block is None:
        raise ValueError("no font-level properties")
    s, e = block
    for i in range(s, e):
        if lines[i] == "key = %s;" % key and lines[i + 1].startswith("value = "):
            lines[i + 1] = "value = %s;" % _plist(value)
            return "\n".join(lines)
    raise ValueError("no font-level singular property %r" % key)


OPS = {"rename": rename, "setnameentry": setnameentry, "setprop": setprop,
       "setparam": lambda t, a: setparam(t, a.split("=", 1)[0] + "=" + _plist(json.loads(a.split("=", 1)[1])))}


def apply_file(path, op, args):
    # newline="": keep CR and CRLF inside strings (licence texts, feature code) byte for byte
    before = open(path, encoding="utf-8", newline="").read()
    after = OPS[op](before, args)
    if after != before:
        open(path, "w", encoding="utf-8", newline="").write(after)
    return before, after != before


if __name__ == "__main__":
    _, changed = apply_file(sys.argv[1], sys.argv[2], sys.argv[3])
    print("changed" if changed else "unchanged")
