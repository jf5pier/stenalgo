# RESULTS 2026-10-04 — suffix-word list, unigram evidence, slot-budget sweep (abbreviations branch)

Reference for later optimizations (for example a max-1-key overlap study, `EXPR_MAX_SHARED_KEYS`; see
`NOTES_2026-10-03-attach-overlap-and-plover-decoder.md` section 4). Continues
`RESUME_2026-10-03-que-briefs-overlap.md`. Nothing here is committed or pushed.

## 1. What changed this session

- `SUFFIX_WORDS` (`src/expressionrules.py`): a SUFFIX attach run may only consist of post-verbal negation adverbs
  (`pas plus jamais rien guère point personne aucunement nullement`) or the auxiliary adverbs
  (`déjà bien trop encore toujours souvent mal`). The auxiliary adverbs are suffix-only (excluded from PREFIX runs).
  Reason: n-gram edges say nothing about suffix quality (`il faut que`: `que` always has a host after it, a suffix
  `que` never fires in running text). Sources: `docs/PRIOR_ART.md`, "French grammar sources".
- `attachCandidates(..., unigramFreq=)`: a one-unit suffix word takes its evidence from its unigram count
  (`scratch/top_ngrams/1gram_top300.tsv`, same orgtre window as the pool), because host + adverb mass is spread over
  hundreds of hosts and no bigram reaches the pool slices. Measured effect at budget 15: none (see 3).
- `EXPR_RULE_BUDGET` 15 -> 20 (user decision 2026-10-04, from the sweep below).
- Tests: 812 pass (`TestSuffixWords`, 4 tests; `test_position_edges` rewritten).

## 2. Slot-budget sweep (pool longform strokes 1.430e10; all with the suffix list and unigram evidence)

| Slot budget | Attaches alone | Exceptions | Shadows | Collisions | With 40 forced briefs | Shadows with briefs |
|---|---|---|---|---|---|---|
| 15 | 22.8% (3.267e9) | 148 | 0 | 1 | 3.862e9 | 0 |
| **20 (adopted)** | **25.6% (3.659e9)** | **160** | **0** | **1** | **4.275e9** | **0** |
| 25 | 26.2% (3.750e9) | 202 | 0 | 1 | 4.325e9 | 1 (`un petit`) |
| 30 | 27.2% (3.895e9) | 198 | 0 | 1 | 4.463e9 | 1 (`un petit`) |

Reference before the suffix list (budget 15): 23.3% (3.328e9), 123 exceptions, 0 shadows, 0 collisions, with briefs
4.088e9 (`scratch/md5_expr_deterministic.txt`).

- The one collision at every budget is `ce que` ~ `que ce` (selector swallowing: the `que` prefix carries `*`).
- "With briefs" adds the same 40 forced briefs (`FORCED_BRIEF_BUDGET`; the 40 most frequent Tao-list expressions
  no attach covers) in every run. Briefs the selection itself picked count in the slot budget and in the attaches-alone
  column: 1 at budget 20 (`j' ai`), 2 at 25, 5 at 30 (`j' ai`, `j' avais`, `a été`, `nous avons`, `j' étais`).
- Rules added from 15 to 20: `avec`, `sur`, `par`, `le`, `s'`, `qui` (prefix) plus the `j' ai` brief. Suffix rule kept: `pas` only.
- None of the adverbs (`bien`, `encore`, `toujours`, `déjà`, `trop`, `souvent`, `mal`) wins a slot at 15, 20, 25 or 30:
  each saves one stroke per occurrence with counts of 1e7-6e7, below `en`, `les`, `y`.

## 2b. Selector order, order ban, 3+-grams as briefs (same day, budget 20; `scratch/que_run_orderban.log`)

- Variant order = `freq + stackMass` (a stacking variant takes the bare slot) and, for gendered families, m/s, f/s,
  m_or_f/s, m/p, f/p, m_or_f/p (`GENDER_NUMBER`, keyed by the variant's last unit). Alone: no change (the que family already
  ranked `qu'` first; no default family is gendered, `le la l' les` only merge with the opt-in `FAMILY_MERGE=1`).
