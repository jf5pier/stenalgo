# RESULTS 2026-10-04 — expression decoder, steps 1-3 (plan: PLAN_2026-10-04-expression-decoder.md)

Code: `src/expressiondecoder.py` (`ExpressionDecoder.decode(strokes) -> list[Decoding]`, every reading), tests
`src/test/expressiondecoder_test.py` (7; whole suite 825 pass, mypy clean for the new file). Scripts (scratch, untracked logs):
`scratch/decode_roundtrip.py` (step 2), `scratch/theory_injectivity.py` (step 3). `src/expressions.py` untouched.

## Step 2 — round trip over the 1,151 pool expressions (committed rules, 24 attaches + 40 forced briefs)

| class | outlines | mass |
|---|---|---|
| composed reading found, only reading | 410 | 59.2% |
| composed reading found, plus rivals | 741 | 40.8% |
| composed reading NOT among the readings (mismatch) | 0 | 0 |
| no reading | 0 | 0 |

The decoder inverts the composer exactly (0 none, 0 mismatch; comparison is spelling-insensitive: the pool unit `j'`/`œil` is the
theory word `j`/`oeil`). Ambiguity is not zero: 741 outlines have at least one rival reading (1,398+536+331+31 rival readings):
335 of those outlines (1.14e9) are plain longform where the stock theory itself segments two ways (`j' avais` = `j` + `avais`
or `ja` + `vais`), 406 (1.92e9) use the layer. Typical layered rivals: `dans` (4,5,11) = `ce`+`pan`; `à la` = cluster `à`+`la` or the
brief `depuis` + `la` + `pas`; `d' un` = `un`/`uns` with `d'`/`de`. The only outline shared by two POOL expressions is `peut être` (a
duplicate pool row, same text). So the driver audit's "0 collisions" is true over the pool and says nothing about rivals that are
not in the pool.

## Step 3 — whole-theory injectivity (171,608 words + 40 briefs as hosts; 23 distinct rules, 174 syllabic-disjoint pairs)

Scope: single rules on first/last stroke, same-side pairs on multi-stroke hosts, any pair on one-stroke hosts. Cross-side
collisions between multi-stroke hosts are not searched. Host frequency = word `frequency`; mass is a share of the theory's
total frequency, counted per merge (so shares of different rules overlap and do not add).

- Single rules: 3.06e6 mergeable (rule, host) pairs, 877k refused by key overlap (these become exceptions or standalones), 10k by an
  illegal union. **4,467 shadows** (merged outline == a live outline of another word or a brief) and **105,023 collisions**
  (two different (stack, host) readings give one outline). Every rule has collisions (4.8% to 53.6% of theory mass per rule),
  so one reading per stroke tuple is NOT legal over the whole theory.
- Cause of the collisions: strict zero overlap makes a merge invertible for a GIVEN keypress, not unique across rules.
  Nested chords collide (`la` 16,19 inside `et` 8,16,19: `la`+host-with-8 == `et`+host-without-8; `ce` 5, `à` 9,17 ...), and the
  selector variants of one family swallow into hosts that carry `*`/`#` (the pairs `de`+`ne` == `d'`+`n'` == `d'`+`ne`...).
  Pairs: 16.4e6 mergeable, 1.47e6 colliding (dominated by selector-variant pairs and nested chords), 121 shadows.
- Heaviest shadows (frequent hosts): `ce` 1,689 hosts (21.3% of mass; `est` + `ce` = `vais`, `ouais` + `ce` = `vouait`),
  `pas` 1,377 (17.5%; `est` + `pas` = `ouais`), `dans` 844 (11.7%), `avec` 139, `par` 190, `s'` 157, `à` 44. The other rules shadow
  almost nothing (0-6 hosts). Brief shadows: `hué` + `l'` = `beaucoup`, `on` + `c'` = `façon`.
- Attach chords against live single-stroke outlines and brief chords (re-checked on the whole theory): no clash.

## Reading

1. A decoder that inverts the composer exactly is in hand (steps 1-2).
2. It cannot return one reading per stroke tuple: it must rank, or the build must forbid at composition time (step 4, decision 4).
   Forbidding means a refusal test `merged outline in live outlines` (composer has none today; 4,467 single-rule shadows would
   become exceptions) and a pairwise-nesting/selector audit over the theory, not over the pool.
