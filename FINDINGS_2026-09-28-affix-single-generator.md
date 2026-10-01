> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Findings: single-generator affix rewrite (2026-09-28/29)

**Audience: the user.** This explains, in plain terms, what the rewrite in
`PLAN_2026-09-28-affix-single-generator-rewrite.md` produced, defines every term used in the
STOP-2 report, and compares the result against the TAO manual (`Tao.md`) and what's known about
Pluvier/OQLF. Nothing here is committed; the code changes are on branch `affix-abbreviation-rules`,
uncommitted.

## 0. What this is, one paragraph

The affix scan looks for spelling patterns at the start or end of French words (like `-ment` or
`re-`) that are common enough, and safe enough (don't collide with other words), to deserve their
own stenotype keypress -- one stroke abbreviates the whole ending instead of spelling it out
syllable by syllable. This session rewrote the part that discovers those patterns ("Phase 1"),
simplified it to one generation mechanism instead of three overlapping ones, and re-ran the whole
pipeline (discovery -> candidate rules -> budgeted selection -> keypress assignment) at three
different cost settings so you can compare the trade-offs.

## 1. Glossary

Read this section once; it's referenced by name throughout §2-3.

- **Anchor.** A pattern node that is allowed to become the *root* of a rule. In the old code,
  three different mechanisms (raw enumeration, "A7" onset-pooling, and lattice growth) all
  competed to be roots, sometimes producing near-duplicate patterns (`ment` and `·°ment`) that
  looked different but covered almost the same words. Now there is exactly one kind of anchor:
  a single-syllable ending/beginning (`ment`, `de`, `té`...), a hand-curated etymological group
  (co-/con-/com-/col-/cor-), or a **variant merge** (below). Everything longer is *grown* from an
  anchor and can never become a root itself.
- **Form.** One specific shape that a rule's keypress covers. A rule usually has more than one
  form: e.g. the `ment` rule's forms are `ment` itself (k=1, one syllable) plus several longer,
  grown variants (`·[...]tement`, `·[...]blement`, etc., k=2-3) that absorb one more syllable to
  cover more words with the same key. "Forms" is the report's word for "the different endings this
  one key actually handles."
- **Rule.** An anchor plus its chosen forms plus (eventually) one keypress. This is the finished,
  shippable unit: one key on the keyboard, abbreviating a specific set of word endings.
- **Variant merge / fusion.** Two different spellings of the *same sound* -- `ment`/`mant`,
  `tion`/`ssion`, `té`/`ter` -- fused into one anchor (`mant|ment`) so they can share one key,
  *if and only if* fusing them doesn't create new collisions between unrelated words. This
  replaces last session's "A7" mechanism, which pooled by sound whether or not that was safe.
- **Rival / rival resolution.** A merged anchor (`mant|ment`) and its two unfused parts (`mant`,
  `ment` separately) can never both become rules -- that would be two keys for the same
  territory, the exact `ment`/`·°ment` bug from two sessions ago. "Resolving the rivals" means:
  before picking any rules at all, decide once per group whether the fusion wins (then only the
  fused anchor competes for a slot) or loses (then only the separate parts compete).
- **Overlap / territory / skip.** Two rules "overlap" when they cover a lot of the same words
  (measured as a frequency-weighted share of the smaller rule's words). If the selection process
  is about to pick a rule that overlaps an already-picked one by 50% or more, it **skips** that
  rule instead of picking it -- one territory, one key. In this run this happened essentially
  never (skips: 0 at L, 0 at M, a couple at H), because the rival-resolution step above already
  settles the one place this used to happen (merged anchors vs. their parts).
- **Exclusion.** When growing a longer form, some absorbed spelling can't fit cleanly (it would
  collide) and gets excluded from that form's coverage by name, e.g. "this form covers `-ément`
  except the syllable `-riez`". Each excluded spelling costs a small penalty (`EXCLUSION_COST`),
  because a form with a growing exception list is harder to learn than a clean pattern.
- **Word exception.** A specific word that carries the pattern's spelling but is deliberately
  *not* abbreviated -- it keeps its normal, unabbreviated outline -- because abbreviating it would
  make it indistinguishable from some other word. This is the day-to-day cost of ambiguity: the
  rule still exists, this one word just doesn't benefit from it.
- **Exception rate.** `word exceptions / (words helped + word exceptions)` for one rule. Capped
  hard at 5% (`MAX_EXCEPTION_RATE`): a rule that breaks on more than 1 in 20 of its own words is
  rejected outright, regardless of how good it looks otherwise.
- **`attestedShare`.** Of a rule's carrier words (weighted by how common the word is), the
  fraction whose *stem* is independently a real French word/lemma. Example: `-ment` covers
  `rapidement` (stem `rapide`, a real word: high attested share contribution) but this plan
  deliberately also lets it cover words whose leftover stem isn't a dictionary word on its own.
  A rule with **`attestedShare` < 0.5** is flagged in the report as a candidate "pseudo-affix":
  the pattern might just be a coincidental shared spelling rather than a real, teachable
  derivational suffix (e.g. `-in`, `-der`, `-nir` in the L/M results below are mostly bare verb
  endings, not a meaningful "suffix"). This is a flag for you to review, not an automatic reject
  (that's the point of relaxing the old hard gate -- see §4 of the plan).
- **Fixture.** A small, hand-written, fake set of test words used in the automated tests
  (`src/test/affixes_test.py`, `affixrules_test.py`), as opposed to the real 167,000-word French
  lexicon. Fixtures let a test check one specific mechanism (e.g. "does a variant merge get
  dropped when it would create a collision?") in isolation, fast, without needing the real data.
  All 711 tests use fixtures; they don't prove anything about French, only that the code does
  what the plan says it should. The numbers in §2-3 below come from the real lexicon.
- **Seed / seed overlap.** `resources/affixSeeds.tsv` is a hand-curated list of ~150 affixes taken
  from the Pluvier/TAO tradition (see §4) -- known-good endings the scan should be checking against
  as a sanity list, not a ranking. "Seed overlap" (mentioned in older reports, not much used here)
  means "this candidate corresponds to one of those known affixes."
- **Credited saving / the curve / "@20" and "@30".** The objective being maximized: for every
  word, only its *best* selected rule gets credit (a word covered by two rules only counts once,
  at whichever rule saves it the most strokes) -- "word-once-credited." The **curve** is this
  running total after each of the 40 best rules is accepted, in order. **"@20"**/**"@30"** just
  means "read the curve's value after 20 (or 30) rules have been picked" -- 30 is the budget this
  run used (`RULE_BUDGET=30`), 20 is a smaller reference point to see how much of the value comes
  early.
- **L / M / H.** Three settings of the same three cost weights, requested by you (plan §U6) to see
  how the selection changes when word exceptions, exclusions and extra forms are penalized more
  or less heavily:
  - `EXCEPTION_ALPHA` -- how much one unit of excepted-word frequency costs.
  - `EXCLUSION_COST` -- flat cost per excluded spelling on a form.
  - `FORM_COST` -- flat cost per extra form added to a rule (more forms = harder to memorize).

  | setting | EXCEPTION_ALPHA | EXCLUSION_COST | FORM_COST | reading |
  |---|---|---|---|---|
  | **L** | 1.0 | 5 | 10 | today's values -- cheap to add forms/exclusions |
  | **M** | 1.0 | 50 | 100 | 10x more expensive to add a form or exclusion |
  | **H** | 2.0 | 150 | 300 | exceptions also cost 2x more, forms/exclusions 30x more |

  Higher settings push the selection toward fewer, simpler rules with fewer forms -- at the cost
  of covering fewer words per rule (each rule's own reach shrinks when growth is expensive), which
  is why H's rules are simpler (60 forms across 30 rules vs. L's 90) but paradoxically shows a
  *higher* credited total -- see the honest caveat in §3.

## 2. Pool and pipeline mechanics (numbers, explained)

- **Pool size 13,624 nodes, 3,089 anchors**, generated in 14 seconds (`GROWTH_MIN_EXPAND=5`,
  chosen after comparing 30/10/5 -- lower keeps growing the pool for no measurable gain past this
  point, see the plan's §3 step 2 budget).
- **1,101 anchors are variant merges** (fused spellings) that survived the "does fusing add new
  collisions?" test; **13 proposed merges were dropped** because fusing would have created new
  collisions between different words.
- **398 "key-collision renames."** Occasionally, growing two different anchors by one more
  syllable produces two children that would end up with the exact same internal key but cover
  *different* words -- this used to silently overwrite one with the other (a real bug found two
  sessions ago, called "F5" in the prior resume file, which had cost one node 78 of its 82 words).
  Now the second one is automatically renamed and kept. **0 overwrites** (checked by an assertion
  that halts the program if one ever happens).

## 3. What came out of the selection (per setting)

| | L (today's weights) | M | H |
|---|---|---|---|
| rules selected | 30 | 30 | 30 |
| total forms across all 30 rules | 90 (avg 3/rule) | 79 | 60 (avg 2/rule) |
| total exclusions | 20 | 15 | 5 |
| total word exceptions | 726 | 953 | 1,605 |
| rules flagged as pseudo-affixes (attestedShare<0.5) | 16 | 15 | 12 |
| worst rule's exception rate | 4.9% (under the 5% cap everywhere) | | |
| worst overlap between any two selected rules | 0.00 | 0.00 | 0.09 (still well under the 0.5 cutoff) |
| credited saving @20 rules | 50,134 | 55,988 | 77,716 |
| credited saving @30 rules | 61,377 | 68,811 | 97,877 |

**Read this carefully -- the "H looks best" reading is misleading.** H's higher saving total
comes packaged with more than double the word exceptions (1,605 vs. 726). The credited-saving
number only rewards strokes saved on *covered* words; it doesn't subtract anything for a word
that stays fully spelled out. A rule that's pickier about which words it touches (fewer forms,
so a narrower, cleaner pattern) can score *more* per word it does cover, while quietly leaving
more words as full exceptions. So the three settings are not simply "H > M > L" -- they're three
different trade-offs between coverage breadth and rule simplicity, and the right one depends on
how much you weigh "fewer rules to memorize" against "fewer words left unabbreviated." That's
exactly why the plan asked for a sweep instead of picking a number.

**Compared to the 2026-09-27 baseline** (before this rewrite, using the old A7 + territory-merge
machinery), the new pool is stricter about what counts as a real pattern, so totals aren't
directly comparable: 61,377 now vs. 73,765 then at L/30. 22 of the old top-30 rules are gone
(including the `ment`/`·°ment` twin -- now one rule -- and two "exception-patch" rules that used
to exist only to fix another rule's mistakes on a second key), replaced by 22 new ones (`pro-`,
`ce-`, `-nir`, `-voir`, `vou-`, and several more small prefixes).

## 4. Comparison against Pluvier / the TAO manual / OQLF

**What I actually had to compare against.** Pluvier itself (the closest prior-art project, a
French Plover dictionary generator, see `docs/PRIOR_ART.md`) is an unreleased work-in-progress
with no published dictionary file I could diff against -- I could not do a side-by-side word list
comparison with it. What I *could* check directly is `Tao.md` at the repo root: a full transcript
of "La TAO en français," the Québec court-reporter shorthand manual (the LaSalle/TAO method)
that Pluvier itself is explicitly built from, and that `resources/affixSeeds.tsv`'s seed list is
drawn from. I have not found a separate, distinct "OQLF abbreviation list" in this repo or online
during this session -- the OQLF (Office québécois de la langue française) is the language
authority that standardizes Québec French terminology in general, but the TAO manual is the
stenography-specific method, and it's what's actually available to compare against here. If you
have a specific OQLF document in mind, point me at it and I'll redo this comparison against it.

**What the TAO manual actually contains.** It documents roughly **218 separate "this spelling
gets this key" rules** across ~40 lessons (counted via its own `Les lettres.../Le
sténogramme...désigne(nt)` rule statements), each with its own worked examples and drill words.
That's the scale of a full professional theory built over months of instruction. Our 30-rule
budget is, deliberately, a much smaller slice -- the highest-value 30 for a 26-key board used by
an automated system, not a hand-taught multi-year curriculum.

**Specific overlaps I checked by hand** (not exhaustive):

- **`-ment`.** TAO assigns **two separate keys**: `-PLT` for plain `-ment`, and a *different*
  key `-FPLT` for `-vement`. That is, TAO's own reference system does exactly the "two keys, one
  territory" thing that this whole plan (and the 2026-09-28 territory-merge bugfix before it) was
  built to prevent in our system. This is a useful sanity check both ways: it confirms `-vement`
  really is a distinct-enough case that a professional theory treats it separately (so if our
  fused `ment|mant|...` rule turns out to abbreviate `-vement` words worse than plain `-ment`
  ones, that would match TAO's own judgment, not contradict it) -- and it confirms our system's
  stricter "one territory, one key" rule is a deliberate design choice to fit a 26-key board, not
  an attempt to replicate TAO's key budget one-for-one.
- **`-tion` family.** TAO uses **at least four separate keys** for what we fused into one rule:
  `-GS` (`-tion`/`-tial`/`-tiel`), `-GZ` (`-zion`), `-BGS` (`-cation`), plus separate `-GS`/`-GZ`
  marks for `-cien`/`-cienne`. Our rule 2 (`ccion|cion|cyon|sion|ssion|tion|tions`, plus grown
  forms for `-cation`-style endings) is trying to cover several of these in one key with multiple
  forms -- a genuinely different strategy from TAO's "one ending, one key" approach, made possible
  by the same "share a key across close forms" machinery Phase 4 already does.
- **`-ité`/`-ilité`/`-bité`/`-bilité`.** TAO gives these **four separate keys** (`ITD`, a
  dedicated one for `-ilité`, `-BT`, `-BLT`), plus yet another (`-FT`) for `-vité`/`-cité`. Our
  system instead grows one `té` anchor down through `·lité -> ·[...]lité -> ·[...]bilité ->
  ·[...]sabilité` as nested forms of the *same* rule (confirmed present, acceptance check 3).
  Again: same territory, different strategy (one key with many forms, vs. many keys).
- **`-logie`/`-logue`/`-logiste`/`-logique`.** TAO gives these four distinct, separate keys too
  (`LO*EG`/`LO*IG`/`LOYIS`/`LOYIK`) -- this is exactly the kind of "sibling family, but not a
  grow-lineage of each other" case our own report lists under "Sibling pairs...out of scope for
  v1." TAO's solution (one shared onset + a distinguishing mark) is a plausible model for how we
  might eventually handle these families, but it's explicitly not attempted in this rewrite.
- **Prefixes `con-`/`com-`, `multi-`, `inter-`, `ex-`.** TAO gives each its own dedicated brief,
  same as our prefix anchors do (`in`, `pro`, `im`, `ex` all made it into our L/M top-30). One gap:
  `multi-` is one of the 16 k>=2 seeds from `affixSeeds.tsv` that our new pool doesn't produce a
  node for at all (acceptance check 2) -- despite TAO treating it as a real, teachable prefix with
  38 lemma-form words in our own lexicon. Worth a follow-up look at why it's not surviving the
  stem-roots threshold.

**Bottom line on coverage.** This rewrite is not attempting TAO-level completeness (218 documented
rules vs. our 30), and it isn't meant to be a copy of TAO's specific key choices -- TAO fragments
many endings across separate keys where our system tries to fuse related endings under fewer
keys with multiple forms, which is a genuinely different design bet suited to a smaller keyboard
and an automated pipeline instead of a taught curriculum. Where I checked by hand, the *territory*
our top rules cover (ment, tion, ité, prefixes like in-/ex-/con-/multi-) does line up with TAO's
own judgment about what's worth a dedicated abbreviation -- that's reassuring. What I have **not**
done is a systematic diff: taking TAO's full ~218-rule list and checking, one by one, how many
have *some* representation (fused into a form of a broader rule, or as a still-unselected
candidate in the pool of 3,089 anchors) versus genuinely missing. That would be the natural next
measurement if you want a real coverage number instead of spot checks.

## 5. Open decisions for you

1. **Which weight setting** (L, M, H, or another point) -- see §3's caveat before picking on the
   raw "credited saving" number alone; it's not a like-for-like measure across settings.
2. **The pseudo-affix rules** (`attestedShare` < 0.5, e.g. `in`, `der`, `er`, `nir`, `voir`, `ve`
   at L): keep them as real rules, or treat low attested share as a reason to drop/reshape them?
3. **The 16 unreached seeds and the 74 old-A7 nodes covered below 0.9** (plan acceptance checks
   1-2): worth a follow-up investigation, or accepted as the cost of removing A7/lemma-gating?
4. **TAO-style coverage measurement** (§4's last paragraph): worth doing as a real next step, or
   is the spot-check above enough?

Nothing in `src/`, `util/`, or the pipeline is committed. The branch is `affix-abbreviation-rules`.

## 6. Systematic diff against OQLF and TAO/Pluvier (2026-09-29)

Local copies + note: `resources/reference/` (README.md). Generator `scratch/affix_reference_diff.py`,
full per-affix table `scratch/affix-reference-diff.md`. This corrects §4: an OQLF table *does* exist
(27 prefixes, 17 suffixes) and the Pluvier TAO rule list is `TAO_rules.md`; both are now compared
mechanically instead of by spot check.

Verdicts (anchor pool of 3,089; selected = any of L/M/H top-30):

| list | affixes | selected as a root | inside a grown form of another rule | candidate anchor, not selected | no k=1 anchor (only grown nodes) | nothing in pool |
|---|---|---|---|---|---|---|
| OQLF | 51 rows | 9 | 8 | 16 | 10 | 8 |
| TAO/Pluvier seeds | 148 | 11 | 6 | 58 | 47 | 26 |

Why the OQLF affixes are missing, in order of weight:

1. **Frequency vs. a 30-rule budget (most of the "unselected candidates").** -able (rank #287 by
   anchor frequency), -age (#362), -ique (#1389), -iste, -isme, -ard, -eux, trans- (#277), pan- all
   pass every safety test (exception rate 0%, attestedShare 0.9-1.0) and simply score below the
   top 30, which are dominated by short high-frequency syllables (ment, tion, de, in, re, der...).
   Nothing conflicts; they lose on value. OQLF affixes are *productive*, not *frequent*.
2. **Anchor definition (single syllable) fragments multi-syllable affixes.** anti-, inter-,
   anté-, extra-, multi-, semi-, post-, ultra-, pluri-, -erie, -ive, -euse and TAO's -cation,
   -vité/-cité, -logie/-logique, -ration have no k=1 anchor: they exist only as grown nodes
   (e.g. inter- 466 carriers, anti- 374, -cation 199), and grown nodes can never be roots.
   -eur is worst: the k=1 `eur` anchor has freq 22 because the real mass sits under teur/leur/
   deur/... onset-specific endings; likewise -able (a+ble). This is a design consequence of the
   "single-generator" rule, not a data verdict: a genuinely useful affix can be structurally
   ineligible. multi- (flagged last session) has no node at all: 38 lemma-form words, below the
   growth/stem-roots thresholds.
3. **Pseudo-affix flag.** pan- (attested 0.06), -ien (0.09), -if (0.00) fail the attested-share
   screen (their leftover stems are not words) -- a real filter, but note -ien/-if are genuine
   OQLF suffixes whose bare-spelling anchors are just mostly verb/noun fragments.
4. **Conflicts / exception rate: essentially never the reason** (0% everywhere in the table;
   the 5% cap and the rival resolution do not bind for any reference affix).
5. **Absorbed elsewhere:** ex-/dé-/dis-/in-/re-/pré-, -ment, -té, -er are selected; sur-, sub-,
   mé-, co-, auto-, -ant, -ion, -ure appear only inside a grown form of another rule (a
   shared key, not a dedicated one).

TAO-specific: TAO's own multi-key splits (-ité/-ilité/-bité/-bilité, -tion/-zion/-cation) show up
as "no k=1 anchor" because our nodes for them are k>=2 grown forms; the 26 "nothing in pool" rows
are mostly the phonetic-cluster briefs (-rbe, -rne, -ande, -cte, -ntre...), which are not
orthographic affixes and are out of scope by design.

## 7. The four open questions, revisited with this evidence

1. **Weight setting.** Still a trade-off (§3); the reference diff does not change it. If the goal
   is "cover what teachers call affixes", none of L/M/H reaches OQLF's productive set -- see 2.
2. **Pseudo-affixes** (`der`, `er`, `nir`, `voir`, `in`, `ve`): the diff sharpens the question --
   the budget is spent on bare-syllable fragments while attested, teachable affixes (-able, -age,
   -iste, -ique, trans-) score well on every quality gate and lose only on raw frequency. A
   value weighting that rewards attestedShare (or a small reserved slice of the 30 for
   OQLF-attested affixes) is the lever; I recommend testing it rather than dropping the
   pseudo-affixes outright.
3. **Unreached seeds / old-A7 nodes:** now explained per affix (§6, item 2): mostly the
   single-syllable anchor rule. Candidate fix: allow a curated multi-syllable anchor list (like
   the etymological groups already permitted) seeded from OQLF + TAO -- anti-, inter-, multi-,
   semi-, -eur, -able, -ique, -cation, -vité/-cité -- rather than relaxing the generator.
4. **TAO-style coverage measurement:** done here (§6) and should be rerun after every selection
   change; the note in `resources/reference/README.md` records that as standing practice.
