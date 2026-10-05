# Affix abbreviation rules

Status: Affix Abbreviation Building (S9) is a stage of the pipeline, run last by `python dictionary.py`. It picks 30 affix rules from
the user's verdicts (`affix_decisions.json`), writes them to `affix_rules.json` and the report `affix_rules_report.md`, and exports an
OPTIONAL abbreviation dictionary on top of the stable theory (`plover_stenalgo_affix_dictionary.json`, `affix_abbreviations.tsv`).
Nothing in the phonetic theory, the disambiguated theory or the main Plover dictionary depends on it.

An **affix rule** puts a frequent affix syllable (`re-`, `-ment`, `-tion`...) on ONE dedicated keypress that is
merged into the neighbouring syllable's stroke, so a word such as `regarder` saves a stroke. The generator
finds the candidate rules, a budgeted selection keeps 30, and every rule gets the keypress that saves the most.
Vocabulary: [GLOSSARY.md](GLOSSARY.md) ("Affix ..." entries). Philosophy, design choices and algorithms: [AFFIX_DESIGN.md](AFFIX_DESIGN.md). Design history (historical, superseded where they differ):
`DESIGN_2026-09-27-affix-rule-selection.md`, `PLAN_2026-09-28-affix-single-generator-rewrite.md`,
`PLAN_2026-10-01-affix-pipeline-implementation.md` (this implementation), the `RESUME_2026-09-*` notes.

## The flow

```
python dictionary.py   ... S8 ...
  S9a  python -m util.build_affix_rules     reads affix_decisions.json (+ the stable theory, starboard3h.json)
         AffixSelection.pickle present and made from the current decisions -> reused as is (seconds)
         present, decisions changed -> reselect (the cached per-rule evaluations are reused; only rules whose forms/verdict
                                       changed, and new roots, are evaluated again, ~30 s each)
         absent                     -> pool (anchors + merges + decided forms) -> rivals by verdict -> select 30 -> bind keys
         writes affix_rules.json, affix_rules_report.md, AffixSelection.pickle (gitignored); lists PENDING decisions
  S9b  python -m util.export_affix_dictionary   plover_stenalgo_affix_dictionary.json, affix_abbreviations.tsv

hand-run: python -m util.review_affix_rules      proposes each pending item, y/n/s/q, writes affix_decisions.json after every answer
          (never deletes the pickle); growth is asked BEFORE fusion (a fusion is judged with its parts' decided growth; a fused merge
          inherits its parts' growth on their own spellings); it reselects by itself after each pass (cached, about a minute) and
          continues with what is newly pending, until nothing is pending, you quit, or a pass saved nothing.
```

Cache convention (the same as `Dictionary.pickle` and `elicitation_answers.json`): the ~2.5-minute selection reruns only when its
pickle is missing (`rm AffixSelection.pickle` to force it, after ANY lexicon or layout change: the cached evaluations are of the old
input; a fingerprint mismatch of the two lexicons and `starboard3h.json` only WARNS, it never reruns by itself); `affix_decisions.json`
is reused while it exists. Nothing interactive runs inside `python dictionary.py`: an undecided item gets the safe default (a merge
kept apart, an anchor alone), is listed as PENDING, and the run continues.

## Code map

| Module | Role |
|---|---|
| `affix_decisions.json` | THE VERDICTS (committed). Per anchor: `position`, `spellings` (the exact `|`-joined merge set), `phono`, `verdict` (`fused`/`apart` for a merge, `-` for one spelling), `growth` (a list of forms; `[]` = no growth, `null` = undecided), `refused` (proposal labels the user said no to), `note`, `date`, `numbers` at decision time |
| `src/affixdecisions.py` | load/validate/save (atomic) the file, `ScopeForm`, `Decisions.growthForms`/`fusionVerdict` (undecided = apart), input fingerprint |
| `src/affixes.py` | word records, k=1 anchors, spelling-variant merges, the decided growth forms, `simulate` (gain of a keypress binding on carriers; collisions cost marks), `SimContext(partialOverlap=True)` |
| `src/affixrules.py` | rule = anchor + decided forms; exact keypress choice (`chooseRuleKeypress`), scope fallbacks (`resolveFallbacks`), rivals by verdict, budgeted selection (30 rules), key sharing; the prices as constants (exception weight 2, fallback 5, form 100) |
| `src/affixbinding.py` | the legal keypresses, each phoneme's keys, the similarity label |
| `util/build_affix_rules.py` | S9a: selection + binding, per-rule cache, fingerprint, report, pending list |
| `src/affixproposals.py` | proposals with help/hurt numbers (fusion, growth) for the review |
| `util/review_affix_rules.py` | the interactive review (the only affix command that asks questions) |
| `src/affixabbrev.py`, `util/export_affix_dictionary.py` | S9b: per word the best allowed short outline, collision-free against the stable theory |