3. Ranking is plausible: the real expression is the attested one; rivals such as `ce pan` for `dans` have no corpus support.
   The cost is a corpus-ranked tie-break inside Plover.

## Step 4 follow-ups (same day)

### Ranking measurement (`scratch/rank_loss.py`)
Precedence: plain live word > pure brief > attested pool reading (by frequency) > other merged readings (rule mass).
Full order: 0 of 611 layered pool expressions lose (the pool audit is collision- and shadow-free, so nothing outranks an attested
reading). Without the attestation class: 281 lose, 1.319e9 strokes (30.7%). So attestation must be exported as data, but it
protects the pool only.

### Shadow frequency (`scratch/shadow_frequency.py`, Google Books top-5000 bigrams)
Before: 17 of 4,464 single-rule shadows are frequent phrases (`ce sont` -> `bon`, `a pas` -> `oie`, `ce soit` -> `bois`...), 2.6e7
occurrences, 0.6% of the layer's saving, 5 rules (`pas`, `ce`, `dans`, `à`, `avec`).

### Stage B theory-wide shadow term (`HostIndex`, `src/expressionrules.py`)
Why it was late: Stage B tested a chord on the 30 top pool carriers and Stage C audited the pool, so hosts outside the pool's n-grams
were never seen. Now each candidate chord also pays the estimated shadowed occurrences over ALL theory hosts and is refused above
`THEORY_SHADOW_MAX_RATE`.

| | previous commit | limit 0.002 (default) | limit 0.01 |
|---|---|---|---|
| attach saving alone | 25.7% | 24.0% (3.429e9) | 24.4% (3.492e9) |
| with the 40 briefs | 4.288e9 | 4.038e9 | 4.095e9 |
| exceptions | 155 | 235 | 219 |
| pool shadows / collisions | 0 / 0 | 0 / 0 | 0 / 0 |
| theory single-rule shadows | 4,467 | 5 | 3 (`la` shadows `les`: 0.98% of word frequency) |
| top-5000 bigrams misread | 17 | 0 | 0 |
| theory single-rule collisions | 105k | 35.5k | 37.3k |
| pool outlines with a rival reading | 40.8% of mass | 21.5% | 22.3% |

Kept 0.002. `ce`, `pas`, `dans`, `à` get new chords (`ce` (7,16,22), `pas` (9,21,25), `dans` (2,16,19), `à` (9,17,23)). The committed
`scratch/expr-*` files are this run (md5 of `expr-rules.tsv`: f98fd383d538...). The remaining collisions are the selector families: a host
that carries `*`/`#` swallows a variant's selector (`que`/`qu'`, `de`/`d'`, `ne`/`n'`, `n' y`, `le`, `qui`: 20-41% of host mass).

### Elision pairs (experiment `ELISION_PAIRS=1`, files in `scratch/expr_elision/`, logs `scratch/que_run_elision*.log`)
User idea: one chord for `que`/`qu'` (and `de`/`d'`, `ne`/`n'`, `ce`/`c'`, `le`/`l'`, `je`/`j'`, `s'`); the decoder picks the form from the word that
follows (vowel sound: elided, consonant: base). Implemented as `src/elision.py`, `AttachRule.elision`, `ExprRule.elision/elisionBase/slot`
(a pair shares a selector slot), the composer refusal (`elision` exception), the decoder filter (a stack is read if some order makes every form agree,
`orderingExists`) and a Stage C audit that does not count hostless pool fragments differing only by a trailing form (`de l'`/`de le`).
First attempt compared the particle with the CONTENT host (`ce n' est` was refused, 97M occurrences); it must compare with the NEXT written word.

| | default (0.002) | `ELISION_PAIRS=1` | `ELISION_PAIRS=1 SELECTOR_RETRY=1` |
|---|---|---|---|
| attach saving alone | 24.0% (4.038e9 with briefs) | 22.4% (3.743e9) | 22.6% (3.776e9) |
| exceptions | 235 | 312 | 286 |
| theory shadows (single rule) | 5 | not run | 27 events, 1 frequent phrase (`de`: 9e5) |
| single-rule collisions of `que`,`qu'`,`de`,`d'`,`ne`,`n'`,`ce`,`c'`,`le`,`l'`,`j'` | 4-41% of host mass | | 0.0-2.0% (`le` 13.4%, `ce` 9.5%) |
| still collide | `n' y`, `il n'`, `je me`: 25-36% | | same (`n' y` 35.7%, `il n'` 31.3%, `je me` 33.1%) |
| decode: no reading | 0 | | 0 |
| decode: composed reading missing | 0 | | 3 (hostless clusters, 1.8e6) |
| pool outlines with a rival | 21.5% | | 25.9% |

