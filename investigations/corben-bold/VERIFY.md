# corben-bold: adversarial verification

**Model**: Claude Opus 5.5
**Date**: 2026-09-23
**Subject**: the corben-bold unit's structured result (4 .sfd edits, 1 flag drop, 11 rows)

## Verdict

REPRODUCED. All 4 edits are kept. Two small wording fixes are needed (E1, E4). One
mechanism changes: the flag drop becomes a harness-rule fix, not a per-style drop. I
found no fidelity explanation that makes any edit unnecessary. Their result misses 4
things: an ungated kerning report, the unread .vfb, a silent failure of the existing
`renameglyph`, and the landing tool that the new op has to go into.

## Pins

| input | pin |
|---|---|
| source | librefonts/corben 94d5b00e6b64 `src/Corben-Bold.sfd`, sha256 2af5e9e5f2c35b4c...; googlefonts/corben master = 94d5b00 (git ls-remote) |
| release | google/fonts b5efa9c32e8f `ofl/corben/Corben-Bold.ttf` (= blob of ee1e172ab) |
| babelfont | gf-sfd-conversion binary sha256 f96e0851990f480753d5239baf418cb4c168214b141b74f63a54e7806c77ff19, mtime 2026-09-23 20:27:57, after f725e6a and before ca43adc (HEAD ca43adc is NOT built). This is the same binary the unit used. |
| builder3 | gftools-builder3 e851b8b (fontc 1.0.0), sha256 d6dd442c2cb549fa... |
| diff and gate | diffenator3 1.1.4; table_gate.py md5 d99eadad22d0ec57d119ba6ce517ed07 (sfd-batch5 cd4f827); baseline.sh md5 e5b0b4033b3bc7c99c29ba3b4c6de46a |
| python | fontTools 4.61.1, uharfbuzz 0.53.3 (gftools venv); vfbLib 0.11.7 (vfblib-py-venv) |

## 1. Reproduction

I built the candidates myself from a fresh `git archive` of the unmodified source:
- E1: hand `sed` on line 49307. Their `renameglyphgid.py` gives the same bytes.
- E2 to E4: my own TSVs through `source_corrections.py`. `gf-source-modernization/tools/sfd_edit.py setfield` gives the same bytes.

All 4 candidates are byte-identical to theirs.

| run | result | rows |
|---|---|---|
| unmodified | BUILD-FAILED | "Unable to proceed; 648 jobs stuck pending" (same as baseline) |
| +E1 | 11 | hhea asc/desc, typo asc/desc, win asc/desc, vend_id, panose_10, weight, sx_height, cap_height |
| +E2 | 5 | |
| +E3 | 4 | |
| +E4 | 3 | us_weight_class [700,400], sx_height [1296,500], s_cap_height [1593,700] |
| +E4, flag dropped | 3 | same 3; cmap equals the release (380) |

- All 5 gate files are byte-identical to theirs (`diff -q`).
- Every gate printed "N blocking table difference(s)".
- The 10 RELEASE-STALE lines are identical in every run (same md5). No edit opens a row.

Their repro (`fontc-dup-repro`) re-run with builder3 e851b8b:
- DupName: "Unable to proceed; 30 jobs stuck pending", exit 1.
- UniqueName: builds.

Their mechanism is confirmed in `fontc-1.0.0/src/workload.rs:246-251`: `count_pending` is incremented once per job, while `jobs_pending` is a HashMap keyed by id.

## 2. Per-edit review (what the unmodified .sfd states)

### E1: `renameglyphgid 547 dcroat dcroat.1`. KEEP, with wording and tooling fixes

- The source has `StartChar: dcroat` twice:
  - line 25881, `Encoding: 273 273 211`: the real glyph, 1783 wide.
  - line 49307, `Encoding: 65704 -1 547`: Width 0, no outline, only the smcp/aalt `Substitution2` lines.
- No `Refer:` or `Kerns2` points at index 547, so the rename is the minimal edit.
- The release keeps both glyphs; fontTools reads the second as dcroat.1.
- smcp and aalt in the release and in our build are identical, including dcroat.1 -> dcroat.sc.

