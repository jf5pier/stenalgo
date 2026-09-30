# Spec: lesson generator

Scope: the trainer branch of Theory Export (S8). `util/export_lessons.py` generates
`steno-trainer/public/data/lessons.json`: a fixed progression of French lessons
(newly introduced keys + a French rule text + example words) in the spirit of
`resources/reference/Pluvier_TAO_rules.md`, so a learner no longer meets the whole
10,000-word pool on day one. The trainer side (an Elm `Lessons` mode that shows the
lesson intro then reuses the Words-mode drill engine) is described here only where it
constrains the JSON.

Inputs: `starboard3h.json`, the phonetic and disambiguated theories
(`util/_theoryio.loadPhoneticAndDisambiguatedTheory`), `realization_report.json`
(its `keypressGroups` carry the markers, `affectedWords` and `chosenKeys` of the
accord/verbe groups — `keypress_groups.json` holds only the Grouping Phase
constraints), `resolved_press_sets.json`. The spec of the marks and
groups themselves is [star-hash-marking.md](star-hash-marking.md) and
[discriminating-features.md](discriminating-features.md). Terms are defined in
[GLOSSARY.md](../GLOSSARY.md); the pipeline view is
[PIPELINE.md §Theory Export (S8)](../PIPELINE.md#theory-export-s8).

## 1. Purpose and determinism

Lessons are **generated, never hand-written**. Every string a learner sees — section
titles, rule texts, examples — is produced by the templates of §7 filled from the
layout and the theories. Nothing is edited by hand in `lessons.json`; a correction
means fixing the generator and regenerating.

Regeneration from the same inputs must be **byte-identical** (the md5 check used for
the other trainer exports applies). Therefore:

- every list is produced by an explicit final sort; no output order may derive from
  `set`/`dict` iteration order or from pickle insertion order;
- no randomness, no timestamps, no environment-dependent values;
- output is written `json.dump(..., ensure_ascii=False, indent=1)` plus a trailing
  newline, in the exporter house style (docstring with a `Run:` line, `main()`,
  `print(f"Wrote ...")`).

Any change to `starboard3h.json`, the lexicons, `elicitation_answers.json`,
`keypress_groups.json` or `resolved_press_sets.json` legitimately changes the output;
that is the point of generating. The exporter only reads existing caches — it never
deletes or rebuilds a pickle.

## 2. Finger-complexity ordering

### 2.1 Keypresses and their parts

A **keypress** is the set of keys one finger presses: the unit of learning. The
layout's keypresses are the keys of `starboard3h.json`'s `phonemesAssignedToStroke`
(e.g. `"(9,)"` → `["w", "N", "G"]`); a keypress's **phoneme set is atomic** — key 9
introduces `w`, `N` and `G` together. A keypress's **part** (nucleus / onset / coda)
is read off `Starboard.keyIDinSyllabicPart` by its first key (a keypress never mixes
parts; the stroke builder enforces it).

### 2.2 The ordering key

Every layout keypress is ordered by

```
(weightSum, nFingers, maxFingerRank, partRank, sorted(keypress))
```

with

```
FINGER_RANK = {"lt":0, "rt":0, "li":1, "ri":1, "lm":2, "rm":2, "lr":3, "rr":3, "lp":4, "rp":4}
PART_RANK   = {"nucleus":0, "onset":1, "coda":2}
```

`nFingers` is always 1 for a *layout* keypress (one finger presses it); it matters in
§2.5 where steps are keyed on `(weightSum, nFingers)`. `maxFingerRank` is the
FINGER_RANK of the keypress's single finger.

**`weightSum`** is the sum over the fingers of
`PositionWeights[finger][sub-keypress]` — exactly the per-finger decomposition
`Starboard.getStrokeCost` performs (`src/keyboard.py`, `getStrokeCost`; finger of a
key from `Starboard._fingerAssignments`), **without** `getStrokeCost`'s extras: no
`getStrokeShapeCost` term and no `0.85 ** nFingers` discount. The lesson ordering
wants the raw per-finger effort, so a one-finger keypress and a two-finger chord are
compared on the plain sum. Sub-keypresses that are not legal (not in
`_possibleKeypress`) cannot occur in the theory; if one is met anyway the keypress is
treated as uncovered (§3).

### 2.3 Verified weight tiers

With the committed `starboard3h.json` (2026-09-30), the ordering lands as:

| weightSum | nFingers | tier content |
|---|---|---|
| 100 | 1 | one-thumb nuclei (`@ 9`, `a`, `i`, `e O`) and one-key index keys (`R`, `w N G`, `j b w`, `s`) — exactly "lesson 1" material |
| 125 | 1 | one-key middle/ring/pinky consonants |
| 150 | 1 | two-key one-finger chords (`° 8`, `E`, `j`, `v`, off-home `Z G`, `m`) |
| 175 | 1 | two-key one-finger home chords (`l`, `g`, `d`, `g`, `z`) |
| 200 | 1 | the pinky vertical off-home chord `S` (24, 25) |
| 200 | 2 | **two-thumb chord nuclei** (`y`, `u`, `§`, `o`) |
| 225 | 2 | first dual-finger consonants (`n`, `z`, `p`, `f`) |
| 250 | 2 | mixed dual-finger consonants and 2+1-thumb nuclei (`2`, `5`, `S`, `Z`, `f`, `b`, `N`) |
| 300 | 2 | the four-key two-thumb nucleus `1` |

This confirms the requested progression: all single-finger consonants (weightSum
≤ 200) come **before** the two-thumb chord nuclei (200, nFingers 2) — the `nFingers`
tiebreak puts the lone (200, 1) keypress ahead of them — and those come **before**
the dual-finger consonants (225+). (The design note "single-finger consonants max
175" missed the `S` coda chord at 200; the `(weightSum, nFingers)` step key absorbs
it without reordering anything.)

### 2.4 Steps and sections

Keypresses are grouped into **steps** at each distinct `(weightSum, nFingers)` value
in the ordering — 9 steps on the current layout. Each step belongs to a **section**
titled per weight tier (French, §7.6).

### 2.5 Chunking into lessons, dealt round-robin over part

Within a step, keypresses are first sorted by the tail of the ordering key
(`maxFingerRank, partRank, sorted(keypress)`). They are then **dealt round-robin over
part**: repeatedly cycle nucleus → onset → coda (PART_RANK order), taking each part's
next unused keypress and skipping exhausted parts, until the step is exhausted. The
dealt sequence is chunked into consecutive **lessons of at most 4 keypresses**. The
round-robin exists so that an early lesson mixes a vowel with consonants and can
already write words; plain left-to-right chunking would give lesson 1 four nuclei and
nothing to consonate them with.

Worked example, step (100, 1). Part queues after the tail sort — nucleus: `(11,)`,
`(12,)`, `(13,)`, `(14,)`; onset: `(8,)`, `(9,)`; coda: `(16,)`, `(17,)`. Dealt
sequence: `(11,), (8,), (16,), (12,), (9,), (17,), (13,), (14,)` (dealing continues
with the remaining nucleus once onset and coda are exhausted). Chunked at 4:
lesson 1 = `{R, j-b-w, a, @/9}` — keys 8, 11, 12, 16 — and lesson 2 = `{s, w-N-G,
i, e}` — keys 9, 13, 14, 17. Lesson 1's pool
includes unmarked vowel-only words such as `à`; `a`/`ah`/`ha` stay out until the
star/hash track (§3, rule 2). On the current layout this yields **15 phoneme
lessons**.

## 3. Coverage and eligibility

The generator keeps a cumulative **covered set** as lessons are emitted, in track
order: covered layout keypresses (phoneme track), then introduced Keypress Groups
(accord, verbe), then introduced star/hash codes (desambiguation track).

Every stroke of the theory is decomposed into per-finger keypresses by the helper
`fingerKeypressesOfStroke(stroke)`: group the stroke's keys by finger (finger of a
key from `Starboard._fingerAssignments`), sort and dedupe each group — the same
grouping `getStrokeCost` uses. A drill record (the practice-words record shape, §5)
of word `w` is **eligible** for a lesson iff:

