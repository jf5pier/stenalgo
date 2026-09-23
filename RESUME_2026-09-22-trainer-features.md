# Resume: steno-trainer features + */# merge + ce/elles fixes (2026-09-22, evening)

Continuation of `RESUME_2026-09-22-alternate-strokes.md` (its open items 1 and 3 are done,
item 2 is carried over below) and `RESUME_2026-09-21-steno-trainer.md` (items 3/4 done). Everything below is
committed and pushed to `origin/main` (live at https://jf5pier.github.io/stenalgo/).

## Commits this session, in order

1. `6c49ed5` — **X-SAMPA/IPA toggle** (`steno-trainer/src/Notation.elm`, display-only,
   rewrites the whole `Layout` + drill strings at view time; `°`→`ə`, `R`→`ʁ` deliberately
   differ from `src/grammar.py`'s commented-out table) + a **phonology line** in the drill
   (`export_practice_words.formatPhonology`: `Word.syllCV`, dot-separated like the strokes).
   Layout tidy: connect button moved to the sidebar, "Second keyboard" heading removed.
2. `c356eb5` — **Sentence mode**. `util/candidate_sentences.jsonl` (Haiku-authored, each token
   annotated `[form, lemma, gramCat, infoVerb tag, gender, number]`, hand-curated: 24 fragments/
   grammar errors removed, 8 question marks fixed) → `util/export_practice_sentences.py` resolves
   each token to exactly one chord or rejects the sentence (out-of-scope tense, unresolvable or
   still-ambiguous token, word outside `practice-words.json`, tokens not spelling the text).
   217 sentences. Elm: Words/Sentences switch; current word underlined, its reading/phonology/
   chord shown. Lexicon quirks handled in lookup: `j'`/`c'`/`qu'` are filed as `j`/`c`/`qu`;
   no hyphenated inversions (`-tu` looked up as `tu`).
3. `a1d0fb5` — **`*`/`#` first mark merged into the last phoneme stroke**
   (`composeReservedKeyStrokes(..., phonemeStrokeCounts=...)`): `a` avoir = `*a` (was `a/*`),
   `soie` = `swa#`, `partis` = `paR/t*i/-s` (mark on the last PHONEME stroke, before Phase P's
   marker stroke). Escalated codes keep further bare-mark strokes (79 left vs 5139 merged).
   `util/_stenorender.py` renders merged strokes with Plover's own hyphen rule (`*iel`, `pvR-#`)
   — verified against real `plover_stroke` in a throwaway venv: 0 parse errors, 0 collisions after
   normalization across all 163238 entries. Also two **lexicon fixes**: `util/fixCeSchwa.py`
   (`ce` /s2/ → /s°/ in all 3 sources; `se` now takes the `*`: `s*@a`) and `lexique.py`
   `pronounParadigmLemme` `("elles","PRO:per") → "elle"` (+ direct `LexiqueMixte.tsv` patch), so
   `elles` = `iel/-s` like `ils` = `il/-s`. Full recompute chain rerun; 0 residual
   same-lemmeGramCat collisions, 0 conjugation-order violations, 593 tests pass.
4. `7c16131` — **Context words** in Words mode (`formatContext`: le/la/l'/les for NOM/ADJ;
   je/j'/tu/il/nous/vous/ils; que je…/qu'il for subjonctif; trailing `!` for impératif; plainest
   reading wins when a chord writes several; small h-aspiré lemma list for elision). **All 1-key
   phonemes on the first keyboard** (`keyboard-layout.json` per-key `phonemes`, e.g. `wNG`, `eO`,
   no hand hyphen).
5. `43bc6f5` — **Definition mode** (`util/export_definitions.py` → `definitions.json`, whole
   lexicon grouped by shared base chord, labels in an index table; `Definitions.elm`, fetched
   lazily, ~0.8 s decode) and a **hints toggle** (Words/Sentences): off = keyboard shows only the
   typed keys, chord line replaced by the strokes correctly typed so far (`TypedStrokes`, ✓ when
   the word completes).

Then `git gc` (local `.git` 386 MB → 43 MB). Packed repo ≈ 20 MiB; `definitions.json` is
~2.1 MB of it; lexicon sources ~13 MB.

## Known gaps / open items

1. **Browser-eyeball** the last features (definition mode, hints-off typed line, context words,
   phoneme keys) — compiled and data-checked, not visually verified by me.
2. **182 nouns have no gender in Lexique383** (`maison`, `voiture`, `main`, …) → no le/la
   context in the singular. A lexicon fix (gender fill) would fix it.
3. Definition search is exact-spelling (case-insensitive only); no accent-insensitive or prefix
   fallback.
4. Hyphenated compounds in sentences (`celle-ci`, `là-haut`) are drilled as two chords; Plover
   would output them as two words.
5. `football` = `kp@et/svel` was reported as "bizarre" — it matches the layout (f=`kp`,
   u=`@e`, b=`sv`, O=`e`, key 14 shared by /e/ and /O/); user never said what looked wrong.
6. **Plover question discussed, not built**: conjugation marker strokes could be a Plover
   *macro* plugin ("replace previous word with its <marker> form", from a (word, marker) → form
   table the Phase E/G data already implies) instead of ~48k static entries — mainly worth it
   for the onboard Javelin target (flash size). Plover's `ORTHOGRAPHY_RULES` can't do it (French
   forms aren't derivable from spelling). Javelin's equivalent capability not yet checked in
   `~/javelin-steno`. See memory `dual_target_architecture`.
7. Optional, carried over: review `elicitation_answers.json` `q31`/`q49` (`sois` impératif
   rows, and `q32`), all flagged `"clean": false` — they resolve without conflict, not blocking.
8. `RESUME_2026-09-21-steno-trainer.md`, `RESUME_2026-09-22-alternate-strokes.md` and this file
   are untracked (older RESUME files are committed).

## Recompute chain (unchanged shape, one more export)

See memory `lexicon_fix_recompute_order`: `dictionary.py` (delete pickles first) →
`src.elicitation` → `util.build_phase_g_assignment` → `util.build_phase_p_realization` →
`export_plover_dictionary`, `export_keyboard_layout`, `export_practice_words` →
`export_practice_sentences` (needs practice-words first) and `export_definitions`.
