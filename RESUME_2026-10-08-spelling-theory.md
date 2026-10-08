# Handoff: design Stenalgo's own French spelling (single-letter typing) theory

Written 2026-10-08 to start a fresh session. Read this file, then `CLAUDE.md`, `docs/PLOVER_COMPLEMENTS.md` ("Fingerspelling" section,
the four candidate designs) and `docs/PIPELINE.md` (S8, S10d/e) before touching code. Nothing below is implemented.

## 1. Context: why this task exists

Stenalgo = French stenotype theory generator for the 26-key Starboard (`CLAUDE.md`, `docs/ARCHITECTURE.md`). The Plover plugin
(`plover_stenalgo/`) ships the theory plus complements (punctuation, commands, numbers). **Single-letter typing is not covered**
(`TODO.md` item 4, letters/fingerspelling; digits were done 2026-10-07).

The three existing spelling theories were converted KEY TO KEY (Ireland key -> Gemini PR button -> Stenalgo key on the same button,
`util/export_plover_complements.py` `convertOutline`, `GEMINI`, `starboardKeys`) and checked against the current theory
(171,737 outlines). Measured 2026-10-07, distinct colliding Stenalgo chords:

| Theory | Chords | Collisions | Notes |
|---|---|---|---|
| Plover English (`X*` lower `{>}{&x}`, `X*P` capital `{&X}`, `X*FPLT` letter+period) | 182 | **15** words (8%) | `*@`=an, `*a`=a, `*e`=eh, `*i`=hi, `*ie`=haie, `s*`=c, `m*`=m', `*ak`, `*aZm`, `s*ik`, `s*@ai`, + number-bar twins `*@#` han, `*a#` ah, `*e#` hé, `*ie#` hait |
| Lapwing (same `*` scheme + `X-FPLT` letter+period, `{^ ^}` spaced, Greek `-LGTS`) | 194 | **10** (9 words + 1 affix) | the same minus a few; `*id`=ides; `ejktn`=affix abbreviation `opté` |
| Pluvier / TAO (`X-FPLT` capital+space, `X*FPLT` letter+period+space, `X-RBGSZ` lower+`)`; Tao.md "Le mode épellation") | 79 | **1** (`ejktn` = U-FPLT = affix `opté`) | no word collision, BUT no plain lower-case letter exists in Pluvier (names/initials only; lower-case letters need an ending that does not exist) |

Findings that drive the new design:
- Endings made of 4+ right-hand coda keys (`-jktn` = top row of the right hand, `-sdRlm` = bottom row, `*jktn`) collide with nothing
  (no theory word, no first stroke, no punctuation, no number). Short suffixes (`*` alone) collide with words.
