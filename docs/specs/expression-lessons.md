# Expression lessons (`expression-lessons.json`, `expression-sentences.json`)

The trainer's `expressions` track teaches the expression abbreviation layer: the attach keypresses that add a particle (`de`,
`il`, `n' y`, ...) to the neighbouring word, the briefs that replace a whole phrase by one stroke, and phrases that combine several
of them. Exporters: `python -m util.export_expression_lessons` (S10a) and `python -m util.export_expression_sentences` (S10b), after
the theory exports. Both files are optional: the trainer merges the lessons over the stub lesson of `lessons.json` (docs/specs/lessons.md
§4.6) and keeps the stub when the file is absent; `practice-sentences.json` and the other trainer data files are never touched.

Nothing is decoded in the trainer. The composer (`src/expressions.composeOutlineTraced`) runs in Python and every accepted outline is
exported; the drill prefix-matches typed strokes against `strokes` + `alternates` as everywhere else.

## Inputs

The committed rule set and pool of the expression layer, through `util/_expressioninput.loadExpressionInputs`: 29 attach rules
(`scratch/expr-rules-final.json`), 40 forced briefs (`scratch/expr-briefs.tsv`), 1,151 pool phrases (`scratch/expr_candidates.tsv`).
A pool phrase takes the FIRST reading of each word (`theory[word][0]`); that is enough for lessons, but a verb form with another reading
would not be taught.

## `expression-lessons.json`

```
{ "rules":   [ {"rank", "kind", "position", "units", "keys", "keyNames", "family", "label"[, "steno"]} x69 ],
  "lessons": [ <lesson> ... ] }
```
- `rules`: the legend. Ranks are 1-based over the attach rules first (family rank, then base form before elided form, then units), then the
  briefs (descending frequency of their phrase). `kind` is `attach` or `brief`; a brief has `steno` (its stroke) and `position` "".
  `label` is French, e.g. `« de » ou « d' » : se joint au mot suivant`, `abréviation de « toutes les »`.
- `<lesson>` is the `lessons.json` lesson schema: `id` `expressions-NN` (dense), `track` and `kind` `expressions`, `index`,
  `sectionTitle`, `title`, `newKeys`, `newChords`, `rules` (kind `expression`: what the keys do, three examples `long → short`, a closing
  sentence), `words`.
- A word is a `practice-words.json` record (`ortho`, `before`, `after`, `label`, `phonology`, `steno`, `strokes`, `frequency`) plus:
  - `alternates: [{"steno", "strokes"}]`, at most 8 (the composed outline's rivals), no duplicates, never the primary outline. In order:
    the partial compositions (the most rules applied first), then the plain word-by-word outline, which is ALWAYS present. The drill accepts any.
  - `ruleRanks: [int]`: the ranks of the rules the composition fires (one per attach merged or standalone, one per brief). The trainer's legend shows
    only these. (Not `rule`: a phrase can use several rules.)
- `ortho` is the phrase as written (`qu'il`, `de la`): spaces between words, none after an elided one. `phonology` joins the units' phonologies by dots.
  `label`: how many strokes it saves (`économise un trait`), and for composed phrases the number of abbreviations.

## Selection

Every pool phrase is composed with the whole rule set; phrases that save nothing are left out. A phrase "fires" the attach rules merged into the
outline or standing alone as a keypress, and the briefs that replaced words; an attach that fell back to its longform (exception) does not count.

1. **Family lessons**, one per rule family, families in descending frequency-weighted saving (a family counts once per phrase it takes part in; ties by name).
   An elision pair (`de`/`d'`, `ne`/`n'`, ...) shares one chord and so one lesson; selector variants (`il`/`il n'`, `je`/`je me`/`j'`) share the family.
   Items: the 20 most frequent phrases that fire exactly one rule of the family; if fewer than ten exist, topped up with multi-piece phrases that include the
   family (families with few phrases such as `par` or `les` end with six or seven items). `newKeys`: the union of the family's keys; `newChords`: each distinct
   keypress of at least two keys. Section titles group families by ten.
2. **Composed phrases**: phrases firing two rules fill up to two lessons of 20, then one lesson of the phrases firing three or more (section "Les phrases composées"). No new keys.
3. **Briefs**: the 40 forced briefs by descending phrase frequency, four lessons of ten (section "Les mots et les expressions abrégés"). Each brief is composed ALONE:
   the composer matches attach particles before briefs, so with the whole rule set `avec`, `dans la` or `toutes les` would not use their brief. The hint is the brief's
   stroke; the plain word-by-word outline stays accepted.

All orders are total (`(-frequency, units)`); regeneration is byte-identical.

## `expression-sentences.json`

A list of sentence records of the `practice-sentences.json` schema (`text`, `phonology`, `steno`, `strokes`, `words`) plus `alternates` (one entry: the plain
word-by-word outline of the whole sentence) and `ruleRanks` (ranks in `expression-lessons.json`). Same candidates and the same token resolution and rejections as
`util.export_practice_sentences`, then the tokens composed as one stream; only sentences that at least one abbreviation shortens are kept (139 of 276 candidates).

Word segmentation of an abbreviated sentence: `words[i].strokeCount` is the number of strokes of the composed outline the word owns, `steno` their rendering
(empty for none), and the counts add up to `len(strokes)` (checked; a sentence that does not add up is left out). A word keeps its strokes (a merged particle changes
keys, not the count); a merged particle owns none; a standalone attach or a brief puts its strokes on the FIRST token of the group it replaces and the other tokens own
none; an attach that fell to an exception keeps each token's longform strokes. The trainer already skips segments of zero strokes (`Drill.currentSegmentIndex`).

## Text conventions

As docs/specs/lessons.md §8: titles, section titles, labels and rule texts contain none of `E O R Z S N G @ ° § 5 8 9 2 1` (the IPA toggle rewrites whole strings), so
numbers are spelled in words (`numberInFrench`). Steno strings, key names and `phonology` follow the toggle on purpose.

## Out of scope

The per-stroke split of rule keys and host keys on the keyboard, a Definitions column for expressions, any decoding in the trainer.
