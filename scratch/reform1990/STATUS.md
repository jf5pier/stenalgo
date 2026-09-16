# 1990 spelling-reform lemme normalization — session handoff

Session paused mid-work. This file plus the approved plan is everything needed to resume.

**Plan file** (approved, still valid): `/home/jfsp/.claude/plans/soul-and-many-other-reflective-catmull.md`

## Already done and committed-ready (separate from this reform work)

Earlier in the same overall task, before the 1990-reform work started, `lexique.py` already
got a `normalizeLemme()` / `spellingVariantLemme` / `pronounParadigmLemme` mechanism, and it's
already been exercised end-to-end (LexiqueMixte.tsv, Dictionary.pickle, FirstTheory.pickle,
ambiguity_report.tsv all regenerated, full test suite green):
- `casher`/`kasher`/`kascher`/`cascher`/`cachère` → collapsed to `kasher` (Larousse-verified:
  kascher/cascher are archaic).
- `ile` → `île` (already the exact same phenomenon as this reform work, done ad hoc).
- Pronoun paradigms: `ils`(PRO:per)→`il`, `celle`/`celles`/`ceux`(PRO:dem)→`celui`.

This is unrelated to whether the 1990-reform work below lands — it's already working code in
`lexique.py`, not blocked on anything.

## Current task: exhaustive 1990-reform word list + optional lexique.py normalization

Goal (see plan file for full context/decisions): build a sourced, exhaustive resource file of
1990-reform old/new spelling pairs (all ~12 rule categories, per user's explicit choice), plus
an **optional** (`APPLY_1990_REFORM_LEMMES = False` by default) `lexique.py` pass that merges
the diacritic-based categories into `spellingVariantLemme`.

### What's been fetched (now copied to `scratch/reform1990/` so it survives — this dir is
NOT in `.gitignore` yet, check before committing anything, it's throwaway research material)

- `scratch/reform1990/annexe.wikitext` — the main Wiktionnaire annex page
  (`Annexe:Rectifications orthographiques du français en 1990`), rule prose + the ~12-category
  breakdown + a small example table per category. **Does not** contain the full word list (that
  lives on 26 letter-subpages, transcluded via `{{/A}}`...`{{/Z}}`).
- `scratch/reform1990/subpages.json` — raw MediaWiki API response for all 26 letter-subpages
  (`Annexe:.../A` through `/Z`), each subpage's wikitext is a bulleted bare list of reformed
  headwords tagged with a category-anchor link like `[[#Accent circonflexe|[6]]]`.
- `scratch/reform1990/match_reform_pairs.py` — the working (bug-fixed) heuristic matcher, see
  below.
- `scratch/reform1990/cat6_matches.tsv` — its output for category 6 (circumflex) only.

### Key finding that changes the plan's shape

The annex/RENOUVO lists only give the **new** (reformed) spelling + a category code — NOT
explicit old→new pairs (the mapping is meant to be mechanically derived from the rule, not
spelled out). Individual Wiktionnaire word-entry pages DO have explicit pairs (via
`{{tradit}}`/`{{ortho1990}}`/`{{moins courant}}` template tags in a "variantes orthographiques"
section — confirmed on the `soûl` page), but scraping ~1,300 individual pages is heavier than
originally scoped.

**User's proposed alternative (in progress): edit-distance heuristic instead of more scraping.**
Since the reform only *removes* an accent from specific letters (never adds one), and Lexique383
often already contains BOTH the old and new spelling as separate corpus rows (we already found
île/ile, soûl/soul this way), the fix is: for each reformed-spelling seed word (from the
26-subpage bullet lists), try re-accenting every eligible letter and check whether the resulting
old-spelling word exists in Lexique383. This only surfaces pairs that are *already both present
in the corpus* — which is actually all that matters for stenalgo's overflow-cluster problem (a
reform spelling that never appears in the corpus can't cause a lemma clash either way). This
turns "scrape 1,300 pages" into "check ~17 candidates by hand" for the circumflex category alone.

Implemented in `scratch/reform1990/match_reform_pairs.py`:
- `weightedEditDistance(a, b)` — general Levenshtein DP with a custom substitution-cost table
  (`ACCENT_PAIRS`: î↔i, û↔u, é↔è, ë↔e, ï↔i, ü↔u all cost 0.1; anything else costs 1.0).
- `findOldSpelling(newWord, lexiqueWords)` — tries every combination of re-accenting eligible
  letters, keeps candidates that are real Lexique383 words.

**Bug found and fixed this session**: a plain letter can map to *more than one* accented form
(plain `i` ← `î` circumflex OR `ï` tréma; plain `u` ← `û` OR `ü`). The first version picked one
arbitrarily via `next()` over a `set`, which made results silently depend on Python's
per-process hash-seed randomization (genuinely nondeterministic across runs — 11 vs 6 matches
on identical input, confirmed and root-caused, not environment flakiness). Fixed by trying
every accented alternative per position via `itertools.product` instead of picking one. Now
deterministic (verified 3 runs in a row, identical output).

### Current output (category 6 / circumflex only, run via
`python3 scratch/reform1990/match_reform_pairs.py` — note: hardcoded paths inside currently
point at the `/tmp/.../reform1990-scratch/` scratchpad location for `subpages.json`, **fix the
path to `scratch/reform1990/subpages.json` before rerunning** since that tmp dir may be gone
next session)

