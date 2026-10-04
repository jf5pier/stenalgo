# NOTES 2026-10-03 — attach key overlap, the Plover decoder, and the qu'il finding

Discussion record for later study (abbreviations branch). Nothing here is implemented except where
stated; the proposal in section 4 is a candidate optimisation, tracked in `TODO.md`
("Branch TODO — max-1-key overlap").

## 1. How an attach merges (the current algebra)

An attach rule is a keypress (a set of keys) merged into the FIRST stroke of the host that follows
(prefix) or the LAST stroke of the host that precedes (suffix). Example, `qu' il est`: longform
3 strokes `k-` / `il` / `est`; composed, one stroke `tiejkdtR` (qu' merged, il merged, est kept).

`composeOutlineTraced` (src/expressions.py) merges a rule into its neighbour stroke only if:
1. a neighbour exists (else `noNeighbour`),
2. `ruleKeysOverlap(_syllabic(neighbour), _syllabic(keypress))` is false, and
3. the union chord is legal (`ctx.isLegal`, else `illegalChord`).

Failure ladder: standalone stroke (the keypress alone) if the span has >= 2 strokes and the
standalone stroke is not a live single-stroke outline; otherwise the longform stays (an
"exception", saving 0). The `*`/`#` selector keys (10/15) are transparent to both checks.

## 2. What `keyOverlap` forbids, today

- **This branch**: `ruleKeysOverlap(neighbour, keys)` (src/affixes.py:1488) returns true for ANY shared
  key. `RULE_PARTIAL_OVERLAP` is `False` here and the expression code never sets it.
- **main**: same function with a `partialOverlap: bool = True` parameter; the decided mode refuses the
  merge only when ALL of the rule's keys are already in the neighbour (any 1-key or partial overlap is
  allowed). The affix layer (S9) is an explicit-entry dictionary, so it does not need to decode.
