# notdef_census

Question: does each release's glyph 0 equal FontForge's synthesized .notdef exactly when the paired .sfd has none, and is post.isFixedPitch FontForge's one-width rule? Backs the recipe gate for --fontforge-notdef / --fontforge-fixed-pitch (2026-10-02: 8 styles without .notdef all ship the rectangle except Comic Relief x2; only NovaMono is fixed-pitch).

Run from gf-source-modernization: /home/fsanches/compartilhado/gftools/venv/bin/python3 tools/probes/notdef_census/notdef_census.py