1. **Phonetic strokes fully covered.** Every per-finger keypress of every stroke of
   `wordToStrokes[w]` (the phonetic theory's base strokes) is in the covered
   keypress set.
2. **Extra disambiguated-stroke content gated by the marker tracks.** The record's
   own strokes (the disambiguated theory: base strokes + feature discriminating
   strokes + star/hash marks) may add content beyond the phonetic strokes. That
   extra content is split into:
   - **star/hash usage**: the reserved keys 10 (`*`) and 15 (`#`) present anywhere
     in the record's strokes, plus the count of reserved-only trailing strokes,
     recompute the star/hash code of [star-hash-marking.md §4](star-hash-marking.md)
     (`∅`, `*`, `#`, `*#`, then `*#` repeated). It must be `∅` or a code the
     desambiguation track has introduced. This keeps marked words out of the
     phoneme-track pools automatically.
   - **marker keypresses**: every stroke of the record that is **not** (after
     `canonicalizeStrokes`) one of `w`'s phonetic strokes and contains no reserved
     key — i.e. a feature discriminating stroke. The Keypress Groups it needs are
     the groups `g` of `realization_report.json` `keypressGroups[*]` whose
     `chosenKeys` are a subset of that stroke's key set (the Realization Phase
     composes a group union into one stroke, so subset matching is the reverse
     mapping). Every such group must have been introduced.

   By construction (S6/S7) no stroke mixes reserved keys with group keys — the first
   mark symbol merges into a phoneme stroke, feature discriminating strokes are
   reserved-free — so the two buckets partition the extra content; the exporter
   asserts this rather than assuming it.