Reading: elision pairs remove the elision families' collisions at the source. The pool saving falls 1.4 points, but per-expression comparison
(default vs `ELISION_PAIRS=1 SELECTOR_RETRY=1`, net -2.6e8 strokes) shows where:

| pool expressions | default | elision |
|---|---|---|
| with a host word (real running text) | 2.465e9 | 2.562e9 (+3.9%) |
| hostless fragments (n-gram slices ending in particles: `à l'`, `dans le`, `et les`, `sur la`) | 1.562e9 | 1.203e9 |

So hosted expressions GAIN; the whole loss (-3.6e8) is fragments, which are 39% of the default saving and an artifact of the pool (a sentence always
continues). A fragment saves its stroke through a CLUSTER (two hostless attaches in one stroke, needing a disjoint, legal union chord); the new shared
chords (`l'` = `le`'s, ...) make several of those unions illegal (`à l'` 6.3e7, `dans le` 4.5e7, `sur le`, `et les`, `que les`... fall to `noNeighbour`
exceptions) and `sur` is no longer selected. Real losses inside the hosted group: the `j' ai` brief is displaced by the new `j'` attach (-3.1e7, attach beats
brief), and some `d'`/`l'` merges now fail on `spanOne` (-5e6 each at most). Consequence: compare runs on hosted expressions (or give fragments weight 0);
the headline saving of every run in these files includes the fragment share.

Related regression found at the same time (not elision): the Stage B shadow term moved the chords so that `il` + `n'` no longer stack on one host
(union illegal, `n'` falls to `spanOne`; the run before it stacked, `il n' est` one stroke). Single-stroke particles that fail to merge: 2.9e7 -> 1.0e8
occurrences (about 0.5 point). Cause: the repair only forces key-disjointness for co-occurring families, not a legal union chord.

## Pinky-diagonal key conflicts (`src/keyconflicts.py`, user idea 2026-10-04)

Why `il` (7,16,24) and `n'` (8,20,23) never stack: keys 24 and 23 sit on the right pinky, which owns a square of four keys (22-25) and cannot press a diagonal
pair (23+24, 22+25) or any triple, only a single key, an edge pair or all four. The left pinky (0-3) is the same; every other finger accepts any combination.
Footprint: each pinky key also occupies its diagonal partner; two key sets can share a stroke iff `expand(a)` and `b` are disjoint. Checked by brute force
(`src/test/keyconflicts_test.py`): equal to `SimContext.isLegal` for every pair of legal keypresses of a finger (the all-four press aside). The partner map is derived
from `Starboard._possibleKeypress`. It is now the overlap test of the composer (`attachKeysOverlap(conflicts=)`, reason `keyOverlap` instead of a late `illegalChord`), the
cluster check, the repair's disjoint-pair constraint, `HostIndex` and the decoder (readings the composer cannot produce disappear).

Fragment-free comparison. The pool counts n-gram slices that end on a particle (`à l'`, `dans le`, `et les`); in text a host always follows, so their saving is an
artifact. Run-independent split (fragment = last unit is a prefix particle of ANY run, or first unit a suffix particle; 895 hosted + 255 fragment expressions),
saving in strokes:

| run | hosted | fragments | total |
|---|---|---|---|
| previous commit `e8444c3` (no theory term) | 2.504e9 | 1.782e9 | 4.286e9 |
| shadow term (`f98fd383`) | 2.419e9 (-3.4%) | 1.608e9 | 4.027e9 |
| shadow term + footprint (default now) | 2.454e9 (-2.0%) | 1.685e9 | 4.139e9 |
| `ELISION_PAIRS=1 SELECTOR_RETRY=1`, no footprint | 2.520e9 | 1.245e9 | 3.765e9 |
| `ELISION_PAIRS=1 SELECTOR_RETRY=1` + footprint | 2.552e9 (+1.9%) | 1.443e9 | 3.994e9 |

(An earlier version of this file said hosted expressions gained 3.9% under elision: that split flagged fragments per run and was inconsistent. The table above replaces it.)

Default + footprint: attach saving 24.8% (3.541e9), 201 exceptions, 4.149e9 with briefs, 0 pool shadows and collisions, `il` + `n'` stack again (`il n' est` one
stroke), 9 theory shadow events, 0 top-5000 bigrams misread, 22.3% of pool mass has a rival reading. Elision + footprint + retry: 24.2% (3.457e9), 235 exceptions, 4.005e9 with
briefs, `que/qu'/d'/n'/l'/c'/s'` collisions under 1% (`de` 26%, `j'` 12%, `je` 20% remain, as do `il`, `à`, `n' y`, `il n'`, `je me`), 50 theory shadow events
(`ce` and `c'` 0.5% of host frequency each, onto the forced briefs `dans la` and `déjà`, which the host index does not see), 31.8% of pool mass with a rival (mostly clusters of
hostless fragments, both elision forms), 4 hostless clusters missing from their own readings. The elision run has the best hosted saving; it stays off by default
until the shadow index also sees brief chords and the remaining collision families are decided.

## Brief chords against attach merges; elision pairs become the default

Gap found by the elision run: `ce` + `me` wrote the chord of the forced brief `dans la`, `c'` + `au` that of `déjà`. Briefs get their strokes after Stage B and only the
attach chord itself was reserved. Now (`attachMergeChords`, `scratch/select_expression_rules.py`, after Stage C when the attach keys are final) every one-stroke chord that an
attach, two stacked attaches or two clustered attaches can write over a one-stroke word is treated as taken: selected briefs on one are re-derived (none needed it),
the forced briefs avoid them (144k chords default, 170k with elision).

| | default, no elision (`ELISION_PAIRS=0`) | elision (new default) |
|---|---|---|
| attach saving alone | 24.8% (3.541e9) | 24.2% (3.457e9) |
| with the 40 briefs | 4.158e9 | 4.014e9 |
| hosted saving (895 expr, run-independent split) | 2.462e9 | 2.560e9 (+4.0%; +2.2% over `e8444c3`) |
| fragments saving | 1.685e9 | 1.443e9 |
| exceptions | 201 | 235 |
| theory shadow events (single rule) / share of host frequency | 7 / 0.004% | 46 / 0.230% (was 50 / 1.078%) |
| top-5000 bigrams misread | 0 | 0 |
| theory single-rule collisions | 43.5k | 35.3k |
| hosted pool mass with a rival reading | 27.3% | 24.1% |
| fragment pool mass with a rival reading | 15.2% | 41.2% (32 points: a hostless cluster read with either elision form) |
| composed reading missing from decode / unreadable | 0 / 0 | 4 hostless clusters / 0 |

Where the elision shadows come from: `un` 15 and `le` 12 (rules the elision run selects with the freed slots: 29 attach rules against 23), `c'` 9 (0.14%, `êtes` -> `jet`),
`qu'` 6, `l'` 3, `ne` 1; none is a frequent phrase. The earlier 31.8% against 22.3% rival share was fragments (hostless clusters), not hosted text.

Decision (user, 2026-10-04): elision pairs are the default (`ELISION_PAIRS=0` restores the previous behaviour; `SELECTOR_RETRY` is on with it). Files: `scratch/expr-*` = elision run
(md5 `expr-rules.tsv` 7e5a6c68eb38...), `scratch/expr_noelision/` = the run without it.

## Decode-time ranking built (`src/expressionranking.py`, `scratch/rank_check.py`)

`ReadingRanker` orders the readings of one outline: 0 plain live words (an attested plain reading first, then the more probable), 1 a pure brief, 2 an attested pool
reading (by frequency), 3 anything else by the independence probability (product of the unigram probabilities of every word of the reading, so extra or rarer words lose:
`en je` beats `d'` + `en` + `avec`). `rankedDecode(decoder, ranker, strokes)` is the one-answer entry point for the plugin; the attested table (`attestedTable`, from
`composedReading` over the pool) and the unigram probabilities (`unitProbabilities`, theory word frequencies) are its only data. The composer needs no `loses` check for
attested expressions (the pool audit has no shadow or collision), and an unattested chord just reads as the winner.

Measured on the committed run (elision default):
- Pool: the top-ranked reading equals the composed reading for all 1,151 outlines (0 differ; hostless clusters compared with the elision forms folded). A first version
  that preferred fewer pieces among plain words lost 15 (`et les` read as the word `hélé`, `par la` as `parla`): the stock theory writes both alike, the attestation and the
  probability settle it.
- Open set: 43,599 merges of a single-unit attach into a one-stroke word (every one the composer performs), weighted by rule frequency x host share:

| decodes to | share |
|---|---|
| the merge itself | 86.19% |
| the same words, grouped differently (`de le` read as the cluster `de` + `le`) | 12.21% |
| another merge | 1.58% |
| a plain word | 0.01% |

So 98.4% of the weighted open-set merges read back as the words that were written. The first ranking (rule mass, more particles = more mass) put 22.5% on another merge.
Largest remaining mis-decodes (weights 1e6): `dans` + `et` and `et` + `dans` (read as `avec` + `la`), `à` + `me`, `à` + `mon`, `de` + `ton`, `j'` + `est`: unnatural pairs for the
most part.

## Plover plugin (step 5; `plover_stenalgo/`, `util/export_expression_data.py`, `docs/PIPELINE.md` S8.10)

**Plover API (read from the v5.4.1 source, notes in `scratch/plover_api_notes.md`).** A dictionary plugin is a `StenoDictionary` subclass registered under the `plover.dictionary` entry point, name = file
extension (`stenalgo`). The translator only calls `enabled`, `longest_key` and `get(key)` (exact tuple of RTFCRE strings, `None` = miss), asking for every suffix window of the buffered strokes up to `longest_key`,
also with the empty prefix stroke; misses are not cached by Plover, so the plugin memoizes. First non-`None` dictionary wins, so the plugin sits above the stock dictionary. Glue: `qu'{^}` (text, then attach the
next word); `{^suffix}` would trigger orthography rewriting of the previous word and is not used.

**Design.** The dictionary answers only when the best reading is ONE expression piece (brief, merged attach, standalone keypress, cluster); plain words and multi-piece keys return `None`, so the stock
dictionary and the translator's shorter windows handle them. The attested text of the pool fixes the order of attaches merged into one stroke (lost in a reading). Data: 0.3 MB (rules, attested readings,
5,000 unit probabilities, particle stroke counts, key conflicts, chord legality) plus the stock dictionary as the outline -> words index (sha256 fingerprint refuses a mismatch). The vendored decoder core
(`_core/`) needs only the standard library.

