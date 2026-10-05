# nosifer -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I rebuilt every edit myself, starting from the unmodified sources that families.tsv names. I did not reuse their edits/ files. Sources: googlefontdirectory-hg 52f780bc9d19, ofl/nosifer/src/Nosifer-Regular-TTF.sfd (md5 6a0292d9) and ofl/nosifercaps/src/NosiferCaps-Regular-TTF.sfd (md5 0a55b204). How the edits were made:
- droplookup: `grep -v -x -F` removes exactly two lines, the `Lookup: 4 0 1 "'liga' ..."` line (source line 57) and `Ligature2: "'liga'" E E` (line 6044). Afterwards the file contains no "'liga'" at all.
- Heights stand-in: `OS2XHeight: 925` / `OS2CapHeight: 854`, placed after OS2Vendor. That is a different position from theirs, to test robustness.

Builds were run one at a time: `TAG=nosifer-verify OUT=<scratch>/inv-nosifer-verify/runs/<name> [SRC_OVERRIDE=...] bash tools/baseline.sh <Style>`. Results:
- v0 Nosifer unmodified: BLOCKING 5 (GSUB feature/lookup/script_list, OS/2 s_cap_height [854,700], sx_height [925,500]), 15 stale.
- v1 droplookup: BLOCKING 2 (the heights only).
- v2 heights: BLOCKING 3 (GSUB only).
- v3 droplookup+heights: CLEAN 0, 15 stale.
- v4 NosiferCaps unmodified: BLOCKING 3 (us_weight_class [800,400] plus the two heights), 16 stale.
- v5 NosiferCaps heights: BLOCKING 1 (us_weight_class).
- v6, extra: detaching the liga feature only (keeping the lookup data) plus heights leaves BLOCKING 3. fontc emits a GSUB with a lookup that no feature uses, so the 2-line droplookup is the smallest edit that closes the rows.

Every RELEASE-STALE list is identical to its unmodified run, and v0's list is identical to the shared baseline. This matches their rows_before and rows_after exactly.

Heights: I wrote my own port (scratch ff2011_heights.py) from FontForge v20110222 (9ec8bff8): splinefont.c SFStandardHeight/SPLMaxHeight, splineorder2.c SplineRefigure2 and splineutil2.c SplineIsLinear. It gives the same per-glyph tops as their oracle-based probe: x 16652/18 = 925.11 -> 925 and cap 22211/26 = 854.27 -> 854; the master rule gives 1387/1388. It also reproduces the 4 other releases they attribute to the era rule: HerrVonMuellerhoff 269/644, Miama 265/894, UnifrakturCook-Bold 319/485 and UnifrakturMaguntia-Book 1095/1409.

Code checked by commit hash:
- 9ec8bff8 (= v20110222 per ls-remote) line 1709 has `tot += curves[i].cnt`; 4d34d21e has `++tot`.
- 37d20840 already has the `tot += cnt` line.
- The glyph lists are the same in v20110222 and master; ca43adc fontforge_standard_height.rs divides by curves.len().
- tottf.c 3496-3499 truncates to int.
- tottf.c 5283-5307 (initATTables) and the release table sets (Nosifer: kern v0, 28 pairs, no GSUB/GPOS/GDEF/DSIG, usMaxContext 1; NosiferCaps: GSUB liga E E -> E_E) confirm what they said.

Pins: baseline.sh md5 e5b0b403; table_gate.py md5 d99eadad. The babelfont binary was built 2026-09-23 20:27, after f725e6a (20:17) and before ca43adc (20:56), and its --help has no height flag. Also gftools-builder3 e851b8b and google/fonts b5efa9c32e8f.

## Verdict

I could not break their findings. My own rebuild from the unmodified sources reproduced every row count before and after, and my own port of the FontForge 20110222 rule gives the same heights.

**Verdicts:**
- **droplookup edit:** KEEP. It is verified and minimal, and it is honest that the absence exists only in the release. It still needs Felipe's decision: reproduce the release, or keep the liga as better than the release.
- **Height rows:** they are converter-fidelity. FontForge 20110222 (in [37d20840, 4d34d21e)) divided the sum of the distinct tops by the number of glyphs. ca43adc divides by curves.len(), so it needs an era switch chosen from the release's FFTM date. That switch is proven for Nosifer, NosiferCaps and 4 other styles, but it is not build-verified.