## 4. The five tracks

Tracks are emitted in this order; ids are stable strings.

### 4.1 `phonemes`

The steps of §2, in order, chunked as §2.5. One lesson per chunk. `newKeys` = the
sorted union of the lesson's keypress keys; `newChords` = the keypresses of ≥ 2 keys,
as sorted lists (e.g. lesson with keypress `(8, 9)` gets `newChords: [[8, 9]]`). One
rule per keypress (kind `phoneme`, §7.1). After each lesson, its keypresses enter
the covered set.

### 4.2 `accord`

One lesson per **gender/number Keypress Group**: every group in
`realization_report.json`'s `keypressGroups` whose marker set ⊆ {`f`, `m`, `p`,
`nbr_s`, `nbr_p`} (on the current answers: `{f}` and `{nbr_p, p}`). Groups are
ordered by descending `keypressGroups[g].affectedWords`, ties by the
alphabetically sorted marker tuple —
group ids are not stable across runs, so code never orders by
id. `newKeys`/`newChords` come from the group's `chosenKeys` in
`realization_report.json`. The pool is the top-50 ADJ/NOM records (§5) whose marker
groups all are introduced (cumulatively) **and** which touch the new group — the
marked stroke *is* the drill, the record ships with its feature discriminating
stroke. One rule per group (kind `accord`, §7.2). After the lesson, the group enters
the introduced set.

### 4.3 `verbe`

1. **Marker lesson** (first lesson of the track): introduces **all remaining
   conjugation Keypress Groups** — every group not introduced by `accord` (on the
   current answers: `conditionnel/infinitif`, `future/passé/pers_3`,
   `imparfait/subjonctif`, `impératif/pers_1`, `pers_2`). One rule per group (kind
   `verb-markers`, §7.3); `newKeys` is the union of their `chosenKeys` (the ≤4
   keypress budget of §2.5 applies only to the phoneme track). Its pool is the
   top-50 VER/AUX records eligible under the now-complete group coverage. This
   lesson always ships (§5): its groups must enter coverage.
2. **One lesson per tense**, in this order, each pairing a mood and tense as
   `Word._infoVerb` atoms (`src/word.py`, `splitInfoVerb`):

   | order | mood+tense atoms |
   |---|---|
   | 1 | `indicatif` + `présent` |
   | 2 | `indicatif` + `imparfait` |
   | 3 | `indicatif` + `future` |
   | 4 | `participe` + `passé` (covers passé composé: the participle carries the mark) |
   | 5 | `infinitif` |
   | 6 | `conditionnel` |
   | 7 | `subjonctif` |
   | 8 | `impératif` |

   (`conditionnel`/`subjonctif`/`impératif` have no tense atom beyond the implicit
   présent; `infinitif` is the single atom.) The pool is the top-50 VER/AUX records
   with that mood+tense among the reading's feature combination — a record counts
   when the reading its label describes (from `resolved_press_sets.json` readings,
   the same pairing `export_practice_words` lines up) contains both atoms — and
   eligible under current coverage. Tense lessons introduce no coverage; under §5
   they are dropped when their pool has fewer than 10 records.

