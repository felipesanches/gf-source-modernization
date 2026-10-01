reland-2026-10-01 shaping/gdef cluster -- probes (scratch, not committed)

All scripts use the gftools venv: PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
Outputs land in ../runs/<tag>/<repo>/ (fonts/ttf, <style>.json = functional_gate JSON, <style>.txt).

build_gate.sh <repo> <tag> [<sources dir>]
    Does <repo>'s converted source (or a patched copy) build and pass the functional
    gate? Builds with gftools-builder (gftools-rust ade8776, fontc 1.0.0), nice -n 10,
    then tools/functional_gate.py --json per style against families*.tsv's shipped font.
run_many.sh <tag> <srcroot|-> repo...
    build_gate.sh for several repos, one at a time; progress in ../runs/<tag>.progress.
summarize.py ../runs/<tag> [--only-fail] [--examples N]
    Which shaping corpora / GDEF rows differ, with the first differing runs
    (release vs build, glyph@x,y).
add_ff_gdef.py <sfd> <in.glyphs> <out.glyphs>
    Emulates the proposed babelfont --fontforge-gdef-classes on a converted .glyphs:
    FontForge's gdefclass() per glyph, written as `table GDEF { GlyphClassDef ... }`.
gdef_oracle_check.py <sfd> <release.ttf>
    Does that gdefclass() rule reproduce the release's GDEF GlyphClassDef glyph by glyph?
prep_gdef.sh repo...
    add_ff_gdef.py over every style of a landed repo -> ../runs/proto-gdef-src/<repo>/sources.
sfd_kern_dups.py <sfd>
    Pairs kerned by Kerns2 in more than one subtable of one lookup.
fold_pairpos_into_kerning.py <in.glyphs> <out.glyphs>
    Emulates dropping (or folding into kerning) the FEA PairPos2 rules of a kern lookup
    that an earlier Kerns2 subtable already holds (Italiana / Sanchez double kerning).
reconvert.py <babelfont binary> <outroot> <repo> [extra flags]
    Re-runs the exact land.py conversion (recipe flags + plan flags + workarounds) with
    another babelfont binary; with upstream 004200b it reproduces the landed .glyphs
    byte for byte (checked on oleoscript).
queue*.sh
    The sequential run order used in this session.

Rust prototype: ../bf-wt (detached worktree of babelfont-rs at 004200b7) + ../bf-wt.patch.
gdef_census.py
    Across every paired style: does the gdefclass() oracle reproduce the release's GDEF
    GlyphClassDef? Output: ../runs/gdef_census.txt (120 exact, 2 mismatches = Thabit).

Prototype binary: ../babelfont-proto (sha256 5af7d73ad030ac5d...), built from
../bf-wt = babelfont-rs 004200b7 + ../bf-wt.patch (cargo target deleted to save 4.5 GB;
rebuild: CARGO_TARGET_DIR=<dir> cargo build --release -p babelfont --features cli).
Verification runs: ../runs/rust/<repo> (reconvert.py with babelfont-proto, then build_gate.sh).
