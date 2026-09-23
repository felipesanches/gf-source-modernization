#!/usr/bin/env python3
"""Write investigations/<unit>/{results.json,FINDINGS.md,VERIFY.md} from the
investigation workflow's structured results.

Question answered: what did each investigating agent and its adversarial verifier
conclude, in a form someone can read without the session transcript?

The subagent harness refused to let most agents write report files, so their reports
exist only as the structured results in the workflow journal. This keeps the whole
record (results.json) and renders it readably. A FINDINGS.md or VERIFY.md an agent
did manage to write is never overwritten. `CONCLUSIONS` holds the conclusion the
parent drew for each unit after reading both reports; it leads FINDINGS.md.

Usage: findings_from_results.py <journal.jsonl> <unit>...
"""
import json
import os
import sys
import textwrap

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONCLUSIONS = {
    "heights": """\
The height rows the current FontForge rule does not reproduce are, with one exception,
FontForge's own older rule. Until commit 4d34d21ef866 (2012-05-14) `SFStandardHeight`
divided the sum of the distinct round tops by the number of GLYPHS. HerrVonMuellerhoff,
Miama, NosiferCaps and UnifrakturCook were exported by FontForge 20110222 (the FFTM stamp),
which gives exactly their released values: UnifrakturCook's 319/485 where today's rule
gives 1087/1577. babelfont gf-sfd-conversion 8b59bc3 adds
`--fontforge-height-glyph-count-mean`; tools/recipe.py passes it when the release's FFTM
stamp is below 1337023489. Selecting the rule by vintage reproduces 29 of 38 styles, against
23 with today's rule alone, and no pre-2012 style matches only under today's rule
(`vintage_selection.txt`, `probe_all.txt`). The old divisor entered in FontForge 37d20840
(2009-05-27); the report below cites 5fba6c9, the same change in a history with no common
ancestor with 4d34d21ef866 (GitHub compare API: 37d20840 is 740 commits behind the fix).

The exception is PatrickHand: its release was exported from the cubic
`src/PatrickHand-Regular.otf` (cap height 661), while the `.sfd` re-imports the hinted
release (660). One documented edit, `OS2CapHeight 661`.""",
    "nosifer": """\
Nosifer-Regular.ttf was exported with FontForge's OpenType tables off (a legacy kern table,
no GSUB), so the source's one `liga` lookup (E E) never shipped. One documented edit drops
it; whether to reproduce that absence or keep the ligature as better than the release is a
decision for Felipe. Both height rows are FontForge 20110222's pre-2012 rule, handled by the
converter; NosiferCaps' only other row is the weight class, handled by the fontc
workaround.""",
    "unifraktur": """\
Seven rows, every one reproduced from the unmodified source with the FontForge build the
release's FFTM names. The cap height is the pre-2012 height rule (converter). The hhea and
win descents are FontForge's exporter bases for offset-mode metrics -- win from the
on-curve-only head bbox, hhea from int() of the true bounds widened to the head bbox -- a
converter change NOT yet implemented. The three GPOS rows are FontForge's empty GPOS, which
shares GSUB's script list when only GSUB has lookups; HarfBuzz gates its fallback mark
positioning on that table's presence, so reproducing it would make marks render worse
(sfd-batch6/UNIFRAKTURMAGUNTIA-EMPTY-GPOS.md). Not landed: the GPOS question is Felipe's.
The Book/Regular file name is a METADATA.pb files mapping, disclosed as a converter
normalisation.""",
    "corben-bold": """\
Corben-Bold failed to build because its `.sfd` names two glyphs `dcroat` (gid 211, the real
U+0111, and gid 547, empty and unencoded); fontc reports that only as "N jobs stuck pending".
Renaming gid 547 alone lets it build; the vertical metrics from the sibling
`Corben-Bold-TTF.sfd`, the family's vendor and the release's PANOSE close 8 more rows. The
verifier found the recipe's `--add-legacy-duplicate-cmap` rule misfiring, which led to a
measurement across all 42 styles (tools/probes/cmap_recipe/): the flag is never right for
these FontForge exports, and 11 landed styles had gained codepoints the table gate tolerates.
The flag is now never passed, and the cmap is checked exactly.""",
    "small": """\
RussoOne: one documented edit, `FSType 0` (google/fonts 8ccda7bf7 fixed the binaries in
2015; the source still states 4). Comic Relief: its underline is FontForge's post-2019 rule,
trunc(position + width/2) (the `.sfd` is SplineFontDB 3.2) -- moot for now, because Comic
Relief has an active upstream and is not being converted.""",
    "tuffy": """\
Tuffy-Bold and BoldItalic are FontForge 2.0 exports of exactly these `.sfd`. Tuffy-Regular
and Italic ship v1.272, a 2017 third-party rebuild (google/fonts PR #1269) of FontForge's
001.271 export, with the traits of a Glyphs.app round trip. Reproducing v1.272 needs a
dozen edits that commit its defects -- 43 Greek iota-subscript glyphs drawn beside rather
than under the letter, fsType 8, 500/700 heights that are Glyphs defaults, not the
design's -- and still leaves 3 GSUB rows per style. The alternative is to land against the
001.271 binary Google Fonts shipped 2015-2017, which our build reproduces at 3 rows. That
choice, and the re-pairing it implies, is Felipe's; tuffy is not landed. Two findings
outlived the family: the table gate's area-measure bug (fixed, sfd-batch5 cd4f827) and
FontForge's synthesised `.notdef` (a proposed converter filter).""",
}


