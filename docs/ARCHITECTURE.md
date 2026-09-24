# Architecture

Stenalgo is a stenotype keyboard layout and stenographic theory generator for French. It
uses constraint programming (Google OR-Tools CP-SAT solver) to optimize steno keyboard key
assignments, minimizing both physical finger strain and the mental complexity of the
resulting theory. The primary target keyboard is the Starboard, a 26-key custom steno
keyboard: 22 phoneme keys split into three banks (onset, nucleus, coda) plus 4 reserved
keys. The output is a full French theory — a Plover dictionary and system plugin, plus data
for a practice web app — built from the Lexique383/LexiqueInfra lexicons through an
eight-stage pipeline.

## Stages at a glance

Eight stages turn the source lexicons into the exported theory. The full per-call detail —
every transformation, threshold and dataset state — is in [PIPELINE.md](PIPELINE.md).

1. **Lexicon Building (S1)** (`python lexique.py`) — merges Lexique383 and LexiqueInfra
   into `resources/LexiqueMixte.tsv` (136,456 rows with frequencies and phoneme/grapheme
   syllable breakdowns); applies `lexiconExclusions.tsv` and the 1990-reform rewrites.
2. **Synthetic Lexicon Building (S2)** (hand-run `--apply` scripts) — appends missing verb,
   noun and adjective paradigm forms to `resources/LexiqueSynthetic.tsv` (42,225 rows).
3. **Dictionary Loading (S3)** (first half of `python -m util.build_phonetic_theory`) — reads both lexicons
   into 167,639 `Word`s (identity merge), indexes them by spelling and lemma, builds the
   syllable inventory; cached in `Dictionary.pickle`.
4. **Keyboard Layout Optimization (S4)** — CP-SAT solve that assigns phonemes to keys per
   syllabic bank, producing `starboard3h.json`. Real but rarely run: the layout statistics
   recompute on every fresh rebuild, and the solver itself runs only through
   `python -m util.optimize_keyboard`.
5. **Phonetic Theory Building (S5)** (second half of `python -m util.build_phonetic_theory`) — the phonetic theory:
   one phonetic stroke sequence per syllable chain, so homophones share raw stroke
   sequences; cached in `PhoneticTheory.pickle`.
6. **Same-Lemma and Grammatical-Category Disambiguation (S6)** — separates the Homophone
   Groups (same `lemmeGramCat`, same canonical strokes) in three phases:
   Discriminating-Feature Elicitation (Elicitation Phase), Discriminating-Feature Grouping
   (Grouping Phase) and Discriminating-Feature Stroke Realization (Realization Phase). Each
   Keypress Group becomes one coda-bank feature discriminating stroke. Must-stay-green
   regression: 0 residual same-lemmeGramCat collisions.
7. **Different-Lemma or Grammatical-Category Disambiguation (S7)**
   (`python -m util.build_disambiguated_theory`, `Dictionary.buildDisambiguatedTheory`)
   — star/hash marks on the reserved `*`/`#` keys for lemma-homophone groups
   (ver/vert/verre, appel/appelle), producing the disambiguated theory.
8. **Theory Export (S8)** (`python -m util.export_*`) — two branches: Plover (dictionary,
   key table, system plugin) and steno-trainer (keyboard legend, word drill, sentences,
   definitions). Nothing reads `disambiguated_theory.tsv`; every exporter recomputes the disambiguated theory.

## Design rationale

### What is being minimized

The generator scores keymap/theory pairs on two families of strain (the project's founding
objective).

**Finger strain** — the average number of keystrokes must be minimized:

- Strokes containing fewer keystrokes are preferable
- Words containing fewer strokes are preferable
- Common words should contain fewer strokes than rarely used words
- Movement of fingers should be minimized
- Pressing fewer keys per finger is preferable

**Mental strain** — the mapping of keys to the sounds they represent must be coherent:

- Phonemes must have a maximum of one canonical representation on the keyboard, one key-set
  of a stroke (never systematically validated — the open phoneme-layer re-validation phase,
  see `ROADMAP.md`)
- Syllables must have the minimum number of stroke representations (variations) on the
  keyboard to distinguish between the different spellings
- Rules (stroke variations) to distinguish between spellings of a syllable must be
  consistent across a maximum of words sharing that syllable
- As much as possible, the order in which phonemes are typed must match the order they
  occur in the syllable

Words that do not respect an established rule are deemed an exception; the number of
exceptions must be minimized.

### The Starboard keymap