Fixes:
- (a) The body should say "SFD glyph index 547 (release gid 548)". The two numbering schemes differ by the .null glyph.
- (b) Land it as an op in `gf-source-modernization/tools/sfd_edit.py`, which `land.py` applies. Adding it only to `source_corrections.py` is not enough.
- (c) The existing `renameglyph` is worse than described. `sfd_edit.py renameglyph dcroat dcroat.1` on this file exits 0 and leaves TWO `StartChar: dcroat.1` (lines 25881 and 49307). It needs a FATAL-on-duplicated-name guard.

### E2: 6 x setfield vmetrics 2826/-969. KEEP

- The source states `OS2TypoAscent: 2300`, `OS2TypoDescent: -940`, `OS2WinAscent: 2300`, `OS2WinDescent: 940`, `HheadAscent: 2300` and `HheadDescent: -940`. All `*Offset` fields are 0, so the values are absolute and FontForge writes them as they are.
- The first google/fonts binary (90abd17b4) carries exactly 2300/-940, so no exporter vintage explains 2826.
- `value_derived_from` is honest. It could be stronger: `src/Corben-Bold.vfb` also states 2826/-969 (read with vfb3ufo: typo, win and hhea, v1.100).
- Suggested body: "the designer's v1.100 Bold (Corben-Bold.vfb, Corben-Bold-TTF.sfd) states 2826/-969; this v1.000 file states 2300/-940".

### E3: `OS2Vendor 'newt'`. KEEP

- The source states `'    '` (4 spaces). FontForge copies a stated vendor (2012 tottf.c:3495-3500), and the 2011 export has `'    '`.
- No Bold source names a vendor: the .sfd has blank, the -TTF.sfd has `'PfEd'`, the .vfb is empty and the OTF ttx has NUL.
- 'newt' comes only from the Regular sources and entered the Bold release in 5b1755d5a. The body says so. Honest and minimal.

### E4: `Panose 2 15 5 5 2 0 0 2 0 4`. KEEP, with a wording fix

- The source states `Panose: 2 0 5 5 2 0 0 2 0 4`, and so do the -TTF.sfd and the .vfb. Only digit 1 changes.
- 90abd17b4 and bacec3651 carry 0; 15 first appears in 5b1755d5a.
- Babelfont's PANOSE fill (f725e6a) applies only when the source states none.
- Fix: the body says both "exists only in the release" and "15 is what the Regular's sources state". Suggested: "No Bold source states it (.sfd, -TTF.sfd and .vfb all give 0); google/fonts 5b1755d5a (2015) set 15, the Regular's serif style."

### Flag drop `--add-legacy-duplicate-cmap`. REVISE (the outcome is right, the mechanism is not)

- With the flag, the build adds U+02C9->macron and U+2219->periodcentered. The release has neither, and the gate does not block additions.
- The harness rule (`dup=yes` when the release maps U+00A0 and U+00AD) misfires wherever those map to distinct glyphs of the source. Corben-Regular misfires too.
  - Converting only (no build), the flag adds 3 codepoints to Corben-Regular: U+02C9, U+2219 and U+03BC. Its release has none of them.
- Fix `baseline.sh`: pass the flag only when the release maps U+00A0 or U+00AD to the same glyph as U+0020 or U+002D, or carries a makeotf-only codepoint. Do not DROP it per style.

## 3. Classification check

- There are no "provenance" rows. Their glyph provenance note is confirmed and strengthened:
  - head.created 1296003342 is 8 s after the .sfd's ModificationTime 1296003334. FontForge 2012 tottf.c:2927-2929 sets created = modified = the export time.
  - cmap: 380 = 380, same glyph for every codepoint.
  - All 551 common glyphs have identical raw outlines (undirected explicit-segment multisets): 0 differ. Advances: 0 differ.
  - The .vfb is v1.100, with 264 glyphs and no dcroat or .sc glyphs, so it cannot be the master.
  - -TTF.sfd is truncated at 229376 bytes inside KernClass2 #955. Its CreationTime 1318235497 equals the OTF ttx head.created (ttx shows 07:31:37, which is 1 h off UTC).
- 5b1755d5a is a table edit, not a re-export:
  - cmap, hmtx, post, maxp, cvt and prep are byte-identical to bacec3651.
  - name, OS/2, hhea and head changed; FFTM and fpgm were dropped.