**Classifications:** all 8 stand. Two small factual slips (m/M tops; the oldkern case) do not change any result. I add strong evidence that the release was exported from exactly this saved .sfd (the .5 rounding and gasp version 0). That rules out "provenance" for the GSUB rows. I also add the likely cause of the non-OpenType export: a python generate() call whose flags omit "opentype" (python.c:13978-13985).

**Files:** the harness rule forbids writing report .md files, so VERIFY.md was NOT written. Its intended content, ASCII, is below for the orchestrator. My scratch at /tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-nosifer-verify/ holds ff2011_heights.py, load_from_disk_evidence.py, edits/, runs/v0..v6 and the FontForge sources fetched by hash. It is volatile. If kept, it should be copied to investigations/nosifer/verify/.

--- VERIFY.md (intended) ---
# nosifer -- adversarial verification
**Model**: Claude Opus 5.5
Pins: baseline.sh md5 e5b0b403; table_gate.py md5 d99eadad; babelfont binary 2026-09-23 20:27 (f725e6a, pre-ca43adc); gftools-builder3 e851b8b (fontc 1.0.0); google/fonts b5efa9c32e8f; FontForge 9ec8bff8 (v20110222), 4d34d21e and 37d20840 fetched from raw.githubusercontent.com; fontTools from /home/fsanches/compartilhado/gftools/venv.
Sources are the ones families.tsv names: hg 52f780bc9d19 ofl/nosifer/src/Nosifer-Regular-TTF.sfd (md5 6a0292d9) and ofl/nosifercaps/src/NosiferCaps-Regular-TTF.sfd (md5 0a55b204). Binaries: ofl/nosifer/Nosifer-Regular.ttf and ofl/nosifercaps/NosiferCaps-Regular.ttf (both byte-identical to the monorepo copies).

## 1. Reproduction (my own edits, starting from the unmodified sources)
v0 unmod 5 | v1 drop 2 (heights) | v2 heights 3 (GSUB) | v3 drop+heights CLEAN 0 | v4 caps unmod 3 | v5 caps heights 1 (us_weight_class) | v6 detach-feature-only+heights 3 (fontc keeps a GSUB lookup that no feature uses).
Every stale list is unchanged. This matches their r0-r5.

## 2. Edits
- droplookup: KEEP (see edit_verdicts).
- Heights stand-in: not an edit. The converter change is the fix. The stand-in is valid only as a fallback (OS2XHeight/OS2CapHeight are real FontForge SFD keywords).

## 3. Classifications
- Heights: converter-fidelity, confirmed by an independent port. x 16652/18 = 925, cap 22211/26 = 854 (master 1387/1388). It also reproduces HerrVonMuellerhoff 269/644, Miama 265/894, UnifrakturCook-Bold 319/485 and UnifrakturMaguntia-Book 1095/1409.
- GSUB: source-edit-from-release, confirmed. The release was loaded from this saved .sfd:
  - The 10 glyf points where the releases differ are exact .5 values in the .sfd, rounded half-to-even in Nosifer only.
  - gasp version is 0 (not saved in SFD 20110222, sfd.c:1595).
  - It was then exported in neither OpenType nor Apple mode (kern v0, no GSUB/GPOS/GDEF/DSIG/morx, usMaxContext 1). The likely cause is a scripted generate() whose flags lacked 'opentype' (python.c:13978-13985). The GUI default is OpenType mode (savefont.c:39).

## 4. Pairing
Correct for both styles.

## 5. Missed
- FINDINGS.md is absent.
- scratchpad/ff/old/20110222-*.c are 404 stubs.
- The shared baseline gate file was made with the old flag order, besides the traceback.
- Slips: m/M tops differ (1375 vs 1408); legacy kern is also written in OpenType mode with oldkern.

## Rerun
```
V=<scratch>/inv-nosifer-verify
cd /home/fsanches/compartilhado/gf-source-modernization
TAG=nosifer-verify OUT=$V/runs/<v> [SRC_OVERRIDE=$V/edits/<file>.sfd] bash tools/baseline.sh <Style>
$PY $V/ff2011_heights.py <sfd>
$PY $V/load_from_disk_evidence.py $V/Nosifer-Regular.orig.sfd
```

## Per edit