`src/keyboard.py` describes the Starboard: which keypresses each finger can physically
make, with penalty scores loosely corresponding to the strain they induce. The layers below
are the 1-keypress and 2-keypress phoneme assignments of the current layout, generated from
`starboard3h.json` by `Starboard.printLayout` (src/keyboard.py:395) — regenerate them after
any layout change with `python -m src.keyboard starboard3h.json`. (The 3-keypress and
4-keypress layers hold only rare multi-key presses:
`2 5 / 25 25` in layer 3, `1 1 / 1 1` in layer 4.)

```
┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓         ┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓
┃     ┃  k  ┃  p  ┃  m  ┃  R  ┃     ┃         ┃     ┃ jbw ┃  k  ┃  t  ┃  n  ┃ ZG  ┃
┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫     ┃         ┃     ┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫
┃     ┃  s  ┃  v  ┃  t  ┃ wNG ┃     ┃         ┃     ┃  s  ┃  d  ┃  R  ┃  l  ┃  m  ┃
┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━┳━┻━━━┳━┻━━━┓ ┏━━━┻━┳━━━┻━┳━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛
  ┃  1-key phonemes layer   ┃ @9  ┃  a  ┃ ┃  i  ┃ eO  ┃
  ┗━━                       ┗━━━━━┻━━━━━┛ ┗━━━━━┻━━━━━┛

┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓         ┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓
┃     ┃ gf  ┃ fdS ┃ Sln ┃ nj  ┃     ┃         ┃     ┃ vp  ┃ pg  ┃  N  ┃ Nz  ┃  S  ┃
┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫     ┃         ┃     ┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫
┃     ┃ gb  ┃ bdZ ┃ Zlz ┃ zj  ┃     ┃         ┃     ┃ vf  ┃ fg  ┃     ┃  z  ┃  S  ┃
┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━┳━┻━━━┳━┻━━━┓ ┏━━━┻━┳━━━┻━┳━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛
  ┃  2-key phonemes layer   ┃°8yu ┃°8§o ┃ ┃ y§E ┃ uoE ┃
  ┗━━                       ┗━━━━━┻━━━━━┛ ┗━━━━━┻━━━━━┛
```

Left hand = onset bank (keys 2-9), thumbs = nucleus bank (11-14), right hand = coda bank
(16-25); each cell lists the phonemes whose stroke includes that key (a phoneme needing two
keys appears in both cells). The reserved keys (`*` = 10, `#` = 15, plus 0 and 1 held for a
possible third mark) sit between the banks and never carry phonemes.

### Phoneme order: a worked example

Ordered biphoneme frequencies tell in which left-to-right order the phonemes should sit on
the keymap so that typed key order matches spoken order within the onset, nucleus and coda
banks; single-phoneme frequencies tell how important each phoneme is. Below is **a worked
example from one Keyboard Layout Optimization (S4) run — not current output** (the greedy
order search is seed-dependent and reruns give slightly different orders). Bar heights are
individual phoneme frequencies per group; negative "disordered" scores are the summed
frequencies of biphonemes that would land in the wrong order.

```
Left hand optimization :

Best order (ordered score 91215.1, disordered score -1400.5):
 dksptSgNxvZmzfnblRwj

Left hand (syllable onset) consonant optimization :
┃                  R   ┃   ┃
┃                  R   ┃   ┃
┃                  R   ┃   ┃
┃     t            R   ┃   ┃
┃   spt            R   ┃   ┃
┃   spt      m     R   ┃   ┃
┃ dkspt    v m    lR   ┃   ┃
┃ dkspt    v m    lR j ┃   ┃
┃ dkspt    v m fnblR j ┃   ┃
┃ dksptSg  vZmzfnblRwj ┃   ┃
┃ dksptSgNxvZmzfnblRwj ┃ G ┃
┗━━━━━━━━━━━━━━━━━━━━━━╋━━━┛
               ordered ┃ floating 

Right hand optimization :

Best order (ordered score 15522.8, disordered score -5759.7):
 wjbpfvdsktgRlzNmnSZ

┃            R        ┃   ┃
┃            R        ┃   ┃
┃            R        ┃   ┃
┃            R        ┃   ┃
┃            R        ┃   ┃
┃            R        ┃   ┃
┃            R        ┃   ┃
┃        s t R        ┃   ┃
┃        s t Rl       ┃   ┃
┃  j    dskt Rl       ┃   ┃
┃ wjbpfvdsktgRlzNmnSZ ┃ G ┃
┗━━━━━━━━━━━━━━━━━━━━━╋━━━┛
              ordered ┃ floating 

Vowel optimization :

Best order (ordered score 6599.0, disordered score 0.0):
 8§i5ea9o2@OE

┃      a       ┃      ┃
┃      a       ┃      ┃
┃     ea       ┃      ┃
┃   i ea     E ┃      ┃
┃   i ea     E ┃      ┃
┃   i ea     E ┃      ┃
┃   i ea   @ E ┃      ┃
┃   i ea o @ E ┃      ┃
┃  §i ea o @ E ┃ °uy  ┃
┃  §i5ea o @OE ┃ °uy  ┃
┃ 8§i5ea9o2@OE ┃ °uy1 ┃
┗━━━━━━━━━━━━━━╋━━━━━━┛
       ordered ┃ floating 
```

