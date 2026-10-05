# Affix lessons (`affix-lessons.json`)

The trainer's `affixes` track teaches the 30 affix abbreviation rules (`affix_rules.json`, docs/AFFIX_RULES.md).
Exporter: `python -m util.export_affix_lessons` (S9c, after S9b). The file is optional: the trainer merges it over the
stub lesson of `lessons.json` (docs/specs/lessons.md §4.5) and keeps the stub when it is absent. `lessons.json` and the
other trainer data files are never touched by it.

## Schema

```
{ "rules":   [ {"rank", "position", "ortho", "phono", "keys", "keyNames", "label"} x30 ],
  "lessons": [ <lesson> ... ] }
```
- `label`: French, `préfixe « re- » (aussi reh-)` (first spelling, up to three variants).
- `<lesson>` is the `lessons.json` lesson schema: `id` `affixes-NN` (dense), `track` and `kind` `affixes`, `index`,
  `sectionTitle`, `title`, `newKeys` (the rule's keys), `newChords` (`[keys]` when the rule has at least two keys),
  `rules` (`kind` `affix`: what the keys do, three examples `long → short`, the saving), `words`.
- A word is a `practice-words.json` record whose `steno`/`strokes` are the SHORT outline (what the hint shows), with
  `alternates: [{"steno", "strokes"}]` holding every other accepted outline (the long one, and both outlines of the
  spelling's homographs, without duplicates) and `rule`, the rank of the rule that shortens it. The drill accepts any
  of these outlines. In the rule lessons one record stands for a spelling; in the verb lesson each conjugated form or
  homograph is its own record, labelled `lemme : mode temps, personne` (abbreviated, persons in words). The trainer's
  "Affix rule hint" shows, for the current word, only the rules in the `rule` fields of its records.

## Selection

- One lesson per rule in rank order, the 20 most frequent spellings among its carriers (`route == 0`, by `(-frequency, ortho)`, homographs merged into one record); a rule with
  no carrier gets no lesson (ids stay dense).
- A last lesson "les formes conjuguées": the 20 most frequent abbreviations with `route >= 1` of verbs (category `VER`),
  over all rules; no new keys. A spelling may appear several times there, once per marked route; each record is labelled with
  its lemma, tense and person (`conjugationText`).
- Section titles group the rules by ten.

## Rule key names

A rule's keys are written with each side grouped (`groupKeyNames`, mirrored in `Keyboard.groupKeyNames`): `-jsd`,
`pm- + -j`. Used in the lesson intros and the trainer's rule hint.

## Text conventions

As docs/specs/lessons.md §8: the notation toggle rewrites the digits 1, 2, 5, 8, 9 of every learner string, so titles,
section titles, labels and rule prose spell numbers in words (`numberInFrench`). Steno strings and phonology are X-SAMPA
and follow the toggle on purpose.
