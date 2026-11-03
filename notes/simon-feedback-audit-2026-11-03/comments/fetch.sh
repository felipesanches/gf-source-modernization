#!/bin/sh
# Downloads the comment threads simon-*.txt is extracted from (unauthenticated API, about 20 calls).
# Usage: sh fetch.sh <scratch dir>; then python3 -I extract.py <scratch dir> > simon-<from>-to-<to>.txt
set -u
cd "${1:?scratch dir}"
for p in 1 2 3; do curl -s -o bf-all-$p.json "https://api.github.com/repos/simoncozens/babelfont-rs/issues/comments?since=2026-05-01T00:00:00Z&per_page=100&page=$p"; done
for x in fonttools/fontspector:667 fonttools/fontspector:669 fonttools/fontspector:670 fonttools/fontspector:684 googlefonts/fontc_crater:100 googlefonts/gftools:1170 googlefonts/googlesans-flex:945 simoncozens/gftools-builder3:1 simoncozens/babelfont-rs:131; do r=${x%:*}; n=${x#*:}; curl -s -o "c-$(echo $r | tr / _)-$n.json" "https://api.github.com/repos/$r/issues/$n/comments?per_page=100"; done
curl -s -o rev-bf-131.json "https://api.github.com/repos/simoncozens/babelfont-rs/pulls/131/reviews"
curl -s -o rc-bf-131.json "https://api.github.com/repos/simoncozens/babelfont-rs/pulls/131/comments"
for p in 1 2; do curl -s -o gfrust-$p.json "https://api.github.com/repos/simoncozens/gftools-rust/issues/comments?since=2026-05-01T00:00:00Z&per_page=100&page=$p"; done
curl -s -o glyphslib-rs.json "https://api.github.com/repos/simoncozens/glyphslib-rs/issues/comments?since=2026-05-01T00:00:00Z&per_page=100"
for p in 1 2; do curl -s -o "gfonts-10490-$p.json" "https://api.github.com/repos/google/fonts/issues/10490/comments?per_page=100&page=$p"; done
echo done