def ascii(text):
    rep = {"—": "--", "–": "-", "’": "'", "‘": "'", "“": '"',
           "”": '"', "…": "...", "→": "->", "←": "<-", "≈": "~",
           "×": "x", "≤": "<=", "≥": ">=", "≠": "!=", " ": " "}
    out = "".join(rep.get(c, c) for c in text)
    return out.encode("ascii", "replace").decode("ascii")


def para(text, width=88):
    """Refill plain prose; leave text that carries its own Markdown alone."""
    lines = text.splitlines()
    if lines and lines[0].startswith("INTENDED CONTENT OF"):
        lines = lines[1:]
    text = "\n".join(lines).strip()
    if "\n#" in text or "\n|" in text or "\n- " in text or text.startswith("#"):
        return text
    return "\n\n".join(textwrap.fill(p, width) for p in text.split("\n\n"))


def findings(unit, inv):
    lines = ["# %s -- investigation findings" % unit, "",
             "**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the",
             "conclusion below). Written from the agents' structured results (`results.json`).", "",
             "## Conclusion", "", CONCLUSIONS.get(unit, "(no conclusion recorded)"), "",
             "## Investigator's report", "", para(inv["verification"]["summary"]), "",
             "Rows before: %s" % inv["verification"]["rows_before"], "",
             "Rows after: %s" % inv["verification"]["rows_after"], "",
             "Confidence: %s" % inv.get("confidence", ""), "", "## Rows", "",
             "| style | row | class | cause |", "|---|---|---|---|"]
    for r in inv["rows"]:
        lines.append("| %s | %s | %s | %s |" % tuple(
            s.replace("|", "/").replace("\n", " ") for s in
            (r["style"], r["row"], r["classification"], r["cause"])))
    if inv["proposed_sfd_edits"]:
        lines += ["", "## Proposed .sfd edits", ""]
        for e in inv["proposed_sfd_edits"]:
            lines += ["- **%s** (%s) `%s %s` -- verified: %s; value from: %s; the source stated: %s"
                      % (e["commit_subject"], ", ".join(e["styles"]), e["op"].split(" (")[0],
                         e["args"].replace("\n", "; "), e["verified"], e["value_derived_from"],
                         e["source_currently_states"])]
    if inv["proposed_converter_changes"]:
        lines += ["", "## Proposed converter changes", ""]
        for c in inv["proposed_converter_changes"]:
            lines += ["- %s" % c["description"].replace("\n", " "), "",
                      "  Evidence: %s" % c["evidence"].replace("\n", " ")]
    if inv["unresolved"]:
        lines += ["", "## Unresolved", ""] + ["- %s" % u.replace("\n", " ") for u in inv["unresolved"]]
    lines += ["", "## Rerun", "", "    " + "\n    ".join(inv["verification"]["commands"])]
    return ascii("\n".join(lines)) + "\n"


def verify(unit, ver):
    lines = ["# %s -- adversarial verification" % unit, "",
             "**Model**: Claude Opus 5.5. Written from the verifier's structured result.", "",
             "Reproduced: %s" % ver["reproduced"], "", para(ver["reproduction_notes"]), "",
             "## Verdict", "", para(ver["overall"]), "", "## Per edit", ""]
    lines += ["- [%s] %s -- %s" % (e["verdict"], e["commit_subject"], e["reason"].replace("\n", " "))
              for e in ver["edit_verdicts"]]
    if ver["classification_objections"]:
        lines += ["", "## Objections", ""] + ["- %s" % o.replace("\n", " ") for o in ver["classification_objections"]]
    if ver["missed"]:
        lines += ["", "## Missed", ""] + ["- %s" % m.replace("\n", " ") for m in ver["missed"]]
    return ascii("\n".join(lines)) + "\n"


def main():
    journal, units = sys.argv[1], sys.argv[2:]
    inv, ver = {}, {}
    for line in open(journal):
        d = json.loads(line)
        r = d.get("result")
        if d.get("type") == "result" and isinstance(r, dict):
            (ver if "overall" in r else inv)[r["unit"]] = r
    for unit in units:
        d = os.path.join(W, "investigations", unit)
        os.makedirs(d, exist_ok=True)
        json.dump({"investigation": inv.get(unit), "verification": ver.get(unit)},
                  open(os.path.join(d, "results.json"), "w"), indent=1)
        for name, render, data in (("FINDINGS.md", findings, inv.get(unit)),
                                   ("VERIFY.md", verify, ver.get(unit))):
            path = os.path.join(d, name)
            if data is None or os.path.exists(path):
                print("%s/%s: %s" % (unit, name, "kept (written by the agent)" if data else "no result"))
                continue
            open(path, "w").write(render(unit, data))
            print("%s/%s: written" % (unit, name))


if __name__ == "__main__":
    main()