- **MERGE HAZARD, RESOLVED 2026-10-03**: the expression layer no longer imports `ruleKeysOverlap`.
  `src/expressions.py` has its own `attachKeysOverlap(neighbour, keys, maxShared=None)` ("refuse when
  more than `maxShared` syllabic keys are shared") driven by the module constant `EXPR_MAX_SHARED_KEYS = 0`
  (strict, the decoder contract; behaviour-neutral against the previous strict default). Merging main
  can no longer flip the expression layer into main's partial-overlap default. The overlap study (section 4)
  only has to change that constant (or pass `maxShared`). `affixes.py`/`affixrules.py` are untouched.
- Overlap as a limit unifies the modes: refuse iff `|shared| > limit`; limit 0 = strict, 1 = the proposal,
  `len(keys) - 1` = main's partial mode. Generalising main's three sites (`_newBase`, `mergeUnions`,
  `affixrules._exceptionRateFloor`) to this form is possible later but would touch the byte-identical
  affix rebuild.

## 3. Plover: what exists, what needs a plugin

- Stock Plover dictionaries are exact lookups from a stroke sequence to a translation. There is no
  mechanism to treat a stroke as "host word + extra keys". `{^}` / `{prefix^}` / `{^suffix}` meta
  commands and orthography rules glue TEXT, not strokes: `qu'` + `il` would still be two strokes.
- Explicit entries: one entry per (attach combination x host). Fine for the affix layer
  (72,204 abbreviations for 80,473 carriers). For expression attaches it multiplies: every verb after
  `qu' il`, every stacking combination. Very large.
- Dictionary plugin (`plover.dictionary` entry point; the repo already ships a `plover.system`
  plugin, `plover_stenalgo`): the lookup receives the stroke tuple, so it can decode — try each attach
  rule whose keys are a subset of the stroke, subtract them, look the remainder up as a normal word,
  recurse for stacked attaches. The attach table is ~30 rules + variants, so the dictionary stays
  small. Caveats: the plugin must reproduce the algebra exactly (adjacency, legality, ladder,
  prefix = first stroke / suffix = last stroke), answer fast on misses (Plover asks about stroke
  prefixes through its longest-match translator), and needs installing. The Plover API details
  (lookup signature, `longest_key` handling) are from memory: verify against a real install first.
- The existing TODO item "Plover conjugation-engine plugin" uses the same mechanism and could share it.

## 4. The proposal: allow up to 1 shared key (max-1-key overlap) — NOT implemented

### Why zero overlap is the current requirement (decoder side)
A stroke is a key SET and a merge is a union. If attach keys K and host H share a key, the union
shows it once; subtracting K removes it from the host too, so the decoder sees H minus the shared key.
Zero overlap makes every merge exactly invertible: `H = S \ K`.

### The idea
Allow |K ∩ H| <= 1. Then H is one of `S \ K` or `(S \ K) + k` for a single k in K — at most |K|+1
candidate lookups (|K| is 3-5 keys here, so 4-6 lookups per attach). The decoder tests each candidate
against the theory. Stacked attaches multiply the candidate count ((|K1|+1)(|K2|+1)...), still small.

### Why it could be worth it
- Fewer exceptions: today ANY host containing any attach key refuses the merge (305 exception
  segments at budget 15; 1-stroke particles turn every refusal into an exception, and exception rates
  drive base choice — see the resume's pitfalls). Allowing one shared key converts the host-with-one-
  shared-key class into merges.
- A bigger pool of eligible keypresses: Stage B/C pick bases whose keys avoid the hosts' keys. Keys
  that are common in hosts (central vowels, frequent consonants) become viable, and the disjointness
  constraint between co-occurring families (Q3 option C, currently syllabic-key-disjoint) could relax
  to "overlap <= 1 per pair", easing the crowding that made the budget-sweep peak at 15 rules.
- No cost for the writer: the writer presses the same union chord whether or not a key is shared.
  Only the information in the chord shrinks.

### The risks that make it a study, not a switch
1. **Ambiguity is per (rule, host) pair, not per rule.** If both H and H+{k} are theory words, both
   decode candidates hit and A+H collides with A+(H+k) (same union S). Each such pair must be forbidden
   (that merge becomes an exception), so the exception count falls less than the raw overlap count
   suggests. The decoder also needs a deterministic tie-break only if collisions are tolerated; the
   cleaner contract is "no collision allowed", checked at build time.
2. **Shadowing widens**: a union S may now equal a live outline for more (rule, host) pairs, since
   hosts missing one key can reach the same chord. The Q7 shadow check and the injectivity audit must
   run over the WHOLE theory (all ~190k outlines as hosts), not only the n-gram pool. The current
   audit result (0 shadows, 0 collisions) covers the pool only.
3. **Stacking**: two attaches on one stroke each add a candidate factor, and an overlap between the
   attaches themselves (not just with the host) adds decodings. Probably keep attach-attach
   syllabic keys disjoint (Q3 option C) and relax only attach-host.
4. **Reserved keys**: `*`/`#` are transparent to the overlap check but are NOT free — selector collapse
   (a host's own mark swallowing a variant's selector) already causes dropped variants. Selectors must
   keep zero tolerance.
5. **Mnemonic noise**: a writer cannot tell from the chord whether the attach "was absorbed"; fine for
   writing, but it hides which of two readings is intended when both are words (see 1).
6. **Explicit-entry route does not need this**: if a family is exported as explicit entries, main's
   "refuse only on full overlap" mode already applies and no decoding is required. The study matters
   for the plugin route.

### Experiments to run (in order)
1. Measure, for the current 15 families and for every legal base keypress: the number and the mass of
   hosts with overlap 0, 1, 2+ (over the theory, not only the pool).
2. For overlap-1 merges, count (rule, host) pairs whose union also equals another host's union or a
   live outline (ambiguity rate); the usable gain is overlap-1 mass minus ambiguous mass.
3. Re-run Stage B/C with max-1 overlap (a parameter, default 0) and compare: total saving, exceptions,
   chosen bases, how many bases become eligible, whether the budget-sweep peak moves beyond 15.
4. Try the same with max-2 to see where ambiguity overtakes the gain.
5. Prototype the decoder offline (stroke -> (attaches, host)) and run it round-trip over all composed
   outlines in the audit: it must recover every (rule, host) exactly, with zero ambiguity.

## 5. Related finding: the pool's bare 2-grams distort adjacent attaches (qu'il, que je)

- `qu' il` composes to `k-/il`, saving 0, and `que je` to `k@a/vt@a`, saving 0. Cause: `qu'` and `il`
  are BOTH attach rules, so the stream is [attach qu'][attach il] with no content segment: `qu'` looks for
  the next residual content token, finds none (il is consumed by its own attach), and both fail with
  `noNeighbour`. The union `qu' + il` would be legal and non-overlapping (13,18,20,21,23); the algebra
  never tries it because `il` is claimed by its own rule.
- In running text there is almost always a host: `qu' il est` -> `tiejkdtR` (saving 2 of 3),
  `qu' il a` -> `t*ajkdtR`, `que je suis` -> `sp*@aijkdtR/-k` (saving 2 of 4). Adding the briefs
  `p-` / `kvt@a` changes nothing in these.
- Consequence: the 8 que+pronoun briefs (QUE_BRIEF_BUDGET=12 in the driver) are all "eaten" by the
  attach and add no saving; the 94M-stroke gain I first quoted was a pool artifact (bare n-gram, no
  host). The pool should test pronoun/particle n-grams WITH a trailing host token.
- RESOLVED 2026-10-03 (later session): adjacent HOSTLESS attaches now compose with each other. In
  `composeOutlineTraced`, a run of consecutive `noNeighbour` attaches is grouped greedily; a group of two or
  more becomes ONE stroke (the union of the keypresses) when no syllabic key is shared (`attachKeysOverlap`), the
  union chord is legal, and it is not an existing single-stroke outline. Trace: the first member is
  `STANDALONE` with reason `attachCluster`, the others `MERGED`. Attaches with a host still stack on it as before.
  Driver effect (same seed): attaches alone 14.4% -> 21.7% of the pool's longform strokes, exceptions 305 -> 206.
  A dedicated `qu'il` attach rule was NOT built: the cluster merge covers it without a rule of its own.
- que briefs, user decision 2026-10-03: option 1, NO que briefs. Measured: keeping a que+pron brief only
  where the attaches save less than the brief would leaves one (`qu' ils`), and it saves nothing extra
  (identical totals with budget 0). `QUE_BRIEF_BUDGET` and the driver's que-brief stage were removed. The `queFamilyOf` family cut stays.
- Option 2 (a brief wins when its attach fails; a retry in `composeOutlineTraced` skipping the failed attaches,
  kept only when it strictly improves) was built and measured: +1.12e8 strokes (+2.9% of the total with briefs,
  3.920e9 -> 4.032e9, 0 shadows, 0 collisions). It was REJECTED and removed: whether a brief fires then depends on
  whether the attach would have merged, which a decoding Plover plugin cannot see from the stroke alone. Revisit
  only if the decoder question is settled differently (the retry was ~25 lines: a `skip` set of attach start
  indices in `planStream` and a second `_composeOnce`).
- FINDING, the driver is hash-seed dependent: Stage C breaks equal-score base ties by set/dict iteration order.
  With `PYTHONHASHSEED=1` the run gives 21.7% / 206 exceptions / 3.838e9 with briefs (`ne` base (8,17,25), `ce` (16,19,23));
  with seed 2: 22.3% / 175 / 3.920e9 (`ne` (8,17,23), `ce` (16,19,25)). Unseeded runs varied. FIXED: `repairKeypresses` (Stage C CP-SAT) now runs with `num_workers = 1` and
  `random_seed = 0`; seeds 1 and 2 give identical `scratch/expr-*` outputs (21.7%, 206 exceptions, 3.838e9 with briefs);
  baseline md5s in `scratch/md5_expr_deterministic.txt` (`md5sum -c` from the worktree root).
  The earlier 22.3% outcome was a lucky tie-break, not a better design.

- RESOLVED 2026-10-03 (suffix `le` / `les` saved 0): when a prefix and a suffix rule share an expression (le, les, ...),
  `planStream` step 1 always matched the prefix twin ("prefix" sorts before "suffix"), so the suffix rule was dead code: `voir le`
  matched prefix `le`, found no host after it and failed `noNeighbour`. Now a prefix rule matching at the very END of the stream
  (nothing after it) with a token before it yields to its suffix twin. Diagnostic: `scratch/why_suffix_le.py`. Effect (deterministic
  driver): attaches alone 21.7% -> 23.3% (3.328e9), exceptions 206 -> 123, with briefs 3.838e9 -> 4.088e9, 0 shadows, 0 collisions.
  Stage C's feedback loop needed 4 rounds (round 3 reached 0 collisions; it ended at 2 collisions, `n' a` vs `n' y a`, with the old
  limit of 3), so the driver's limit is now 6 rounds. Position choice depends only on the stream edge, which a decoder knows.

## 6. State (end of the 2026-10-03 later session)

- Committed on `abbreviations`: overlap policy, cluster merge, no que briefs, deterministic Stage C, suffix-twin fix (see git log).
- Baseline outputs: `scratch/md5_expr_deterministic.txt` (`md5sum -c` from the worktree root; same under PYTHONHASHSEED 1 and 2).
- 808 tests pass.

## 7. Family-merge experiment (late 2026-10-03)

Merging `un`/`une` (both positions) and `le`/`la`/`l'`/`les` (prefix only) into families lowered the result (21.8% vs 23.3%, 1 shadow). A family
of up to 4 variants separates its members by the `*`/`#` selectors, and a selector is lost whenever another rule or the host already carries that
mark (`que` prefix has `*`; the host `a` of `il y a un/une` carries marks). Stage C then drops the weaker variant. For the decoder this is the same
fact as section 4: a selector is only decodable when the host stroke cannot already hold it. Details, traces and the open decision:
`RESUME_2026-10-03-que-briefs-overlap.md` section 0b.