- `source-edit-from-release` for PANOSE: the evidence is sufficient, and no fidelity explanation exists.
- Mild objection, vendor vs PANOSE: neither 'newt' nor 15 is stated by any of the three Bold sources, and both are stated by the Regular's. One is labelled from-source and the other from-release. That is defensible (vendor is family-wide, PANOSE is per style), but the reason should be stated.
- The BUILD-FAILED row is labelled `build-failure`. It is really a source defect, closed by a source edit whose new name follows how fontTools reads the release. Acceptable as written.
- `converter-fidelity` rows: ff_heights_oracle reports "Corben-Bold v2 1296/1296 1593/1593 MATCH", and the .sfd states TTFWeight 700. Correct.

## 4. Pairing

`families.tsv` row Corben-Bold pairs `src/Corben-Bold.sfd` with `ofl/corben/Corben-Bold.ttf`. baseline.sh pairs them by construction, and every probe of theirs and mine used that pair. Correct.

## 5. Missed

1. The diffenator3 `kerns` section reports "There are 2732 changes, check manually!". table_gate.py reads only `tables` and `cmap_diff`, and `arbitrate_gpos` accepts GPOS rows without shaping whenever both fonts have lookups. So kerning is ungated in this pipeline. For this style I checked it by shaping every pair:
   - 142,129 encoded pairs, default features and smcp: 0 differ.
   - 41,028 and 23,884 pairs are kerned, in both fonts. This is a gap for every other family.
2. The .vfb was not read (see section 3).
3. The existing `renameglyph` fails silently on duplicated names, and the new op belongs in `sfd_edit.py` (see E1).
4. The Corben-Regular dup-cmap misfire adds 3 codepoints (U+03BC too), not 2.
5. FINDINGS.md is still not written.

## Rerun

    S=<scratch>; mkdir -p $S/tree $S/cand
    git -C upstream_repos/repo_archive/librefonts/corben.git archive 94d5b00e6b64f85258d17e766a1e8e6d85554adc | tar -x -C $S/tree
    sed '49307s/^StartChar: dcroat$/StartChar: dcroat.1/' $S/tree/src/Corben-Bold.sfd > $S/cand/v-e1.sfd
    cp $S/cand/v-e1.sfd $S/cand/v-e1234.sfd; for a in "OS2TypoAscent 2826" "OS2TypoDescent -969" \
      "OS2WinAscent 2826" "OS2WinDescent 969" "HheadAscent 2826" "HheadDescent -969" "OS2Vendor 'newt'" \
      "Panose 2 15 5 5 2 0 0 2 0 4"; do python3 gf-source-modernization/tools/sfd_edit.py $S/cand/v-e1234.sfd setfield $a; done
    [DROP_FLAGS=--add-legacy-duplicate-cmap] TAG=corben-bold-verify OUT=$S/runs/<name> SRC_OVERRIDE=$S/cand/<cand>.sfd \
      SCRATCH=$S bash gf-source-modernization/tools/baseline.sh Corben-Bold      # one at a time
    vfblib-py-venv/bin/vfb3ufo $S/tree/src/Corben-Bold.vfb          # writes Corben-Bold.ufo beside it

Kerning probe. It shapes every ordered pair of encoded codepoints through both fonts; the
answer is 0 differing pairs.

    import sys, itertools, uharfbuzz as hb
    from fontTools.ttLib import TTFont
    F = [(hb.Font(hb.Face(open(p, "rb").read())), TTFont(p)) for p in sys.argv[1:3]]
    cps = sorted(set(F[0][1].getBestCmap()) & set(F[1][1].getBestCmap()))
    cps = [c for c in cps if c > 0x20 and c not in (0xA0, 0xAD)]
    def sh(f, t, s, ft):
        b = hb.Buffer(); b.add_str(s); b.guess_segment_properties(); hb.shape(f, b, ft)
        go = t.getGlyphOrder()
        return [(go[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(b.glyph_infos, b.glyph_positions)]
    for ft in ({}, {"smcp": True}):
        print(ft, sum(sh(*F[0], chr(a) + chr(b), ft) != sh(*F[1], chr(a) + chr(b), ft)
                      for a, b in itertools.product(cps, cps)))

Outline probe (0 of 551 differ):
- For each glyph, draw the raw glyf through `glyf[n].draw(pen, glyf)`. This skips fontTools' lsb shift, which would otherwise make the stale AE/Lslash/lslash lsb look like an outline difference.
- Use a `BasePen` subclass that decomposes and records `_lineTo` and `_qCurveToOne` segments as undirected tuples, rounded to 0.5.
- Compare the resulting `Counter`s.
