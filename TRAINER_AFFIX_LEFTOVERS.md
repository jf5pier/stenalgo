# Affix trainer: leftovers (branch `affix-trainer`, nothing pushed)

Done (one commit per step): shared loader `util/_affixio.py`; exporter `util/export_affix_lessons.py` + 9 tests
(`src/test/affix_lessons_test.py`; wired in `dictionary.py` as S9c); Elm either-outline drill, lessons merge and
"Affix rules" legend; docs. pytest: 1024 pass; the five trainer JSONs and the two S9b outputs are byte-identical to
`tmp/trainer_golden/`; `affix-lessons.json` is deterministic (two runs, same md5).

## Not verified
1. **Elm version**: this machine has Elm 0.19.1, `elm.json` asks 0.19.2. I compiled a scratch copy with the version
   patched (plain and `--optimize`: success, no warnings) and exercised `Drill.applyStroke` in `elm repl`. Please rerun
   `cd steno-trainer && elm make src/Main.elm --output=main.js` (and `--optimize`) with 0.19.2.
2. **Manual browser check** (not possible here): `cd steno-trainer && python -m http.server`, open Lessons ->
   Affixes: 30 rule lessons + "les formes conjuguées"; an intro lights the rule's keys; in a drill, typing the short OR
   the long outline advances (the typed-strokes line shows what was typed), a wrong stroke retries, the hint shows the
   short outline; the "Affix rules" sidebar legend appears once Lessons was opened; Words/Sentences/Definitions and
   other tracks unchanged; the IPA toggle does not mangle titles.

## Questions / choices to confirm
1. **Alternates schema**: I made `alternates` a list of `{steno, strokes}` (not bare stroke lists as the plan said), so the
   typed-strokes line can print a long outline's text. OK?
2. **Verb lesson duplicates**: the top 20 route>=1 verb items repeat a spelling (e.g. « arrête » with `-k`, `-R`
   marks). Faithful to the plan; dedupe by spelling instead?
3. **Legend timing**: the "Affix rules" legend appears only after Lessons mode is first opened (that is when
   `affix-lessons.json` is fetched). Fetch it at startup instead?
4. **Track description** "à venir" is replaced in Elm (`Lessons.mergeAffixData`) to keep `lessons.json` byte-identical;
   the stub/`TRACKS` text in `util/export_lessons.py` still says "à venir".
5. **Rule text**: generic wording ("se joignent à la frappe de la syllabe voisine, ou forment une frappe à elles
   seules"); it does not say per rule which case applies. Want rule-specific merge/standalone wording?
6. `export_affix_lessons` assumes `str(GramCat.VER)` ends in `VER` (`isVerb`); verified `GramCat.VER` prints so.
7. Merge to main / push: untouched, awaiting your call.
