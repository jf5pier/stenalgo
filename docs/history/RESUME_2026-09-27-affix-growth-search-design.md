> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Resume: affix growth/merge search design (2026-09-27)

> **SUPERSEDED for implementation (2026-09-27): the design was agreed with the user. Implement
> `DESIGN_2026-09-27-affix-rule-selection.md`.** This file remains the problem statement; its
> §5-6 "menu" and "what to do next" are replaced by that design.

**Read this file, then `PLAN_2026-09-26-affix-abbreviations.md`, then
`RESUME_2026-09-26-affix-scan-state.md`.** This file is for one specific unresolved design
question raised at the end of a long session implementing A9 (iterative affix growth). It is a
*design discussion*, not an implementation ticket — the user wants to think through the algorithm
with a stronger model (this file exists so they can `/clear` and switch to Opus) before any more
code changes. Do not start implementing until the design is agreed.

Everything below is measurement/proposal work on a steno theory generator. Nothing here is wired
into production (`dictionary.py`/the real pipeline). `pytest src/test/` (674 tests) and `mypy src/`
must stay clean; use `env/bin/python`, run from the repo root, serialize heavy runs (7 GB RAM).

## 1. What exists today (all implemented and verified this session)

`src/affixes.py` discovers **suffix/prefix candidates**: a candidate is `(position, k, phono,
ortho)` — a k-syllable affix, its phoneme content (`phono`) and spelling (`ortho`), plus the
`carriers` (real words) that have it. Candidates are found two ways:

- **Exhaustive per-word discovery** (original mechanism): every word contributes a candidate for
  every `k` in `1..MAX_AFFIX_SYLL`. Survivors need `MIN_CARRIER_LEMMAS`/`MIN_STEM_ROOTS`/
  `MIN_CANDIDATE_FREQ`, or are one of ~150 hand-picked seeds in `resources/affixSeeds.tsv` that
  bypass thresholds.
- **A7 (`poolTailVariants`)**: pools same-`k` candidates whose tail syllables match and only the
  nearest-to-stem syllable's *onset consonant* differs (same nucleus+coda, called `rest`) —
  e.g. `bilité, cilité, tilité, ...` pool into one `·[b|c|t|...]ilité` candidate. This is how rare
  spelling variants that fail thresholds alone can clear them together. Deliberately narrow: only
  the onset varies, nucleus+coda stays fixed, so every pooled variant is phonetically the same
  shape.
- **A8 (`poolKnownAffixGroups`)**: a tiny hand-curated etymology lookup (`co-/con-/com-/col-/cor-`),
  irrelevant to this discussion.
