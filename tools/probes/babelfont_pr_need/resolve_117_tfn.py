#!/usr/bin/env python3
"""Resolve the textual conflict between glyphs3-localized-name-entries (#117) and
typographic-family-names in glyphs3/customparameters.rs by keeping both sides: the union of
the imports, then #117's additions followed by typographic-family-names' NameTableEntry.
Used once, in the combined converter's worktree, before committing the trial merge:

    python3 resolve_117_tfn.py <worktree>/babelfont/src/convertors/glyphs3/customparameters.rs
"""
import re
import sys

p = sys.argv[1]
s = open(p).read()
s = s.replace("<<<<<<< HEAD\n    convertors::glyphs3::{get_cp, KEY_CUSTOM_PARAMETERS},",
              "    convertors::glyphs3::{get_cp, glyphs_family_name, KEY_CUSTOM_PARAMETERS},", 1)
s = re.sub(r"(    BabelfontError, Font, MetricType, NameId,\n)=======\n.*?>>>>>>> typographic-family-names\n",
           r"\1", s, count=1, flags=re.S)
s = re.sub(r"<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> typographic-family-names\n",
           lambda m: m.group(1) + "}\n\n" + m.group(2), s, count=1, flags=re.S)
assert "<<<<<<<" not in s and ">>>>>>>" not in s
open(p, "w").write(s)