**Does it need the unit probabilities? (`scratch/rank_static_rule.py`, open set of `rank_check.py`.)** Unattested readings compete on 24.0% of the open-set weight; the probability ranker picks the composed merge on
79.9% of that, the static tie-breaks (fewest words/pieces, merges last, most merges first) only 30-42% and would need 579-649 exception chords to match the ranker. Cutting the table to the most frequent words: 200 words
change the winner on 3.83% of the contested mass, 1,000 on 0.97%, 5,000 on 0.17%, 20,000 on 0.01%. Shipped: 5,000 words (0.16 MB), which also loses one pool expression in the real simulation
(`rapport d'impôt`).

**Real Plover check (`scratch/plover_translator_sim.py`, Plover's own `Translator`, [plugin, stock dictionary]).** 1,095 of the 1,151 pool expressions (97.4% of frequency mass) come out as written (91.5% before
the attested texts, order and elision twins). The 56 others: plain-word shadows (`et les`/`hélé`, `et la`/`héla`, `par la`/`parla`, `par les`/`parlé`: the longform of an unabbreviated pair equals a stock
word's outline, the plugin leaves plain readings to the stock dictionary), elision twins sharing one chord (`que l'`/`que le`, `dans l'`, `et d'`), wrong readings of unattested partial chords (`il m'a`,
`rapport d'impôt`) and `d'œil`/`d'oeil`. Load time 2.7-4.5 s (the word index parse is about 2.8 s), memoized lookups afterwards. Live: `de l'` on a Starboard (COM7) in Plover 5.4.1.

**Why `et les` is the longform.** `et`, `les`, `la`, `par` are prefix attaches: in a hostless pair the first has no neighbour (`noNeighbour`) and two attaches cannot union into one stroke when they share keys
(`et` (9,16,19), `les` (2,16,19) share 16 and 19). Not a plugin bug; see `TODO.md`.

**Pitfalls met.** The installed plugin must go under Plover's own plugin folder (`PYTHONUSERBASE=<config>\plugins\win`), not the default user site; plugins load at Plover start only; dictionaries added while the
English system is active report every Stenalgo stroke as invalid steno (the system switch needs Apply).