The 25 % disordered ratio on the right hand is mostly the "R" biphonemes, since R can come
before or after other consonants (`tR` "montre" frequency 4110 vs `Rt` "forte" 1822; `dR`
"tondre" 2265 vs `Rd` "horde" 1339); the algorithm picks the least penalizing option.
There is no single best order: phonemes that never co-occur in a syllable are free to
swap. The pairwise order matrix below (same run) shows this slack — for the "v" line, `v`
may sit anywhere after `k`/`s` (`<<`) and anywhere before `l`/`R`/`w`/`j` (`>>>>`):

```
   ↓↓             ↓↓↓↓
 ┃dksptSgNxvZmzfnblRwjG
━╋━━━━━━━━━━━━━━━━━━━━━
d┃=>>><=====>>=====>>>=
k┃<=>>><===><>>>>=>>>>=
s┃<<=>><>==>=>=>>>>>>>=
p┃<<<=><=======>>=>>>>=
t┃><<<=>>====>>><>>>>>=
S┃=>>><======>==>=>>>>=
g┃==<=<======>>=>=>>>>=
N┃==================>==
x┃==================>==
v┃=<<=============>>>>=  ←←
Z┃<>================>>=
m┃<<<=<<<=======>===>>=
z┃=<==<=<=========>>>>=
f┃=<<<<===========>>>>=
n┃=<<<><<====<===>>>>>=
b┃==<=<=========<=>>>>=
l┃=<<<<<<==<==<<<<==>>=
R┃<<<<<<<==<==<<<<==>>=
w┃<<<<<<<<<<<<<<<<<<===
j┃<<<<<<<==<<<<<<<<<===
G┃=====================
```

This order analysis (`Syllable.optimizeBiphonemeOrder`, src/grammar.py:644) still runs on
every fresh rebuild as part of the layout statistics; its pairwise matrix is the order term
of the Keyboard Layout Optimization (S4) solver.

### Recorded design decisions

Recorded so they are not re-litigated each session (they originate from the ROADMAP's
design-decision log); reworded to the current vocabulary.

1. **The reserved-key budget is 2 keys, not 4.** Of the Starboard's 4 reserved keys, only
   `*` (key 10) and `#` (key 15) are guaranteed to remain available long-term — one more
   than a traditional Ireland layout effectively offers, whose only free non-phoneme key is
   `*` (its `#` is the number bar). The other two reserved keys (0 and 1) exist today but
   cannot be counted on.
2. **`*`/`#` serve lemma-homophones only.** Two keys give 4 modifier values (no mark, `*`,
   `#`, `*#`). No mark goes to the most frequent member of a lemma-homophone group, so up
   to 4 members per group are differentiable this way; larger groups (ver, vert, verre,
   vers, vair…) need escalated codes — repeated `*#` symbols beyond the first, which become
   \*/# marker strokes. These keys are explicitly **not** spent on conjugation (that is
   Same-Lemma and Grammatical-Category Disambiguation (S6)'s job) or on prefixes.
3. **Rejected approach (superseded 2026-09-18 by the elicitation-first pivot):** solving
   same-lemma homophones with solver-chosen "meaningful" phoneme-key strokes. The user's
   own elicited feature presses chose the features instead; see the next subsection.
4. **Prefix formation is a confirmed but unbuilt densification goal** — see `ROADMAP.md`.
5. **Dual-target architecture confirmed:** a large precomputed static dictionary for
   Plover, and a small dictionary plus runtime rule engine for a microcontroller build
   modeled on Javelin. Both consume the same underlying paradigm-table data.

### Why elicitation, not solver-picked features

