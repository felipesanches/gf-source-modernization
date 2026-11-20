Title: Source metadata: 36 families whose .vfb is an import of the shipped fonts

Body:
Metadata only, no binaries change. One commit per family (METADATA.pb `source` block + upstream_info.md), as in #11237.

Each family's only published source is a `-TTF.vfb` (googlefontdirectory-hg for 22 families, librefonts for 14), a FontLab import of the shipped fonts rather than a design source (#10490). So each now points at a new https://github.com/googlefonts/<family> repository: the shipped fonts imported unmodified, the Unified Font Repository template, then the conversion to `.glyphs`.

Families: Berkshire Swash, Bigelow Rules, Clicker Script, Dynalight, Eagle Lake, Engagement, Fascinate, Fascinate Inline, Galindo, Grand Hotel, Hanalei, Hanalei Fill, Jim Nightshade, Marcellus, Marcellus SC, Margarine, McLaren, Mervale Script, Mouse Memoirs, Oregano, Original Surfer, Parisienne, Peralta, Purple Purse, Quintessential, Ribeye, Risque, Romanesco, Rum Raisin, Shojumaru, Spicy Rice, Stalemate, Stint Ultra Condensed, Stint Ultra Expanded, Uncial Antiqua, Yesteryear.

- Converted with babelfont-rs's TTF reader at 26fdcfa (branch 2026-11-02 of https://github.com/felipesanches/babelfont-rs); built with gftools-builder (gftools-rust 1e638bd, fontc 1.0.0).
- Each build was rebuilt from the recorded commit and checked against the shipped fonts with https://github.com/felipesanches/gf-source-modernization (table gate and functional gate, hinting included): functionally equivalent, the same codepoints.
- One known difference, disclosed in each upstream_info.md and README: fontc numbers or packs some GSUB lookups differently (a lookup only a contextual lookup calls; chained contextual rules); every rule is the same and the text shapes identically.

Assisted by an AI agent (Claude Opus 5.5)