11 raw candidate matches, but **manual cross-check against the actual reform text found 4 are
false positives** — homograph collisions with unrelated pre-existing words, not real reform
pairs:
- `faîte`→`faite` — collides with "faite" (fem. past participle of *faire*, extremely common)
- `fût`→`fut` — collides with "fut" (standard passé-simple of *être*, "il fut")
- `mûre`→`mure` — collides with "mure" (conjugated form of *murer*, "to wall up" — confirmed via
  the actual Lexique383.tsv row: `mure  myR  murer`)
- `sûre`→`sure` — **this one is a documented Académie exception**, not an oversight: the reform
  text itself explains circumflex is *kept* on sûr/sûrs/sûre/sûres specifically because "sure"
  already means something else (sour/tart)

7 look genuinely clean: `boîte/boite`, `croît/croit`, `dessoûler/dessouler`, `faîne/faine`,
`île/ile` (already implemented separately, see above), `mû/mu`, `soûl/soul` (already implemented).

### Resolved: filtering approach for homograph collisions

Tested the automatic gramCat-overlap filter (option 1) before committing to it: it correctly
flags `mûre/mure` and `faîte/faite`, but it ALSO wrongly flags two genuine reform pairs
(`boîte/boite`, `soûl/soul` — their reform-spelling row only carries an unrelated homograph's
gramCat in the corpus) and MISSES the other two real false positives (`fût/fut`, `sûre/sure`
both happen to share a gramCat with their collision). So automatic gramCat filtering alone is
unreliable — not just "misses fewer/more," it makes different, uncorrelated mistakes than the
ones it was meant to catch.

**Decision: manual review (option 2), with gramCat/frequency shown as an advisory hint, not a
hard filter.** For category 6 the candidate list is only 11 words total, so full manual
verification against the reform rule text is cheap and strictly more reliable than the automatic
filter. This is now implemented in `match_reform_pairs.py` via a `CAT6_EXCEPTIONS` dict
(hardcoded, hand-vetted) rather than a `gramCatsOverlap()` hard gate — that function is kept only
to print an advisory `gramCatOverlap=` column for manual review of future categories.

**Category 6 is now fully resolved and output in the plan's final column spec** at
`scratch/reform1990/cat6_matches.tsv` (7 accepted pairs, 4 excluded with notes: `faîte/faite`,
`fût/fut`, `mûre/mure`, `sûre/sure`).

### Category 5 (accent grave) — done

`extractFirstWord()` needed a fix first: category 5's entries are formatted like
`[[abcéder|abcèdera]] (il)` — a piped wikilink where the target is the unchanged infinitive
lemma (`abcéder`) and the reform-affected word is the display text (`abcèdera`, future tense).
The old code always took the link target, so it silently extracted the WRONG word for every
piped line. Fixed `extractFirstWord()` to prefer display text over target when a pipe is
present. This also fixed 3 category-6 entries that were silently broken the same way
(`complaire|complait`, `déplaire|déplait`, `plaire|plait` — they landed in the "old spelling not
found" bucket before the fix, now correctly land in "new-spelling word absent from Lexique383"
since those conjugated forms genuinely aren't corpus words; no new false positives introduced,
verified by hand).

Category 5 produced 6 candidates, **all accepted, zero exceptions needed**: `allégement/
allègement`, `allégrement/allègrement`, `empiétement/empiètement`, `piétement/piètement`,
`événement/évènement` (the textbook example of this reform), `événementiel/évènementiel`.
Spot-checked each against Lexique383's `cgram`/`lemme` columns by hand — no homograph
collisions, all are unambiguous nouns/adverbs. (Two of the six — `empiètement`,
`évènementiel` — only appear as a `lemme` value in the corpus, not their own `ortho` row, which
is why they printed `gramCatOverlap=True` via the "missing data, can't rule out" fallback rather
than a real overlap; this is a data nuance, not a bug.)

Most of category 5's ~289 seed words are rare verb-conjugation forms (e.g. `abcèdera`,
`acièrerai`) that simply aren't corpus words at all — expected, per the heuristic's own design
(see "Key finding" section above: it only surfaces pairs where BOTH spellings are already
corpus-attested).

