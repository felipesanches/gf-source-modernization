#!/bin/sh
# Question answered: does Datatype's static build ("No master was present at location ...") fail
# because the TTF reader marks its masters inactive (active = 0), because its instances sit at
# F2Dot14-rounded locations (wght 700.0183), or neither?
# Builds four copies of the probe's converted source with the probe's own config (buildVariable:
# false): as converted, without "active = 0", with whole-number instance locations, and both.
#   B3=<gftools-builder> sh datatype_static_variants.sh <probe's Datatype[wdth,wght]/sources> <scratch>
# Result 2026-11-12 (gftools-builder of tools/land.py B3_DEFAULT): all four fail the same way, at the
# first instance off a master (only "exact" got one static out first: Black, at a master's
# location; which job finishes first varies). With buildVariable:
# false and more than one master, gftools-builder makes each static with InstantiateSource, which
# needs a master at the instance's location. Neither the flag nor the rounding is the cause.
set -eu
SRC=${1:?sources dir}; T=${2:?scratch}; B3=${B3:?gftools-builder}
G='Datatype[wdth,wght].glyphs'
for v in asis active exact both; do
  mkdir -p "$T/$v/sources"; cp "$SRC/config.yaml" "$T/$v/sources/"
  python3 - "$SRC/$G" "$T/$v/sources/$G" "$v" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
if sys.argv[3] in ("exact", "both"):
    s = re.sub(r'axesValues = \(100,(\d+\.\d+)\);', lambda m: 'axesValues = (100,%d);' % round(float(m.group(1))), s)
if sys.argv[3] in ("active", "both"):
    s = s.replace('\nactive = 0;\n', '\n')
open(sys.argv[2], 'w').write(s)
PY
  (cd "$T/$v/sources" && "$B3" config.yaml > ../build.log 2>&1) || true
  echo "$v: $(ls "$T/$v/fonts/ttf" 2>/dev/null | wc -l) font(s); $(grep -m1 'No master' "$T/$v/build.log" | sed 's/.*Filter error: //')"
done
