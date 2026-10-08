# RESUME 2026-10-07: Pluvier set, punctuation/command lessons, numbers (next session)

Nothing of this session is committed. `pytest src/test/` (1207 tests) and bare `mypy` were green at the last run; the trainer was checked in headless Chrome
(lesson list, intro, drill, style toggle, Definitions), never with a real Starboard, and the new chords were never typed in Plover.

## Done this session

1. **Plover plugin dictionaries.** `plover_stenalgo_pluvier_punctuation.json` is listed in `system.DEFAULT_DICTIONARIES` **below** `plover_stenalgo_punctuation.json`
   (Plover 5 has no disabled-by-default entry; the higher dictionary wins a shared chord; a Pluvier user toggles a set in Configure > Dictionaries).
   `util/export_plover_plugin.py`: the Pluvier file is in `COMPLEMENTS` (no `EXTRAS` any more).
2. **Pluvier set is complete and independent** (131 entries): all Plover-derived punctuation + commands + the 22 Pluvier chords, which win a chord both define
   (only `spmR-jktn`: `!` in Pluvier, `:` in Plover). `completePluvier` in `util/export_plover_complements.py`.
3. **Settled Pluvier rows**: `STROFL` = "strophe" (Pluvier's own dictionary maps it to the word, no `-L` sound) -> apostrophe `{^'^}` on `stR*esd` / `stRe#sd`;
   guillemets `ks*ij`, `ks*ij/ks*ij` (+ `#` twins); dash `t*ie#R`; parentheses `pR-nl` / `pR-nl/pR-nl`; percent `pR-n` = `{^%}` (glued, no space); `OE`, `PWHR-BG` covered by `t-d`, `svmt-k`.
   These chords were chosen by me: confirm by typing them.
4. **Plover-side additions**: single quotes become the French inner quotes `vw-sR` `{~|“^}`, `vw*sR`/`vw-#sR` `{^~|”}`; `COMMAND_ALIASES`: BackSpace `mt-jk` (+`*`/`#`), Return `w*s`, glued newline `w-s`,
   Delete `pv*iel`/`pvie#l`; straight guillemets `vt@Rl` / `vw@Rl` (`{~|"^}`, `{^~|"}`; phonetic aliases, so in both files). Plain Return/BackSpace/Delete did not exist before.
5. **Trainer lessons, both styles** (S10d, `util/export_punctuation_lessons.py` -> `steno-trainer/public/data/punctuation-lessons.json`; plan in `~/.claude/plans/jiggly-scribbling-flute.md`):
   tracks `ponctuation` (7 lessons) and `commandes` (6) between desambiguisation and affixes; drills are phrases (`Oh !`, `Il dit : « Merci »`, paired marks together), commands are bare chords and are never executed.
   Authored inputs: `resources/punctuationLessons.json` (families, punctuation entries, `keywords`) and `util/punctuation_examples.jsonl`. Added to `dictionary.py`, CLAUDE.md, docs/PIPELINE.md.
6. **Global Plover/Pluvier switch** (`steno-trainer/src/Style.elm`, sidebar next to X-SAMPA/IPA; session-only; default Plover): swaps lesson texts, drill chords and the Definitions page.
   Each style offers **only its own chords** (a meaning keeps the other style's chords out as soon as the style has one of its own; shared chords such as the brackets stay). Rule lines: one stable order (authored order,
   "ouvrante" before "fermante"; commands by key, modifiers, repeat), format `Le crochet fermant ( ] ) : mtw*dRn.`. Definitions finds a mark by glyph, chord, `keywords` (`"` finds the guillemets) or name (3+ letters).
   Other Elm changes: `Drill.Segment.spaceBefore`, lesson words may carry `segments`, `isSegmented` in `Main.elm`, `phonologyLine`.
   `steno-trainer/main.js` is gitignored; rebuild with `elm make src/Main.elm --output=main.js` and hard-reload the browser.

## Open / to check next