- A bare letter chord is a WORD in the theory (`@`=en, `i`=y, `ie`=est, `a`=à, `e`=et, `s-`=s'). So the letter chord needs a right-hand ending.
- Plover/Lapwing/Pluvier letter chords are Ireland shapes (`PW`=B, `TK`=D...) -> in Stenalgo they land on keys whose phonemes
  do not match the letter (Pluvier T = `p-`). The user judged none of the three worth keeping.

## 2. The task (the user's words, then the constraints)

> "None of these theories work well, lets come up with our own theory: a mapping of all French characters (a-z, à, â, é, è, ê, ô, ù, ï, ç)
> using the left-hand keys + vowel phoneme keys. All of ` ^ and ¨ should ideally have a common key each. On the right side we need 4 chords
> for the four pair combos: (lower-case, upper-case) x (no space, followed by a space). Simple chords (same line, or forming a square of
> 4 keys) are preferred. Combining left, thumbs and right hand, there should not be any conflicts."

Hard constraints:
1. Characters: a-z (26) + à â é è ê ô ù ï ç (9) = 35. Missing from the user's list but common in French: î û ë ü ÿ œ æ (and the capitals
   É À Ç ...): **ask the user** whether to include them (cheap if the diacritic keys compose with any vowel).
2. Letter chord = left-hand keys (onset bank, keys 2-9, plus `*` key 10 and the reserved `&` `%` keys 0-1 if free) + vowel keys (thumbs 11-14).
3. A diacritic key is shared by every letter that takes it: one key for grave `` ` `` (à è ù), one for circumflex `^` (â ê ô), one for
   diaeresis `¨` (ï). Also needed: acute `´` (é; the user did not list it among the three, so é may be the default of the e chord or have
   its own key: **decide with the user**) and cedilla (ç: its own key or the `c`+key combination).
4. The right hand supplies exactly 4 ending chords: lower/no-space, UPPER/no-space, lower/space-after, UPPER/space-after. "Simple" means
   keys on the same row across fingers (e.g. `-j -k -t -n` = 16,18,20,22) or a 2x2 square of keys.
5. No conflict for any complete stroke (left + thumbs + right) with: theory words (`plover_stenalgo_dictionary.json`), first strokes of
   multi-stroke outlines, punctuation / commands (`plover_stenalgo_{punctuation,commands,pluvier_punctuation}.json`), number chords
   (`reservedNumberStrokes()`, ~1100 chords with `#`), the affix abbreviation layer (`plover_stenalgo_affix_dictionary.json`, optional),
   the expression layer (`plover_stenalgo_expressions.stenalgo`: keyed by words; check how its outlines use strokes), and between letters.
   Every chord must be pressable (per-finger legal keypress tables below).
6. Output semantics must be Plover-expressible: `{&a}` glue, `{&A}` capital, an accented char is just `{&é}` (precomposed); the "followed by a
   space" form needs the right translation (check Plover: `{&a}{^ ^}` or a trailing space inside the glue; verify with `plover_stenalgo/`
   tooling or the trainer's `typePieces`).

## 3. Layout facts (verified in `src/keyboard.py`, `starboard3h.json`, `plover_stenalgo/_generated_keys.py`)

```
 index   0  2  4  6  8 [10*]            [15#]  16 18 20 22 24         top row    (key 0 `&`, 1 `%` = left pinky, reserved)
         1  3  5  7  9                         17 19 21 23 25         bottom row
                 thumbs: 11 12  |  13 14   (left thumb 11-12, right thumb 13-14)
 fingers: lp = 0,1,2,3   lr = 4,5   lm = 6,7   li = 8,9,10 | ri = 15,16,17   rm = 18,19   rr = 20,21   rp = 22,23,24,25
```
KEYS order (stroke renderer, indices 0-25): `& % k- s- p- v- m- t- R- w- * @- a- -i -e # -j -s -k -d -t -R -n -l -Z -m`.
Banks: onset 2-9 (left), nucleus 11-14 (thumbs), coda 16-25 (right). `*`=10 and `#`=15 are the homophone-mark keys (S7), `&` `%` reserved.
Legal key sets per finger (anything else is unpressable; `util.export_plover_complements.pressable(starboard, stroke)` checks it):
lp: single, (0,1) (2,3) (0,2) (1,3), all four | lr: (4)(5)(4,5) | lm: (6)(7)(6,7) | li: (8)(9)(10), (8,9) (8,10) (9,10), (8,9,10) |
lt: (11)(12)(11,12) | rt: (13)(14)(13,14) | ri: (15)(16)(17), (16,17) (15,16) (15,17), (15,16,17) | rm: (18)(19)(18,19) | rr: (20)(21)(20,21) |
rp: (22)(23)(24)(25), (22,23) (24,25) (22,24) (23,25), all four.
Right-hand 2x2 squares that are legal: {16,17,18,19}, {18,19,20,21}, {20,21,22,23}, {22,23,24,25}. Same-row runs: top 16-18-20-22-24, bottom 17-19-21-23-25.

Current phoneme assignment (1-2 key chords; `starboard3h.json`):
onset: k=2, g=2+3, f=2+4, s=3, b=3+5, p=4, d=4+5, S=4+6, v=5, Z=5+7, m=6, l=6+7, n=6+8, t=7, z=7+9, R=8, j=8+9, w/N/G=9.
nucleus: @=11, a=12, o=12+14, i=13, e=14, E=13+14, y=11+13, u=11+14, §=12+13, °=11+12 ... (full table in the JSON).
Natural letter<->key correspondences exist for most consonants (k, s, p, v, m, t, R=r, w, g, f, b, d, l, n, z, j); the awkward letters are
c (k or s), h, q, x, y. Vowels a e i o u y have thumb chords. The designer should decide letter-by-phoneme-position vs letter-name
(an explicit fork to propose to the user).

## 4. Candidate approach to validate (not decided)

- Letter chord = the left-hand onset chord that is the letter's main sound (b=3+5, d=4+5, f=2+4, g=2+3, j=8+9, k=2, l=6+7, m=6, n=6+8, p=4, r=8,
  s=3, t=7, v=5, w=9, z=7+9; c, h, q, x, y chosen by hand) or the vowel chord (a, e, i, o, u, y on the thumbs).
- Diacritics: one key each, held with the vowel chord. Natural free keys: `&` (0), `%` (1), `*` (10) for grave / circumflex / diaeresis (matches
  "one key per accent"); acute and cedilla still open (`#` 15 is the number/mark key; or defaults). `*` and `#` already carry S7 marks:
  every spelling chord holding them must be checked, and S7 can reserve chords exactly like the numbers (`reservedStrokes` in
  `composeReservedKeyStrokesForEntries`).
