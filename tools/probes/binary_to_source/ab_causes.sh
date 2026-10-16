#!/bin/sh
# Question answered: of the families converter_ab.py found DIFFERENT, which differ by
# localized name records (a Name Table Entry with a Windows language id, 0x0...: what
# simoncozens/babelfont-rs#117 writes) and which by anything else (typographic-family-names:
# name IDs 16/17 entries and the typographic familyName)?
#
#   sh ab_causes.sh <converter_ab output> <its scratch dir>
#
# Prints one line per DIFFERENT repository: its name, the number of changed lines with a
# language id, and the number of other changed lines (braces and the bare
# `name = "Name Table Entry";` line not counted).
set -eu
OUT=${1:?converter_ab output}
SCRATCH=${2:?converter_ab scratch dir}
awk '$2 == "DIFFERENT" {print $1}' "$OUT" | while read -r repo; do
  lines=$(cat "${SCRATCH:?}/${repo:?}"/*.diff | grep -E '^[-+]' | grep -v -E '^(\+\+\+|---)' || true)
  localized=$(printf '%s\n' "$lines" | grep -c '0x0' || true)
  other=$(printf '%s\n' "$lines" | grep -v -E '0x0|^[-+][{}(),; ]*$|^[-+]name = "Name Table Entry";$' | grep -c . || true)
  printf '%-22s %4d %4d\n' "$repo" "$localized" "$other"
done
