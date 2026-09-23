#!/bin/sh
# Question answered: is Comic Relief's released post.underlinePosition (-97)
# exactly what its own release toolchain -- sfdLib 2.0.0.post0 `sfd2ufo`
# (requirements.txt at loudifier/Comic-Relief 856315f = tag v1.2) followed by
# ufo2ft -- makes of the UNMODIFIED .sfd (UnderlinePosition -185,
# UnderlineWidth 175)?
#
# Fetches the two pure-Python wheels from PyPI (sha256-checked) into a scratch
# dir, runs sfdLib's parser on each style's .sfd from the READ-ONLY archive, and
# compiles the resulting UFO with ufo2ft from the gftools venv. Prints, per style:
# the .sfd's two fields, sfdLib's postscriptUnderlinePosition, the compiled
# post.underlinePosition, and the release's.
#
# Usage: sh probes/sfdlib_underline.sh [scratch-dir]
# Expected (EXPECTED-sfdlib_underline.txt): sfdLib -97.5, compiled -97, release -97.
set -eu
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
D=${1:-/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-small/sfdlib}
mkdir -p "$D"
fetch() {  # url sha256
  f="$D/$(basename "$1")"
  [ -s "$f" ] || curl -sfL -o "$f" "$1"
  echo "$2  $f" | sha256sum -c --quiet
  (cd "$D" && unzip -qo "$f")
}
fetch https://files.pythonhosted.org/packages/87/a1/f92a8f0c7ed542f323edcc26585fe28aace9948c1b04fdc13d99df737b3d/sfdLib-2.0.0.post0-py3-none-any.whl \
      18aae8c93ac6f6e990bc6ee1cf1abacb2af1093c80163d381c327ce957aa2e6e
fetch https://files.pythonhosted.org/packages/b8/31/b73dcd68274a47f339bc54cc749230d85d7a053c2c04a849cf1d51593e16/sfdutf7-0.1.0-py3-none-any.whl \
      fa66a97f4c102cbc408a5b2a8a7f5d21de3a56cefbc556dff7c64e2318a35d30
echo "sfdLib/parser.py lines that decide the value:"
grep -n -A1 'FontForge does not match OpenType here' "$D/sfdLib/parser.py"

PYTHONPATH="$D" "$PY" - "$D" <<'EOF'
import subprocess, sys, os
from ufoLib2 import Font
from sfdLib.parser import SFDParser
import ufo2ft
from fontTools.ttLib import TTFont
ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/loudifier/Comic-Relief.git"
C = "856315f5a45dfdad75090e4454f1ebfd019296b9"
D = sys.argv[1]
for s in ("Regular", "Bold"):
    sfd = os.path.join(D, "ComicRelief-%s.sfd" % s)
    with open(sfd, "wb") as fh:
        fh.write(subprocess.check_output(["git", "-C", ARC, "show", "%s:sources/ComicRelief-%s.sfd" % (C, s)]))
    fields = {}
    for line in open(sfd, encoding="utf-8", errors="replace"):
        k = line.split(":", 1)[0]
        if k in ("UnderlinePosition", "UnderlineWidth"):
            fields[k] = line.split(":", 1)[1].strip()
        if line.startswith("BeginChars"):
            break
    ufo = Font()
    SFDParser(sfd, ufo, False, False, False).parse()
    built = ufo2ft.compileTTF(ufo, removeOverlaps=False)
    rel = TTFont("/home/fsanches/compartilhado/google/fonts/ofl/comicrelief/ComicRelief-%s.ttf" % s)
    print("%-8s sfd UnderlinePosition %s UnderlineWidth %s | sfdLib postscriptUnderlinePosition %s "
          "thickness %s | ufo2ft post.underlinePosition %d thickness %d | release %d %d"
          % (s, fields["UnderlinePosition"], fields["UnderlineWidth"],
             ufo.info.postscriptUnderlinePosition, ufo.info.postscriptUnderlineThickness,
             built["post"].underlinePosition, built["post"].underlineThickness,
             rel["post"].underlinePosition, rel["post"].underlineThickness))
EOF
