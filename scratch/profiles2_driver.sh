#!/bin/bash
# Round-2 per-step cProfile batch (PERF_ROUND2_HANDOFF.md §2 recipe).
cd /home/jfsp/stenalgo-fix || exit 1
PY=/home/jfsp/stenalgo/env/bin/python
mkdir -p scratch/profiles2
cp pipeline_timings.log scratch/profiles2/pipeline_timings.before.txt
rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle

run() {
  name=$1; shift
  echo "=== $(date +%T) profiling $name: $*" >&2
  PYTHONUNBUFFERED=1 "$PY" -m cProfile -o "scratch/profiles2/$name.pstats" -m "$@" \
    > "scratch/profiles2/$name.run.log" 2>&1 \
    || echo "FAILED $name (see scratch/profiles2/$name.run.log)" >&2
}

# Dependency order: S3-S5 first (writes the two unchecked pickles), then the four
# S2 appenders individually (the wrapper only subprocesses; converged -> appends 0),
# then S6-S8 exactly as dictionary.py runs them (S7 writes DisambiguatedTheory.pickle,
# so the later steps profile the cache-hit path like the pipeline does).
run build_phonetic_theory util.build_phonetic_theory
run completeVerbParadigms util.completeVerbParadigms --apply
run generateMissingNomAdjForms util.generateMissingNomAdjForms --apply
run fixPayerDualFormGaps util.fixPayerDualFormGaps --apply
run fixAsseoirDualFormGaps util.fixAsseoirDualFormGaps --apply
run elicitation src.elicitation
run build_keypress_groups util.build_keypress_groups
run build_disambiguated_theory util.build_disambiguated_theory
run build_realization_report util.build_realization_report
run export_plover_dictionary util.export_plover_dictionary
run export_practice_words util.export_practice_words
run export_practice_sentences util.export_practice_sentences
run export_definitions util.export_definitions

# Extracts: top-20 by cumulative and by tottime per step
for f in scratch/profiles2/*.pstats; do
  b=$(basename "$f" .pstats)
  { "$PY" -c "import pstats; pstats.Stats('$f').sort_stats('cumulative').print_stats(20)"
    echo "===== sort by tottime ====="
    "$PY" -c "import pstats; pstats.Stats('$f').sort_stats('tottime').print_stats(20)"
  } > "scratch/profiles2/$b.top.txt"
done
cp pipeline_timings.log scratch/profiles2/pipeline_timings.after.txt
echo "ALL DONE $(date +%T)" >&2