- **A9 (`growAffixes`/`_growOneLevel`, this session's new work, PLAN §13)**: starting from any kept
  candidate, tries absorbing one more syllable toward the stem (up to `GROWTH_MAX_DEPTH=3`),
  generalizing over whatever is found there. Mechanism: bucket the newly-absorbed syllable by its
  exact phono value (leaves), then **greedily agglomerate** leaves pairwise, always merging
  whichever pair has the lowest resulting *exception share* (carriers that would collide — share a
  stem stroke with a different-lemma carrier — if the syllable is generalized away; those carriers
  simply keep their unabbreviated outline, they don't block the merge), stopping a merge only when
  even the best remaining pair would exceed `GROWTH_MAX_EXCEPTION_SHARE=0.02`. Grown candidates are
  held to `GROWTH_MIN_*` = 7x the ordinary thresholds (tuned empirically this session to keep the
  family count at the pipeline's existing sanity ceiling of 300).

Then **Part B** (`src/affixbinding.py`) turns candidates into keypress bindings:
- `discoverFamilies`/`buildFamily` clusters candidates by `candidateSim` (string+phono similarity,
  with a nested-substring bonus) into **families** — a family later gets ONE keypress (or splits
  into sub-groups only when collisions force it).
- `growthMerges` (added this session): before the general pass, tries merging a grown candidate's
  family with its *exact* parent's family (`Candidate.grownFromKey`, a real traced edge), held to a
  strict `GROWTH_MERGE_KEEP=0.98` gain-retention bar.
- `unifyFamilies`: a **greedy, round-based, nearest-neighbour-by-cosine merge** across ALL families
  of one position — each family finds its top `MERGE_PARTNERS=3` most similar families by
  phoneme-salience cosine, all proposed pairs across the whole family set are sorted by cosine, and
  the globally-best-first pairs are accepted each round (subject to `MERGE_SIM_MIN=0.85`,
  `MERGE_KEEP=0.9`, `MERGE_MAX_MEMBERS=8`). Once a family is consumed into a merge, its original
  identity is gone for all later rounds.

## 2. Two bugs found and fixed this session (context, not the open question)

1. **Runtime**: `_growOneLevel`'s merge loop was recomputing the whole pairwise matrix every
   iteration (O(g^3)); fixed to incremental (O(g^2)).
2. **`growthMerges` accounting bug**: for a TRUE parent/child growth pair, the child's carriers are
   a strict subset of the parent's, so naively summing `ga + gb` as the "separate" baseline
   double-counts the overlap (crediting the same word once at its shallow saving, again at its deep
   saving, though a word can only ever be typed one way). Fixed to a per-carrier max across the two
   options. Verified against `S026` (a grown child of `-té`) and `S064` (grown from `S026`): the
   real retention was 99.9%, not the wrongly-computed 82.5% that caused a bad rejection.

## 3. The open design question (the actual thing to solve)

**Investigated case, with real data**: `-ilité` is a hand-typed seed (along with 7 sibling
variants, `resources/affixSeeds.tsv`), not discovered by growth. The *correct* organic path would
be `-té` (k=1, real candidate, 566 lemmas) -> grow, absorbing "li" -> `-lité` (k=2) -> grow,
absorbing "i" -> `-ilité` (k=3, matches the seed). Checked: **`-lité` (exact `li.te`, k=2) does not
survive as its own candidate anywhere** — `_growOneLevel`'s greedy merge pooled "li" together with
7 *phonetically unrelated* syllables (`bER, fR§, ky, ni, no, sje, ti` — different vowels entirely)
into one wildcard at the very first merge step, because that pairing happened to be cheap (low
exception share). "li" never got a chance to survive alone and be grown further.

**The user's hypothetical, generalizing this into the real design problem:**

> Say `-té` alone isn't interesting (too much conflict / not semantically coherent), but growing it
> once to `-ité` is a real win. Continuing to grow `-ité`, we reach `-lité`. Algorithmically (by
> raw phoneme-salience cosine) `-lité` looks close to the *unrelated* existing family `-liste`, and
> `unifyFamilies`' greedy nearest-neighbour merge would happily fuse them — but if we'd kept
> growing `-lité` *downward* first, we'd have found `-ilité`, then `-bilité`/`-cilité` (i.e. the
> `-Xlité` wildcard, already found this session as `S064`), which are the *real*, semantically
> coherent, larger-and-better additions to the `-ité` family. **How do we reward the eventual
> larger family (more words, more frequency-weighted stroke savings) while still catching and
> using genuine sideways-merge wins (when a `-liste`-style merge really is better), without
> greedily locking in the sideways merge before the deeper vertical growth has had a chance to be
> explored?**

This reframes A9 (growth) and `unifyFamilies`/`growthMerges` (sideways merging) — currently two
separate, sequential, each-locally-greedy phases — as needing to be **one search problem** over a
graph where a "family hypothesis" node has (at least) two kinds of outgoing edges: *grow deeper*
(absorb one more syllable, A9's existing mechanism) and *merge sideways* (unify with a
phonetically-similar but etymologically-unrelated family, `unifyFamilies`' existing mechanism). The
question is what search strategy over that combined graph avoids the premature-commitment failure
above.

## 4. A new fact that changes the cost/benefit calculus: only ~20-30 families ship

**User's key added constraint, stated at the end of this session**: only the top 20-30 families
(by whatever final scoring) will ever actually become theory rules. Everything below that line is
discarded. This means the earlier objection to "just keep way more candidates around and sort it
out later" (Theory A in the prior turn — keep every node of the merge dendrogram, not just the
final cut — rejected for reopening the 800-family explosion problem from earlier this session) may
no longer be the right call: if only the top 20-30 survive to the end regardless, **generating a
much larger number of candidate hypotheses is fine as long as final ranking/selection is cheap and
correct** — the sanity-bound-driven threshold tuning done this session (`GROWTH_MIN_*` = 7x,
`GROWTH_MAX_SLOT_VALUES=8`, etc.) may have been solving the wrong problem, or at least a problem
whose stakes are lower than assumed.

## 5. Four competing theories discussed so far (none implemented, this is a menu, not a decision)

- **Theory A — keep the whole merge dendrogram** (every intermediate cluster, not just the final
  cut, becomes a candidate). Previously rejected for reopening the family-count explosion; **may
  deserve reconsideration** given §4's "only top 20-30 ship" fact — the objection was about
  intermediate blowup, not final output size.
- **Theory B — protect self-sufficient leaves from being swallowed.** Before generalize-merging,
  split leaves into "clears growth thresholds alone" (emit as-is, keep growable) vs. "needs
  pooling to survive" (only these enter the greedy merge). Cheap, low blast-radius, but unverified
  whether "li" alone actually clears even the 7x-raised threshold without any pooling — may need
  pooling with *some* partners, just not the specific ones it grabbed.
- **Theory C — constrain generalization to phonetic coherence.** Only allow merging syllables that
  share the same nucleus+coda (A7's own `rest` invariant — vary only the onset), instead of the
  current pure collision/exception-share criterion which is blind to phonetic content. Sanity
  checked against the actual data: `li/ti/ni` (all bare "i" nucleus, no coda) would separate out
  into their own group under this rule — which **is** `-ilité`. Also directly fixes the "unlearnable
  wildcard mixing unrelated vowels" complaint raised earlier about `S026`/`S007`. Cost: strictly
  fewer merges allowed overall, so some currently-accepted low-conflict-but-incoherent merges would
  be lost.
- **Theory D — true beam search** (keep top-K partitions per base, not committing to one greedy
  merge). Most literal reading of "explore breadth-first." Most expensive, needs a scoring/pruning
  rule. Given §4, this may now be affordable in a way it wasn't thought to be last turn.

## 6. What the next session should actually do

1. Read this file, the two above it, and skim `src/affixes.py` (`growAffixes`, `_growOneLevel`,
   `poolTailVariants`) and `src/affixbinding.py` (`growthMerges`, `unifyFamilies`) — these are
   short enough to read in full rather than trust this summary.
2. Design (on paper / in discussion first, per the user's explicit request — do not jump to code)
   a search/scoring strategy that treats "grow deeper" and "merge sideways" as edges in one graph,
   exploits §4 (cheap to generate many hypotheses; only the final top-20-30 selection needs to be
   careful), and solves the concrete `-té -> -ité -> -lité -> {-ilité, -bilité, -cilité} vs -liste`
   case correctly: it should end up preferring the deeper, more coherent `-ité` family growth over
   the shallow `-lité`+`-liste` merge, *unless* a sideways merge is actually the better-scoring
   final outcome once both are fully explored.
3. Only after the design is agreed, implement and re-verify against the real lexicon the same way
   this session did: `pytest src/test/`, `mypy src/`, `PYTHONPATH=. env/bin/python -m
   util.affix_scan --part a --refresh` then `--part b`, sanity-check family counts and specific
   worked examples (the `-ité`/`-ilité`/`-liste` case is the concrete regression test).

## 7. Constants reference (current values, all tunable, none sacred)

`src/affixes.py`: `MAX_AFFIX_SYLL=3`, `MIN_CARRIER_LEMMAS=5`, `MIN_STEM_ROOTS=5`,
`MIN_CANDIDATE_FREQ=20.0`, `FAMILY_LINK_SIM=0.6`, `NESTED_SIM=0.8`, `GROWTH_MAX_DEPTH=3`,
`GROWTH_MAX_EXCEPTION_SHARE=0.02`, `GROWTH_MAX_SLOT_VALUES=8`, `GROWTH_MIN_CARRIER_LEMMAS/
STEM_ROOTS/CANDIDATE_FREQ = 7x` the base constants.
`src/affixbinding.py`: `SPLIT_MAX_LOSS=0.02`, `MERGE_SIM_MIN=0.85`, `MERGE_MAX_MEMBERS=8`,
`MERGE_KEEP=0.9`, `MERGE_SIM_DROP=0.9`, `MERGE_PARTNERS=3`, `GROWTH_MERGE_KEEP=0.98`.

## 8. Do not

Do not commit or push (nothing in this line of work has been committed all session — it's all
uncommitted working-tree changes to `src/affixes.py`, `src/affixbinding.py`, `util/affix_scan.py`,
plus the two `PLAN_`/`RESUME_` docs). Do not touch the real pipeline
(`dictionary.py`/`util/build_*`/exports) — this is measurement/proposal tooling only, per
`PLAN_2026-09-26-affix-abbreviations.md` §10 ("Out of scope").
