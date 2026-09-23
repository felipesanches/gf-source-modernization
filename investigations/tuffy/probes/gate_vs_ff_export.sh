#!/bin/bash
# Question: how far is our baseline build of Tuffy Regular/Italic from
# FontForge's OWN 2011 export of the same .sfd (v001.271, the monorepo's
# ofl/tuffy/Tuffy-<Style>.ttf at 52f780b -- byte-identical to what google/fonts
# shipped 2015-03 .. 2017-10), rather than from the 2017 v1.272 release?
# Needs the baseline build first:  TAG=tuffy OUT=... tools/baseline.sh <Style>
# Usage: gate_vs_ff_export.sh <Style> <built.ttf> <outdir>
set -euo pipefail
style=$1; built=$2; out=$3; mkdir -p "$out"
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
ref=$out/$style.ff-export-001.271.ttf
git -C "$ARC" show "52f780bc9d197280a9f430574e179a5f233c56b6:ofl/tuffy/$style.ttf" > "$ref"
"$D3" -J 1 --no-languages --no-match --json --succinct "$ref" "$built" > "$out/$style.d3.json" 2>/dev/null || true
"$PY" "$TG" "$out/$style.d3.json" --fonts "$ref" "$built" > "$out/$style.gate.txt" 2>&1 || true   # the gate exits non-zero when rows block
grep -v ACCEPTED "$out/$style.gate.txt" | grep -E '^(BLOCKING|[0-9]+ blocking)'