`match_reform_pairs.py` now processes both categories through one `processCategory()` function
and writes a single combined file, **`scratch/reform1990/cat5_6_matches.tsv`** (17 rows: 13
accepted + 4 excluded), in the plan's final column spec.

### Category 7 (tréma) — done

Transcribed directly from `annexe.wikitext`'s two explicit old/new tables (~line 254-306, no
heuristic matching needed — these give real pairs, not just new-spelling seeds like categories
5/6's subpages did). 11 pairs total: `aiguë/aigüe`, `ambiguïté/ambigüité`, `arguer/argüer`,
`bringeure/bringeüre`, `chargeure/chargeüre`, `égrugeure/égrugeüre`, `gageure/gageüre`,
`mangeure/mangeüre`, `plingeure/plingeüre`, `rongeure/rongeüre`, `vergeure/vergeüre`.

Checked each against Lexique383: **none of the 11 new (tréma-added) spellings appear in the
corpus at all** — only 4 old spellings do (`aiguë`, `ambiguïté`, `arguer`, `gageure`), the rest
are absent on both sides. So `appliesToLemmeNormalization=False` for all 11 (per the "Key
finding" above: a reform spelling that never appears in the corpus can't cause a lemma clash
either way) — these rows exist only for the exhaustive reference file, not the `lexique.py`
normalization pass. Written to `scratch/reform1990/cat7_matches.tsv` in the same column spec,
kept as a separate file from `cat5_6_matches.tsv` since it's hand-transcribed rather than
script-generated (categories 5/6 come from the heuristic matcher; combine both files when
building the final `resources/reform1990.tsv`).

### Scope decision — categories 1-4, 8-12 deferred

User chose (2026-09-16): wire up `lexique.py` now using categories 5/6/7, defer the other 9
categories. Rationale: those 9 are non-diacritic (hyphenation, pluralization, consonant
simplification, etc.), need bespoke transformation logic per category rather than the
accent-substitution heuristic, are much larger (~1700+ candidate words total across them), and
**none of them would feed `lexique.py`'s normalization pass anyway** (`spellingVariantLemme` only
merges diacritic-only lemma variants). If/when exhaustive coverage matters again, this is a
separate future task, not blocking.

### `lexique.py` wiring — done

Built `resources/reform1990.tsv` (comment-header style matching `verbModelExceptions.tsv`'s
convention) from `cat5_6_matches.tsv` + `cat7_matches.tsv` — 28 rows total (12
`appliesToLemmeNormalization=True`, 16 `isException=True` or corpus-absent).

One row needed a manual call: **`île`/`ile`** is a real category-6 pair, but `lexique.py`
already has an ad-hoc `spellingVariantLemme["ile"] = "île"` entry (opposite direction — canonical
is the traditional accented form, frequency-driven, since "ile" barely appears in the corpus at
all: freq old=166.6 vs new=0.0). Applying the plan's stated old→new direction for the new table
would have created `{"ile": "île", "île": "ile"}` — a 2-cycle that breaks `normalizeLemme`
entirely for this word. Marked `île` as `isException=True` in `reform1990.tsv` with a note
explaining why, rather than changing the existing ad-hoc entry's direction (that one was already
verified and is correctly frequency-driven, unlike the "apply the reform" pairs).

Added to `lexique.py` (~line 93-124): `APPLY_1990_REFORM_LEMMES: bool = False` constant,
`loadReform1990Lemmes()` (same comment/header-skip parsing style as
`loadVerbModelExceptions`/`loadNomAdjModelExceptions`), and a module-load-time
`spellingVariantLemme.update(...)` guarded by the flag.

**Verified per the plan's Verification section:**
- Flag off (committed default): `python lexique.py` reproduces `LexiqueMixte.tsv` byte-identical
  to before this session's changes. Confirmed via diff.
- Flag on: only `lemme` columns change (no `ortho`/`phon`/frequency drift), for exactly the 12
  accepted pairs — spot-checked `boîte→boite`, `dessoûler→dessouler`, `événement→évènement`,
  etc. all correctly merged. Confirmed `île`, and all 4 excluded homograph pairs
  (`faîte`/`fût`/`mûre`/`sûre`), are untouched in the output.
- `pytest src/test/`: 413 passed, both flag states.
- `mypy lexique.py`: same 9 pre-existing errors as on `main` before this session (confirmed via
  `git stash` A/B comparison) — nothing new introduced.
- `python dictionary.py` (flag on): completes cleanly, `satOptimizeDiscriminator` still proves
  0 special keys needed.
