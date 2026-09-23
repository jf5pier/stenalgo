#!/usr/bin/env bash
# Full clean rebuild of every pipeline artifact, then md5 of each output.
# Usage: bash docs/refactor/rebuild_and_hash.sh > docs/refactor/<label>.md5
# Used by the docs refactor to prove live behaviour is unchanged (compare to baseline.md5).
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=env/bin/python
# Pickle building iterates hash-ordered sets; pin the seed so rebuilds are comparable
# (without it, phase_p_keypress_realization.json residual lists vary run to run).
export PYTHONHASHSEED=0
rm -f Dictionary.pickle FirstTheory.pickle
$PY dictionary.py                          >&2
$PY -m src.elicitation                     >&2
$PY -m util.build_phase_g_assignment       >&2
$PY -m util.build_phase_p_realization      >&2
$PY dictionary.py                          >&2   # theory 2 against the fresh press-sets
$PY -m util.export_plover_dictionary       >&2
$PY -m util.export_plover_system           >&2
$PY -m util.export_keyboard_layout         >&2
$PY -m util.export_practice_words          >&2
$PY -m util.export_practice_sentences      >&2
$PY -m util.export_definitions             >&2
md5sum theory.tsv theory2.tsv resolved_press_sets.json questionnaire.json \
  phase_g_keypress_assignment.json phase_p_keypress_realization.json \
  plover_stenalgo_dictionary.json plover_stenalgo/plover_stenalgo/_generated_keys.py \
  steno-trainer/public/data/*.json
# The tracked Phase P report's residual-collision lists depend on the hash seed the pickles
# were built with (see todo.md suspected bugs); keep the committed copy in the working tree.
git checkout -- phase_p_keypress_realization.json