- [keep] Drop the E E ligature the release does not carry -- The unmodified .sfd states the lookup at line 57 and the E_E entry at line 6044, and the edit removes exactly those 2 lines, so it knowingly drops designer data. The subject and body say so plainly, and 'the absence exists only in the release' is accurate, so value_derived_from is honest. Only a converter 'non-OpenType export' flag could replicate this as fidelity. babelfont has no such flag, the .sfd does not record the export mode, and such a flag would hide a change in shaping (BEEF/SEE/EEE) inside converter arguments. The rule forbids exactly that for a value the source states, so the visible .sfd edit is the right vehicle. It is minimal: detaching only the feature (v6) leaves 3 rows. Verified by me (v1, v3). It remains conditional on Felipe's decision to reproduce the release rather than keep the liga as documented better-than-release. Optional wording: name 'FontForge 20110222, exported 2011-12-19 in neither OpenType nor Apple mode' in the body.
- [drop as an .sfd edit; use the converter change] (fallback stand-in only, not proposed) OS2XHeight 925 / OS2CapHeight 854 -- The source states no OS2XHeight/OS2CapHeight (grep: 0), and FontForge 20110222 computed 925/854 from the unmodified outlines, so this is fidelity, not a source edit. The keywords are real FontForge SFD fields (master sfd.cpp:2309/2311/7882/7886), so if the converter change is declined the fallback would still be valid, and its commit body must say the values are FontForge 20110222's computation. It closes only the height rows (v2, v3, v5).

## Objections

- None of the 8 row classifications is wrong. GSUB x3 = source-edit-from-release is correct and is NOT provenance: independent evidence shows the release was generated from exactly this saved source state (see missed[0]). Only the export mode differs, and the .sfd does not record it.
- Factual slip in the s_cap_height cause: 'The lowercase tops equal the capitals' letter for letter' is false. m=1375 but M=1408, both round, as their own runs/heights_2011_rule.txt shows. The numbers are not affected.
- Imprecise in the GSUB cause: v20110222 tottf.c:5306 also writes the legacy kern in OpenType mode when ttf_flag_oldkern is set. So 'legacy kern only when neither OpenType nor Apple mode is on' leaves out a case. It does no harm, because the missing GSUB/GPOS/DSIG and usMaxContext 1 already rule out OpenType mode, and kern version 0 with no morx rules out Apple mode.
- NosiferCaps us_weight_class [800,400] = converter-fidelity (in progress) is correct. The source states TTFWeight: 800 (it is 400 in Nosifer, whose release has 400).

## Missed

- Evidence that would strengthen the GSUB finding. The Nosifer release was generated from a font LOADED from the saved -TTF.sfd, not from a live session. (a) At all 10 points (9 glyphs) where the two releases' glyf differ, the .sfd prints an exact .5 value (-42.5, 473.5, 779.5, 222.5, 512.5, 1599.5). The Nosifer release holds the half-to-even rounding of each (-42, 474, 780, 222, 512, 1600), while the NosiferCaps release is off by 1 at exactly those points. (b) gasp version is 0 in Nosifer and 1 in NosiferCaps: FontForge 20110222 sfd.c:1595 does not save gasp_version, so a font loaded from .sfd exports version 0. The two .sfd glyph sets are identical (diff shows only names, TTFWeight and vertical metrics). Rerun: scratch/inv-nosifer-verify/load_from_disk_evidence.py.
- The likely mechanism for the non-OpenType export went unstated. The GUI default is OpenType mode (v20110222 savefont.c:39 old_sfnt_flags = ttf_flag_otmode). But python.c:13978-13985 turns any generate() flags tuple that names neither 'opentype' nor 'apple' into 0x90 = neither mode. Four fonts generated in the same second (Butcherman, Creepster, Eater, Nosifer, 2011-12-19 18:44:21) points to such a script.
- findings_path /home/fsanches/compartilhado/gf-source-modernization/investigations/nosifer/FINDINGS.md does not exist. The directory holds only edits/, probes/ and runs/.
- The brief's reference copies scratchpad/ff/old/20110222-splinefont.c and 20110222-tottf.c are 14-byte '404: Not Found' stubs (same md5, 3be7b8b1). Their evidence came from their own clone via ff_evidence.sh, and I re-fetched by hash 9ec8bff8. Other units that rely on those two files are reading nothing.
- The shared baseline/Nosifer-Regular.gate.txt was also produced by an older baseline.sh flag order (--fontforge-os2-defaults last), on top of the JSONDecodeError traceback they reported. The current script (flag first) gives identical rows and stale lists.
- Nothing else missed: both styles are covered and correctly paired (sources and binaries per families.tsv; the google/fonts binaries are byte-identical to the monorepo copies, md5 e1875da4 / 5f57edc5). No edit opened a row.