Same-Lemma and Grammatical-Category Disambiguation (S6) was originally designed like the
rest of the pipeline: let the solver pick each word's discriminating features, then shape
constraints around the outcome to make it learnable. A design walkthrough of the *parler*
paradigm made the flaw obvious — the solver could only pick physically feasible feature
sets, not ones a human can recall while writing. Working through the forms: "je parle" is
phonology only (indicatif présent is the default expectation, typed bare); "tu parles"
presses the person feature matching the written *-s*, which is what the writer is actually
conscious of; "ils parlent" presses a person+plural combination that may be over-specific
(one feature alone might not discriminate) yet must still produce the right spelling;
"que je parle" may press the subjonctif feature defensively even though it is spelled like
the default form; and the participle/infinitive forms each take gender/number or
tense features — or nothing, when the bare form already resolves. The 2026-09-18
elicitation-first pivot inverted the design: the user's own writing reflexes are the spec,
collected pair by pair in `elicitation_answers.json`, and only what remains — grouping the
atomic features onto Keypress Groups — is optimized afterwards.

### Suffixes and prefixes

- **Suffixes: solved.** Grammatical suffixes (person, number, tense, gender…) are exactly
  what the feature discriminating strokes of Same-Lemma and Grammatical-Category
  Disambiguation (S6) discriminate; see
  [docs/specs/discriminating-features.md](specs/discriminating-features.md).
- **Prefixes: open.** Composing a prefix stroke with a base word's outline instead of
  enumerating every prefixed form is an unbuilt densification goal; see `ROADMAP.md`.

## Data model

### Phonology (`src/grammar.py`)

- **`Phoneme`** — a single-character X-SAMPA sound (the Lexique variant that gives every
  phoneme one ASCII character), with an occurrence frequency. French uses 16 nucleus
  (vowel) phonemes (`aeiE@o°§uy5O9821`, where `8` = ɥ) and 20 consonant phonemes
  (`RtsplkmdvjnfbZwzSgNG`), plus a temporary `x`. `8` is a nucleus phoneme; `j` and `w`
  are consonants.
- **`Biphoneme`** — an ordered pair of phonemes co-occurring in one syllabic part, with
  its frequency (the signal behind the phoneme-order term).
- **`Multiphoneme`** — an ordered group of phonemes found together in one part (onset,
  nucleus, coda) of a syllable; the unit the ambiguity term reasons about.
- **`PhonemeCollection` / `BiphonemeCollection` / `MultiphonemeCollection`** — the
  inventories with their frequency sorts and the greedy order search
  (`BiphonemeCollection.optimizeOrder`).
- **`Syllable`** — onset + nucleus + coda, parsed from the lexicon's `syll_cv`: consonants
  before the first vowel go to the onset, every vowel to the nucleus, every consonant
  after the first vowel to the coda; a vowel-less syllable puts all its consonants in the
  onset. Carries class-level collections (`allPhonemeCol`, `phonemeColByPart`,
  `biphonemeColByPart`, `multiphonemeColByPart`) that accumulate the corpus-wide syllable
  statistics, plus `SyllableCollection`, the inventory `buildPhoneticTheory` looks syllables up in.

### The Word (`src/word.py`)

The `Word` dataclass is the lexicon entry:

- `ortho` (spelling), `phonology` (X-SAMPA string), `lemme` (lemma), `gramCat` (a `GramCat`
  enum value — 22 categories such as `NOM`, `VER`, `ADJ:pos`, `PRO:per`), `orthoGramCat`
  (all categories of words sharing the spelling), `gender` and `number` (noun/adjective),
  `infoVerb` (conjugation tags such as `ind:pre:1s`).
- `rawSyllCV` / `rawOrthosyllCV` (the phoneme/grapheme syllable breakdowns from Lexicon
  Building (S1)) and their parsed forms `syllCV` / `orthosyllCV`.
- `frequencyBook` and `frequencyFilm`, the two corpus frequencies (written books, film
  subtitles). `frequency` is set to the film frequency only — book frequency is read but
  never used (a mix formula sits commented out in `Word.__post_init__`).
- Derived: `lemmeGramCat` (the `"lemme_GramCat"` key, e.g. `rucher_NOM`, that almost every
  "same lemma" test actually uses) and `_hash` (a per-process salted hash of the identity
  tuple `(ortho, phonology, lemme, gramCat, gender, number)`; equality and pickling go
  through it). Dictionary Loading (S3)'s identity merge folds later lexicon rows with a
  known identity into the first Word, merging only verb tags.

### The keyboard (`src/keyboard.py`)