Tests: `src/test/affixdecisions_test.py`, `affixes_test.py`, `affixrules_test.py`, `build_affix_rules_test.py`, `affixproposals_test.py`,
`review_affix_rules_test.py`, `affixabbrev_test.py`, `affixbinding_test.py`. The generic growth lattice and the legacy family pipeline
were deleted (2026-10-01): no growth without a verdict.

## How a rule is built

1. **Anchor**: a k=1 candidate (position, spelling, phonology), for example suffix `ment` /m@/ with its carriers
   (the words ending in it). Spellings with the same sound can be **fused** into one anchor
   (`am|an|ant|em|en|...` /@/) that shares one key; the merge is keyed by its exact spelling set.
2. **Growth form**: the anchor fused with the NEIGHBOUR syllable (before a suffix, after a prefix) on the same
   stroke, k=2 (`·[C*[ai]]tion`: `-ation`, `-ition` on one stroke). The engine always keeps at least one stem syllable.
3. **Scope**: the condition that selects the growth form's carriers: a pattern on the neighbour's SOUND (X-SAMPA), the
   anchor's spelling, a few literals, or the neighbour's spelling (`-ment`'s `C{1,2}[eui]+`). Stored in `affix_decisions.json`.
4. **Fallback**: a carrier a form names but that gains nothing under the rule's keys (collision, no legal chord)
   keeps the anchor alone. It is counted and priced 5 per word, so a scope that falls back often loses.
5. **Keypress**: `chooseRuleKeypress` tests every legal keypress on the pooled carriers (fallbacks resolved per
   key) and keeps the best score; a rule must keep its exception rate under `MAX_EXCEPTION_RATE`. The per-key
   sweep (`sweepKey`, over a fork pool: `--workers N`) is a lean re-implementation of `simulate` for one rule group
   (`simulateRuleBase`/`simulateRuleDelta` in `src/affixes.py`); it MUST mirror `simulate`, which the differential
   test `src/test/affixrules_sweep_test.py` and the winner's `simulate` cross-check enforce (identical results).
6. **Selection**: lazy greedy over the roots, each word credited once at its best rule, 30 rules; two rules may share
   a keypress when a joint simulation loses little.

Score of a rule = benefit (strokes saved x frequency) - 2 x exception frequency - 5 x (slot exclusions + fallbacks) - 100 x (forms - 1).
A rule merges into the neighbouring stroke unless ALL its keys are already in it (the decided mode).

## Decisions: the user confirms, the algorithm proposes

Growth and fusion are never accepted by a numeric rule. `python -m util.review_affix_rules` shows each proposal with
`helps N words freq F | hurts N fb freq F, N exc | net ±N | similar rule: ...` and asks `accept? [y/n/s/q]`:

- **fusion** of a merged anchor: the merged rule (the decided parts' growth kept on their own spellings, the added spellings
  anchor-only) against the decided parts alone, each on its own best keypress; flags "added spelling already in rule X" and
  "two decided rules on one key";
- **growth**: candidate forms from a grammar on the neighbour's sound (onset {exact, C, C{1,2}, C*, [mn]} x nucleus {exact, vowel
  class, oral vowel, any}), per anchor spelling, scored at the rule's keys; the best first, then an accepted form's best
  extension (at most 4 alternatives), then sibling spellings of an accepted form (`dez` -> `dez|der|dé`); exact neighbour
  spellings only when they beat the best sound candidate; flag "pattern already used by rule X". Refused labels are not asked again.

Judgement examples (2026-10-01): `cé`+`m@` kept at +7 (other rules already grow on `m@`); `ssion`+`pRe` refused at +247 (few words,
resembles no rule). The 30 existing rules were migrated one-to-one from the old tables (`SCOPES`, `APPROVED_FUSIONS`, refused
fusions); ten of the 30 are merges that were never judged as fusions and are recorded as `fused` ("grandfathered").

A merged anchor with no entry, or one whose spelling set changed after a lexicon change, is undecided: it behaves as "apart" and is
reported PENDING next to the closest decided entry; a changed set is never applied automatically. The report also lists decided
merges that are no longer in the pool.

## The optional abbreviation dictionary (usable output)