### 4.4 `desambiguation`

Lessons in **mark-complexity order**: `*`, `#`, `*#`, then one lesson per escalated
depth (`*# *#`, `*# *# *#`, …) present in the data, ascending. `newKeys`: `[10]`,
`[15]`, `[10, 15]`, then `[]` for escalated lessons (no new keys); `newChords` is
`[[10, 15]]` on the `*#` lesson only. The pool is the top-50 records whose star/hash
code is **exactly** the lesson's code, eligible otherwise — plus the canonical
(unmarked, code-∅) member of every included lemma-homophone group, so the §7.5
contrast template is always renderable; members of one
lemma-homophone group rank side by side (§5). One rule per mark (kind `mark`, §7.5).
Dropped when the pool has fewer than 10 records (§5).

### 4.5 `affixes` (stub)

A single placeholder lesson, id `affixes-01`, kind `affixes`: rule text
"Abréviations d'affixes : à venir." (§7.6), no words, no keys. It reserves the track
so the UI can show it; the real affix-abbreviation lessons are out of scope (§9).

## 5. Word selection and the word-count rule

The candidate stream is the **full disambiguated theory** rendered into
practice-words-shaped records — the record building of `util/export_practice_words.py`
(`buildReadingsByWord`, `chordsWithReadings`, `formatReadingsLabel`, `formatContext`,
`formatPhonology`), one record per independently-valid stroke, **without** that
exporter's 10,000-record `--limit`: lesson pools are ranked by frequency over the
whole lexicon, not over the shipped drill file.

Per lesson: filter the stream to eligible records (§3) meeting the track's pool rule
(§4), then keep the **top 50 by `(-frequency, ortho, steno)`** — `frequency` is the
record's frequency field (`Word.frequency`, the film mix), `steno` the rendered
RTFCRE stroke string, both tiebreaks ascending.

**Word-count rule.** Lessons that introduce coverage (every phoneme lesson, every
accord lesson, the verbe marker lesson) **always ship**, even with a thin or empty
pool — their keys must enter coverage, and an early phoneme lesson legitimately has
few writable words. Lessons that introduce no coverage (verbe tense lessons,
desambiguation lessons) are **dropped** when fewer than 10 eligible records exist.
A dropped desambiguation lesson leaves its code's words permanently ineligible; that
is accepted — these pools are among the largest. Track-local `index` and lesson ids
are renumbered densely after drops (ids stay `track-NN`, NN zero-padded to 2).

The `desambiguation` pools rank lemma-homophone groups, not lone records: records of
one group are keyed by the group's maximum frequency (then `ortho`, `steno`), and
whole groups are taken in rank order until the next group would exceed 50 — pair
members are never split by the cap.

## 6. lessons.json schema

```json
{"tracks": [{"id": "phonemes", "title": "Phonèmes", "description": "…"}],
 "lessons": [{"id": "phonemes-01", "track": "phonemes", "index": 1,
   "sectionTitle": "…", "title": "…", "kind": "phonemes",
   "newKeys": [8, 9, 11], "newChords": [[8, 9]],
   "rules": [{"kind": "phoneme", "text": "La touche … écrit …", "examples": ["si"]}],
   "words": [ {practice-words record, verbatim shape} ]}]}
```

- `tracks`: `{id, title, description}` per track of §4, in track order. Titles and
  descriptions are French (§7.6).