- Type aliases: `Keypress` = the keys one finger presses together, `Stroke` = the key
  indices pressed at once (one per syllable, plus extra strokes), `Strokes` = the tuple of
  strokes for a whole word.
- **`Keyboard`** is the abstract base (key template, finger assignments,
  `maxKeysPerPhoneme` constraints, stroke enumeration and costing). **`Starboard`** is the
  26-key implementation: 4 reserved keys (0, 1, 10, 15) excluded from phonemes — 10 (`*`)
  and 15 (`#`) carry the star/hash marks, 0 and 1 are held for a possible third mark —
  leaving 22 phoneme keys in three banks: onset 2-9 (left fingers), nucleus 11-14 (thumbs),
  coda 16-25 (right fingers), with at most 5/4/5 keys per phoneme.
- **`FingerWeights`** is the cost scale per finger situation (e.g. pinky 1-key home 125,
  off-home 150; index 1-key home 100; thumb 1-key 100; multi-key presses cost more).
  **`PositionWeights`** (`_possibleKeypress`) maps each finger to the legal key
  combinations it can press and their cost — this is also the feasibility oracle: a stroke
  whose per-finger key union is not a legal keypress is an illegal stroke
  (`getStrokeCost` returns `None`).
- `getStrokeCost` sums the finger costs, adds zig-zag and row-gap shape penalties for
  onset/coda strokes, and applies a `0.85^fingers` discount for using multiple fingers.
- `starboard3h.json` persists the layout as `phonemesAssignedToStroke` (48 layout entries;
  some entries are shared by rare phonemes).

### Solver constants (`src/cpsatsolver.py`)

Keyboard Layout Optimization (S4) solves one independent CP-SAT model per syllabic part
(onset, nucleus, coda). Each phoneme gets one stroke of its bank and the objective
minimizes the sum of three terms:

| Constant | Value | What it weights |
|---|---|---|
| `AMBIGUITY_PENALTY` | 30000 | The ambiguity term: when two phoneme groups that occur in real words would end up with the same key-set, the words that differ only by those groups become indistinguishable; the cost is that collision's frequency mass (the syllabic-part ambiguity) × 30000. |
| `ORDER_PENALTY` | 500 | The phoneme-order term: pairs whose keys read left-to-right in the order they are usually spoken earn a bonus; pairs in the wrong order pay a penalty (from the pairwise order matrix). |
| `STROKE_ASSIGNMENT_PENALTY` | 1 | The ergonomic term: each phoneme's frequency times the physical cost of its stroke, so frequent phonemes get the easiest keys. |
| `SOLVER_TIME` | 90.0 s | Solver time limit, per syllabic part. |
| `MAX_MULTIPHONEMES` | 2000 | Only the 2,000 most ambiguous phoneme-group pairs get an explicit ambiguity term. |

Because frequencies are per million, one ambiguous pair outweighs almost any ergonomic or
order gain — the three weights encode "ambiguity first, then order, then ergonomics".

## Artifacts

What each root-level data file is, whether it is tracked in git, and the command that
rebuilds it (full rebuild order in [PIPELINE.md](PIPELINE.md) §How to run a full rebuild).
After any lexicon or layout change, first `rm -f Dictionary.pickle PhoneticTheory.pickle` —
the pickle caches are never checked for staleness.

### Tracked outputs and inputs

