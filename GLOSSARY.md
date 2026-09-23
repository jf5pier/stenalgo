# Glossary

> **Superseded by [`docs/GLOSSARY.md`](docs/GLOSSARY.md)** (2026-09-22 docs refactor); kept only until Interactive Triage (Pass 4).

Canonical vocabulary for this codebase. When a term below has a preferred synonym,
use the preferred synonym in new code, comments, and docs — the entry is kept only so
older prose (commit messages, past planning docs) stays decipherable.

## Cluster

See **Homophone Group**.

## Homophone Group

A group of `Word`s that share a lemma and grammatical category (`LemmeGramCat`) *and*
share a pronunciation (a `Strokes` key) — i.e. words that are homophones of each other
specifically because they're forms of the same lemma (as opposed to two unrelated
lemmas that happen to sound alike, a separate cross-lemma track handled by the `*`/`#`
reserved keys). Built by `buildLemmaHomophoneGroups()` (`src/elicitation.py`), keyed by
`LemmaHomophoneGroupKey = tuple[Strokes, LemmeGramCat]`.

## Reading

A grammatical reading: one specific grammatical parse of a homograph — e.g. "parle" has
two readings, 1st-person-singular présent and 3rd-person-singular présent. Was
implemented as a bare `frozenset[str]` of atomic features.

**Preferred synonym: Feature Combination** (`FeatureCombination` in
`src/elicitation.py`) — the atomized counterpart of the `combination`/`combinationStr`
vocabulary already used by `Word.getFeatures()` in `src/word.py`. Built per-word by
`wordFeatureCombinations()`.

## Signature

The set of markers (atoms) whose press is implied for a given spelling, once you union
the checked atoms across all of that spelling's readings within a homophone group. Two
different spellings in the same group ending up with the same signature is a conflict
(the chord no longer tells you which spelling to produce) — this is what the Elicitation Phase's step E5
(validate) checks for.

**Preferred synonym: Press-set** — the term the plan document itself already uses
(`ATOMIC_KEYPRESS_REWIRE_PLAN.md`, Elicitation Phase steps E5/E6: "every press implied by the data",
"per-cluster resolved press-sets").
