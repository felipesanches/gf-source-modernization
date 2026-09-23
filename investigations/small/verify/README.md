# small/verify -- adversarial verification probes

Written by the verifier of unit "small"; the investigation's own files (../edits,
../probes, ../runs) are read, never modified. Findings: ../VERIFY.md.

| script | question it answers |
|---|---|
| probes/make_edits.sh | the exact .sfd copies converted: FSType 0 (proposed edit) and UnderlinePosition -97 (simulation only), made fresh from the archive |
| probes/conv_checks.sh | which babelfont flags change the ComicRelief conversion (f725e6a and ca43adc); is the simulation copy different only in underlinePosition |
| probes/ff_underline_vintage.sh | FontForge's post.underlinePosition rule per release tag, and which FontForge writes SFD 3.2 |
| probes/binary_facts.py | RussoOne binary history (what 8ccda7bf7 changed); Tuffy FSType stated vs shipped |
| rerun.sh | all of the above plus the 8 harness runs, one build at a time |

Signal read: the gate's closing line "N blocking table difference(s)" in
runs/<run>/<Style>.gate.txt; 0 = CLEAN. runs/gate_summary.txt collects them.
