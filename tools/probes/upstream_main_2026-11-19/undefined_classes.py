#!/usr/bin/env python3
"""Question answered: does a converted .glyphs carry feature code that names classes nothing
defines -- neither a feature class of the file nor a kerning group (babelfont main turns FontLab
kerning classes into kerning groups and no longer defines them for the VFB's own feature code)?

Usage: undefined_classes.py <converted .glyphs>...   -> one line per file: undefined class names
"""
import re
import sys

import glyphsLib

for path in sys.argv[1:]:
    f = glyphsLib.GSFont(path)
    code = "\n".join([c.code for c in f.featurePrefixes] + [x.code for x in f.features])
    code = re.sub(r"#[^\n]*", "", code)
    defined = {c.name for c in f.classes} | set(re.findall(r"@([\w.\-]+)\s*=", code))
    used = set(re.findall(r"@([\w.\-]+)", code)) - defined
    print("%s\t%d undefined\t%s" % (path.rsplit("/", 1)[-1], len(used), " ".join(sorted(used)[:4])))