- `lessons`: flat list in generation order. Fields:
  - `id`: `"{track}-{index:02d}"`;
  - `track`, `index` (1-based, dense per track after drops);
  - `sectionTitle`: phoneme lessons use the weight-tier section title (§2.4/§7.6);
    other tracks repeat the track title;
  - `title`, `kind`: per §4 (kind = `phonemes` / `accord` / `verbe` /
    `desambiguation` / `affixes`);
  - `newKeys`: ints indexing into `keyboard-layout.json` `keys[]` — the trainer's
    `Keyboard.view` highlights these;
  - `newChords`: lists of such ints, key-sets pressed together within one new
    keypress or mark;
  - `rules`: `{kind, text, examples}` per §7; `examples` are orthography strings
    drawn from the lesson's own `words` (at most 3, in pool order; empty allowed);
  - `words`: **must reuse the `practice-words.json` record shape verbatim**
    (`ortho, before, after, label, phonology, steno, strokes, frequency`), produced
    by the same helpers, so the trainer's `Drill.elm` decoders work unchanged. The
    records are *copies*: lesson pools never reference the practice-words file.

## 7. Rule-text templates (French)

All learner-facing text is French, in the tone of
`resources/reference/Pluvier_TAO_rules.md` (matter-of-fact, example-driven, one
sound per line). `{…}` are placeholders filled from the data named below; key names
are `keyboard-layout.json` `keys[i].name` (e.g. `k-`, `-s`, `a`), phonemes are the
repo's X-SAMPA (`src/grammar.py` dialect; no IPA table is introduced on the Python
side — examples carry the sound, and the trainer already renders X-SAMPA to IPA in
`Notation.elm`), steno strings are RTFCRE (`util/_stenorender`).

### 7.1 kind `phoneme`

One key, one part, one phoneme:

- onset: `La touche {touche} écrit le son /{phoneme}/ en début de syllabe ({exemples}).`
- coda: `La touche {touche} écrit le son /{phoneme}/ en fin de syllabe ({exemples}).`
- nucleus: `La touche {touche} écrit la voyelle /{phoneme}/ ({exemples}).`

Multi-phoneme keypress (the keypress is atomic, so one rule): `La touche {touche}
écrit {phonèmes} selon la position ({exemples}).` with `{phonèmes}` =
`/w/, /N/ ou /G/`.

Chord keypress (≥ 2 keys): `Les touches {touches} pressées ensemble écrivent
/{phoneme}/ en {début|fin} de syllabe ({exemples}).`

Two-thumb nucleus chord: `Les touches {touches} pressées ensemble écrivent la
voyelle /{phoneme}/ ({exemples}).`

`{exemples}` = up to 3 example orthographies joined with `", "`, each wrapped as
`« mot »`.

### 7.2 kind `accord`

`La touche {touche} marque {marqueur} : {exemple_marqué} par rapport à
{exemple_base}.` where `{marqueur}` is the French rendering of the group's markers
(`f` → `le féminin`, `p`/`nbr_p` → `le pluriel`, `m` → `le masculin`, `nbr_s` → `le
singulier`; several markers join with ` et `, deduped — `{nbr_p, p}` renders as `le
pluriel`). `{exemple_marqué}` is the pool's first record's `ortho` + `steno`
(`{ortho} → {steno}`); `{exemple_base}` is the same word's phonetic-theory steno
(the stroke without the feature discriminating stroke), giving the contrast.

### 7.3 kind `verb-markers`

`La touche {touche} marque {marqueurs} : {exemples}.` with `{marqueurs}` the
group's markers rendered in French (`pers_1` → `la première personne`, `pers_2` →
`la deuxième personne`, `pers_3` → `la troisième personne`, `infinitif` →
`l'infinitif`, `impératif` → `l'impératif`, `subjonctif` → `le subjonctif`,
`imparfait` → `l'imparfait`, `future` → `le futur`, `passé` → `le passé`,
`conditionnel` → `le conditionnel`), joined with ` et `. The person labels are
spelled out (never `1re`/`2e`/`3e`) because of §8's IPA-toggle invariant.

### 7.4 kind `verb-tense`

`Pour {mode_temps}, les marques de conjugaison sont {touches} : {exemples}.` with
`{mode_temps}` from the §4.3 table (`l'indicatif présent`, `l'imparfait de
l'indicatif`, `le futur de l'indicatif`, `le participe passé` — append `, comme au
passé composé` —, `l'infinitif`, `le conditionnel présent`, `le subjonctif
présent`, `l'impératif présent`) and `{touches}` the marker keys that the tense's
records actually press (union of `chosenKeys` of the groups touched by the lesson's
selected records, sorted).

### 7.5 kind `mark`