The theory is complete and stable without the affix rules, so the abbreviations are an OPTIONAL layer added after it
(user decision, 2026-10-01): nothing in S1-S8 changes if they are ignored, and the long outlines stay as the fallback for a
learner who does not remember the rules.

```bash
python -m util.build_affix_rules            # S9a: affix_rules.json, affix_rules_report.md (also run by `python dictionary.py`)
python -m util.export_affix_dictionary      # S9b: also the last step of `python dictionary.py`
# needs: the stable theory (as util.export_plover_dictionary), the committed affix_rules.json
# outputs: plover_stenalgo_affix_dictionary.json (short outline -> word), affix_abbreviations.tsv (long, short, saved, rule, k, freq, route)
```

- `affix_rules.json` (repo root, committed; a plain list of the 30 rules: rank, position, anchor spelling and phonology, keys) is
  written by S9a. The exporter warns when the selection cache was made from other lexicons/layout, and skips with a warning a rule
  whose anchor is no longer in the pool.
- `src/affixabbrev.py` builds the pool from the stable theory's records, takes each rule's carriers and forms, and computes the short
  outline with the rule's keys. Per word and route: one abbreviation, the one saving the most strokes (growth form, then
  anchor alone; a tie goes to the better-ranked rule). A route is one of the word's outlines in the stable theory (route 0 is the
  primary one; the others carry the other conjugation or homograph marks and trailing feature strokes), and the abbreviation keeps
  that route's marks and strokes after the shortened base. When several spellings or routes want one outline, the most frequent
  spelling keeps it, whatever its route (a tie goes to the primary route; `route` column of the TSV). The affix keypress cannot swallow a mark: the marks are keys
  10 and 15, never among the 22 phoneme keys a rule's keypress is made of.
- An abbreviation exists only if its outline equals no outline of the stable theory (all words, all readings) and no more frequent
  spelling's abbreviation. It keeps the word's own star/hash and feature marks, and never adds a mark, so it cannot disturb the theory.
  The exporter also fails if one collides with `plover_stenalgo_dictionary.json`.
- Result on the current lexicon (2026-10-02, after the growth-before-fusion review and the route marks): 79,715 abbreviations (72,121
  primary-route ones, 7,594 for other routes) for 80,473 carrier words; 176 carriers have no allowed form and 1,815 lost a shared
  outline to a more frequent spelling; strokes saved x frequency = 142,244.
  The selection includes the anchor-alone rules `a`, `co+col+com+con+cor` and `ma` in place of `par`, `ger`, `cher`; nothing is pending.
  The main dictionary is unchanged. Use it in Plover as a second dictionary of higher priority; remove it and nothing else changes.
- Key search (`scratch/keysearch_misses.py`, `scratch/wider_shortlist.py`, 2026-10-01): `chooseRuleKeypress` shortlists on the 2,000
  most frequent carriers; with 5 finalists it missed the best key of 3 of the 15 rules that exceed the sample (`a|ah|ha|hâ|â` +3%,
  `am|an|...` +2%, `de|des|dé|déh` +7%; the best keys ranked 25th, 40th and 6th on the sample). `MAX_ALTERNATIVES` is now 30 (part of
  the cache fingerprint); the finalists cost a few seconds per rule. Not proven exhaustive.

Timings (2026-10-01): full S9a selection 1,214-1,345 s (30 exact rule evaluations, ~40 s each); reselection after one changed verdict
36-43 s (1 rule re-evaluated, 29 from the cache, result identical to the full run); unchanged decisions, pickle present: under 1 s;
S9b 16 s. Two full runs under different `PYTHONHASHSEED` give byte-identical `affix_rules.json` and report.

## Pitfalls

- The engine keeps one stem syllable, so a word made of the anchor plus one syllable cannot fuse (`enfant`).
- Scope matching reads the CARRIER's syllables (`rec.orthoSylls`, `phonoSylls`); a word whose syllable counts differ
  between spelling and strokes is skipped.
- Decisions are keyed by (position, spellings, phono) exactly as the pool's anchor prints; a typo is a pending item, not a silent
  change.
- The per-rule cache is valid only for a byte-identical pool: the signature of a rule includes its carrier set, so a lexicon change that
  moves one carrier re-evaluates that rule; evaluations are not rechecked against the layout (rm the pickle after a layout change).
- Scratch scripts of the 2026-09 analysis that import `util.affix_scan` or `src.affixscopes` (both deleted; kept as
  `scratch/affix_scan_legacy.py` and `scratch/affixscopes_legacy.py`) no longer run: they are history. Pool pickles and
  `scratch/*-before/` snapshots are untracked (over 5 MB); never run `git clean -x`.