- `orderBan` (`src/expressionrules.py`, `Rules.orderBan`, `planStream`): two attach keypresses unite commutatively, so
  when the pool holds both orders of an adjacent pair the less frequent order is banned and its second particle stays a content
  word. Bans found: `que + ce`, `s' + il`. This removes the `ce que` ~ `que ce` collision.
- `MAX_ATTACH_UNITS = 2`: 3+-unit runs (`ce qu' il`) are no longer attach candidates; they compete as briefs.
- Result: attaches alone 25.7% (3.672e9), 155 exceptions, 0 shadows, 0 collisions; with the 40 forced briefs 4.288e9 (budget 20
  before: 25.6%, 160, 0, 1, 4.275e9). 24 selected rules in 20 slots.
- Stage C is still needed: round 0 still found 2 collisions and the loop dropped 3 variants (`je me`, `il n'`, `il y` prefix) to
  reach 0 by round 2. Those collisions are host-level (`il a` ~ `il n' a` ~ `il y a`), not the commutative pair kind.

## 2c. Marginal value of the collapsed variants (`scratch/que_run_attribution.log`; `ATTRIBUTE="je me,il n',il y" KEEP_COLLAPSED=1`)

Pool saving with the rule minus without it, everything else as selected (the two collisions still present; nothing dropped):

| Rule | Fires in (pool expressions) | Marginal | Verdict |
|---|---|---|---|
| `je me` | 3 | -1.07e7 strokes | net negative |
| `il n'` | 25 | -9.6e6 | net negative |
| `il y` | 13 | +3.4e6 (exception mass +1.7e7) | marginal, 0.09% of total |
| `je` (reference) | 33 | +9.0e7 | |
| `il` (reference) | 45 | +1.19e8 | |

Other tried variants of Stage C: `SELECTOR_RETRY=1` (selector override before dropping; rescues `je me` and `il n'`, still drops `il y`,
25.5%, 156 exceptions) and `KEEP_COLLAPSED=1` (25.6%, 2 collisions): both lower than the collapse (25.7%). Option A (CP-SAT choosing
the selector permutation) is therefore not justified by savings; only by "no variant dropped by construction".

## 3. Files

- Budget-20 outputs: the tracked `scratch/expr-{rules,rules-proxy,rules-final,briefs,savings,composability}` (md5s below).
  Logs: `scratch/que_run_suffixlist.log` (15), `scratch/que_run_suffix_unigram.log` (15 with unigram evidence),
  `scratch/que_run_budget{20,25,30}.log`. The 25/30 outputs were not kept (rerun with `python scratch/select_expression_rules.py N`).
- Reproduce: `PYTHONPATH=. env/bin/python scratch/select_expression_rules.py 20` (about 5 min; deterministic).

md5 of the budget-20 outputs:

```
d07c2be18749b92ae1e9351c0642813c  scratch/expr-briefs.tsv
64c25741c941f1765868986b5e374272  scratch/expr-composability.tsv
135ac3dc35bdc783efb73a67735a8be9  scratch/expr-rules-final.json
c8fa4461424d690ec52cc4fb7403a71f  scratch/expr-rules-proxy.tsv
282cf21b9408378d274e08ddd0daf77c  scratch/expr-rules.tsv
f5f3850db4f7d63ef5b2fdc4e493846d  scratch/expr-savings.tsv
```

## 4. Open

- The `*`/`#` selector order (variants take the selectors by their own frequency) is not tested for composability; a
  stacking variant should take the bare slot (option B in the session: rank by own frequency + co-occurrence, or let
  Stage C's CP-SAT choose the permutation with a nogood loop for 3-way stacks). The `que` prefix carrying `*` causes
  the remaining collision.
- A host + adverb pool, or one shared `adverb` family, would be needed for the adverbs to be tested at all.
- The 25/30 "with briefs" shadow `un petit` (4, 6, 7, 11, 12, 13) must be fixed before using a larger budget.
- Max-1-key overlap study (`EXPR_MAX_SHARED_KEYS`), Phase 4 wiring and docs, as in the previous resume.
