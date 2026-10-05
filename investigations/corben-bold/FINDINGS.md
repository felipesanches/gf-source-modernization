# corben-bold -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Corben-Bold failed to build because its `.sfd` names two glyphs `dcroat` (gid 211, the real
U+0111, and gid 547, empty and unencoded); fontc reports that only as "N jobs stuck pending".
Renaming gid 547 alone lets it build; the vertical metrics from the sibling
`Corben-Bold-TTF.sfd`, the family's vendor and the release's PANOSE close 8 more rows. The
verifier found the recipe's `--add-legacy-duplicate-cmap` rule misfiring, which led to a
measurement across all 42 styles (tools/probes/cmap_recipe/): the flag is never right for
these FontForge exports, and 11 landed styles had gained codepoints the table gate tolerates.
The flag is now never passed, and the cmap is checked exactly.

## Investigator's report

E1 (rename gid 547 dcroat -> dcroat.1) turns BUILD-FAILED into a finished gate with 11
rows. Cumulative runs: +E2 11->5, +E3 5->4, +E4 4->3, dropping --add-legacy-duplicate-
cmap 3->3 with empty cmap_diff. Each step closed exactly its rows and opened none; every
gate printed its closing 'N blocking table difference(s)' line. All 551 common glyphs
have equal advances and equal areas vs the release; tight bounds differ only for
AE/Lslash/lslash (9/5/5 units), which is the release's stale lsb: FontForge 2011 wrote
glyf xMin = hmtx lsb from on-curve points (-10/3/-38), and the 2015 fontTools save in
google/fonts 5b1755d5a recomputed xMin (-19/-2/-43) without the lsb (gate: RELEASE-
STALE). Tools: babelfont gf-sfd-conversion f725e6a (binary mtime 20:27:57, before
ca43adc; sha256 prefix f96e0851990f4807), gftools-builder3 e851b8b (fontc 1.0.0, sha256
prefix d6dd442c2cb549fa), diffenator3 1.1.4, table_gate.py md5
d99eadad22d0ec57d119ba6ce517ed07 (sfd-batch5 cd4f827), baseline.sh md5
e5b0b4033b3bc7c99c29ba3b4c6de46a, release google/fonts b5efa9c32e8f.

Rows before: BUILD-FAILED (Unable to proceed; 648 jobs stuck pending); after E1 alone the build completes and shows 11 blocking: hhea.ascender, hhea.descender, OS/2.s_typo_ascender, OS/2.s_typo_descender, OS/2.us_win_ascent, OS/2.us_win_descent, OS/2.ach_vend_id, OS/2.panose_10, OS/2.us_weight_class, OS/2.sx_height, OS/2.s_cap_height

Rows after: 3 blocking: OS/2.us_weight_class [700,400], OS/2.sx_height [1296,500], OS/2.s_cap_height [1593,700] -- all three the converter work in progress (TTFWeight: 700 stated; oracle MATCH 1296/1593). cmap_diff {} with the flag dropped. 10 RELEASE-STALE non-blocking rows unchanged throughout.