| File | What it is | Rebuilt by |
|---|---|---|
| `resources/LexiqueMixte.tsv` | Mixed lexicon: 136,456 rows × 12 columns (frequencies, phoneme + grapheme syllable breakdowns) | `python lexique.py` (Lexicon Building (S1)) |
| `resources/LexiqueSynthetic.tsv` | Synthetic rows: 42,225 generated paradigm forms | hand-run `python -m util.completeVerbParadigms --apply`, `python -m util.generateMissingNomAdjForms --apply`, `util/fix*.py` (Synthetic Lexicon Building (S2)) |
| `starboard3h.json` | The keyboard layout (26 keys, 48 layout entries) | rarely: `python -m util.optimize_keyboard` writes `starboard3h_optimized.json`; adopting it into the seed is deliberate; see PIPELINE.md, Keyboard Layout Optimization (S4) |
| `elicitation_answers.json` | The elicitation answers (200 oppositions): the only hand-authored input of Same-Lemma and Grammatical-Category Disambiguation (S6) | by hand, through the questionnaire page (Answer Collection) |
| `conjugation_disambiguation_order.txt` | The precedence spec: intended feature-press precedence | hand-authored; checked by `python -m util.check_conjugation_disambiguation_order` |
| `keypress_groups.json` | The Keypress Groups (K=7, proven minimal) and their features | `python -m util.build_keypress_groups` (Grouping Phase) |
| `realization_report.json` | The realization report: chosen coda keys per Keypress Group, costs, residual buckets | `python -m util.build_realization_report` (Realization Phase, report build) |
| `plover_stenalgo_dictionary.json` | Plover dictionary: 163,238 RTFCRE steno → spelling entries | `python -m util.export_plover_dictionary` (Theory Export (S8)) |
| `plover_stenalgo/plover_stenalgo/_generated_keys.py` | Plover key table (KEYS, implicit-hyphen keys, Gemini PR keymap) | `python -m util.export_plover_system` (Theory Export (S8)) |
| `steno-trainer/public/data/*.json` | Trainer data: keyboard-layout, practice-words, practice-sentences, definitions | `python -m util.export_keyboard_layout`, `python -m util.export_practice_words`, then `python -m util.export_practice_sentences`, then `python -m util.export_definitions` (Theory Export (S8)) |
| `excluded_words.txt` | Excluded words (44 spellings dropped in Dictionary Loading (S3)) | hand-maintained input |
| `resources/reform1990.tsv` | 1990-reform spelling table (source input of the reform rewrites and doublet pairs) | hand-maintained input |

### Gitignored caches and regenerables

| File | What it is | Rebuilt by |
|---|---|---|
| `Dictionary.pickle` | Word list + indexes + syllable and layout statistics (57.8 MB) | `python -m util.build_phonetic_theory` on a cache miss (Dictionary Loading (S3) + the layout statistics) |
| `PhoneticTheory.pickle` | The phonetic theory (52 MB) | `python -m util.build_phonetic_theory` on a cache miss (Phonetic Theory Building (S5)) |
| `questionnaire.json` | Questionnaire items (200) | `python -m src.elicitation` (Questionnaire Generation) |
| `resolved_press_sets.json` | Resolved discriminating feature sets (47,828 groups, ~32 MB) | `python -m src.elicitation` (Press-Set Resolution) |
| `elicitation_questionnaire.html` | The Answer Collection questionnaire page | `python -m util.build_questionnaire_page` |
| `phonetic_theory.tsv` | Human view of the phonetic theory | written by `python -m util.build_phonetic_theory` on every run (pickle hit or miss) |
| `disambiguated_theory.tsv` | Human view of the disambiguated theory (read by nothing — every exporter recomputes it) | `python -m util.build_disambiguated_theory` (Different-Lemma or Grammatical-Category Disambiguation (S7)) |
| `conjugation_disambiguation_report.json` | Precedence-spec check report | `python -m util.check_conjugation_disambiguation_order` |
| `morphalou/Morphalou3.1_CSV.csv` | External Morphalou 3.1 download (not in git; [Ortolang repository](https://repository.ortolang.fr)), used optionally by NOM/ADJ gap generation | download by hand; `python -m util.generateMissingNomAdjForms --morphalou PATH` |

Diagnostics, also gitignored: `ambiguity_report.tsv` is written by hand-running
`python src/ambiguitychecker.py` after Phonetic Theory Building (S5) — it is not part of
any rebuild.

## Deployment notes

- The Plover plugin directory `plover_stenalgo/` is tracked here, but Plover's git-based
  plugin installer needs a real git remote: it must be hand-synced to the separate GitHub
  mirror, github.com/jf5pier/stenalgo-plover, whenever its source changes.
- The steno-trainer deploys to GitHub Pages automatically on push to `main` when anything
  under `steno-trainer/**` changes (`.github/workflows/deploy-steno-trainer.yml`).

## Further reading

- [PIPELINE.md](PIPELINE.md) — the full per-call pipeline: every transformation, threshold
  and dataset state, stage by stage.
- [GLOSSARY.md](GLOSSARY.md) — the canonical vocabulary, with legacy-name mappings.
- [specs/star-hash-marking.md](specs/star-hash-marking.md) — spec of Different-Lemma or
  Grammatical-Category Disambiguation (S7).
- [specs/discriminating-features.md](specs/discriminating-features.md) — spec of
  Same-Lemma and Grammatical-Category Disambiguation (S6).
- [PRIOR_ART.md](PRIOR_ART.md) — survey of related steno-theory projects.
- `ROADMAP.md` — the forward-looking plan and open decisions.
- `TODO.md` — suspected bugs and queued follow-ups.