`La marque {marque} ({touches}) distingue {mot_marqué} ({steno_marqué}) de
{mot_référence} ({steno_référence}).` where `{marque}` is `*`, `#`, `*#` or
`*#`×k, `{touches}` the reserved key names, and the pair is the first complete
lemma-homophone contrast in the lesson's pool (the marked record and the canonical
member of its group; if the canonical member is not in the pool, fall back to the
first marked record alone: `La marque {marque} ({touches}) s'ajoute à la fin du
mot : {exemple}.`).

### 7.6 Titles

Track titles: `Phonèmes`, `Accord (genre et nombre)`, `Verbes`,
`Désambiguïsation`, `Affixes`. Track descriptions are one French sentence each
(`phonemes`: `Les touches et les sons, de la plus simple à la plus complexe.`;
`accord`: `Les marques de genre et de nombre.`; `verbe`: `Les marques de
conjugaison, temps par temps.`; `desambiguation`: `Les marques * et # qui
distinguent les homophones.`; `affixes`: `Abréviations d'affixes — à venir.`).

Phoneme section titles per weight tier, with a generic fallback so any future
layout regenerates: 100 `Les premières touches`, 125 `Les autres doigts`, 150
`Accords à deux touches`, 175 `Accords à deux touches, suite`, 200 `Derniers
accords d'un doigt` / (200, 2) `Voyelles à deux pouces`, 225 `Consonnes à deux
doigts`, 250 `Accords à deux doigts, suite`, 300 `La voyelle complète`; fallback
`Complexité {weightSum en lettres}` — the weight spelled out in French words
(`Complexité trois cents`; distinct `(weightSum, nFingers)` steps sharing a
weightSum share the section). Lesson titles spell the lesson number in French
words too (§8's IPA-toggle invariant; digits 1, 2, 5, 8 and 9 are mapped):
`Leçon {index en lettres} : {premiers phonèmes de la leçon}` (phonemes), `Leçon
{index en lettres} : {marqueur}` (accord), `Leçon {index en lettres} :
{mode_temps}` (verbe), `Leçon {index en lettres} : la marque {marque}`
(desambiguation), `Leçon un : à venir` (affixes). (`numberInFrench` in
`util/export_lessons.py` renders the cardinals, 0-999.)

Affixes rule text: `Abréviations d'affixes : à venir.`

## 8. Invariants

- Regeneration is byte-identical (§1); no hand-edited fields exist.
- Lesson 1's words use only lesson-1 keypresses (tier 100); every lesson's words
  use only covered keypresses (§3, rule 1) and covered marker/mark content (rule 2).
- A word with a star/hash mark never appears before the `desambiguation` track; a
  word with a feature discriminating stroke never appears before its groups'
  introducing lesson.
- `newKeys`/`newChords` only ever contain indexes valid in `keyboard-layout.json`
  `keys[]`; keys 0 and 1 never appear.
- `words` records decode with the trainer's existing `Drill.elm` decoders — same
  field names, same types, same reading-label semantics as `practice-words.json`.
- Track order, lesson order within a track, and every pool order are total orders
  (the `(-frequency, ortho, steno)` key or its group variant) — no ties left to
  chance.
- French prose in the §7 templates — rule texts, lesson/section/track titles,
  track descriptions — never contains a character of the trainer's IPA table
  (`E O R Z S N G @ ° § 5 8 9 2 1`; `ipaByXSampa` in
  `steno-trainer/src/Notation.elm`) outside the three places phonetics belong:
  `/phoneme/` spans, key names and steno examples. The trainer's
  "Phonemes: X-SAMPA / Show IPA" toggle rewrites the entire rendered string
  character by character, so a mapped character in prose would come out as an
  IPA glyph ("Leçon 1" would render "Leçon œ̃"). Hence the spelled-out person
  labels (§7.3), the number words in titles and the fallback section title
  (§7.6), and the affixes stub's wording (§4.5).

## 9. Out of scope

- Real affix-abbreviation lessons (the `affixes` track stays a stub; that work is
  ongoing separately).
- Learner progress persistence in any form.
- A lesson-ordering configuration file (the progression is fixed by this spec).
- Any IPA rendering on the Python side (the trainer renders X-SAMPA itself).
