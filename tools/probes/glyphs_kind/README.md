# glyphs_kind -- metadata.py / verify_landed.py on `glyphs` rows

**Model**: Claude Opus 5.5. **Date**: 2026-10-02.

Question: after teaching tools/verify_landed.py and tools/metadata.py the `glyphs` row kind
(families.tsv; tools/land.py builds such a repository as upstream history + template +
"Add a gftools-builder config for <source>"), is the output for every other kind unchanged,
and what do they say for Play?

- `metadata_dryrun.py` runs `metadata.main()` unchanged but redirected: a throwaway git
  repository under `<scratch>` stands in for the google/fonts worktree (only the family's
  METADATA.pb and upstream_info.md, from a fixed google/fonts ref), and a synthetic
  landed.tsv marks each repo CLEAN at its HEAD. Prints each commit's message and files;
  nothing time- or hash-dependent, so runs diff cleanly.

## Identity proof (2026-10-02)

Run each command with tools/ at the parent commit (before) and at the commit adding this
directory (after), then `cmp` the outputs. PY=/home/fsanches/compartilhado/gftools/venv/bin/python3,
R=/home/fsanches/compartilhado/tmp/reland-gdef/repos (landed repos: ledger, magra = hg;
cardo, comicrelief = upstream; abrilfatface = fork; allerta = allerta), google/fonts ref
23e54b51ddffbc7713c583748e3bd86f62b1fa4a.

    OUT=$R FAMILIES=families-next.tsv $PY tools/probes/glyphs_kind/metadata_dryrun.py <scratch>/a 23e54b51 ledger magra cardo
    OUT=$R $PY tools/probes/glyphs_kind/metadata_dryrun.py <scratch>/b 23e54b51 abrilfatface allerta comicrelief
    OUT=$R SCRATCH=<scratch> FAMILIES=families-next.tsv $PY tools/verify_landed.py ledger magra cardo
    OUT=$R SCRATCH=<scratch> $PY tools/verify_landed.py abrilfatface allerta comicrelief

Result: metadata output byte-identical (493 + 496 lines); verify_landed output byte-identical
(VERIFIED x4; cardo FAILED BUILD, comicrelief FAILED, same lines) except one line: the order
of two tied 55 px glyphs (U+03A6, U+0424) in comicrelief Bold's rendering summary. That tie
order is nondeterministic in tools/functional_gate.py itself: the unchanged verify_landed.py
(`git show <parent>:tools/verify_landed.py`, run with PYTHONPATH=tools) printed both orders
across runs, as did the new one.

Play (OUT=/home/fsanches/compartilhado/tmp/agent-play2/repos, landed b8121a3 with the
builder-fixes variant): verify_landed.py reports no ORIGINAL, LICENCE, SHAPE, MESSAGE or
REMOTE problem; it fails GATE/CMAP/FUNCTIONAL because it rebuilds with the stock B3
(ade8776, hex unicodes read as decimal), the only builder binary present then.
