#!/usr/bin/env bash
# Full rebuild (S2-S9) with md5 snapshots, to compare against the pre-change baseline.
# Usage: ./rebuild_md5.sh
# Produces md5_before.txt (from git HEAD, so the committed outputs are the baseline) and md5_after.txt, then diffs them.
# Run it outside the claude.slice cgroup, e.g.: systemd-run --user --scope ./rebuild_md5.sh
set -euo pipefail
cd "$(dirname "$0")"

FILES=(
  phonetic_theory.tsv disambiguated_theory.tsv
  resolved_press_sets.json keypress_groups.json realization_report.json
  plover_stenalgo_dictionary.json
  affix_rules.json affix_rules_report.md
  plover_stenalgo_affix_dictionary.json affix_abbreviations.tsv
)

IGNORED=(phonetic_theory.tsv disambiguated_theory.tsv resolved_press_sets.json)  # gitignored: no committed baseline

# Baseline = md5 of the committed (HEAD) version of every tracked output.
snap_head() {
  for f in $(git ls-files "${FILES[@]}" 'steno-trainer/public/data/*.json'); do
    echo "$(git show "HEAD:$f" | md5sum | cut -d' ' -f1)  $f"
  done
}
snap() {
  md5sum $(git ls-files "${FILES[@]}" 'steno-trainer/public/data/*.json') 2>&1
}

step() { echo; echo "=== $(date +%T) $*"; "$@"; }

snap_head > md5_before.txt
echo "Baseline (git HEAD) written to md5_before.txt"
[ -f phonetic_theory.tsv ] && md5sum "${IGNORED[@]}" > md5_ignored_before.txt \
  && echo "NOTE: md5_ignored_before.txt = current gitignored outputs (possibly from a crashed run, not a true baseline)"

# Cold start: caches are never staleness-checked (except DisambiguatedTheory)
rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle AffixSelection.pickle

time step python dictionary.py   # S2-S9, incl. the affix layer

snap > md5_after.txt
md5sum "${IGNORED[@]}" > md5_ignored_after.txt
[ -f md5_ignored_before.txt ] && { diff md5_ignored_before.txt md5_ignored_after.txt && echo "ignored outputs: identical to pre-run copy"; }
echo; echo "=== Comparison (empty diff = identical)"
if diff md5_before.txt md5_after.txt; then echo "IDENTICAL"; else echo "DIFFERENCES FOUND"; exit 1; fi
