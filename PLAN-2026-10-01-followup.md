# Follow-up plan after the re-land on upstream tools (2026-10-01)

**Latest (2026-10-02): 108/149 functional PASS, 105 CLEAN** with fixes 1-3, 5, 6 and the
section-2 edits (babelfont #101-#106). What still fails, grouped by fix:
investigations/reland-2026-10-02/RESIDUALS.md.

Baseline: all 101 repositories re-landed with babelfont upstream main 004200b7 and gftools-rust
ade8776 (fontc 1.0.0). `logs/reland-2026-10-01/`, `tools/reland_triage.py`: **149 styles, 39 pass
the functional gate, 29 CLEAN** (before: 26 of 94). Research per failure cluster:
`investigations/reland-2026-10-01/` (README lists every file), scripts in research-scratch
(sessions/2026-10-01_reland-r, _reland-s). Styles counts below are from those reports; the
same style can appear under several causes, so counts do not add up.

Principle for where a fix goes: in a conversion fontc only compiles the .glyphs babelfont wrote,
so anything the source should state is a babelfont fix; a compiler fix only where the source
already states it and the compiler cannot follow (parity with fontmake). A release that differs
from what FontForge exported from the recorded source gets a documented source edit (its own
commit), never a converter hack.

## 1. babelfont fixes, ranked by styles they unblock

| # | fix | styles | state | evidence |
|---|---|---|---|---|
| 1 | `--fontforge-gdef-classes`: FontForge's GDEF class rule (explicit GlyphClass, else mark anchor = mark, Ligature2 = ligature, else base) as an explicit GlyphClassDef. A Glyphs source cannot state "base without anchors". | ~31 (shaping+gdef; 27 close fully) | Rust prototype | shaping/ patch, gdef_census.txt (rule matches 120/122 releases) |
| 2 | **APPROVED by Felipe 2026-10-01.** Names: SFD reader gives `LangName 1033` precedence over FullName/FamilyName/FontName (as FontForge and babelfont's own TTF reader do), derives ID 2 FontForge's way, names the master from it; `.glyphs` writer emits "Name Table Entry" for IDs 1/2/4 + localized records when they differ from what fontc derives | +73 / -27 of the names check | designed, verified by editing .glyphs | names/fix*.txt |
| 3 | `--fontforge-legacy-os2-version`: clear fsSelection bits 7/8 when OS2Version is 1-3 (those FontForge builds never set USE_TYPO_METRICS) | ~16 (8 verified) | branch fontforge-legacy-os2-version 987264f, PR-QUEUE 1 | linespacing/ |
| 4 | `--round-coordinates` (second half of #98) | Over the Rainbow + 5 exposed repos | branch round-coordinates 1d45ec6c; full measurement in logs/reland-2026-10-01-roundcoords | |
| 5 | Drop kern pairs an earlier subtable of the same lookup shadows | 2 (Italiana, Sanchez) | Rust prototype | shaping/ patch |
| 6 | Insertion marker `# Automatic Code` | Lohit-Bengali (+Cardo) | Rust prototype (one string) | shaping/ patch |
| 7 | Advancing marks are Spacing Combining (reader + `--set-subcategory`) | Lohit-Tamil, Cardo | reader-half patch | next-provenance/probes/ |
| 8 | `--fontforge-notdef`: FontForge's synthesized box when the source has none (stem (asc+desc)/30, advance 748/374) | ~7 | verified by adding the glyph | outlines/README.md |
| 9 | `isFixedPitch` custom parameter when every width is equal | NovaMono | verified by adding the parameter | outlines/ |
| 10 | Cardo: LCarets2 -> caret anchors, lookup precedence around generated lookups, `--fontforge-no-anchor-propagation`, FEA-name diagnostics | Cardo (+ others) | designs; anchor-propagation patch in next-provenance | next-cardo/FINDINGS.md |
| 11 | sfdLib interpolated-point reading, opt-in (Comic Relief was built with sfdLib 2.0.0) | 2 | verified by emulation | outlines/ |
| 12 | Thabit: lookupflag on every lookup, baselig anchor names | 2 | patches | next-provenance/probes/ |
| 13 | aalt language systems (Poly-Italic); legacy offset win/hhea metrics (4 families) | 1 + 4 | prototypes | next-emptygpos/, next-vmetrics/ |

## 2. Source edits to write into plans/ (ours, mechanical, already verified)

DONE 2026-10-02 (sfd-reland 1440532; logs/reland-2026-10-01-planedits, -os2) except: Tuffy
encodings (needs a new op), the vmetrics of MountainsofChristmas-Bold, NothingYouCouldDo and
Unifraktur. Now CLEAN: Ledger, LilitaOne, Magra, Megrim, MergeOne, Rambla, Sail, TextMeOne.

- BlueValues heights (`addprivate BlueValues`): Ledger, LilitaOne, Lustria, Magra-Bold, MergeOne,
  OleoScript x2, OleoScriptSwashCaps x2, Rambla-Bold/BoldItalic, Sail, TextMeOne (next-heights).
- Vertical metrics: Limelight, MountainsofChristmas-Bold, NothingYouCouldDo, Unifraktur (next-vmetrics).
- `setfield FSType 0`: TitilliumWeb x9 (google/fonts 93550bd32 changed the binaries).
- Ledger `nbspwidth`; Megrim three `droplookup` (next-gsub); Cardo `renameglyph 10192.04
  u10192.04` + Italic `nbspwidth`; Tuffy `.null`/`nonmarkingreturn` encodings (needs a new
  sfd_edit op); Ultra `setfield TTFWeight 400` (or re-pair to 2d042ebbd); Thabit/Kristi
  `OS2Version 1`; ComicRelief `OS2_UseTypoMetrics 1`.
- After babelfont fix 2: per-family name edits for the 41 styles whose releases were renamed after
  export or at onboarding (14 + 27; names/fix-others.txt).
- Corben-Bold names: DONE (plans/corben.json, fcb28f2).

## 3. Pairing corrections (families-next.tsv / pair_next.py)

Lohit-Bengali -> 0df83ad, Lohit-Tamil -> 361b23b (the 2.5.0 release); Titillium ExtraLight x2
unpaired (rule 4 never applied); Ultra (drifted .sfd).

## 4. Compiler / builder (only where the source already states it)

- fontc + gftools-rust: shared layout scripts (empty-GPOS releases: Varela, UnifrakturMaguntia).
- fontc: KernFeatureWriter `ignoreMarks=false` (+ babelfont writes the option): Cardo.
- gftools-rust: bump fontc (main 018e193c reads "Italic" in a master name): Overlock-BlackItalic.

## 5. Our tooling

- land.py: keep the builder's stderr tail (Cardo's failure read "not produced (nothing)").
- functional_gate.py: add default-ignorables the release kerns (U+00AD) to the pair corpus (Smokum).
- reland_triage.py: classify rendering by the gate's geometry count; label shaping-confirmed-only
  separately (currently mislabels Nosifer, Thabit, Tuffy-Italic as .notdef).
- ufr-template CI: download gftools-builder from simoncozens/gftools-rust, not gftools-builder3.

## 6. Decisions for Felipe

Kept in one place: GoogleFonts/bottleneck.md (priority order, extremely succinct).

## 7. Felipe's decisions recorded 2026-10-01

- Repo name `googlefonts/unifraktur` confirmed for UnifrakturMaguntia.
- Rule: represent each family by the most faithful available source of what shipped.
  - Play: alexeiva/play `sources/Play.glyphs` (d84ad58, v2.101) -- googlefonts/play carries that
    history; the hg .sfd stays in history. Needs glyphslib-rs #4 (all-digit hex unicodes).
  - Tuffy: the .sfd with documented edits to v1.272 (2017 rebuild; its source was never published).
  - Thabit: the .sfd plus its build's inputs, as documented commits: new sfd_edit ops
    `mergepsfont` (src/cour/*.pfa, IBM Courier) and `mergefea` (Thabit.fea), FamilyName edit,
    oblique pairing (investigations/next-provenance/FINDINGS.md).
- Disclosures: plans/<repo>.json "disclose" -> README "Known differences from the released fonts"
  (14 families; sfd-reland 898eb3c).
