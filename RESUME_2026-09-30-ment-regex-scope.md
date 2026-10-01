# RESUME 2026-09-30 — learnable scopes for the affix rules (`-ment` done, `re`/`ré` analysed)

Written for a fresh Sonnet session. Everything below is on disk; nothing depends on the earlier chat.
Detail sections (definitions, tables, methods) follow the front matter; read "Definitions" first.

## 1. Mission

The affix scan (`util/affix_scan.py --sweep`, outputs `scratch/affix-sweep-partial/{L,M,H}/`) proposes ~30 rules
(a key that replaces an affix syllable, optionally fused with the neighbouring syllable = "growth"). Growth scopes
are enumerated syllable lists (`·[be|ble|…]ment`), unlearnable. Goal: replace each by a short, human-checkable
pattern (regex on the neighbour syllable's spelling) or drop the growth, measured through the REAL simulator,
within the 20-30 rule budget (memory `affix_rule_learnability`; one key + a scope condition, never split a rule:
memory `feedback_no_splitting_rules`). "Done" for a rule = user-approved scope + its numbers recorded here.
The engine (`src/affixes.py`, `src/affixrules.py`) does NOT yet accept regex scopes (option C below).

## 2. Where things are

- Repo `/home/jfsp/stenalgo`, branch `affix-abbreviation-rules` (base `main`), HEAD `7c0ee5f`. Interpreter:
  `env/bin/python` (bare `python` is not on PATH); ~7 GB RAM → one heavy run at a time; long runs with
  `PYTHONUNBUFFERED=1`. Another worktree exists (`/home/jfsp/stenalgo-fix`, branch `lesson-generator`): not ours.
- Uncommitted, intentional, from the previous session (flag `RULE_PARTIAL_OVERLAP`, see
  `RESUME_2026-09-29-affix-partial-overlap-flag.md`): `src/affixes.py`, `src/affixrules.py`, `src/affixes_test.py`,
  `util/affix_scan.py`, `RESUME_2026-09-29-affix-after-lexicon-fix.md`, `scratch/affix-sweep/comparison.md`.
  Uncommitted from THIS session: `TODO.md` (+11 lines: `re`+consonant `R2` phonology entry), this file, and ~40 untracked
  `scratch/` scripts/logs listed in section 3. No `src/` file was touched this session. Do not commit unless asked.
- Inputs used: `scratch/affix-pool.pickle` (lattice pool), `scratch/affix-H-partial-by-anchor.json` (per-anchor sweep
  results, H setting, flag ON: keys and current enumerated lists), `scratch/affix-records.pickle` via
  `util.affix_scan.loadRecords`. Permanent docs were NOT changed (measurements only).

## 3. State

DONE and verified by running (all numbers in the detail sections below):
- `-ment` (rank 1, keys (20,21,25)): scorer `scratch/ment_regex_score.py`, search `scratch/ment_regex_search.py`.
  **USER DECISION: fallback price 5; scope `C{1,2}[eui]+` on the syllable before `ment`** (benefit 8729, 76 fallback
  words of summed freq 85; the enumerated list scores 8525 with 105 fallbacks). Memory `ment-regex-scope-decision`.
- Generic tools for any rank: `scratch/affix_scope_table.py RANK` and `scratch/affix_scope_search.py RANK [PRICE]`.
- `re` (rank 2, keys (16,19)): **USER PRINCIPLE: no growth for `re-`** (meaning-carrying prefix; memory
  `feedback-prefix-meaning-no-growth`); expand only by morpheme variants (`ré-`, `r-`). Measured: anchor alone = 5,846
  words gain, 85 hard-exception words (freq 60, negligible). `re`+`ré` fusable on one key (−1.8% benefit vs two
  rules). The 328 `re`+consonant words coded `R2` are lexicon errors (TODO.md; treated as `R°` in-memory they merge
  at no cost: `scratch/re_r2_patched.py`). Rank 17 (`ra|rai|raie|re|rhé|ré|réh`) is ~all `ré` (3,031 words), contains
  no `R°` word; `ra/rai/raie` (not "again") should stay out.
- Scripts written (all under `/home/jfsp/stenalgo/scratch/`): ment_regex_score.py, ment_regex_search.py, ment_debug.py,
  affix_scope_table.py, affix_scope_search.py, re_compose.py, re_morph.py, re_fusion.py, re_variants.py, re_r2.py,
  re_r2_merge.py, re_r2_patched.py; outputs `ment-regex-*.md`, `ment-syllable-table-*.md`, `scope-table-rank2-H.md`,
  `scope-search-rank2-H.md`. Not running: no background job is active.
NOT done: rank 3+ (en, de, in-, -tion, é, -ter, …); the engine change (option C); the `re`+`ré` merge in the engine;
L/M settings for the `-ment` search (only H was run, L table exists for the scorer).

## 4. Decisions and constraints (the user's, with reasons)

- Fallback price 5 per fallback word (L-setting EXCLUSION_COST): exceptions are cheap, simplicity wins; onset
  exclusion lists like `C\{gj}{1,2}[eu]+` were judged not worth their extra complexity.
- Meaning-carrying prefixes (`re-`) stay anchor-alone; phonetic endings (`-ment`) may get regex scopes.
- `R2` lexicon fix will be done later IN THE MAIN BRANCH by the user; until then treat as `R°` in analyses only.
- Rejected, with reason: `C+ar` / literal-syllable lists for `re` (links two meanings: repartir vs regarder);
  merging `ra/rai/raie` into the `re` key (not the same morpheme, 575 exception words); exhaustive tweak search
  (34k scopes ≈ hours of simulator time, restricted to ≤2 excluded letters).

## 5. Next steps

1. Sanity (2 min): `cd /home/jfsp/stenalgo && env/bin/python -m pytest src/test/affixes_test.py -q` → expect 44 passed.
2. Ask the user which rule next (suggested: rank 6 `in-`, rank 7 `-tion`, both with 3-syllable growth; first classify each
   as meaning-carrying prefix vs phonetic ending). Then for the chosen rank R:
   `PYTHONUNBUFFERED=1 env/bin/python scratch/affix_scope_table.py R H on` (table of current list vs anchor alone vs every
   neighbour, ~2 min) then `... scratch/affix_scope_search.py R 5 H on` (regex search, ~5 min, single-syllable grammar
   only; 3-syllable growth needs the script extended to the two-neighbour case). Acceptance: the regex row beats the
   enumerated list in `objective(5)` with ≤ 5 atoms, reported as in the `-ment` table; write results into this file.
3. Open `re` questions for the user (do not decide alone): merge `re`+`ré` into one key? drop rank 17 then? is `r-`+vowel
   (rouvrir; not a syllable, no saving) worth engine work? strict "stem is a lemma" scope (drops 1,238 covered words)?
4. Option C (about a day, only after the user approves a set of regex scopes): let `src/affixes.py`/`src/affixrules.py`
   accept regex scopes (Candidate slots/lattice, `exclusionCountOf`, `_exceptionRateFloor`, report form column, tests);
   price fallbacks at 5 in the score; verify with one `--sweep` run and md5 comparison per `CLAUDE.md` verification bar.
5. Still owed from `RESUME_2026-09-29-affix-partial-overlap-flag.md`: `scratch/choose_bench.py` equality check,
   comparison tables L/M/H (steps 6-7), and the commit of the uncommitted code (ask the user first).

## 6. Verification bar

- `env/bin/python -m pytest src/test/` must pass (715 at last count); `mypy src/` has ~127 pre-existing errors (diff the
  count against a clean checkout, memory `mypy_preexisting_errors`).
- Scorers must reproduce the sweep before being trusted: `ment` alone = 1 exception, benefit 4,787 (H, flag on).
  Any engine change: sweep outputs compared with `scratch/affix-sweep-partial/` (md5) and explained if different.

## 7. Pitfalls

- Set `A.RULE_PARTIAL_OVERLAP = True` (what `--partial-overlap` does) and the H weights (alpha 2, exclusion 150,
  form 300) or the numbers differ from the sweep; the scripts do both.
- Scores printed by `Rule`-based helpers include FORM_COST per form (300 at H) → compare benefit and exception
  counts, not raw scores, across groupings with different form counts.
- The sweep hides fallbacks (failed 2-stroke words silently revert to k=1); the scripts count them (Definitions).
- Pooling `R2` carriers without changing their stroke gives false `lostDistinction` (relation/relations); patch the
  records (see `re_r2_patched.py`).
- Do not write `while pgrep -f …` wait loops (hook blocks them and they never end): wait on a PID.
- `scratch/` is mostly untracked; scripts run from the repo root (`sys.path.insert(0, ".")`).

## 8. Stop and ask the user when

- choosing which rule to do next, the fallback price for a different kind of rule, or any scope that uses an exclusion list;
- anything about merging rules/keys (`re`+`ré`, rank 17), `r-`, or starting option C (engine change);
- committing, pushing, or touching permanent docs; fixing the `R2` lexicon (the user does it on main).

## 9. Doc updates owed before merge

None yet (measurements only). When a regex scope is wired in: `docs/PIPELINE.md`/`docs/GLOSSARY.md` (define "scope",
"fallback") and the affix rules report format; `TODO.md` `R2` entry removed once the lexicon fix lands.

---
# Reference sections (detail)

## Definitions (used in every table below)

- **Regex scope**: fully matched against the spelling of the neighbour syllable absorbed by the 2-stroke form (the one
  BEFORE the anchor for a suffix such as `ment`, AFTER it for a prefix such as `re`). Match → 2-stroke form (neighbour +
  anchor on one stroke with the rule key); no match → 1-stroke form (anchor alone). `C` = any consonant letter.
- **Fallback word**: a word the regex says gets the 2-stroke form (previous syllable + `ment` on one
  stroke) but which cannot have it, because the combined stroke would collide with another word's outline
  (`lostDistinction`, or `markCostTooHigh`: the homophone marks cost more than the saving). It is written
  with the plain `ment` stroke instead. It still works, it only loses the extra saving; but a learner who
  applies the rule would predict the 2-stroke form, so each fallback word is an exception to memorise.
  Example: `largement` (previous syllable `ge` matches `[eiu]`) collides once merged.
- **Fallback freq**: summed usage frequency of the fallback words (`jument` is cheap to learn as an
  exception, `seulement` is not).
- **Hard exception**: a word that fails even as plain `ment` (1-3 words only).
- **Fallback price**: score points lost per fallback word. An open design choice; the sweep's analogue is
  `EXCLUSION_COST` (L 5, M 50, H 150). Option B therefore prints one table per price instead of one winner.
- **Atoms** (option B): vowel letters + excluded onset letters in a regex; the learnability measure.
- The real sweep does NOT count fallbacks: a word failing as 2-stroke is silently dropped from the
  enumerated list and reverts to `ment` at no cost (~226 words). A regex cannot drop them silently.

## Option A — DONE (this session): offline scorer through the REAL simulator

`scratch/ment_regex_score.py [L|M|H] [on|off]` (defaults H, partial-overlap on = the sweep run to
reproduce; ~10 s per run). It loads the pool pickle + engine like `scratch/choose_bench.py`, takes the
2,724 carriers whose last syllable is `ment`, fixes the sweep's keys `(20, 21, 25)`, builds each word
as a 2-stroke or 1-stroke carrier according to the regex, and calls `simulate` (so `lostDistinction`,
`markCostTooHigh`, `standaloneTrap` are the true ones, not a proxy).
A 2-stroke word that gains nothing retries as plain `ment`: this is a FALLBACK (a word the pattern
names but the learner must know is an exception). Outputs per setting:
`scratch/ment-regex-scores-{L,H}-partial.md` (the candidate table),
`scratch/ment-syllable-table-{L,H}-partial.md` (per previous syllable: marginal score if it alone is
2-stroke, words, examples, whether it is in the current list), logs `scratch/ment-regex-score-*.log`.
`scratch/ment_debug.py` = throwaway check of the real rule's pooled forms.

Validation: the `ment`-alone row reproduces the sweep exactly (1 exception, benefit 4,787). The
enumerated-list row does NOT reproduce the sweep's "1 exception": the real rule silently sends ~226
list words back to plain `ment` (lattice carriers that fail are dropped from the 2-stroke form at no
cost), whereas here they are counted as fallbacks. That is the honest cost for a regex, since a regex
cannot drop them silently. Also seen: the real rule may hold 3-stroke forms (2 previous syllables);
the H sweep kept only k=1 and k=2, and this scorer models only those.

Results (H, flag on; benefit in stroke-frequency units; fallbacks = words named by the pattern that
fall back to plain `ment`):

| scope | k2 words | fallback words | fallback freq | benefit |
|---|---|---|---|---|
| current enumerated list (100 syllables) | 2623 | 105 | 481 | 8525 |
| `(C+[eiuéû]+)?`  (user A) | 2562 | 102 | 426 | 8544 |
| `(C+[eiu]+)?`  (user B) | 2481 | 76 | 85 | 8723 |
| `C+[eiu]` (exactly one vowel) | 2243 | 72 | 71 | 8609 |
| `C+[eiuéûa]+` | 2589 | 119 | 446 | 8606 |
| `C+` + any vowels | 2652 | 168 | 963 | 8516 |
| anything | 2724 | 197 | 1032 | 8494 |

Conclusions: **B `(C+[eiu]+)?ment` is preferable to A**: highest benefit of all (even above the
enumerated list), 76 fallback words of summed frequency 85 (A: 102 words, freq 426 — the `é`/`û`
syllables bring `seulement`, `éléments`, `élément`, `compliment(s)`, `sacrément`, `largement`). Widening
beyond `[eiu]` only adds fallbacks. Fallbacks of B: `jument`, `ciment`, `piment` (fail alone) and
the rest by collisions inside the rule (e.g. `largement`, `rarement`, `parlement`, `argument`,
`bêtement`, `aliments`). Syllables B leaves out but that would gain alone (H marginal): `ca` (+42,
médicament), `cé` (+24, forcément), `lé` (+24, élément(s), isolément) — small; not worth widening.
At L (fallback cost 5) the ranking is the same (B 8327 vs list 7984, A 8014).

Suggested rule text for the user's decision: "`-ment` on one stroke with the previous syllable when that
syllable is consonants + e/i/u (no é, no û); else `ment` alone; exceptions ≈ 76 rare words".
Not yet decided by the user.

## Option B — DONE (first pass, 2026-09-30): automatic regex search

`scratch/ment_regex_search.py [L|M|H] [on|off]` (H/on run took ~4 min) → `scratch/ment-regex-search-H.md`
(full tables) and `.log`. Grammar: onset `C+ | C* | C | C{1,2}`, optionally minus up to 2 excluded consonant
letters (`C\{gj}` = any consonant except g, j), nucleus `[subset of e u i é o a û y î]` with or without `+`;
atoms = vowel letters + excluded onset letters. Each distinct matched-syllable set is scored once by the
real simulator (4,178 scopes from the grammar, 1,029 distinct simulator runs). Tables per fallback price
(0, 5, 20, 50, 150) × atom budget (2-6) plus a benefit-vs-fallback Pareto list.

Headline (H, flag on; benefit, fallback words / their summed freq):
- Reference `(C+[eiu]+)?`: 8723, 76 / 85.
- Price 0-5: `C{1,2}[eui]+` (3 atoms) 8729, 76 / 85; `C{1,2}[euia]+` 8786, 91 / 105 (little more benefit, more
  fallbacks). Excluding `f`/`j` from the onset trims only ~10 fallbacks for ~0 benefit.
- Price 20: `C\{gj}{1,2}[eu]+` (4 atoms) 8344, 29 / 16 (the soft-g/j onsets `ge`, `je` are what collide:
  `largement`, `jument`, `rarement`…).
- Price 50: `C\{gr}{1,2}[eu]+` (4 atoms) 7940, 16 / 13.
- Price 150: `C\{gv}[e]` (3 atoms) 7077, 4 / 5 — but it keeps only 1,084 words as 2-stroke (benefit 7077
  vs 8723), the price of near-zero exceptions.
Pareto knee: the benefit falls slowly from 8729 (74 fallbacks) to ~8100-8300 (21-29 fallbacks, 4-5 atoms),
then steeply below ~16 fallbacks (7940) and ~8 (7459). `é`/`û`/`o` never pay off as vowels; `u` always
does once `e` is in; `i` adds ~390 benefit for ~45 more fallbacks.

Reading: with a fallback price <= 5 the simple rule is `consonant(s) + [eiu]` (1-2 leading consonants);
at a price 20-50 an onset exclusion list of 2 letters (g + j or r) cuts fallbacks 2.5-5x for 4-5 %
less benefit. Whether a 2-letter exclusion counts as "simple" is the user's call (affix_rule_learnability).

Not done / limits: stage-2 tweaks start from the top 3 stage-1 scopes per (price, budget) cell and exclude
at most 2 consonant letters (not exhaustive; a bigger MAX_TWEAKS made 34k scopes ≈ hour+ of simulator time);
the key stays (20,21,25); no coda/literal-syllable alternatives (`ille`, `oie`…); no 3-stroke forms; only
the H/on setting was run (rerun `L on` and `M on` to see stability). Fallbacks partly come from
collisions among the rule's own words, so always rescore a whole regex.

## Option C — NOT done: wire a regex scope into the real evaluator (est. about a day)

Let `src/affixes.py` / `src/affixrules.py` accept a regex scope instead of an enumerated syllable list
(`Candidate.slots` / lattice, `exclusionCountOf`, `_exceptionRateFloor`, the report forms column,
tests in `src/test/affixes_test.py`), so the sweep itself proposes learnable scopes for EVERY rule
(`re`, `en`, `-tion`, …), not only `-ment`. A sweep costs 11-94 min per run. Prerequisites: option B
proving a regex beats the enumerated list on `-ment`; a decision on how regex fallbacks are priced
(EXCLUSION_COST per fallback word is what the scorer prints as "fallback 150 each" at H — at that price
even B pays 76×150; the price to use is the open design question); generalising `C` (consonant letters)
and vowel classes to French orthography (`qu`, `gu`, `ç`, `y`).

## DECISION (user, 2026-09-30) — `-ment` scope

Fallback price = 5 per fallback word (the L-setting EXCLUSION_COST). Adopted scope for `-ment`:
**`C{1,2}[eui]+` before `ment`** = one or two leading consonant letters, then one or more of e/i/u, matched on
the syllable right before `ment` (full match) → 2-stroke form; otherwise plain `ment` alone. Measured (H, flag on,
keys (20,21,25)): benefit 8729, 76 fallback words (summed freq 85), 1 hard exception. Not yet wired into the
evaluator (option C); until then the sweep still reports the enumerated list for `-ment`. Method to reuse
on the next rules: `scratch/ment_regex_score.py` + `scratch/ment_regex_search.py`, generalised per rule
(carriers of the rule's anchor, previous/next syllable spelling, fixed keys from the sweep, fallback price 5).

## Next rules — generic tools and first result for rank 2 (`re`)

Generic tools (any sweep rank, prefix or suffix; neighbour = the syllable absorbed by the 2-stroke form: the one
before a suffix anchor, after a prefix anchor; keys and current lists read from `scratch/affix-H-partial-by-anchor.json`):
- `scratch/affix_scope_table.py RANK [L|M|H] [on|off]` → `scratch/scope-table-rank{RANK}-H.md` (current list vs
  anchor alone vs every neighbour, plus a per-neighbour marginal table).
- `scratch/affix_scope_search.py RANK [PRICE] [L|M|H] [on|off]` → `scratch/scope-search-rank{RANK}-H.md` (regex grammar:
  onset × vowel subset × coda; ~5 min for `re`). `scratch/re_compose.py` = greedy "regex + literal syllables" test.

Rank 2 `re` (keys (16,19), 5,931 carriers, price 5, H, flag on; objective = benefit - 2*excFreq - 5*fallbacks - 300):
- anchor alone: objective 5731 (benefit 6151, 85 HARD exceptions: relax, relais, recours, relève, renard…);
  the current 20-syllable list: 5878 (benefit 6666, 73 fallbacks); giving EVERY following syllable the 2-stroke
  form is a disaster (3,603 fallbacks, -13,524).
- Best single regex on the syllable after `re`: **`C+ar`** (consonant(s) + `ar`: regarder, remarquer, retarder, repartir)
  objective 6301, benefit 6827, 214 words, 21 fallbacks (freq 11): better than the current list with 2 atoms.
  Wider vowel/coda grammars (`C+[au]r`, `C[a][rst]`, `C[a][rn]`…) only add fallbacks.
- The followers that gain most are scattered, not regular: `ve` (revenir), `co` (recommencer, reconnu), `trou`
  (retrouver), `mer` (remercier), `vien` (reviendra), `fu` (refuser), `pré` (représenter), `ssem`, `tour`.
  Greedy literals on top of `C+ar` (objective 6301): +ve 6608, +trou 6830, +mer 6949, +vien 7047, +fu 7129, +pré 7201,
  +ssem 7250, +tour 7297 (but 34 fallbacks, freq 201), +li 7338, +pro 7368 — each literal is one more atom for a
  shrinking gain (~ +300 → +30). A learnability cut around `C+ar` + {ve, co, trou, mer} (5-6 atoms, ~7000) looks sensible;
  NOT decided by the user.
- **USER DECISION / PRINCIPLE (2026-09-30): no k=2 growth for `re`.** `re-` is a very productive, meaning-carrying
  prefix ("again", attachable to almost any verb): repartir = "leave-again" (partir), retarder (tarder) are
  transparent, whereas regarder (garder is a different word/meaning) is an accident. Fusing `re` with the next
  syllable (`gar`, `tar`, `par`…) links two unrelated meanings, so the `C+ar` regex and the literal-syllable list
  above are NOT to be adopted (kept only as measurements). If `re` is expanded, expand it by MORPHEME VARIANTS,
  not by following syllables: `ré-` (réarmer) and `r-` (rouvrir), even though `r-` would bring no saving
  (consistency of the "again" key). Note the sweep also has a separate phonetic rule, rank 17
  `ra|rai|raie|re|rhé|ré|réh` on keys (3,4,16), which overlaps this family — the two need reconciling.
- Measured (scratch/re_morph.py; `re` anchor alone, keys (16,19), flag on): 5,846 words gain (freq ~6,150);
  85 words are hard exceptions (46 lostDistinction: renard, relaie, revend, recueillons…; 39 markCostTooHigh:
  recours, relève, repaire, repère, relax, relais), summed freq only ~60 — mostly words where `re-` is not the
  prefix. CORRECTION of an earlier statement: the 85 exceptions are NOT a real lever (frequency ~1%).
  Of the gaining words, 4,608 have a stem that is itself a lemma (revoir, revenir, retrouver…) and 1,238 do not
  (ressemble, reçu, regrette, recherche, relation, recevoir) — the rule treats both the same (phonetic, key on
  the `re` syllable); a stricter "stem is a word" (morphological) scope would drop those 1,238 (freq ~1,090).
- Morpheme variants in the lexicon (naive "rest is a lemma" count, inflated by false morphology — rire<ire,
  rose<ose, race<ace, rare<are): `ré-` 147 lemmas (freq 216; réunir, réagir, réessayer, réécrire, réintégrer), `r-`
  + vowel 128 (freq 1,358; rappeler, ramener, rapporter, raccrocher, rassurer — mostly the `ra-` syllable), `re-` 535
  (freq 5,556). `ré-` is a real but small family; `r-` needs a verb-only filter. `r-` is not a syllable, so the
  current lattice (syllable-aligned affixes) cannot express it: that is option C-level engine work.
- Suggested next step for `re`: keep the anchor-alone rule; decide (a) merge the ré- spelling into the same key
  (the sweep's variant-merge mechanism, cf. `resolveVariantRivals`), (b) whether rank 17 (ra/re/ré) is redundant,
  (c) whether `r-`+vowel is worth engine work.

### Can `re` (no growth) be fused with rank 17? (scratch/re_fusion.py, H, flag on, k=1 forms only)

Rank 17 (`ra|rai|raie|re|rhé|ré|réh`, keys (3,4,16)) is in fact almost only `ré-` (3,031 of ~3,090 words: récit,
régner, répondre, réel, réveil — mostly NOT the "again" prefix); the other spellings total < 60 words in the sweep.
Benefit (stroke-freq units) / hard-exception words (freq), each group on one key:
- `re` alone on (16,19): 6142 / 194 (154);  `ré` alone on its own key (3,4,16): 2722 / 12 (0) → two rules, two keys: 8864.
- `re`+`ré` fused on (16,19): 8703 / 307 (314) → −161 benefit (−1.8%), +~100 hard-exception words (collisions between
  re- and ré- outlines: réponds/répond(ent), réveil, relation…), frees one key and one rule of the 20-30 budget.
  `ré` alone on (16,19) gives 2613 / 27 (109); the fusion loses only 52 more to cross-collisions.
- Best key for the fused rule by the evaluator: (6,9,18) 8768 / 303 (250) — a slightly better key than (16,19).
- Adding ra/rai/raie/rhé/réh (2,605 pool words: raconter, rapport, rappelle, racisme — NOT "again") raises
  benefit to 10751 but hard exceptions to 575 words (freq 678); on (3,4,16) it is bad (1154 exc). Not recommended
  (`ra-` is not the re- morpheme).
Verdict: YES, fuse `re` and `ré` into one anchor-only rule (one key, ~2% benefit loss); leave `ra/rai/raie` out. To do
in the engine: a variant merge (cf. `resolveVariantRivals`) of anchors `re` + `ré` with growth disabled; check the
learner-facing wording ("re-/ré- = key X"). Scores printed by the script include FORM_COST per phono variant of `re`
(5 root forms), so compare benefit and exceptions, not raw score.

### Odd `re` phonologies (checked 2026-09-30; scratch/re_variants.py, scratch/re_r2.py)

Rank 17 contains NO `R°` word: its `re` anchor is the 17 words spelled `re` pronounced `Re` (revolver, requiem, reggae,
reflex, referendum, revoter); `R°` (5,931) is rank 2 only. 328 words `re`+consonant have first syllable `R2` (relations,
recontacter, revérifier…), all from `LexiqueMixte.tsv`, none spelled `reu`: probable lexicon errors → TODO.md entry added;
until fixed they are not carriers of the `re` anchor. (My earlier `re`+`ré` fusion test pooled every `re` pronunciation,
so its `re` figures include these 328 words.)

### `R2` re-words treated as `R°` (scratch/re_r2_patched.py; in-memory patch only, no file touched)

Method: for the 350 records whose first stroke is the `R2` stroke (8,11,13,14) and spelling `re…` (not `reu…`), set the first
stroke to the `R°` stroke (8,11,12) and the first syllable to `R°`, in both the simulator context and the carriers. (Merely pooling the
328 `R2` carriers WITHOUT changing their stroke is misleading: `relation` (R°) vs `relations` (R2, same lemma, different base) then
counts as `lostDistinction` — an artefact of the lexicon error.) Keys (16,19), H, flag on, anchors only:
- `R°` alone: benefit 6151, 85 hard-exception words (freq 60).
- `R°` + `R2`(as `R°`): benefit 6172, 95 words (freq 76); 324 of the 328 `R2` words gain (fail: repend(s), rependent, repende(s),
  record). So the `R2` words merge into the `re` rule at no cost (+21 benefit, +10 exception words, freq +16).
  Best key for the merged rule: (9,18), benefit 6199, 40 exception words (freq 49).
- `R°`+`R2`+`ré` (Re) fused: benefit 8733, 208 hard-exception words (freq 236) on (16,19); best key (6,9,18): 8801, 195 (freq 168).
  Compare two separate rules (re 6172 + ré 2722 = 8894): the fusion costs ~160 benefit (−1.8%) and ~110 exception words
  (réponds, répond(ent), réveil, reparti, revoler…). After the lexicon fix (main branch) these numbers become the real ones.

## UPDATE 2026-09-30 (evening) — lexicon fix landed; `re`/`ré` remeasured on the REAL lexicon

- `R2` fix done on main (`5087bd5`, `util/fixReSchwa.py`, 164 Lexique383 rows; pushed), merged into this branch (`066897d`).
  Records and pool regenerated (`--refresh --part a --partial-overlap`); H-only sweep rerun
  (`util.affix_scan --part b --reuse-pool --sweep --partial-overlap --settings H`, 25 min, 1,365 s of it in the
  variant-rival step): `scratch/affix-sweep-partial/H/`. `re` anchor `R°` now 807 lemmas, freq 6,248 (was 715 / 6,211);
  the `R2` anchor is gone. `scratch/affix-H-partial-by-anchor.json` is STILL the old sweep (rank/keys equal for
  rank 2, but its "current list" columns are stale; `affix_scope_table.py` reads it).
- `-ment` rerun: regex `C{1,2}[eui]+` unchanged (benefit 8,729, 78 fallback words / freq 85, 1 hard exception);
  enumerated list 8,525 / 105 fallbacks; `(C+[eiu]+)?` 8,723. Decision stands.
- `re`/`ré` (scratch/re_fusion.py, re_morph.py; H, flag on; benefit / hard-exception words (freq)); no patch needed now:

| group | (16,19) | best key |
|---|---|---|
| `re` alone | 6,219 / 98 (76) | (9,18): 6,246 / 47 (49) |
| `ré` alone | 2,613 / 27 (109) | own key (3,4,16): 2,722 / 12 (0) |
| `re`+`ré` fused | 8,781 / 211 (236) | (6,9,18): 8,845 / 207 (172) |
| rank 17 (`ré`+`rhé`+`réh`+`rai`+`raie`+`ra`) | 5,000 / 84 (134) | (2,11,18): 5,092 / 93 (42) |
| all of rank 2 + 17 | 10,829 / 480 (600) | (9,18): 10,824 / 486 (606) |

  Two rules (6,219 + 2,722 = 8,941) vs fused 8,781: fusion costs 160 benefit (-1.8%) and ~113 more hard-exception
  words, frees a key and a budget slot. Matches the earlier patched estimate (8,733 fused, -1.8%).
- `re` anchor alone: 6,159 words gain (4,880 stem-is-a-lemma + 1,279 not); 95 hard exceptions (freq ~76).
- Sweep on the merged lexicon, top of the list (H): 1 `-ment` 8,587; 2 `re|reh` 6,415 (still with growth forms);
  3 `en`; 4 `de|des|dé|déh`; 5 `de`; 6 `-tion`; 7 `in-`; 8 `é`; 17 `ra|rai|raie|re|rhé|ré|réh` 2,689.
- Still open: the `re`/`ré` decisions of section 5 step 3 (fuse, rank 17, key, `r-`, strict stem scope).

- CORRECTION (same evening): the rows "rank 17" and "all of rank 2 + 17" above (and the earlier "ra/rai/raie adds raconter,
  rapport" claims) are contaminated: `scratch/re_fusion.py` picks roots by spelling only, so its `ra` root also pulled
  in the separate `Ra` prefix anchor (441 lemmas). The REAL rank 17 anchor (phonology `Re`) holds ~3,740 carriers, of
  which `ra` = 1 word (rayâmes), `rai` = 6, `raie` = 6, `rhé` = 14 carriers: the extras really are negligible
  (TODO.md entry added for the `ra`+`Re` oddity). DECISION (user): `re` (`R°`) and `ré` (`Re`) stay separate rules (status
  quo, no phonology-class merge); the `re`+`ré` merge section of this note is kept as measurement only. Also measured:
  best 2-key pair for fused `re`+`ré` = (6,18): benefit 8,896, 214 hard exceptions (freq 122) (`scratch/re_fusion_2keys.py`).
