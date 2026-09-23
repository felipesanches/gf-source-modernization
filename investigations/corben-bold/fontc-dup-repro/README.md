# fontc: a duplicated glyph name ends in "Unable to proceed; N jobs stuck pending"

Question answered: is Corben-Bold's build failure caused by the duplicated glyph name
alone, independently of Corben?

`DupName.glyphs` has two glyphs named `a`; `UniqueName.glyphs` is byte-identical except
the second is `a.1`.

    fontc 0.6.0 (3518040e):  DupName -> "Unable to proceed; 29 jobs stuck pending", exit 1
                             UniqueName -> builds, exit 0
    gftools-builder3 e851b8b (fontc 1.0.0): DupName -> "Unable to proceed; 30 jobs stuck
                             pending", exit 1; UniqueName -> DupName-Regular.ttf, exit 0

Mechanism (fontc-1.0.0/src/workload.rs): `insert_with_bookkeeping` bumps
`count_pending[Glyph]` once per job, but `jobs_pending` is a HashMap keyed by
`Fe(Glyph(name))`, so the second `a` replaces the first. One completion decrements
the counter once; it never reaches 0; `Fe(GlyphOrder)` (which reads the whole Glyph
variant) is never launchable and everything downstream is reported stuck.

Rerun:
    fontc --build-dir /tmp/x -o /tmp/x.ttf DupName.glyphs
    (config.yaml: "sources: [DupName.glyphs]") gftools-builder config.yaml
