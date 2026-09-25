# babelfont-rs PR #95: does 8042926 change behaviour against b4dc853?

Question: after 8042926 moved the `sfntRevision` parse from a step after the
header into the `sfntRevision` arm (with a flag that stops `Version` from
overwriting it), does the SFD reader give the same `Font`, and does the SFD
round trip still hold?

Command (about 10 minutes, two debug builds):

    tools/probes/pr95_sfnt_revision_review/run.sh

- `harness.rs` is appended to `babelfont/src/convertors/fontforge/tests.rs` in a
  `git archive` copy of each commit. It loads every ordered arrangement of up to
  three lines taken from 3 `Version:` and 8 `sfntRevision:` variants (1112
  headers: valid, negative, unparseable, empty, out-of-range). For each one it
  records `font.version`, name ID 5, the raw `format_specific["sfntRevision"]`,
  the whole `Font` as JSON (minus `date`, the load time), the emitted SFD, and
  whether `load(emit(font))` gives the same `font.version` and the same SFD.
  It also loads every unique `.sfd` of the local corpus (845 files) and records
  `font.version`, the raw `sfntRevision` and a hash of the emitted SFD.
- `compare.py` diffs the two dumps. `RESULT.txt` is its output for the run on
  2026-09-25.

Reading `RESULT.txt`:

- "differing" headers are the ones where anything recorded differs.
- Every differing header has two or more `sfntRevision` lines, a valid one
  followed by a later invalid one. b4dc853 let the last line decide (invalid
  meant `Version`); 8042926 keeps the earlier valid value, while the writer still
  emits only the last raw line, so `font.version` changes over a round trip in
  those headers (28 to 200 round-trip changes; the 28 in both are headers with
  several `Version` lines). FontForge never writes a second `sfntRevision` line,
  and none of the 845 corpus files has one.
- With at most one `Version` and one `sfntRevision` line, in either order and
  including missing, negative and unparseable values, both commits agree on
  everything recorded and the round trip holds.
- Corpus: all 845 lines identical between the commits (5 files fail to load in
  both, for reasons unrelated to the header).
