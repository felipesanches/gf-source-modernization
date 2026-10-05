#!/usr/bin/env python3
"""Question answered: what should fontc_crater's targets.json say for the current
google/fonts, changed as little as possible?

Inputs: the current targets.json (googlefonts/fontc_crater) and the output of
google-fonts-sources run against google/fonts main. Output: the merged targets.json.

  1. The generated entries are the truth: an entry exists, with its rev and config, iff
     google-fonts-sources finds it.
  2. Entries google-fonts-sources cannot discover are kept verbatim, where they were:
     the private repositories marked "auth" (googlesans, googlesans-flex) have no source
     block in google/fonts and are listed by hand.
  3. To keep the diff small, an entry that only changed in place (same repo_url and
     config) stays at its old position, and a new entry goes right after its predecessor
     in the generator's order, so unchanged lines are never moved.
  4. The file is written in the generator's format (serde_json pretty, two-space indent)
     with the trailing newline the committed file has.

Usage: crater_targets.py <current targets.json> <generated.json> > targets.json
Prints a summary to stderr: kept, added, removed, rev changes.
"""
import json
import sys


def key(e):
    return (e["repo_url"], e["config"])


def main():
    old = json.load(open(sys.argv[1]))
    gen = json.load(open(sys.argv[2]))
    gen_keys = {key(e) for e in gen["sources"]}
    gen_urls = {e["repo_url"] for e in gen["sources"]}
    # 2. hand-kept entries: private repositories the generator cannot see
    kept = [(i, e) for i, e in enumerate(old["sources"])
            if e.get("auth") and e["repo_url"] not in gen_urls]

    # 3. position every generated entry: at its old place if it has one, else just
    #    after the entry before it in the generator's order
    old_pos = {}
    for i, e in enumerate(old["sources"]):
        old_pos.setdefault(key(e), []).append(i)
    placed = []
    prev = -1.0
    for n, e in enumerate(gen["sources"]):
        slots = old_pos.get(key(e))
        if slots:
            pos = float(slots.pop(0))
        else:
            pos = prev + 1e-6 * (n + 1) / (len(gen["sources"]) + 1)
        placed.append((pos, n, e))
        prev = pos
    for i, e in kept:
        placed.append((float(i), -1, e))
    sources = [e for _, _, e in sorted(placed, key=lambda t: (t[0], t[1]))]

    out = {"version": gen["version"], "fonts_repo_sha": gen["fonts_repo_sha"], "sources": sources}
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    old_by = {(e["repo_url"], e["config"], e["rev"]) for e in old["sources"]}
    new_by = {(e["repo_url"], e["config"], e["rev"]) for e in sources}
    old_k = {key(e) for e in old["sources"]}
    added = sorted(k for k in gen_keys if k not in old_k)
    removed = sorted(k for k in old_k if k not in {key(e) for e in sources})
    moved = sorted({(u, c) for u, c, r in new_by - old_by} - set(added))
    print("old %d entries, generated %d, kept by hand %d (%s), result %d"
          % (len(old["sources"]), len(gen["sources"]), len(kept),
             ", ".join(e["repo_url"].rsplit("/", 1)[-1] for _, e in kept), len(sources)),
          file=sys.stderr)
    print("added %d, removed %d, rev changed %d" % (len(added), len(removed), len(moved)),
          file=sys.stderr)
    for tag, rows in (("+", added), ("-", removed), ("~", moved)):
        for u, c in rows:
            print("  %s %s  %s" % (tag, u, c), file=sys.stderr)


if __name__ == "__main__":
    main()
