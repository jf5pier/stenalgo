# Homophone-collision residual investigation (2026-09-21)

Written so a fresh (cleared-context) session can pick up without re-deriving context.
**Status as of end of session: two real bugs fixed and committed (theory 2 wasn't wired
into either dictionary exporter). A small residual gap in `decideStarHashMark` itself
is identified but NOT YET investigated** -- that's this doc's actual task.

## Bottom line

This session built `steno-trainer/` (a from-scratch Elm web app for practicing
Stenalgo's theory on real hardware via Web Serial -- see `steno-trainer/README.md`,
already committed and working) and then found + fixed a real bug the user noticed
while using it: `à`/`a`/`as` (and homophones generally) were colliding onto the same
steno chord in both the practice trainer and the real Plover dictionary.

**Root cause (fixed):** `util/export_plover_dictionary.py` and
`util/export_practice_words.py` both read `FirstTheory.pickle` (theory 1 -- base
onset/nucleus/coda strokes only, no homophone marks) instead of theory 2
(`Dictionary.buildFinalTheory`, `dictionary.py:339-366` -- composes theory 1 with
Phase P's same-lemma coda-bank marks and the `*`/`#` lemma-homophone track). Neither
exporter was wrong about what `FirstTheory.pickle` contains; they were just never
updated once theory 2 started existing (`ROADMAP.md`'s "Status update" section,
2026-09-20 entry, "The `*`/`#` pipeline wired into `dictionary.py`'s persisted output").

**Fix, committed in two commits (`Add steno-trainer...` and `Wire theory 2 ...`):**
- `util/_theoryio.py` gained `loadFinalTheory(keyboard, phaseGPath, resolvedPressSetsPath)`,
  a thin wrapper around `Dictionary.buildFinalTheory` that also preserves the
  `Dictionary` object `loadFirstTheory` used to discard.
- `util/_stenorender.py` (new): `renderFinalStrokesToRTFCRE(starboard, strokes)` --
  `Starboard.strokesToRTFCRE` alone crashes (`KeyError`) on any stroke containing
  `STAR_KEY`/`HASH_KEY` (10/15, `src/ambiguitychecker.py:350-351`), since those keys
  carry no syllabic part and aren't in `keyIDinSyllabicPart`. Phase P's coda marks and
  the `*`/`#` track's marks are always concatenated as separate whole strokes, never
  merged into one (`composeReservedKeyStrokes`, `src/ambiguitychecker.py:409-430`), so
  a stroke is always either "normal" (render via the existing method) or "bare
  star/hash" (render as a plain key-name concatenation) -- never both.
- Both exporters now call `loadFinalTheory` + `renderFinalStrokesToRTFCRE`.
- Result: `plover_stenalgo_dictionary.json` went from 87,506 strokes/47,370 collisions
  to 160,716 strokes/18,802 collisions. `à`->`a`, `a`(avoir)->`a/*`, `as`(avoir)->`a/-t`
  (the `pers_2` Phase P mark) are now distinct, verified.

## Lexicon-size tangent (answered, no action needed)

User asked how many words from `LexiqueMixte.tsv` + `LexiqueSynthetic.tsv` end up in
the theory. Answer: 137,655 + 58,395 = 196,050 raw rows -> 184,524 distinct `Word`
objects after `Dictionary.readCorpus`'s identity-based merge (`dictionary.py:110-134`)
-> **all 184,524 make it into `theory`/`FirstTheory.pickle`, zero dropped anywhere**.

## The open task: is 18,802 collisions actually fine?

User's reaction to 18,802 collisions: "that's a lot, what is happening?" Investigated
this session (all ad hoc, not committed as a script -- reproduce via the snippet
below) and found the raw count is a misleading headline:

- **13,487 groups (72%) are pure spelling homographs** -- same written word, different
  grammar (`le`/ART vs `le`/PRO, `est`/VER vs `est`/AUX, `je`, `de`, `pas`, `tu`, `ça`,
  `un`, `il`, `en`, `l'`, `les`...). These *should* share one stroke -- marking them
  differently would be pointless since you always want to type the same spelling. This
  is "homograph exemption," the first rule in `decideStarHashMark`'s stack
  (`src/ambiguitychecker.py:182-259`), working as designed.
- **5,315 groups (28%) involve genuinely different spellings** colliding -- the metric
  that actually matters. Together: **3.2% of total lexicon frequency mass** (28,912 /
  900,794).
- Most of that 3.2% is the "10x frequency-ratio exemption" rule (also in
  `decideStarHashMark`) correctly declining to spend a mark distinguishing a common
  pronoun from an unused verb form: `ne`(13,357) vs `nuas`("nuer," freq 0.0),
  `me`(4,929) vs `mua`("muer," 0.1), `te`(4,006) vs `tuant`("tuer," 6.4),
  `se`(2,814) vs `suant`/`sua`/`suât`("suer," ~0.1 each).
- **The genuinely interesting residual: ~52 groups** where the top two *nonzero*
  competing readings are within 10x of each other (i.e. NOT explained by that
  exemption) -- computed via `top2Ratio` in the reproduction script below. Standouts:

  | steno words (ortho[lemme/gramCat/freq]) | ratio |
  |---|---|
  | `quatre`[quatre/ADJ:num/150.9] vs `carte`[carte/NOM/96.1] | 1.57x |
  | `star`[star/NOM/28.9] vs `tsar`[tsar/NOM/11.7] | 2.48x |
  | `masque`[masque/NOM/23.2] vs `max`[max/NOM/5.9] | 3.90x |
  | `ski`[ski/NOM/13.8] vs `gui`[gui/NOM/2.9] | 4.77x |
  | `merde`[merde/ONO+NOM/221.5+206.7] vs `merdre`[merdre/ONO/0.0] | n/a -- `merde` alone is high-freq, still worth checking why it's not marked at all |
  | `croyons`[croire/VER/4.5] vs `croyions`[croire/VER/0.7] (SAME LEMMA, present vs imparfait) | 6.58x |

  Full list of 52 is reproducible below, not saved to a file.

**User's instruction: note findings here (this file) rather than dig in now, so a
fresh session can investigate without this session's now-long context.**

## Next session: what to actually do

1. **Reproduce the residual list** (script below, run from repo root with the venv
   active -- `Dictionary.pickle`/`FirstTheory.pickle`/`phase_g_keypress_assignment.json`/
   `resolved_press_sets.json` all already exist, no rebuild needed):

   ```python
   import pickle, sys
   from collections import defaultdict
   from dictionary import Dictionary
   sys.modules['__main__'].Dictionary = Dictionary
   from src.grammar import Syllable
   from src.keyboard import Starboard
   from util._stenorender import renderFinalStrokesToRTFCRE

   with open('Dictionary.pickle','rb') as f:
       dictionary = pickle.load(f)
       Syllable.allPhonemeCol = pickle.load(f)
       Syllable.phonemeColByPart = pickle.load(f)
       Syllable.biphonemeColByPart = pickle.load(f)
       Syllable.multiphonemeColByPart = pickle.load(f)
   with open('FirstTheory.pickle','rb') as f:
       theory = pickle.load(f)

   starboard = Starboard.fromJSONFile('starboard3h.json')
   finalTheory = dictionary.buildFinalTheory(
       theory, starboard, 'phase_g_keypress_assignment.json', 'resolved_press_sets.json')

   stenoToWords = defaultdict(list)
   for word, strokes in finalTheory.items():
       stenoToWords[renderFinalStrokesToRTFCRE(starboard, strokes)].append(word)

   collisionGroups = [w for w in stenoToWords.values() if len(w) > 1]
   realAmbiguous = [g for g in collisionGroups if len(set(w.ortho for w in g)) > 1]

   def top2Ratio(g):
       freqs = sorted((w.frequency for w in g if w.frequency > 0), reverse=True)
       return freqs[0] / freqs[1] if len(freqs) >= 2 else float('inf')

   notExempt = [g for g in realAmbiguous if top2Ratio(g) < 10 and sum(w.frequency for w in g) > 1.0]
   # notExempt is the ~52-group residual list -- inspect from here.
   ```

2. **Pick one or two concrete pairs** (recommend starting with `quatre`/`carte`, since
   it's the highest-mass, most clearly-not-exempt case, and `merde`/`merdre` since
   `merde` alone is high-frequency yet still colliding) and **trace them through
   `decideStarHashMark`** (`src/ambiguitychecker.py:182-259`) and
   `rankHomophoneCluster`/`assignStarHashMarks` (`src/ambiguitychecker.py:260-367`)
   step by step to find the actual reason they're not getting marked. Candidate
   hypotheses to check, in rough order of likelihood -- NONE confirmed yet:
   - A rule earlier in the stack than the 10x exemption is firing incorrectly for
     these pairs (check `MARKING_OVERRIDES`, `src/ambiguitychecker.py:129`, and the
     1990-reform-doublet check first -- `quatre`/`carte` and `star`/`tsar` are not
     doublets of each other, so this would be a bug if it's firing).
   - `groupHomophonesByReservedStroke` (`src/ambiguitychecker.py:379`) might be
     grouping by the wrong stroke identity (e.g. pre- vs post-Phase-P), causing these
     pairs to never even reach `decideStarHashMark` as a pair to consider.
   - For the SAME-LEMMA cases (`croyons`/`croyions`, `entendiez`/`entendriez`,
     `jouiez`/`joueriez`, `tueriez`/`tuiez`, `revoyons`/`revoyions`) -- these are
     present-vs-imparfait or conditionnel-vs-imparfait person/tense collisions within
     one lemma, i.e. Phase P's job, not the `*`/`#` track's. Check whether
     `imparfait`'s Phase G group (group 1, `['imparfait','pers_2']`,
     `phase_g_keypress_assignment.json`) actually covers the specific person
     combinations these pairs need, or whether the elicited marker set has a real
     coverage gap here (never elicited a distinguishing choice for this specific
     tense/person combination) rather than a marking-logic bug. This is a different
     root cause from the diff-lemma cases above and may need the user's input on
     whether it's worth a new elicitation round, not just a code fix.
3. Whatever's found, this is the user's carefully-tuned marking policy (0.53% of
   theoretical optimum keystroke cost per `ROADMAP.md`) -- don't change
   `decideStarHashMark`'s rule stack without discussing the tradeoff with the user
   first. Report findings, propose a fix, get agreement, then implement.