- `python -m src.ambiguitychecker` — **done, with an important gotcha found along the way**:
  `dictionary.py` caches `Dictionary.pickle`/`FirstTheory.pickle` and reuses them if present
  rather than rebuilding from `LexiqueMixte.tsv` (`if os.path.exists("Dictionary.pickle"): ...
  pickle.load(...)`). The first attempt at this comparison silently read a stale pickle from
  earlier the same day (predating all reform work), giving byte-identical "before" and "after"
  ambiguity reports — a false negative, not a real result. Fixed by deleting the pickles and
  forcing a genuine rebuild for both flag states before rerunning the checker.

  **Targeted result (the case that motivated this whole task): confirmed fixed.** The `s@el`
  cluster's two sub-clusters each went from 6 distinct lemmas to 5 — `soûl` no longer appears as
  its own lemma; `['saoul','sou','soue','soûl','soul','sous']` →
  `['saoul','sou','soue','soul','sous']` and similarly for the `-er`-form cluster. This matches
  the plan's expected outcome ("should shrink or drop below the n≥5 threshold") exactly, though
  it shrinks rather than drops below 5, since the remaining 5 lemmas (`saoul`, `sou`, `soue`,
  `soul`, `sous`) are genuinely distinct words, not spelling variants — nothing more to merge here.

  **Aggregate result: mixed, worth reporting honestly rather than declared a clean win.**
  Total lemma-homophone clusters dropped (7391→7386, a real improvement — fewer distinct
  ambiguity groups overall), but frequency-weighted overflow mass ticked up slightly
  (110173.62→111215.02, +0.9%) and the 5-lemma overflow tier grew (39→41 clusters). This is a
  real, explainable side effect, not a bug: when a merged pair's new canonical spelling happens
  to already homophone-clash with an unrelated pre-existing cluster, two previously-separate
  (and separately-small) clusters get unioned into one bigger cluster — correctly reflecting that
  they're now genuinely one ambiguity problem, but not what "did it shrink" naively suggests
  looking only at the aggregate number. Cross-category clashes also ticked up by one (99→100)
  for the same reason. None of this was traced to a specific pair — would need per-cluster diffing
  across all changed clusters to identify which merge caused which union, not just the targeted
  soûl one above; not done here given the scope decision to stop after wiring, not chase further.

Found and fixed one bug in `loadReform1990Lemmes()` along the way: `row.split("\t")` under-counts
fields when the trailing `note` column is empty (no trailing tab byte on that line), same
`ValueError: not enough values to unpack` class of bug `loadVerbModelExceptions` already guards
against with its `fields += [""] * (n - len(fields))` padding — applied the same fix here.

## Scope correction (2026-09-16, same day): lemme-merge alone was the wrong goal

After the lemme-merge work above was reported complete, the user clarified the actual goal is
bigger: `LexiqueMixte.tsv` should be **generative under the new (1990) norm**, not just
collision-free. Lexique383 is empirical (trained on text that can predate 1990), so a word that
only ever appears old-spelling in the corpus (e.g. only `événement`, never `évènement`) was being
left untouched by the lemme-merge mechanism, since there's no collision to resolve. That's not
what "follow the new norm" means. This required a second mechanism -- see the new plan file
`/home/jfsp/.claude/plans/luminous-wandering-puzzle.md` for the full design (Phase 1 built this
session; Phase 2 = category 8 `-eler`/`-eter`, rule-based via Verbiste, design-only; Phase 3 =
remaining 6 sourced-list categories, deferred, multi-session scope). Categories 1 (numéraux
composés) and 11 (participe passé de "laisser") were determined to be phrase/syntax-level rules
with no row-level hook in a word lexicon -- documented as out-of-scope placeholder rows in
`resources/reform1990.tsv` rather than built.

### Phase 1 (ortho-rewrite mechanism) -- done

`resources/reform1990.tsv` gained an `appliesToOrthoRewrite` column. `lexique.py` gained
`APPLY_1990_REFORM_ORTHO` (independent flag from `APPLY_1990_REFORM_LEMMES`),
`loadReform1990OrthoRewrites()`, and a rewrite hook in `outputMixedLexique()` -- see the plan file
for the full architectural reasoning (why the rewrite has to happen at output time, not on
`word.ortho` itself, since `words_by_ortho`/`LexiqueInfraCorrespondance` matching needs the
original spelling to keep working).

**Two real bugs found and fixed during this session's own verification, both worth remembering:**

1. **`mû` was silently never rewritten** by either mechanism (lemme-merge OR ortho-rewrite),
   because its only corpus row has `lemme="mouvoir"` (the infinitive), not `"mû"` itself --
   lemme-keyed lookup can't find irregular participle citation forms this way. Fixed by adding a
   fallback: `_reform1990OrthoRewrites.get(word.lemme) or _reform1990OrthoRewrites.get(word.ortho)`.
   Safe because dict lookup is exact-string equality, not prefix matching -- it can't accidentally
   catch an unrelated word like `mûr` that merely shares a prefix.
