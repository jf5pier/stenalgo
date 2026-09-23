# Resume: steno-trainer practice-tool features (2026-09-21)

Continuation doc for the steno-trainer 4-phase feature plan and a dictionary bug found while
testing it. Plan file (Claude Code plan mode): `~/.claude/plans/i-want-to-add-dazzling-bear.md`
— read that first for full phase-by-phase design detail; this doc is the status snapshot +
the new bug.

## Update 2026-09-22: every item in this file is resolved

Phase 2 was committed; the "calmez" over-marking bug and the reading-label gap were fixed
(`RESUME_2026-09-22-alternate-strokes.md`); Phase 3 (sentence mode) and Phase 4 (IPA toggle)
shipped (`RESUME_2026-09-22-trainer-features.md`). Kept for history.

## Phase status

1. **Chord-board 2-key phoneme display** — DONE, committed (`785f4ad`). Each 2-key phoneme now
   renders once, as a badge positioned by pixel geometry (not CSS grid spanning) straddling the
   boundary between its two keys; non-adjacent ("skip-over") thumb-cluster pairs get orthogonal
   connector lines, anchored/offset (raised+shifted-left for a left-anchored pair, lowered+
   shifted-right for a right-anchored one, centered on a third deeper line when neither side is
   unambiguous) so no two pairs' lines or badges ever coincide. Also dropped the leading/trailing
   hyphen from nucleus key labels (`@`, `a`, `i`, `e`) on the interactive keyboard — display-only,
   `src/keyboard.py`'s `Starboard.keyDisplayName` (the real Plover-facing naming convention) is
   untouched. See `steno-trainer/src/Keyboard.elm`.

2. **Basic mode: shuffle + next-word preview** — DONE, **not yet committed**. `git status` shows
   `steno-trainer/elm.json`, `steno-trainer/src/Drill.elm`, `steno-trainer/src/Main.elm`,
   `steno-trainer/style.css` modified. Added `elm/random` dependency. `Drill.applyStroke` now
   returns `(State, Bool)` — the bool signals "this stroke completed a full pass" (index wrapped
   to 0) so `Main.elm` knows when to reshuffle; `Drill.elm` itself stays `Cmd`/`Random`-free by
   design. `Main.elm` has a `shuffleGenerator` (random-key sort over `elm/random`'s
   `Random.float`) and a `ShuffledWords` message that either starts the first drill (on load) or
   reshuffles the existing one in place (on pass completion). `viewDrill` now shows the next word
   next to the current one, de-emphasized. User confirmed working in browser. **Action: commit
   these changes** (not done only because the bug below was found first and the user asked to
   pause for documentation).

3. **Short-sentence practice mode** — NOT STARTED. Design already spec'd in the plan file: Haiku
   subagent authors candidate French sentences (common words, no subjonctif/passé simple/rare
   words) → new `util/export_practice_sentences.py` validates each sentence's words resolve via
   `loadFinalTheory`/`byOrtho` and filters out disallowed moods (`Word.infoVerb` tag prefixes
   `sub:*` or `ind:pas`) and rare words → new `practice-sentences.json` → new Elm `Mode` type
   (`WordMode`/`SentenceMode`) with a mode-switch UI, reusing `Drill.elm`'s state machine
   (generalize `PracticeWord.ortho` to a mode-neutral display field, or alias the sentence JSON's
   `text` field into the same `.ortho` slot).

4. **X-SAMPA / IPA toggle** — NOT STARTED. Design already spec'd in the plan file: a verified
   X-SAMPA→IPA table already exists (commented out) in `src/grammar.py` (vowels: line 32 vs
   1288; consonants: line 33 vs 1289) — hardcode it in Elm (session-only toggle, no Python
   changes for the mapping itself). Also adds `word.phonology` to `util/export_practice_words.py`'s
   output (and the future sentence exporter) for a new phonetic line in the drill view, since
   that field isn't exported today.

## New bug found while testing Phase 2 (shuffle): over-precise conjugation marking

Word "calmez" appeared in the drill (screenshot) rendered as:

```
calmez
kal/me/-kt
```

Two problems, reported by the user:

1. **UI bug**: the drill gives no indication of *which* grammatical reading is intended —
   "calmez" is ambiguous between "indicatif présent, 2e personne du pluriel" and "impératif, 2e
   personne du pluriel" (same-lemma homophones, Phase P's problem — see `ROADMAP.md`'s
   same-lemma-homophones section). The trainer currently only shows `ortho`/`steno`/marks, with
   no grammatical-category/mood/person label, so a user drilling this word has no way to know
   which reading's chord they're supposed to produce. Would need `util/export_practice_words.py`
   to export something like a human-readable grammatical label per word (from `Word.gramCat`/
   `Word.infoVerb`) and `Drill.elm`/`Main.elm`'s `viewDrill` to display it.

2. **Dictionary/theory bug** (the more important one — a real Phase P over-marking bug, not just
   a display gap): the stroke `-kt` marks the word with **both** the "impératif" conjugation
   marker (`-k`, per the sidebar's "Conjugation markers" legend, generated from
   `phase_p_keypress_realization.json`/`phase_g_keypress_assignment.json`) **and** the "pers_2"
   (2nd person) marker (`-t`) simultaneously. The user's diagnosis: only **one** of the two
   candidate readings needs marking to disambiguate this specific homograph pair — either
   `kal/me/-k` (marking just "impératif," leaving the unmarked/other form as indicatif) or
   `kal/me/-t` (marking just "pers_2") should be sufficient to separate the two readings; the
   combined `kal/me/-kt` is over-precise and shouldn't be required. This suggests Phase G's
   keypress-assignment (`src/phaseg.py`/`src/phasegsat.py`) or Phase P's realization
   (`src/ambiguitychecker.py::realizeKeypressGroupsAsExtraStroke`) is choosing to mark *both*
   grammatical features elicited for this pair instead of recognizing that either one alone
   already discriminates the two words needing separation — worth investigating whether this is
   a genuine bug in the elicitation/grouping logic, or a case where the user's own elicitation
   answers (`elicitation_answers.json`) requested both markers for this pair and the fix is
   there instead (see `src/elicitation.py`, the web questionnaire answers file). Needs a fresh
   investigation session — not diagnosed further here per the user's request to just document
   and continue later.

**Not fixed yet** — user asked to stop and write this note instead, for continuation after
`/clear`. Next session should: (a) commit the Phase 2 changes above, (b) decide whether to fix
the UI ambiguity (item 1) as part of Phase 3/4 work or standalone, (c) investigate the
over-marking bug (item 2) starting from `elicitation_answers.json` and `phase_g_keypress_assignment.json`
for the "calmez"/kal-me lemma pair, cross-referencing `ROADMAP.md`'s and
`ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s authoritative status sections per root `CLAUDE.md`'s
instructions.
