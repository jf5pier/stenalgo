# Affix abbreviations: philosophy, design choices, algorithms

Why Affix Abbreviation Building (S9) is the way it is. The operational reference (commands, files, flow, pitfalls) is
[AFFIX_RULES.md](AFFIX_RULES.md); the vocabulary is [GLOSSARY.md](GLOSSARY.md); the place in the pipeline is
[PIPELINE.md](PIPELINE.md). The dated `DESIGN_/PLAN_/FINDINGS_/RESUME_*` notes at the repo root are the history of how
these choices were reached; where they differ from this file, this file wins (and the code wins over both).

## 1. Philosophy

1. **The theory comes first, abbreviations are a layer on top.** The stable theory (phonetic theory, same-lemma features,
   star/hash marks) is complete without any abbreviation. An abbreviation is an EXTRA, shorter outline for a word that
   keeps its long outline. A learner who forgets or ignores the rules loses nothing; removing the affix dictionary
   changes nothing else. So S9 never touches S1-S8 outputs, and an abbreviation is added only when its outline collides
   with nothing in the stable theory: it never needs a mark and cannot change a collision outcome.
2. **A rule is one thing a human must recognise.** The cost of a rule is cognitive, per pattern, not per key. Two
   unrelated affixes on one keypress are two rules; sharing a key never justifies keeping a rule. Hence a small total
   budget (30 rules, prefixes and suffixes together) and "fewer rules with simple logic" over raw savings.
3. **Learnability is judged by the user, not computed.** A numeric score ranks and filters, but growing a rule onto a
   neighbouring syllable or fusing spelling variants is never accepted by a threshold: the algorithm proposes with
   evidence (helps / hurts) and the user confirms. Verdicts live in a committed file the pipeline only reads, so the
   pipeline runs without an agent. Examples of why no single threshold exists: `é` +633 refused, `tion` +344 accepted;
   `cé`+`m@` kept at +7 because other rules already grow on `m@` (a pattern already known costs less), `ssion`+`pRe`
   refused at +247 (few words, resembles no other rule).
4. **One key per rule.** Cutting a rule's exceptions by splitting it into several keys or conditions was measured
   (30-80% fewer exceptions) and rejected: it adds a key and a condition per rule and does not make the rules easier to
   learn. The tools left are a scope condition on the one rule, or a fix to the evaluator.
5. **Meaning-carrying units stay whole.** A productive prefix such as `re-` ("again") maps key to meaning; fusing it with
   whatever syllable follows (`re`+`gar`) makes unrelated units look linked. Such rules stay anchor-alone and widen by
   morpheme variants (`ré-`, `r-`), never by absorbing the next syllable. Phonetic endings (`-ment`, `-tion`) are
   different: a syllable-pattern scope is fine there.
6. **Exceptions are cheap to learn, simplicity wins.** Hence a small price per fallback word (5) and a small price per extra
   form (100), against a heavy price for a word that collides (twice its frequency).

## 2. Vocabulary in one paragraph

An **anchor** is an affix syllable (position prefix/suffix, spelling, sound) with its **carriers** (words that start or
end with it, whose remainder, the stem, is an attested lemma of at least 3 letters). **Spelling variants** of one sound can
be **fused** into one anchor (`am|an|ant|em|en|...`). A **growth form** fuses the anchor with the neighbouring syllable
(before a suffix, after a prefix) on the same stroke (`-ation`, `-ition`), selected by a **scope** (a pattern on the
neighbour's sound or spelling). A **fallback** is a carrier a scope names that cannot use the rule and reverts to the
anchor alone. A **rule** is one anchor plus its decided growth forms plus ONE **keypress** (1-3 keys).

## 3. The mechanism the algorithms optimise

A rule's keypress K replaces the affix syllable(s) of a carrier, merged into the neighbouring syllable's stroke
(`_newBase` in `src/affixes.py`): the word loses `span` strokes. When the merge is physically impossible (every key of K
already in the neighbour, `ruleKeysOverlap`; or the union is not a legal chord) the affix becomes a standalone stroke
(`span - 1` strokes saved), unless that is no gain or the outline already exists. The shortened outline must then be safe:

- it may collide with a different lemma's outline only at the price of marks (`markCost`); a gain that the marks eat is
  `markCostTooHigh`; a collision with another form of the SAME lemma is `lostDistinction`;
- the reasons `lostDistinction`, `markCostTooHigh` and `standaloneTrap` are **word exceptions** (the learner must know
  the word does not follow the rule). `keyOverlap` / `illegalChord` are physical and handled by the standalone fallback,
  never counted as exceptions: the writer can feel an impossible chord.

`simulate` evaluates all carriers of a binding together, so collisions between carriers of different rules cost marks too.

## 4. Score of a rule

```
score = benefit                      strokes saved x word frequency, over the carriers that gain
      - 2   x exception frequency    word exceptions (collisions)
      - 5   x (slot exclusions + fallbacks)
      - 100 x (forms - 1)
```

Prices were fixed by the user on 2026-09-30 after a sweep of three weightings (L/M/H). H (heavy forms, 300) picked broad,
high-frequency rules and few forms; L picked many narrow rules. The user's prices are in between: forms are cheaper than
H's 300, exceptions weigh double, fallbacks are almost free. A hard cap sits beside the score: a rule whose exception rate
(exceptions / (covered + exceptions)) exceeds 5% is rejected whatever its score. It was found on `re`: the key most similar
to the prefix's sound (R) had an 18.7% exception rate (reviens, revient, retrouve...), while a key with almost no phonetic
similarity scored 41% higher with a fraction of the exceptions.

## 5. The algorithms, stage by stage

### 5.1 Candidate pool (`src/affixes.py`: `extractRecords`, `buildCandidates`)
Records are the stable theory's words with their syllable strokes. Anchors come from seeds (`resources/affixSeeds.tsv`,
drawn from the TAO method / Pluvier) and the detected affixes; carriers must leave a real stem. **One generator**: only
anchors are roots; a grown form is only ever a form of its anchor's rule (an earlier lattice generator produced
overlapping families and made the selection contradictory; see `FINDINGS_2026-09-28-affix-single-generator.md`).