2. **`croît` was a genuine new-collision bug, not just a hypothetical risk.** Lexique383 has two
   distinct-lemma rows both spelled `croît`: NOM ("le croît" = growth/increase, freq ~0, basically
   unused) and VER (3rd-pers. présent of `croître` = "it grows", freq 1.55/1.2). The lemme-keyed
   rewrite only touched the NOM row (its lemme is literally `"croît"`), leaving the VER row
   (`lemme="croître"`) untouched -- so post-rewrite, "croît" (grows) stayed circumflexed while
   "croît" (growth) became "croit", newly colliding with the very common `croit` (VER, croire =
   believes). Found via a systematic check (`grep` distinct-lemma-count per accepted word against
   raw Lexique383) run *because* Phase 1's own plan called for scanning for exactly this kind of
   thing -- confirmed `croît` is the *only* one of the 12 pairs with this multi-lemma-same-spelling
   structure. Excluded as a new `isException=True` row (same reasoning family as
   `fût`/`faîte`/`mûre`/`sûre`: rare word, real collision, nothing lost by excepting it). This also
   fixed a secondary finding: including `croît` had been the cause of the earlier lemme-merge-only
   run's aggregate overflow-mass regression (+0.9%, see below) -- excluding it brought the
   aggregate metric back to exactly flat.

**Verification, both flags on together (12 accepted pairs: 6 circonflexe + 6 accent_grave, after
excluding `île`/`croît`):**
- Confirmed `ortho` (and `orthosyll_cv`) actually rewrites for **every** corpus row in a family,
  not just the literal words in the table -- e.g. `boîte`/`boîtes` (plural, never listed
  explicitly) both became `boite`/`boites`; all 9 `dessoûler`-family conjugated forms became
  `dessouler`-family; `événement`'s word-initial `é` correctly stayed put while only the second
  (target) `é` became `è`, matching the reform's own "initial é stays" exception, via
  occurrence-counting rather than a naive first-match replace.