Confidence: high: the build-failure cause is shown three ways (fontc's blocked-job list, the source code, and a minimal repro that fails with a duplicate name and builds when it is renamed). All 4 edits and the flag drop were checked with baseline.sh one run at a time, and each gate printed its closing line. The classifications for vendor (value taken from the sibling style's sources) and PANOSE (value found only in the release) are judgement calls, and both are stated plainly.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Corben-Bold | BUILD-FAILED: operation 'Fontc' ... Unable to proceed; 648 jobs stuck pending | build-failure | Source defect: src/Corben-Bold.sfd has two glyphs named 'dcroat': gid 211 (Encoding 273 273 211, U+0111, the real glyph) and gid 547 (Encoding 65704 -1 547, Width 0, no outline, carrying only the smcp/aalt Substitution2 lines to dcroat.sc). babelfont writes both as 'glyphname = dcroat;'. fontc keys glyph jobs by name: workload.rs insert_with_bookkeeping counts 2 Glyph jobs, jobs_pending (a HashMap) keeps 1, the Glyph counter never reaches 0, so Fe(GlyphOrder) is never launchable and everything downstream is reported stuck. Not a scheduler hang, composite cycle or feature-code problem. Closed by edit E1 (rename only gid 547 to dcroat.1). |
| Corben-Bold | hhea.ascender [2826, 2300] | source-edit-from-source | The release was edited after export: google/fonts 5b1755d5a (2015-09-21) rewrote the vertical metrics. The value is stated by src/Corben-Bold-TTF.sfd (the later 2011-10-10 revision of this style in the same tree): HheadAscent: 2826. Corben-Bold.sfd states HheadAscent: 2300 (HheadAOffset: 0). |
| Corben-Bold | hhea.descender [-969, -940] | source-edit-from-source | As hhea.ascender: Corben-Bold-TTF.sfd states HheadDescent: -969; this .sfd states -940 (HheadDOffset: 0). Release value set by google/fonts 5b1755d5a. |
| Corben-Bold | OS/2.s_typo_ascender [2826, 2300] | source-edit-from-source | Corben-Bold-TTF.sfd states OS2TypoAscent: 2826 (OS2TypoAOffset: 0); this .sfd states 2300 (OS2TypoAOffset: 0). Release value set by google/fonts 5b1755d5a. |
| Corben-Bold | OS/2.s_typo_descender [-969, -940] | source-edit-from-source | Corben-Bold-TTF.sfd states OS2TypoDescent: -969 (OS2TypoDOffset: 0); this .sfd states -940. |
| Corben-Bold | OS/2.us_win_ascent [2826, 2300] | source-edit-from-source | Corben-Bold-TTF.sfd states OS2WinAscent: 2826 (OS2WinAOffset: 0); this .sfd states 2300. |
| Corben-Bold | OS/2.us_win_descent [969, 940] | source-edit-from-source | Corben-Bold-TTF.sfd states OS2WinDescent: 969 (OS2WinDOffset: 0); this .sfd states 940. |
| Corben-Bold | OS/2.ach_vend_id ["newt", "NONE"] | source-edit-from-source | Neither Bold source states a real vendor: Corben-Bold.sfd has OS2Vendor: '    ' (blank) and Corben-Bold-TTF.sfd has 'PfEd' (FontForge's fallback placeholder, tottf.c). The family's vendor 'newt' is stated by src/Corben-Regular.sfd and src/Corben-Regular-TTF.sfd; it entered the Bold release via google/fonts 5b1755d5a. Value is from a sibling style's source, not this style's. |
| Corben-Bold | OS/2.panose_10 {"1": [15, 0]} | source-edit-from-release | Both Bold sources STATE Panose: 2 0 5 5 2 0 0 2 0 4 (bSerifStyle 0). The value 15 exists for this style only in the release: google/fonts 5b1755d5a (2015) changed it; the original FontForge export 90abd17b4 had 0. 15 is the Regular sources' value (Panose: 2 15 5 3 ...), which explains where the 2015 edit got it. Overrides a value the source states, so it must be an explicit commit. |
| Corben-Bold | OS/2.us_weight_class [700, 400] | converter-fidelity | Converter, in progress (fontc does not set it for a static single-master source). The .sfd states TTFWeight: 700. |
| Corben-Bold | OS/2.sx_height [1296, 500] | converter-fidelity | Converter, in progress. FontForge's exporter rule reproduces the release from the unmodified .sfd. |
| Corben-Bold | OS/2.s_cap_height [1593, 700] | converter-fidelity | Converter, in progress. Oracle reproduces 1593 from the unmodified .sfd. |

## Proposed .sfd edits

- **Rename the empty duplicate dcroat to dcroat.1** (Corben-Bold) `renameglyphgid 547 dcroat dcroat.1` -- verified: True; value from: The name is how fontTools reads the release's second copy (the raw post table names gid 211 and gid 548 both 'dcroat'). Diff is one line: 49307 'StartChar: dcroat' -> 'StartChar: dcroat.1'.; the source stated: StartChar: dcroat / Encoding: 65704 -1 547 / Width: 0 / Substitution2 smcp+aalt -> dcroat.sc (second glyph of that name; the first is StartChar: dcroat / Encoding: 273 273 211)
- **Take the vertical metrics of Corben-Bold-TTF.sfd** (Corben-Bold) `setfield OS2TypoAscent 2826; OS2TypoDescent -969; OS2WinAscent 2826; OS2WinDescent 969; HheadAscent 2826; HheadDescent -969` -- verified: True; value from: src/Corben-Bold-TTF.sfd header in the same tree (2011-10-10 revision of this style): OS2TypoAscent: 2826, OS2TypoDescent: -969, OS2WinAscent: 2826, OS2WinDescent: 969, HheadAscent: 2826, HheadDescent: -969, all *Offset: 0. The Regular sources state the same.; the source stated: OS2TypoAscent: 2300, OS2TypoDescent: -940, OS2WinAscent: 2300, OS2WinDescent: 940, HheadAscent: 2300, HheadDescent: -940; OS2TypoAOffset/DOffset, OS2WinAOffset/DOffset, HheadAOffset/DOffset all 0 (absolute), so no offset edit needed
- **OS2Vendor newt** (Corben-Bold) `setfield OS2Vendor 'newt'` -- verified: True; value from: src/Corben-Regular.sfd and src/Corben-Regular-TTF.sfd: OS2Vendor: 'newt'. Release achVendID 'newt' since google/fonts 5b1755d5a.; the source stated: OS2Vendor: '    '
- **PANOSE serif style 15** (Corben-Bold) `setfield Panose 2 15 5 5 2 0 0 2 0 4` -- verified: True; value from: Release OS/2 panose bSerifStyle 15 (only there for this style); the other nine digits are unchanged from this .sfd. Corben-Regular sources state Panose: 2 15 5 3 2 0 0 2 0 4 for the Regular.; the source stated: Panose: 2 0 5 5 2 0 0 2 0 4 (Corben-Bold-TTF.sfd states the same)

## Proposed converter changes

- babelfont (diagnostic only, not a fidelity flag): when an SFD has two StartChar with the same name, fail or warn naming the glyphs and their gids, instead of writing a .glyphs file with duplicate glyphname entries that fontc cannot compile. No output change for valid sources.

  Evidence: Corben-Bold.sfd gid 211 and gid 547 both 'dcroat' -> converted Corben-Bold.glyphs lines 20947 and 42080; build then fails with 'Unable to proceed; 648 jobs stuck pending'. Same pattern observed (not rebuilt) in sfd-batch7/work-legacy/dhyana/sources/Dhyana.glyphs and Dhyana-Bold.glyphs: duplicate 'macron' (the other 'stuck pending' family in sfd-batch7/FONTC-JOBS-STUCK-PENDING.md).
- UPSTREAM fontc (not the converter; for Felipe to file): a duplicated glyph name should be reported as such, not as 'Unable to proceed; N jobs stuck pending'. Cause in fontc-1.0.0/src/workload.rs: insert_with_bookkeeping increments count_pending per job while jobs_pending is a HashMap keyed by Fe(Glyph(name)), so the second job with the same name replaces the first and the Glyph counter never reaches 0.

  Evidence: investigations/corben-bold/fontc-dup-repro/ (DupName.glyphs vs UniqueName.glyphs, README.md): fontc 0.6.0 -> 29 jobs stuck, gftools-builder3 e851b8b (fontc 1.0.0) -> 30 jobs stuck; the a.1 control builds in both.

## Unresolved

- FINDINGS.md was NOT written: the Write tool refused it ('Subagents should return findings as text, not write report files'). I did not work around that refusal. Everything it would say is in this structured result. The probes, TSVs, repro and run outputs are under /home/fsanches/compartilhado/gf-source-modernization/investigations/corben-bold/. Someone with permission should write FINDINGS.md from this result.
- Provenance (glyph data): the release's glyph set, cmap, advances and GSUB/GPOS bindings come from FontForge's 2011-01-26 export of src/Corben-Bold.sfd. Evidence: head.created 1296003342 is 8 s after the .sfd's ModificationTime 1296003334; 551 + generated .null = 552 glyphs; cmap 380 = 380. google/fonts 5b1755d5a (2015) then edited the header metadata and ee1e172ab (2017) ttfautohinted it. src/Corben-Bold-TTF.sfd cannot be the source: it is truncated at exactly 229376 bytes (56 x 4 KiB), cut off mid-record in its 955th KernClass2 before BeginChars (0 glyphs). Its CreationTime (1318235497, 2011-10-10) matches the head.created of the 264-glyph src/Corben-Bold.otf.*.ttx build, which lacks 129 of the release's codepoints. src/Corben-Bold.vfb was not read (no pinned reader).
- E1 keeps a designer defect of the release: U+0111 dcroat never gets smcp/aalt, because the rule sits on the unencoded orphan. Fixing it would be a correction, not a reproduction, and would need a separate decision.
- The name table differs widely because of the 2015 edit (copyright, uniqueID, version, URLs, full and PostScript names). The table gate does not block on name records (full_table_diff.py discloses them), so no name edits are proposed here.
- Dhyana (sfd-batch7) shows the same duplicate-name pattern (macron) in its older conversions. I have not rebuilt or verified it in this unit.
- Before the 3 remaining converter rows can close, the babelfont work in progress (worktree HEAD ca43adc, heights) and the us_weight_class fix need to be rebuilt and rerun. I did not build babelfont.

## Rerun

    TAG=corben-bold OUT=investigations/corben-bold/runs/e1-dcroat1 SRC_OVERRIDE=<scratch>/cand/e1-dcroat1.sfd SCRATCH=<scratch> bash tools/baseline.sh Corben-Bold
    TAG=corben-bold OUT=investigations/corben-bold/runs/e12-vmetrics SRC_OVERRIDE=<scratch>/cand/e12.sfd SCRATCH=<scratch> bash tools/baseline.sh Corben-Bold
    TAG=corben-bold OUT=investigations/corben-bold/runs/e123-vendor SRC_OVERRIDE=<scratch>/cand/e123.sfd SCRATCH=<scratch> bash tools/baseline.sh Corben-Bold
    TAG=corben-bold OUT=investigations/corben-bold/runs/e1234-panose SRC_OVERRIDE=<scratch>/cand/e1234.sfd SCRATCH=<scratch> bash tools/baseline.sh Corben-Bold
    DROP_FLAGS=--add-legacy-duplicate-cmap TAG=corben-bold OUT=investigations/corben-bold/runs/e1234-nodupcmap SRC_OVERRIDE=<scratch>/cand/e1234.sfd SCRATCH=<scratch> bash tools/baseline.sh Corben-Bold
    bash investigations/corben-bold/rerun.sh <scratch-dir>   (regenerates all candidate sources from the archive and repeats the 5 runs, sequentially)
    RUST_LOG=warn fontc(0.6.0, sfd-batch5/d4d5-probe/fontc-3518040) --build-dir X -o X.ttf <unmodified Corben-Bold.glyphs>  -> runs/fontc060-unmodified-blocked.log
    gftools/venv/bin/python3 investigations/corben-bold/release_history.py > release_history.txt
    gftools/venv/bin/python3 investigations/corben-bold/cmap_provenance.py <tree> google/fonts/ofl/corben/Corben-Bold.ttf > cmap_provenance.txt
    gftools/venv/bin/python3 investigations/corben-bold/outline_compare.py <release.ttf> <built.ttf> > runs/e1234-nodupcmap/outline_compare.txt
    gftools/venv/bin/python3 tools/ff_heights_oracle.py | grep Corben