### 5.2 Fusion of spelling variants (`resolveVariantRivals`, `affixproposals.proposeFusion`)
A merged anchor (`ment|mant`) and its parts are rivals, never a family. The verdict in `affix_decisions.json` settles it
before selection: `fused` replaces all parts, `apart` keeps the parts. No verdict = apart, reported PENDING. To propose,
the engine scores the merge against the parts alone, **each with its decided growth**, each on its own best keypress; the
merge keeps the parts' growth on their own spellings only (added spellings stay anchor-only); it is also judged at the
parts' own keys because the key search can miss them (section 6). The user accepts spelling by spelling, so a merge is
the parts plus the accepted spellings.

### 5.3 Growth proposals (`affixproposals.proposeGrowth`)
For an anchor with a key, candidate scopes are generated from a grammar on the neighbour's sound (onset: exact / C /
C{1,2} / C* / [mn]; nucleus: exact / vowel class / oral vowel / any), per anchor spelling, each scored at the rule's keys.
Shown best first, per addition (anchor spelling + neighbour sound), with an accept line each; an accepted form's best
extension is offered next. Exact neighbour spellings only when they beat the best sound pattern. Refused labels are never
asked again. Regexes on SOUND are preferred over word lists (a list of 100 syllables is unlearnable).

### 5.4 Order of decisions: growth before fusion
Growth is asked first, for every anchor, then fusion. Reason: `té` grows into `lité`, then `bilité`; fusing `té` with `ter`
before that would block a growth that makes more sense than the fusion, and a fusion is only judged fairly with its parts'
growth in place. A fused merge that has no growth verdict of its own inherits its parts' growth (on their own spellings).
The review loops by itself: after each pass the selection is rebuilt (cached evaluations) and the newly pending items are
asked, until nothing is pending, the user quits, or a pass saves nothing.

### 5.5 Key search (`affixrules.chooseRuleKeypress`)
Tests EVERY legal keypress (1,751), not the phonetically closest: similarity hid the best answer on `re`, so it only
labels the final pick. Two passes: (1) all keys on a sample of the 2,000 most frequent carriers, with a cheap exact lower
bound on the exception rate to skip hopeless keys; (2) the top `MAX_ALTERNATIVES` = 30 keys on all carriers. The sample
trades exactness for time: with 5 finalists it missed the best key of 3 of the 15 rules larger than the sample (the best
keys ranked 25th, 40th and 6th on the sample; +3%, +2%, +7%); 30 finalists cost a few seconds more per rule. Not proven
exhaustive.

### 5.6 Budgeted selection (`selectRules`, `swapPass`)
Lazy greedy over the roots with a three-stage heap (raw upper bound, proxy marginal, exact marginal), each recomputed
against the current selection, so the expensive key search runs at most once per root and only for roots that reach the
top. **Each word is credited once, at its best selected rule**, so a rule is worth its marginal gain. A root overlapping a
selected same-position rule by half or more is skipped (a safety net: with one generator it should not fire). A swap pass
tries replacing each selected rule by the 20 best unselected exact-evaluated ones (3 passes), keeping swaps that raise
the word-once total. A full selection takes about 20 minutes; per-rule evaluations are cached by a signature of the rule
and its carriers, so one changed verdict reselects in about a minute.

### 5.7 Keypress binding (`bindKeypresses`)
After selection, each rule takes its best key, best score first. Two rules of the same position may share a key when a joint
simulation loses at most 2% of either. Sharing is a packing step AFTER selection and never decides whether a rule is kept.
Keys 0, 1, 10, 15 are reserved and never used.

### 5.8 The abbreviation dictionary (`src/affixabbrev.py`, S9b)
For each carrier, the shortened outline of the best rule is added when it is free in the stable theory; a form that is not
allowed falls back to the rule's anchor alone, then to no abbreviation. One abbreviation per word (the largest saving; a tie
goes to the better-ranked rule). The long outline stays valid. Output: a Plover JSON dictionary and a TSV for review.

## 6. Known limits

- The key search is sample-based (5.5). The selection and the keys depend on it.
- The selection is greedy; the swap pass improves it locally, nothing proves optimality.
- Numbers are in frequency units of the lexicon (books + subtitles); the savings measure strokes, not typing time or finger
  strain.
- Learnability is an argument, not a measurement: no learner has been tested on the 30 rules. The TAO manual teaches roughly
  218 such rules over a multi-year curriculum; 30 is deliberately a small slice for an automated, optional layer.
- A lexicon or layout change invalidates the cache (`rm AffixSelection.pickle`); decisions are keyed by exact spelling sets, so
  a changed set becomes a pending item rather than being applied silently.