- Systematic new-collision scan (`(ortho,phon)` pairs with a lemma set that wasn't already
  present before the rewrite): with only `APPLY_1990_REFORM_ORTHO` on, found 12 -- 8 were exactly
  the already-known family collisions that `APPLY_1990_REFORM_LEMMES` resolves when both flags run
  together (confirmed: dropped to 0 once both flags were on), and the remaining 2
  (`boite`/`boiter`, `soule`/`soul`) are legitimate new cross-lemma homographs that are an
  intentional, expected consequence of correctly applying the reform (same class as
  pre-existing, untouched homography like `croit`(croire)/`croît`(croître) before any of this
  session's work) -- not bugs, left as-is, the steno theory's existing homograph-disambiguation
  machinery (featureextractor etc.) already handles ordinary French homography.
- Flag-off (both): `LexiqueMixte.tsv` byte-identical to session start, confirmed via diff.
- `pytest src/test/`: 413 passed. `mypy lexique.py`: same 9 pre-existing errors, nothing new.
- `dictionary.py`/`ambiguitychecker` rerun with freshly-deleted-and-rebuilt pickles (remember the
  caching gotcha from earlier in this file). Result with both flags on:
  lemma-homophone clusters 7391→7386 (same improvement as the lemme-merge-only run), but overflow
  frequency mass stayed **exactly flat** at 110173.62 (vs. +0.9% in the earlier lemme-merge-only
  run) -- confirms excluding `croît` fixed that regression. Targeted check: the `soûl`/`soul`
  cluster still shows the same 6→5 lemma improvement as before, now also correctly spelled
  `soul`/`souls` in `ortho` (not just merged in `lemme`).

Working tree is back in the flag-off, committed-default state (`LexiqueMixte.tsv` verified
byte-identical to session start) as of the end of Phase 1.

### Phase 2 (category 8, `-eler`/`-eter` verbs) -- done, same session, continued

**Important correction to the Phase-1-era plan writeup**: category 8 does **not** change
phonology. Both the doubled-consonant convention (`amoncelle`) and the grave-accent convention
(`amoncèle`) encode the exact same open-e sound -- confirmed by the official report's own wording
("L'emploi du e accent grave pour noter le son «e ouvert»... est étendu à tous les verbes de ce
type") and by direct inspection of Lexique383's `phon` column, which is identical before and
after for every rewritten row. So this needed the same `ortho`/`orthosyll_cv`-only mechanism as
categories 5/6/7, not a bigger phonology-aware rebuild as originally assumed.

**Primary-source validation caught a real error in the secondary source.** Fetched the official
Journal officiel report directly (`academie-francaise.fr/sites/academie-francaise.fr/files/
rectifications.pdf`, converted via `pdftotext -layout`) rather than trusting the Wiktionnaire
annex alone. The annex's summary table lists "appeler, rappeler, interpeler" as the exception
verbs that keep doubling. The official report's own rule text says: *"On ne fait exception que
pour appeler (et rappeler) et jeter (et les verbes de sa famille)"* -- **interpeler is not named**.
So `interpeler` actually regularizes like any other `-eler` verb (`interpelle` → `interpèle`)
under the reform; the annex was wrong (or at least materially incomplete) on this point. This is
exactly the kind of discrepancy multi-source validation was supposed to catch.

"Jeter's family" isn't enumerated in the report either. Taken as `jeter` plus every
Verbiste-`j:eter`-tagged verb whose infinitive literally ends in `-jeter` (`déjeter`, `forjeter`,
`interjeter`, `introjeter`, `projeter`, `rejeter`, `surjeter`) -- the etymologically natural
reading, all sharing the `jet-` radical via prefixation. Cross-checked: Verbiste has no other
`-appeler`-suffixed verb besides `appeler`/`rappeler` itself, so that exception set is exactly 2.

**Key implementation finding**: Verbiste's own `app:eler`/`j:eter` template tags reflect the
*pre-reform* default, not the reform's norm -- of the 64 `app:eler`-tagged verbs, only 2
(`appeler`, `rappeler`) are true reform exceptions; the other 62 (including `interpeler`,
`ruisseler`, `amonceler`, etc.) should regularize. Same pattern for `-eter`: 70 `j:eter`-tagged,
8 true exceptions (`jeter` + 7 derivatives), 62 regularize. So the rule is genuinely "everything
regularizes except this short, explicit, sourced list" -- confirmed this by testing, not assumed.

**Implementation** (`lexique.py`, after the Phase 1 code): `APPLY_1990_REFORM_ELER_ETER` flag
(off by default, independent of the other two flags), `APPELER_EXCEPTIONS`/
`JETER_FAMILY_EXCEPTIONS` constants, `loadElerEterQualifyingVerbs()` (parses
`resources/verbiste/verbs-fr.xml` directly for the qualifying set), and a general
doubled-consonant→grave-accent transform (`regularizeElerEterOrtho()`/
`regularizeElerEterOrthosyll()`) applied in `outputMixedLexique()` alongside the Phase 1 hook --
this is a *programmatic rule*, not a static pair table like Phase 1/`reform1990.tsv`, since it
covers ~124 verbs generatively from their radical rather than needing each conjugated form
listed individually.

Also implements the reform's rule-5 "-ment"-derived nouns (`amoncèlement`, etc. -- 9 of the
report's 18 named words are actually attested in Lexique383 under their doubled-consonant lemme;
the rest either aren't in the corpus, or, for `martèlement`, the corpus already only has the
reformed spelling as its lemme, so there's nothing to rewrite there).

**A genuinely tricky bug found and fixed during verification**: the doubled consonant in
`orthosyll_cv` isn't always within the same syllable segment as its preceding "e" -- most
conjugated forms show it as one token, `c_e_ll_e` (e.g. `amoncelle`), but `amoncelleraient`
breaks across a syllable boundary instead: `c_e|ll_e|r_aient`. A plain substring replace on
`"_e_" + doubled + "_"` would have silently missed this and every conjugated form shaped like it.
Fixed with a boundary-agnostic regex (`e([_|])` + doubled consonant) that matches either
separator. Verified against this exact case by hand: `amoncelleraient` → `amoncèleraient`,
syllable breakdown `a|m_on|c_è|l_e|r_aient`, letter count checks out (14 vs. original 15, the
expected -1 from de-doubling).

**Verification**: spot-checked ~10 conjugated forms across 5 different verb stems (`amonceler`,
`chanceler`, `cliqueter`, `ruisseler`, `voleter`, `épeler`) -- all correctly rewritten with `phon`
untouched; confirmed `appeler`/`rappeler`/`jeter`/`rejeter`/`projeter` correctly stay doubled
(exceptions working); confirmed all 9 attested "-ment" nouns rewrite correctly. New-collision
scan (flag alone) found exactly 2 hits: `cliquettement`/`cliquètement` is a genuine new family
collision of the same class Phase 1 already established as expected/acceptable (and, unlike
categories 5/6/7, category 8 has **no lemme-merge companion mechanism** -- this collision won't
auto-resolve the way Phase 1's did when `APPLY_1990_REFORM_LEMMES` is also on; noted as a known
gap, not fixed this session, low-stakes given the word's frequency is 0.07); `jumelle`'s lemma
set *shrank* (3→2, `jumeler` moved off it to `jumèle`) which is a false-positive flag from the
scan script (it flags any change, not just growth) -- not a real problem, a correct improvement.
413 tests pass, mypy clean of new errors, both flag-off byte-identical and all-three-flags-on
ambiguitychecker runs completed cleanly (the lemma-homophone cluster metric is unchanged from the
Phase-1-only run, as expected -- category 8 never touches `lemme`, only `ortho`/`orthosyll_cv`,
so it's invisible to that particular lemma-based report).

Working tree is back in the flag-off, committed-default state as of the end of Phase 2.

### Phase 3, partial (categories 9 and 10) -- done, same session, continued further

Picked the two smallest/most tractable of the 6 remaining categories: category 9
(`-illier`/`-illière` loses its "i", e.g. `quincaillier` -> `quincailler`) and category 10
(`-olle`/`-otter` doubled consonant reduced, e.g. `cocotter` -> `cocoter`). Both categories'
Wiktionnaire subpages give **explicit old/new pairs directly** via "X, au lieu de Y" phrasing --
no edit-distance heuristic matching needed, unlike categories 5/6/7. Extracted 9 pairs
(category 9) and 40 pairs (category 10, one dropped for having no named old form), classified
each against Lexique383 (BOTH/OLD_ONLY/NEW_ONLY/NEITHER attested) and ran the same croît-style
"does this exact spelling have >1 distinct lemma" danger check established in Phase 1 -- zero
danger flags this time, every pair is clean. Final: 4 accepted pairs for category 9 (rest either
unattested or already-only-new-spelling), 30 accepted for category 10 (8 already colliding in
the corpus, 22 old-spelling-only) -- all written to `resources/reform1990.tsv` with categories
`illier_illiere`/`olle_otter`.

**Extended the Phase 1 mechanism to support single-character deletions, not just
same-position substitutions.** These pairs differ by a removed letter (e.g. `quincaillier`
(12) -> `quincailler` (11)), unlike categories 5/6's same-length accent swaps. Added
`computeSingleEditRule()` (handles both substitution and deletion, encoding a deletion as
`newChar=""`) and generalized `loadReform1990OrthoRewrites()` to call it instead of assuming
same length.

**A second genuinely tricky bug found and fixed**: `applyOrthoRewrite()`'s deletion case
originally just blanked the target character in place (`chars[i] = ""`), which is correct for
the flat `ortho` string but leaves a dangling double-separator artifact in `orthosyll_cv`
(`"ll__er"` instead of `"ll_er"`, from blanking a letter-slot between two `"_"` separators
without also removing one of them). Fixed by making the deletion path drop the character's list
index outright and then drop one adjacent separator character if present -- verified this is a
no-op for the separator-free `ortho` string (no accidental extra deletion there) and correctly
collapses the syllable-string artifact for `orthosyll_cv`. Caught via the same
"reconstruct the word letter-by-letter from orthosyll_cv and compare to ortho" spot-check
discipline established in Phase 1/2 -- this bug would have silently corrupted the syllable data
consumed downstream by the CP-SAT optimizer if unchecked.

**Verification**: spot-checked all 4 category-9 and a sample of category-10 rewrites
letter-by-letter against `orthosyll_cv`, confirmed `phon` unchanged throughout (pure spelling
convention changes, same as the other mechanisms), confirmed the family-based lemma matching
correctly generalizes to inflected forms not literally in the source table (e.g. `ballotter`'s
conjugated form `ballotte` -> `ballote`, not just the infinitive) -- same intended "generative,
not just literal word list" design as Phase 1. New-collision scan (ortho flag alone, categories
5/6/8/9/10 combined) found 15 hits, all traced to already-understood causes: the established
Phase 1 family collisions, or new-but-legitimate homograph collisions from generalizing across
conjugated forms (`ballote`/`ballotter`, `boulotte`/`boulot` -- same acceptable class as
`boîte`/`boiter` from Phase 1, not bugs). 413 tests pass, mypy clean of new errors, all-four-flags-
combined run (`LEMMES`+`ORTHO`+`ELER_ETER`) completes cleanly, flag-off byte-identical to
session-start baseline confirmed.

Working tree is back in the flag-off, committed-default state as of the end of this session too.

### Phase 3, categories 2/4 ruled out, category 12 done -- done, same session, continued further

**Major scope reduction discovered while starting category 4 (mots soudés, hyphen removal):
zero hyphenated words exist in `LexiqueMixte.tsv` at all** (confirmed via direct count, not just
grep). Hyphenated compounds fail `outputMixedLexique()`'s `word.orthosyll_cv != []` filter --
`resources/LexiqueInfraCorrespondance.tsv` has no grapheme-phoneme associations for them, so
`breakdownSyllables()` never populates their syllable data and they're silently dropped from the
generated lexicon. This makes category 4 **entirely moot** for this pipeline: there's nothing to
rewrite, since the source words never appear in the output to begin with. Checked category 2
(pluriels de mots composés) the same way -- **100% of its target words are also hyphenated
compounds**, so it's moot too, for the identical structural reason. This cuts the remaining
Phase-3 scope roughly in half (from ~1450 words across 4 categories to ~623 across 2: mots
empruntés ~521 + autres rectifications ~102).

**Category 12 (autres rectifications) -- done.** A grab-bag of ~90 idiosyncratic per-word fixes
with explicit "X, au lieu de Y" / "X, plutôt que Y" / "X, remplacé par Y" pairs in the
Wiktionnaire subpages (plus one extraction bug caught and fixed: a "saccharine (et sa famille:
saccharase, saccharate, ...)" family-list line broke the 2-link "au lieu de" regex, silently
pairing unrelated family members together -- re-extracted properly, only `saccharine`/`saccharose`
of that ~23-word family turned out to be corpus-attested).

**Extended `computeSingleEditRule`/`orthoRewriteOccurrence`/`applyOrthoRewrite` to support
insertions**, not just substitutions and deletions -- several category-12 pairs ADD a letter
(e.g. `chariot`->`charriot`, `combatif`->`combattif`), the mirror case of categories 9/10's
deletions. Represented as `oldChar=""` (nothing there in the old spelling), anchored on the last
character of the shared prefix, with the new character inserted directly adjacent to that anchor
(no separator) -- this naturally produces a doubled-letter token in `orthosyll_cv` (e.g. `"rr"`)
matching the same digraph convention already established for categories 8/9/10, rather than a
separately-separated letter-slot. Verified letter-by-letter against `orthosyll_cv` for all
insertion and deletion cases; `phon` confirmed unchanged throughout.

**Two pairs excluded due to genuine homograph danger, beyond the mechanical multi-lemma check**:
`absous`/`absout` and `dissous`/`dissout` (the reform target is the VER past-participle sense,
but both spellings are ALSO separate, unrelated ADJ lemmas at the exact same spelling -- the
existing lemme-or-ortho fallback lookup can't distinguish which row is which without deeper
gramCat-aware logic not built this session). `repartie`/`répartie` and `repartir`/`répartir`
also excluded -- `repartie` is a genuine 3-way homograph (NOM "a witty retort" vs VER fem.
participle of "repartir"), and `repartir`("to leave again")/`répartir`("to distribute") looked
on inspection like two established, unrelated modern French verbs rather than a clear reform
spelling-variant pair -- needs manual research not done this session, so left undecided rather
than guessed.

**A genuinely useful side-finding, documented as a known gap rather than fixed**: category 12's
source list also includes `interpeller`->`interpeler`, which turns out to explain why category
8's mechanism (Phase 2) silently never touched this verb -- Lexique383's own `lemme` for it is
`"interpeller"` (double-l), but Verbiste's (and the primary source's) canonical infinitive is
`"interpeler"` (single-l), so the lemma-keyed lookup in `loadElerEterQualifyingVerbs()` never
matches. A plain single-edit ortho-rewrite here would also be wrong on its own (it would
incorrectly touch the STRESSED conjugated forms too, producing `interpele` instead of the
correct accented `interpèle`, since those need category 8's radical+accent regeneration, not a
plain deletion). Documented as an `isException=True` row with a detailed note rather than either
mechanism; a real fix would need an alias table in category 8's matching logic, not attempted
this session.

**Verification**: same rigor as Phases 1/2 -- all new pairs spot-checked letter-by-letter against
`orthosyll_cv`, `phon` confirmed unchanged, full collision scan (ortho flag, all categories
combined) found 21 changed keys, all traced to expected causes (5 new category-12 `BOTH`-status
family collisions matching my own classification, the rest already-known Phase-1-era family
collisions) -- no new danger signs. 413 tests pass, mypy clean of new errors, all-flags-combined
run completes cleanly, flag-off byte-identical to session-start baseline confirmed.

## If resuming: what's genuinely still open

- **Category 3** (mots empruntés/loanwords, ~521 words) is the only sourced-list category left
  entirely unstarted -- needs new transformation logic (pluralization-suffix regularization,
  e.g. `matches`->`matchs`, `maxima`->`maximums`; not a simple character edit like the categories
  done so far) not yet designed.
- **Category 8's lemme-merge companion** (so `cliquettement`/`cliquètement`-style family
  collisions resolve the same way the diacritic categories' do) -- small, well-scoped follow-up.
- **`interpeller`/`interpeler`** (see above) -- needs an alias fix in category 8's matching, not
  a `reform1990.tsv` row.
- **`absous`/`dissous`/`repartie`/`repartir`** (see above) -- excluded pending dedicated
  gramCat-aware handling (absous/dissous) or manual linguistic research (repartie/repartir) not
  done this session.
- Categories 1, 2, 4, 11 are conclusively out of scope for this pipeline (phrase-level rules or
  100%-hyphenated word lists that never survive into `LexiqueMixte.tsv`) -- nothing more to do
  there, this isn't a "come back later" item.
- Nothing here is blocking; this file plus the plan file are a complete record if the thread needs
  to be picked back up later.
