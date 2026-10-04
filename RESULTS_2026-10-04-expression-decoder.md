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

Reading: elision pairs remove the elision families' collisions at the source, but the pool saving falls 1.4 points (6.5% with briefs) and the
rival share is higher, so it stays OFF by default. The cause of the lost saving is not isolated (the elision refusals are gone after the next-word fix;
the budget picks `un`, `elle`, `en`, `les` for the two freed slots while `sur` drops). Next, if wanted: re-weigh the freed slots, and decide
`n' y`/`il n'`/`je me` (their `*` selector is swallowed by `a`, `est`... ).