- Right-hand endings: 4 chords among the simple ones, e.g. rows of the right hand (`-jktn`-like), squares ({22,23,24,25}...), keeping lower/upper
  and space as two orthogonal gestures where possible (so the user learns 2 bits). Prior data says 4+ key coda chords collide with nothing,
  fewer keys may. The enumeration below decides; do not assume.

## 5. Method (do this, in order)

1. Enumerate letter chords (left + thumbs, legal) and ending chords (right, legal, "simple"); build the candidate stroke set
   `chord = letterChord U accentKey U ending`.
2. Collision engine: reuse `util/check_number_collisions.py` (`collisions()`, first-stroke index), the `plover_stenalgo_*.json` files and
   `reservedNumberStrokes()`. Report per ending: stroke count, collisions by category (word / first stroke / punctuation / command /
   number / affix / intra-set duplicate / unpressable). Choose the 4 endings minimising collisions, then the accent keys.
3. Where a residual collision remains, prefer another ending/accent key; as last resort reserve the chord in S7 (the numbers precedent:
   `util/export_plover_numbers.py` `reservedNumberStrokes`, `src/ambiguitychecker.py` `forbiddenMarkSymbols`), which moves a word's mark.
4. Write the dictionary generator (new `util/export_plover_spelling.py` + test), output `plover_stenalgo_spelling.json`; ship it in the plugin
   (`util/export_plover_plugin.py` `COMPLEMENTS`, `plover_stenalgo/plover_stenalgo/system.py` `DEFAULT_DICTIONARIES`, below the theory? decide;
   a spelling chord never equals a theory chord once collision-free, so the order is free).
5. Trainer: spelling lessons (same pattern as `util/export_number_lessons.py` -> `steno-trainer/public/data/spelling-lessons.json`; Elm side generic:
   `Style.elm`, `Lessons.elm`, `Main.elm`; Definitions entries). One theory only, so no new switch unless the user wants an alternative.
6. Docs: `docs/PLOVER_COMPLEMENTS.md` (replace the "Fingerspelling" candidate section by the adopted design), `CLAUDE.md` command list,
   `docs/PIPELINE.md`, `TODO.md` item 4, GLOSSARY if a new term appears.

## 6. Decisions to confirm with the user (ask before building; AskUserQuestion)

1. Extra characters: î û ë ü ÿ œ æ and capital accented letters (É À Ç ...)?
2. Acute and cedilla: own keys, defaults, or combinations? Which keys for the accents (`&` `%` `*` proposed)?
3. Letters by sound position (phoneme key = letter) or by French letter name /be/ /se/...?
4. The "space" meaning: a space AFTER the letter (as stated); also a spaceless run of glued letters is the lower/no-space chord.
5. Any wish to keep Pluvier/Plover/Lapwing as alternates (a switch like Style) or drop them for good.

## 7. Verification

- `pytest src/test/` and bare `mypy` must pass (1225 tests on 2026-10-08; `CLAUDE.md` "Verification approach", typing conventions: annotate
  every function, parameterise generics, no variable reuse with another type).
- Collision report = 0 for the final set against all categories of section 2.5; every chord pressable.
- Round-trip: `renderFinalStrokesToRTFCRE` of the chosen key sets parses back (`util/export_punctuation_lessons.checkedOutline`).
- If the theory/S7 changes: rebuild per `docs/PIPELINE.md` (S7 `python -m util.build_disambiguated_theory`, then exporters; remove
  `AffixSelection.pickle` after a theory change); `DisambiguatedTheory.pickle` fingerprints its inputs.
- Trainer: `cd steno-trainer && elm make src/Main.elm --output=main.js`, headless Chrome check, hard reload.
- Never wait on a background job with `pgrep -f` (CLAUDE.md Process rules).

## 8. Reusable code map

- Conversion/pressability: `util/export_plover_complements.py` (`parseIreland`, `convertOutline`, `pressable`, `starboardKeys`, `GEMINI`),
  `util/_stenorender.py` (`renderFinalStrokesToRTFCRE`).
- Collision tools: `util/check_number_collisions.py`, `util/export_plover_numbers.py` (`reservedNumberStrokes`, `convertEntries`).
- S7 reservation: `src/ambiguitychecker.py` (`forbiddenMarkSymbols`, `assignMarkNodeCodes`, `composeReservedKeyStrokesForEntries`), `dictionary.py`
  `buildDisambiguatedTheory`, `util/_theoryio.py` fingerprint inputs.
- Lessons: `util/export_punctuation_lessons.py` (`phraseItem`, `typePieces` with `{&..}` glue, `ruleLines`), `util/export_number_lessons.py`,
  `util/number_lessons.py`, `resources/numberLessons.json`, Elm `Lessons.elm` (`mergeNumberData`), `Definitions.elm`.
- Reference data for comparison: Lapwing `lapwing-base.json` (aerickt/plover-lapwing-aio), Plover `main.json`, Tao.md "Le mode épellation".