- Commit (nothing is committed); plugin version bump + mirror sync (`util.sync_plover_mirror`) + reinstall; type the new chords in Plover (dash, parentheses, percent, straight guillemets, Return, Delete).
- The user reported `"` not found in Definitions before the last rebuild; after the straight-guillemet entries (glyph `"`) and a hard reload it should work: **verify in the browser**.
- Not yet in the sets, so not taught: Tab, Ctrl/Super shortcuts, Plover control (suspend/resume), F-keys (`phonetic-en`/`mnemonic` commands, TODO item 3), letters/fingerspelling (item 4).
- "Leçon N" numbering is global: affix/expression lessons shifted by 13.
- A way to switch Plover/Pluvier chords inside Plover itself (outside the dictionary panel) is still open (TODO).
- Expression data was not compared with the new chords (TODO item 1b).

## Numbers: comparison of Plover English, Lapwing, Pluvier (the next task)

We have **no number definitions**: `NUMBER_KEY = None`, the Stenalgo `#` is a homophone mark key, the stock dictionary only has words (`un`, `deux`, `cent s*@#/*#`, `mille`, `zéro`),
`dicofr.json` (Pluvier) has no digit entries. The `#` chords we kept are only number-bar twins of other entries (e.g. Shift+Return `w-#s`).

| | Plover English | Lapwing | Pluvier (TAO/LaSalle) |
|---|---|---|---|
| number key | `#` bar, shift-like; with a letter key gives a digit | `#` is a normal key, first in steno order (keymaps can put it on the top `S`) | same as Plover ("works exactly like common Plover theory") |
| digits | `S T P H A O F P L T` = 1 2 3 4 5 0 6 7 8 9 | right-hand numpad: `#-R` 1, `#-B` 2, `#-G` 3, `#-FR` 4, `#-PB` 5, `#-LG` 6, `#-F` 7, `#-P` 8, `#-L` 9 | Plover's mapping (Tao.md lists S-=1, T-=2, P-=3, H-=4, A=5...) |
| several digits | in steno order in one stroke (`#STPHAF` = 123456; `#SP-L #H #TAP` = 1384257) | one stroke per magnitude: `E` tens (`#ER` 10), `U` hundreds (`#UR` 100), `EU` thousands (`#EUR` 1000), glued with `{&N}`; separate `lapwing-numbers.json`; times `#-R/#-BG` = 1:00 | in keyboard order one stroke, otherwise two; series separated by commas |
| words for numbers | - | - | phonetic: 100 `SUN` (`S-N` multiplied), 1000 `PHRIL` (`WR-RB` multiplied + 000), others in Tao.md "Les nombres écrits phonétiquement" (9 `TPH-FL`, 14 `KORZ`, 20 `WR-`, 30 `TW`...); `-FRBGS`/`-RPBGS` glue a comma/period inside numbers |

Not verified (from memory, not read): Plover English `-Z` for "00" and `EU` to reverse digits; Lapwing's entries for 0, decimals, dollars/percent; the full `lapwing-numbers.json`
(<https://raw.githubusercontent.com/aerickt/plover-lapwing-aio/main/plover_lapwing/dictionaries/lapwing-numbers.json>), Pluvier's number rules (<https://raw.githubusercontent.com/Vermoot/Pluvier/main/TAO_Rules_Organized.md>,
local copy `resources/reference/Pluvier_TAO_rules.md`, French course `Tao.md` lines ~1699-1830 and ~3609, ~4107-4135).

Design options (my recommendation = 1): (1) Lapwing-style numpad on the right-hand keys with `#` held, `E`/`U`/`EU` for tens/hundreds/thousands (fits the 22 phoneme keys + marks; same chords for both styles);
(2) Plover bar mapping, needs a number mode because we have no number key; (3) Pluvier's phonetic words (`SUN`, `PHRIL`), mostly what the theory already does for spoken numbers.
Next steps: read the full Lapwing numbers file, decide the design with the user, document it in `docs/PLOVER_COMPLEMENTS.md`, add the entries to both sets (then the Plover/Pluvier lesson data picks them up), add a "Chiffres" lesson family
(`resources/punctuationLessons.json` + `util/punctuation_examples.jsonl`), and update TODO item (4).
