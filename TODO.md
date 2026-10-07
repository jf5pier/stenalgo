# TODO

Written to survive a `/clear` — read this file first in a fresh session.

## Branch TODO — Plover expression dictionary plugin (abbreviations branch, 2026-10-04)

State: plugin built, installed in the user's Windows Plover 5.4.1 and working on a Starboard (`de l'` verified live); data export in `util/export_expression_data.py`,
docs in `docs/PIPELINE.md` S8.10. Open items, most important first:

- **INVESTIGATE LATER — plain-word shadows of unabbreviated pool pairs.** `et les` / `et la` / `par la` / `par les` compose to their LONGFORM (`e/mte`, `e/mta`,
  `paR/mta`, `paR/mte`): the `et`, `les`, `la`, `par` attaches are all prefix rules, so in a hostless pair the first has no neighbour (`noNeighbour`) and the two cannot
  union into one stroke (shared keys 16 and 19). The longform is also the stock theory's two-stroke word `hélé`, `héla`, `parla`, `parlé`, so the plugin returns `None` (a plain
  reading) and the stock dictionary wins. The ranker already prefers the attested `et` + `les` by frequency; the plugin discards plain readings by design. To study: how many frequent
  pool pairs collide with a stock word's outline (the "plain-word shadows"), whether the stock theory should move the rare word (a mark on `hélé`) or whether a suffix/hostless form
  of `et`/`les`... is worth a slot. Do NOT make the plugin override plain-word outlines without a decision (it changes the stock theory's output).
- Remaining real-Plover mismatches (`scratch/plover_translator_sim.py`, 1,095 of 1,151 pool expressions = 97.4% of mass): the four shadows above; elision twins that share one chord (`que l'` /
  `que le`, `dans l'`, `et d'`: only the more frequent one is writable); wrong readings of unattested partial chords (`il m'a` -> `de l'a`, `rapport d'impôt` -> `rapport de hein peau`);
  `d'œil` written `d'oeil` (theory spelling vs pool spelling; check where the attested text is lost).
- **Install source: `github.com/jf5pier/stenalgo-plover`** — version 0.2.0 ships the stock dictionary and the `.stenalgo` data inside the package (`dictionaries/`, asset URIs in `system.DEFAULT_DICTIONARIES`); the mirror alone stores them (gitignored here).
  Publish with `python -m util.sync_plover_mirror <clone> --push` after `export_expression_data` (mirror at `bffad81`, 2026-10-04; a pip install from it was checked in a scratch folder). Remaining: test the install in the real Plover
  (`plover_plugins install git+https://github.com/jf5pier/stenalgo-plover` with `PYTHONUSERBASE`, `--force-reinstall` on a same-version reinstall) and edit the existing `plover.cfg` dictionary list of the Stenalgo system (the
  defaults apply only to a config with no list of its own; Plover closed, ask first); bump `version` on every theory change.
- **Expression lessons in the trainer (2026-10-04): DONE, committed on `abbreviations`.** Python: S10a `util/export_expression_lessons.py`, S10b `util/export_expression_sentences.py`, spec `docs/specs/expression-lessons.md`,
  files `expression-lessons.json` (27 lessons, 430 items, 69 rules) and `expression-sentences.json` (139 sentences), `expressions` stub track in `lessons.json`. Elm: optional merge of both files (`Lessons.replaceTrack` keeps track order
  whatever file arrives first), `Drill.PracticeWord.ruleRanks`, `Keyboard.viewExpressionLegend`, the "Abbreviation rule hint" now covers the expressions track and abbreviated sentences, an "Abbreviated sentences" switch in Sentences mode.
  Checked in headless Chromium (lesson intro and drill, brief lesson, legend, sentences switch, both files absent); NOT tried with a real steno machine. Open: the current-word highlight of an abbreviated sentence follows the
  abbreviated outline (lags when the learner types the plain outline); a brief is composed alone because the composer matches attach particles first (`avec`, `dans la`, `dans les`, `toutes les`, `avec les` never use their brief in the
  full composition: check the decoder reads them); a trainer item takes the first reading of each word.

- **Clean-profile test of the Plover plugin install (2026-10-04, for another time).** Check that a first-time user gets working dictionaries without hand-editing `plover.cfg`: install only
  `git+https://github.com/jf5pier/stenalgo-plover` into a fresh Plover config (a spare Windows user, or an empty config directory; read how Plover 5.4.1 picks its config folder first), switch
  to the "Stenalgo French" system, and check in `plover.log` that the four default dictionaries load (`user.json`, `commands.json`, then the packaged expressions above the packaged stock JSON) with no
  invalid-steno or fingerprint errors. Also check: the English-system trap (dictionaries loaded before the system switch gave 171k invalid-steno errors), the machine (Gemini PR) and keymap steps a new user
  still does by hand, and that a GUI dictionary-list edit freezes an explicit list that later plugin updates do not change. Then write the first-time install section of the mirror README (plugin install,
  choose the system, choose the machine) and add it through `util.sync_plover_mirror`. Verified so far only on the existing profile: removing the `dictionaries =` line of the system section made
  the defaults apply.

- **Briefs out of the `.stenalgo` file into their own `.json` for Plover.** The 40 forced briefs (and the selected briefs) are plain outline -> text entries, so a stock JSON dictionary can hold them: the
  decoder needs them only to recognise a brief as a reading, the plugin does not need to compose them. To do: export them (outline in RTFCRE, written text) as `plover_stenalgo_briefs.json` next to the
  stock dictionary, drop `rules.briefs` from the `.stenalgo` data, load them into the decoder's content index from that file (with its own fingerprint, like the word index) or leave them to Plover's own lookup
  and keep them only as ranking/shadow information; check the pure-brief rank (class 1) and the `isExpression` rule still hold, and update `docs/PIPELINE.md` S8.10.
- Test more strokes in the GUI (the elision glue `qu'{^}`, briefs, clusters) and record what differs from the simulation; the Gemini PR keymap of the Stenalgo system worked unchanged.
- The user's `plover.cfg` still says `[System] name = Lapwing` (plugin not installed under Plover 5.4): harmless fallback to English at each start.
- Pipeline integration: `python dictionary.py` does not run `util.export_expression_data` / `util.export_plover_plugin` (the rule set comes from `scratch/expr-*`, produced by
  `scratch/select_expression_rules.py`, not by the pipeline). Decide when the layer joins the orchestrator.
- The 5,000-word probability cut (`UNIT_PROBABILITY_WORDS`) was measured on the committed rules (`scratch/rank_static_rule.py`: 0.17% of the contested open-set mass changes winner); re-measure
  after a rule-set change. `docs/GLOSSARY.md` has duplicated entries in the expression-layer section ("Decoder (expression layer)", "Key conflicts"), a merge leftover to clean.

## Branch TODO — complementary Plover plugins and commands for the base theory (abbreviations branch, 2026-10-05)

- **Review what the Plover ecosystem offers.** Survey the popular plugins and `commands.json` files (Plover's stock `commands.json`, `main.json`/`user.json` conventions, Lapwing, Plover Plugins Registry, and the dictionary-adjacent
  plugins: plover-stroke / plover-dict-commands / plover-last-translation / plover-emoji / plover-number-format and the like) and rank them by popularity and by how well they complement a base theory.
  Output: a short report (e.g. `docs/PLOVER_COMPLEMENTS.md`) listing, per candidate, what it adds, whether it depends on key positions, and whether it fits the Stenalgo French system.
- **Minimum gaps in Stenalgo today** (the shipped dictionaries cover words and expressions only; `commands.json` is whatever the user brings): punctuation (with the French spacing rules: space before `: ; ? !`, none before `, .`, guillemets),
  alphanumeric characters (letters, fingerspelling, capitals, digits and number mode; `NUMBER_KEY = None` in `plover_stenalgo/system.py` means no number key exists), special keyboard keys (Return, Tab, Escape, BackSpace, Delete,
  Home/End, Page_Up/Page_Down, arrows, F1-F12) and their combos (`{#Control_L(Left)}`, `{#Control_L(c)}`, `{#Alt_L(Tab)}`, ...).
- **Layout dependence.** Many stock entries are written for the Ireland (Plover default) key layout, so their RTFCRE outlines (`-PL`, `STPH-`...) hit different physical keys in the Stenalgo layout (`_generated_keys.py`, `GEMINI_PR_KEYMAP`).
  Investigate what is needed to convert them: classify each entry as (a) layout-independent (the output side, e.g. `{#Return}`, kept as is), (b) outline-dependent (must be re-assigned a Stenalgo stroke), or (c) mnemonic-dependent
  (letters/steno-order meaning lost), then design the conversion: a mapping from the Ireland key to the Stenalgo key per entry kind, a collision check against the existing theory (reuse `src/keyconflicts.py` and the attach/selector keys),
  and a generator (`util/export_*`, output into the plugin's dictionaries, fingerprint-checked like the others). Decide the French-specific conventions at the same time (accented letters, AZERTY vs QWERTY effect of `{#...}` combos:
  Plover sends key names, so check the keys meant by `Control_L(c)` on an AZERTY/Bépo host).
- **Fit with the other TODOs.** Decide whether these entries ship in `user.json`/`commands.json` defaults of the system (`DEFAULT_DICTIONARIES` in `plover_stenalgo/system.py`) or as a new packaged dictionary, and keep the stroke budget
  in mind: they must not take outlines already used by words or expression briefs (run the ambiguity checks after adding them).

## Branch TODO — compare docs/GLOSSARY.md with the grahp.dev steno glossary (abbreviations branch, 2026-10-05)

- **Reference to add.** `https://grahp.dev/steno-glossary` ("A glossary of steno terms I've made", unnamed author, ~80 terms, **CC BY-SA 4.0**). Add it to `docs/PRIOR_ART.md` (survey of existing theories and systems) and to the README `## References` list
  (README lists numbered references `[1]`-`[3]` today, all papers; add the next number with title, URL and access date). Note the licence: reusing its wording needs attribution and share-alike, so prefer citing and comparing over copying definitions.
- **Compare, term by term.** Its terms, as read from the page: Key, Chord, Stroke, Outline; Translation, Command, Untran, Entry, Dictionary, Lookup, Reverse Lookup; Generated, Programmatic, Modal, JSON Dictionary; Theory Rule, Theory, Long, Short,
  Phonetic, Orthographic, Full-English, Hobbyist, Professional; Conflict, Conflict Resolution, Word Boundary, Word-affix, Homophonic, Proper Noun; Writing, Write-out, Brief, Misstroke, Arbitrary, Phrase, Shorten, Mandatory, Vestige, Raw Steno;
  Steno Order, Layout, WSI Layout, Extended Stenotype Layout, Steno Writer/Machine/Keyboard, NKRO, QWERTY, WPM; Steno Engine, Plover, Javelin, Embedded, System, Text Input System; Chorded, Serial; Bank, Initial, Vowel, Final, Skeleton, Label, Merge;
  Fingerspelling, Orthospelling, Shrimple, Unique, Dedicated, Realtime, Undo Stack. Method: read the page in full (the list above is a summary), and for each term mark it as (a) already in `docs/GLOSSARY.md` with a compatible meaning,
  (b) in the Stenalgo glossary under a different name or a different meaning, (c) missing from ours, (d) not relevant (hardware, engines).
- **Deliverable: a list of suggested corrections and additions**, not an automatic edit, for the user to decide (the glossary's terminology was settled in the Glossary Review, Pass 1d: do not re-litigate it without cause). Likely candidates to check:
  *Brief*, *Conflict*/*Conflict Resolution* vs our ambiguity and disambiguation vocabulary, *Homophonic* vs our same-lemma / different-lemma homophones, *Long*/*Short* vs our long form and abbreviations, *Word-affix* vs the S9 affix rules,
  *Phonetic*/*Orthographic* theory, *Misstroke*, *Untran*, *Shrimple*, *Mandatory*, *Vestige*, *Skeleton*, *Bank*/*Initial*/*Vowel*/*Final* vs our onset/nucleus/coda, *Steno Order*, *Layout* (vs the Starboard layout), *Realtime*.
  Where Stenalgo uses a community term in another sense, flag the clash in the glossary ("avoid"/"not to be confused with") rather than renaming. Also check that our docs use the community terms for the Plover-facing parts (S8, the plugin, the README).
- **Verify.** Doc-only change; if any term in `docs/GLOSSARY.md` is renamed or added, grep the docs and code comments for the old term, and run `pytest src/test/` only if a test checks the glossary.

## Branch TODO — stand-alone brief suggestor for personal Plover dictionaries (abbreviations branch, 2026-10-05)

- **Goal.** A tool for a user who wants to add their own brief to a personal `user.json`: type a word (or phrase), get several candidate brief strokes, each shown with the long form (the full-word outline from the published theory)
  so the learner sees what the brief shortens. First target: the Elm trainer website (static, no server). Check whether that is feasible; fall back to a small stand-alone page or a CLI (`python -m util.suggest_brief WORD`) sharing the same algorithm.
- **Limit by design.** It knows only the published Stenalgo theory (the data the trainer already loads: `practice-words.json`, `definitions.json`, `keyboard-layout.json`, the affix and expression JSONs). It cannot see the user's own `user.json`,
  so it cannot detect conflicts with the user's entries: say so on the page, and offer an optional "paste your dictionary JSON" box that checks the candidates locally in the browser (nothing uploaded) as a later step.
  It must still avoid conflicts with the published theory (words, affix abbreviations, expression briefs): look the candidate up in those data and drop or flag collisions, reusing the key-conflict rules (`src/keyconflicts.py`, the overlap rule of the max-1-key section above).
- **Word known to the dictionary.** Take its long form (phonetic outline and strokes) and propose briefs by **phoneme overlap with the original**: keep the stressed/onset-and-coda skeleton in one stroke, drop unstressed syllables, try prefix/suffix
  forms, ranked by how many phonemes survive in order and by finger cost (`FingerWeights`/`PositionWeights` in `src/keyboard.py`). Study what `deriveBriefStroke` (`src/expressionrules.py`) and the affix rules (`docs/AFFIX_DESIGN.md`) already do,
  so the suggestions follow the same conventions as the shipped briefs; the algorithm should be ported to Elm or precomputed (decide: precompute per-word candidates into a trainer JSON, which is simple but large for 167,639 Words, versus a small Elm port working from the stroke data).
- **Word new to the dictionary.** No phonetics available: use a **simple spelling heuristic** (grapheme-to-phoneme rules for French, e.g. the common digraphs `ou`, `on`, `ch`, `qu`, `eau`, silent final letters, `gn`) to guess a rough phoneme string, then run the same overlap procedure
  and show the guessed long form, clearly labelled "guessed". Consider reusing the lexicon builder's or the Synthetic lexicon's phonetizer if one exists (`util/completeVerbParadigms.py`, S2 appenders) and measure the heuristic on known words (accuracy of guessed vs real phonemes) to set expectations.
- **Output.** For each candidate: the brief stroke (keys highlighted on the Starboard picture, as in the trainer's keyboard view), the long form beside it, the length saved, and a copy-ready JSON line `"BRIEF": "word"` for `user.json`, plus a reminder that the user's dictionary
  priority decides which entry wins. Several suggestions per word (e.g. 3 to 5), not a single answer.
- **Verify.** Run the suggestor over the shipped briefs and affix abbreviations and check that it would have proposed (or ranked high) the real ones; pytest for the Python reference, an Elm test for the port; no pipeline rebuild unless a precomputed JSON is chosen (then add it to the exporter list and the md5 comparison).

## Branch TODO — publish the Starboard layout as an SVG for plover_svg_layout_display (abbreviations branch, 2026-10-05)

- **Target plugin** (`github.com/opensteno/plover_svg_layout_display`, MIT): it shows the last stroke on a custom picture. Per its README a layout is two files, settings being saved per steno system (`Ctrl+S` in the display window):
  an **SVG** whose top-level `<g>` elements each have a unique `id`, and a **Python script** with `def convert_stroke(stroke: Tuple[str, ...], translation: str) -> List[str]` returning the ids of the shapes to draw (in order, later ones on top).
  The default is `:/svgld/en_layout.svg` + `:/svgld/en_convert.py`; the layout and script paths are typed in the settings. The README does not say how a third-party system ships its layout.
- **Still to search/read** (the README is thin): the plugin's source (how `stroke` is passed: RTFCRE keys of the active system? `translation` use?), its default `en_layout.svg` / `en_convert.py` as a model, the Plover plugin registry
  entry, open issues about custom systems, and whether other systems (Lapwing, Emily's modifiers) already publish layouts for it.
- **Design.** A generator `util/export_svg_layout.py` from `starboard3h.json` (via `src/keyboard.py` / `Starboard`, the same source as `util.export_plover_system` and `util.export_keyboard_layout`): one `<g id="key-<name>">` per
  key of `KEYS` (`_generated_keys.py`) placed at the Starboard's physical positions (reuse the geometry the trainer's `keyboard-layout.json` already has), each labelled with its phoneme and, where useful, coloured by finger;
  a base shape plus a lit variant per key; the star/hash/attach keys marked as in the realization-report legend. The generated `convert_stroke` maps the stroke's RTFCRE keys (as `plover_stenalgo/stroke.py` `parseStroke` reads them,
  with `IMPLICIT_HYPHEN_KEYS`) to the lit-key ids, stdlib-only. Outputs: `stenalgo_layout.svg` + `stenalgo_convert.py`, and a check that the id set equals `KEYS` so a layout change cannot leave them stale (a test, like the `_core` staleness test).
- **Evaluate where it lives.** Ship in the plugin package (`plover_stenalgo/plover_stenalgo/`, next to the dictionaries; `export_plover_plugin` copies them, the sync to the `stenalgo-plover` mirror carries them) with a README section: "in the SVG
  Layout Display settings set the layout path to ... and the script path to ...", locating the installed files (the plugin's `site-packages` path, or a one-line `python -c` that prints it). Compare with a separate download/documented
  location and with offering it as a PR to the display plugin's own layouts. Check that the paths accept absolute file paths on Windows (the Plover install is on Windows, see the install memory note) and that the `:/svgld/` resource form is not needed.
- **Verify.** Load it in Plover 5.4.1 with the Stenalgo system, stroke a few chords (including `*`/`#` marks and two-stroke words) and compare with the trainer's keyboard view; add a pytest for the generator and mypy; no pipeline rebuild (layout-only output, rerun after an adopted layout change).

## Branch TODO — trainer input mode: keyboard or Plover (abbreviations branch, 2026-10-05)

- **Goal / UI.** Let the learner choose the trainer's input: the connected keyboard (Web Serial, Gemini PR: `steno-trainer/js/serial.js`, `src/Ports.elm`, `src/GeminiPr.elm`, `Main.elm` `IncomingBytes`)
  or Plover typing into a text field. The mode switch is remembered in localStorage. In Plover mode the trainer shows a focused text field and compares the produced text to the expected word.
  Weakness: text shows only the translation, not the strokes, so a right text from wrong strokes, abbreviations and undo are invisible; hence the two investigations below.
- **INVESTIGATE — a Plover extension that emits the strokes.** `plover_stenalgo` is a pure dictionary plugin (entry points `plover.system` and `plover.dictionary` only): it subscribes to no engine hook and cannot observe strokes.
  Add a `plover.extension` entry point (class with `__init__(engine)`, `start`, `stop`) using `engine.hook_connect('stroked', ...)` (the stroke's keys / RTFCRE) and `'translated'` (old/new translations, undo).
  Check: the hook signatures in the installed Plover 5.4.1, whether `stroked` fires for the undo stroke `*`, the behaviour when the Stenalgo system is not the active one, and that the extension loads on the Windows install (see the Plover install memory note).
- **INVESTIGATE — transport from the extension to the trainer.** (a) A local WebSocket server inside the extension; the trainer page connects to `ws://localhost:PORT` (check mixed content, CORS/origin, port conflicts; compare with the existing plover-websocket-server plugin).
  (b) Localhost HTTP with SSE or polling. (c) No transport: the extension types a tagged sentinel into the focused field (fragile, pollutes the text). (d) Clipboard or file (awkward). Prefer (a).
  Message: `{"keys": [ids], "rtfcre": "...", "undo": bool}`, using the key ids already shared through `_generated_keys.py` / `plover_stenalgo/stroke.py` `parseStroke`, so the trainer needs no re-mapping.
- **Trainer side.** A new port `incomingStroke` plus a small `js/plover.js` WebSocket client (reconnect, status like `serialStatus`); the message becomes the `Set Int` that `Drill.applyStroke` already takes.
  The Gemini PR path stays untouched. Without the extension, the text-field mode falls back to comparing the text only.
- **Verification once built.** A pytest for the extension's message builder (stdlib-only, tested like `_core`), an Elm test for the port decoder, `mypy` clean, `util.export_plover_plugin` refreshed, a manual run
  with real Plover and the trainer in Chromium and Firefox. No pipeline rebuild: the theory does not change.

## Branch TODO — trainer lessons: focus or recap switch (abbreviations branch, 2026-10-05)

- **Goal.** Each lesson gets a switch between two practice modes: **focus** (only the current lesson's words) and **recap** (a 50-50% mix: half current-lesson words, half words drawn from the previous lessons).
  The mode is remembered in localStorage, like the other trainer preferences.
- **To settle.** How the recap half is drawn (uniformly over all previous lessons, or weighted toward recent ones or toward words the learner missed); behaviour on the first lesson (no previous words: the switch is disabled or falls back to focus);
  whether it applies to the affix and expression lesson tracks too (`affix-lessons.json`, `expression-lessons.json`) or only to the base lessons (`lessons.json`).
- **Where.** Trainer side only (Elm: the lesson/drill word selection in `steno-trainer/src`, plus the switch in the lesson view); `util/export_lessons.py` already writes per-lesson words, so check that the previous lessons' words are reachable
  from the JSON before adding any export field. No pipeline rebuild if the selection stays in Elm; add an Elm test for the 50-50 mix.

## Branch TODO — trainer Definitions page: attach words and composed attach words (abbreviations branch, 2026-10-05)

- **Goal.** The trainer's "Definitions" page (`steno-trainer/public/data/definitions.json`, `util/export_definitions.py`) should also present the **attach words** (the particles written as an attach keypress on a host:
  `de`, `la`, `le`, `les`, `par`, `et`, `sur`...) and the **composed attach words** (several particles chained, e.g. `de la peau`, `sur le sol`), not only the dictionary words and the affix "Abbrev." column (S9d).
- **Information per entry.** The long form (the plain outline(s) that write the words out), the shortest form (the attach/abbreviated outline the expression layer produces), and the homophones as usual (the page's existing homophone presentation).
- **To settle.** Which entries to list (every attach rule of `scratch/expr-rules-final.json`, or only those that occur in the expression lessons; composed ones from the pool of `expr_candidates.tsv` or from the composer's output);
  how a composed entry is keyed and searched (by its words, like a phrase); how the attach host is shown (a rule can need a host: the `noNeighbour` / hostless case, `docs/PIPELINE.md` S8.10);
  whether the shortest form depends on the host (then show a representative one, or one per host class).
- **Where.** Python side: a new exporter or a section of `util/export_definitions.py` / `util/export_expression_lessons.py` reading the same inputs as the expression layer (both pickles, `starboard3h.json`, the committed expression rule set, `plover_stenalgo_dictionary.json`), output next to the other trainer JSONs; Elm side: the Definitions view.
  Reuse the expression composer so the shown shortest form equals what the Plover plugin emits. Rebuild and compare the md5s of the trainer JSONs other than the new one (they must stay identical), `pytest src/test/` and `mypy` clean.

## Branch TODO — a Dosh/Taipo-style chorded French typing layer on the Starboard (abbreviations branch, 2026-10-05)

- **Idea (user).** Use the Starboard as a plain chorded keyboard for French letters, symbols and control keys, with the left half of the keyboard defining the chords and the right half mirroring it
  (hands alternate, as in Taipo/Dosh). Non-modal French letters: `é è ê à â ç ù`. Every other accented letter is built with a modal dead key `^` `¨` `` ` `` if needed. No dedicated `œ` key. This would also answer the open fingerspelling
  point of `docs/PLOVER_COMPLEMENTS.md` (what the French theory uses to select a letter), and the letter selector of Emily's/Jeff's modifiers.
- **Survey so far (2026-10-05, thin).** Dosh (<https://www.davidb.org/post/2026/dosh/>): an 18-key chording layout (9 keys per hand, fully symmetric halves, free hand alternation including double letters), built for the Taipo system
  (<https://www.davidb.org/post/2024/taipo/>, not read yet): modifiers are Taipo's, on same-finger vertical pairs; 19 of the 26 letters are shared with Taipo; punctuation and digits follow the Posh layout (<https://inkeys.wiki/en/keymaps/posh>, not read);
  the author measured chord times with a drill app and moved the apostrophe off a two-finger-both-thumbs chord (1330 ms average) to a single chord. The full cheat sheet is `DOSH.md` in the author's firmware repository (not read), the implementation is one file.
  A search for other chording layouts only turned up Georgi (QMK chord engine), QMK combos, Half-QWERTY and ASETNIOP; nothing equivalent for French.
- **To do.** (1) Read the Taipo and Posh pages and `DOSH.md`; check the Dosh licence before reusing chords (cite, do not copy). (2) Count the Starboard keys per half and which fingers can chord (the pinky-square rule of `src/keyconflicts.py`
  forbids diagonals and three-key pinky presses, which Dosh also avoids by dropping the upper pinky key), and what the thumbs offer. (3) Frequency-rank the French characters (letters, `é è ê à â ç ù`, space, `, . ' - ? ! : ;`, digits, the control keys) from the corpora
  already in `resources/` and assign chords by comfort, the way the layout solver weighs finger strain (S4); this is a new CP-SAT model or a hand design. (4) Dead keys: `^` `¨` `` ` `` as one-shot modifiers composing with a vowel (`ê`, `ï`, `ù`...);
  decide whether `œ` and `æ` are then typed with no key of their own (`o` + `e` stroked in sequence, or a Plover entry). (5) Layer switching with the steno theory (a chord on a reserved key such as `&` or `%`, to be checked against the word theory with `src/keyconflicts.py`).
  (6) Output as a firmware layer or a Plover dictionary; the static-JSON route keeps Plover's reverse lookup, firmware does not need Plover. (7) A drill in the trainer (a new lesson track) with the timing capture that Dosh used.
- **Open.** Whether a typing layer belongs in Stenalgo at all, or only the symbol/control-key subset (which is the minimum gap of `docs/PLOVER_COMPLEMENTS.md`); how the mirrored half interacts with the star/hash keys.

## Branch TODO — Plover system plugin: more machine protocols (abbreviations branch, 2026-10-05)

- **Today.** `plover_stenalgo/system.py` has `KEYMAPS["Gemini PR"]` only, generated into `_generated_keys.py` (`GEMINI_PR_KEYMAP`) by `util/export_plover_system.py`.
  Plover picks the keymap by the machine's name, so any other machine has no mapping.
- **DONE 2026-10-05 (code), to verify on the board: `KEYMAPS["Plover HID"]`** = `PLOVER_HID_KEYMAP` (same labels as Gemini PR; the `plover-machine-hid` source confirms the key names `S1-`..`-Z`, `*1`-`*4`, `#1`-`#9`, `#A`-`#C`, `X1`-`X26`), generated by `util/export_plover_system.py`, plugin version 0.3.0, test `TestMachineKeymaps`. NOT yet checked: whether the QMK HID bit of keys 0, 1, 2, 10, 15 yields `#A #B #C #1 *4` like the sniffed Gemini bits (press each key alone with the Plover HID machine and read the paper tape). Original item: add `KEYMAPS["Plover HID"]` (machine from the `plover-machine-hid` plugin). Check that the plugin's key names are the Ireland names
  of Gemini PR; if so the map is the same table, otherwise derive it. The 26 extra `X1`-`X26` keys have no Stenalgo role yet: leave unmapped, or use them for the typing layer.
- **Review the other machines Plover offers** (the English Stenotype system lists, as far as I remember, `Keyboard`, `Passport`, `Stentura`, `TX Bolt`, `Treal` besides `Gemini PR`; check Plover 5.4.1):
  `Keyboard` (QWERTY, NKRO) is worth a map as a no-hardware way to try the theory (also give `Keyboard` a printable key layout, e.g. in `docs/`); `TX Bolt` carries only 24 keys, fewer than Stenalgo's 22 phoneme keys plus `*`, `#`, `&`, `%`,
  so it can only work for a subset and probably not at all; the others by key count. Decide per machine: map, document as unsupported, or skip.
- **Generator and tests.** Extend `util/export_plover_system.py` to write one table per supported machine from `starboard3h.json`, keep `_generated_keys.py` as the single source, add a test that every mapped machine
  key resolves to a Stenalgo key and that none is mapped twice; `util.export_plover_plugin` and `util.sync_plover_mirror` must carry the change (the install-source repository), and the plugin version bumps.
- **Trainer follow-up (separate TODO above).** A Plover HID board needs a WebHID reader besides `serial.js` / `GeminiPr.elm`.
- **No pipeline rebuild.** The theory, dictionaries and trainer data do not change; check `pytest src/test/` (the `_core` copy test) and `mypy`.

## Branch TODO — verify the `-ment` affix rule (abbreviations branch, 2026-10-06)

- **Observed.** `gouvernement` gets a `-ment` affix abbreviation, but `environnement` does not. Check why (`affix_rules_report.md`, `affix_rules.json`, `affix_decisions.json`,
  `docs/AFFIX_RULES.md`, the trainer's affix lessons): a legitimate selection result (the rule's coverage or cost threshold, the stem/word being in a different route) or a bug in the matching of the suffix on `environnement`
  (spelling `environement`/`environnement`, the `-nement` ending, a phonological mismatch of the final `@`/`mA~`). Fix or document, then rebuild the affix layer (S9) and compare the S9 md5s.

## Branch TODO — trainer Introduction page (abbreviations branch, 2026-10-06)

- The trainer now lands on an "Introduction" page (`viewIntroPage` in `steno-trainer/src/Main.elm`) that only says "À venir." Write it: what Stenalgo is, the Starboard layout and its two machine protocols (Gemini PR over serial, Plover HID), how the modes fit together (Leçons, Mots, Phrases, Définitions), what the hints, the abbreviation hints and the abbreviated sentences are, and the phonetic notation switch (X-SAMPA / IPA).

## Branch TODO — star/hash marks belong to the lemma (abbreviations branch, 2026-10-06)

- **IMPLEMENTED 2026-10-06 (uncommitted, working tree): the family variant** (spec `docs/specs/star-hash-marking.md` section 5b, `markFamilyKey`/`assignMarkNodeCodes` in `src/ambiguitychecker.py`). Full rebuild done: 0 collisions, mark-key mass 48.6k -> 55.7k (+14%), no non-verb lemma group with mixed marks. The md5s of the theory exports changed as expected; `plover_stenalgo_expressions.stenalgo` and the plugin copy were refreshed; the plugin version is NOT bumped, the mirror is NOT synced. DONE 2026-10-06 too: the S1 lemma merge `aux`->`au` and 37 sibling closed-class plurals (`pronounParadigmLemme`, 38 pairs; rebuilt, 0 collisions; marked forms 6,866 -> 6,754; `aux` `ae/-s`). Left out because Lexique gives no number: `tiens` PRO:pos/ADJ:pos, `certaines` PRO:ind; `leurs` ADJ:pos keeps its own lemma (`+10`), `les`/`le`, `des`/`un`, `ces`/`ce`... differ in phonology, not merged. Open: the plugin version bump and mirror sync (the published install is stale), the expression rule set re-measure against the new theory, the optional-redundant-marks wish, the trainer check in a browser.

- **The principle to adopt.** A `*`/`#` mark applied to a word means its lemma accepts the same mark in all its forms: the singular and the plural of a noun or adjective, and every conjugated form of a verb, carry the same
  mark, so the learner meets one mark per lemma. Today the plural of `eau` is `ae/-s` while `eau` is `*ae#`; `aux` is not even the plural of `au` (own lemma, `ae#`); `hauts` is `*ae/-s` while `haut` is `*ae#/*#`.
- **The data (2026-10-06, read from `disambiguated_theory.tsv`, no code changed).** Grouped by (lemma, base strokes): 87,122 groups, 4,032 with a marked form, 1,949 mismatched (759 with a verb). Kinds: (1) one form marked, the others made unique
  by a feature stroke `-s -j -k -d -t -R -l` (600 noun/adj, 617 verb: `son`/`sons/-s`, `sûr`/`sûre/-j`, `avoir` a`*`/as`/-d`, `savoir` sait`*`/sais`/-k`); (2) one form marked, another with neither mark nor feature stroke (450, 101: `une`/`unes*/-s`, `parler` noun `*`/
  verb `-l`); (3) two different marks (140, 41: `ver #`/`vers *#/-s`, `faite #`/`faites */-s`, `sui *#`/`suis */-s`, `aller` noun/`allers #/-s`). Report with every group: `tmp/mark_mismatch_report.tsv` (untracked; regenerate by parsing
  the `extraStrokes` column: a leading `+10,15` is a mark merged into the last phoneme stroke, appended strokes made only of keys 10/15 are further marks, any other appended stroke is a feature stroke). Some groups mix two categories
  of one spelling (`aller` noun and verb) and look worse than they are.
- **What the change involves** (nothing implemented yet; discussed 2026-10-06):
  1. Lemma merges in `lexique.py`/S1 where a pair is one word split by Lexique: `aux` -> lemma `au` (today `aux` has lemma `aux`, so S6's same-lemma grouping never sees it, and S7 gives it `#`). Check that the same-lemma grouping
     (S6, `-s` accord group) accepts `ART:def`; find the other such pairs (`les`/`le`, `des`/`un`, `du`...).
  2. S7 `composeReservedKeyStrokesForEntries` (`src/ambiguitychecker.py`): cluster on the base strokes (up to the last phoneme stroke), rank LEMMAS (lemma frequency, not one form's), and let every form of a lemma take its lemma's
     code in the last phoneme stroke, feature strokes after it. Expected: `au ae`, `aux ae/-s`, `oh *ae`, `eau *ae#`, `eaux *ae#/-s`, `haut *ae#/*#`, `hauts *ae#/*#/-s`. Forms with different base strokes (verbs: `parlai`, `parler`) cannot
     share one cluster, so decide what "same mark" means for them (the lemma's mark pressed in the last phoneme stroke of EVERY form, even when the base stroke differs?).
  3. Rewrite `docs/specs/star-hash-marking.md` (R1-R7 assume per-entry clustering), the S7 sections of `docs/PIPELINE.md`, the tests of `src/test/ambiguitychecker_test.py`.
  4. Dry run first: a script applying the rule to the current theory, counting changed entries, new collisions (S7.17), extra marks added to forms that never needed one. Then the full rebuild and md5 comparison of `CLAUDE.md`.
- **Dry run (2026-10-06, `scratch/lemma_mark_coloring.py`, read-only on `DisambiguatedTheory.pickle`; primary entries, frequency-only ranking, the R4-R6 rule stack NOT modelled).**
  Finding 1: copying today's mark onto the other forms of its lemma is UNSAFE (524 to 954 new collisions, e.g. `sur`/`sûr`, `allez`/`halez`, `est`/`haie`): the mark must be chosen per lemma over ALL its clusters at once, i.e. a colouring.
  Model: nodes = lemmas (merged when they share a spelling in one cluster or form a reform doublet), edge = two nodes with different spellings sharing one unmarked final stroke (4,130 clusters, 5,022 nodes in a conflict), greedy by lemma frequency.
  Finding 2: it fits the budget: lemmas by code `()` 2,253, `*` 2,304, `#` 323, `*#` 101, escalated 41 (today 53 forms past the budget; top: `haute` 4, `ho` 5, `ô` 6). Collision-free by construction.
  Finding 3: the price is more marks: marked forms 5,358 -> 13,157; mark-key mass (frequency x extra keys) 50k -> 79k per 900k word mass (+56%); 11,531 forms change code. Part of it is the rule stack being absent (a category rule would mark the rarer
  lemma, not the more frequent form's neighbours): next step is to put R3-R6 into the lemma ranking (rank lemmas pairwise on their most frequent clashing forms), re-measure, and decide with the user whether +56% is acceptable.
  Re-measure WITH the rule stack (`scratch/lemma_mark_coloring.py freq|rules|dominant`; mark-key mass, today 50k): frequency only 79k (+56%), rule stack on the lemmas' dominant forms 112k (+122%, 15% of the pairwise votes still
  disagree), rule stack voted over every clashing form pair (Copeland) 216k (+330%: `a`, `fait`, `me`, `où` escalate). Escalated lemmas stay 41 in all three. Reading: R3-R6 assume a mark per ENTRY; a lemma's forms lose different clashes
  under the category rules (a verb loses to a noun in one cluster, wins in another), so one code per lemma cannot follow them and costs mass. Frequency ordering is the cheap option; the category mnemonic is what is traded away.
  ALTERNATIVE TRIED (`scratch/family_mark_coloring.py freq|dominant`, `NOFAMILY=1` = control): the lemma carries the mark only for m/f/s/p families (non-verbs by lemma+category; past participles by lemma), conjugated verb forms stay single-word nodes ranked
  by the pairwise rules as today. Result: mark-key mass 51.8k (freq order) / 58.2k (rules on dominant forms) against 50.4k today; the control run (every form its own node, same greedy colouring) gives 65.4k, so about 15k is model noise (228 forms the greedy
  order ranks differently from today's sort, some frequent); the family rule itself costs nothing measurable over the control. 2,782 forms change code (2,256 more marked, 526 less; 9.9k vs 1.9k of mass), escalated lemma nodes 45 (control 49).
  Families end consistent: `eau *#`/`eaux *#`, `sûr *`/`sûre *`/`sûrs *`/`sûres *`. Collision-free by construction. Cost visible in the examples: `ans` (an), `mot`/`mots`, `sûre` gain a mark they did not need.
  Caveats to settle: alternates (entries after the first) not modelled; verbs whose forms have different base strokes work in the colouring (the mark sits in each form's last phoneme stroke); `aux`/`au` still needs the S1 lemma merge.
- **WISH LIST, may not be possible without the Plover entry below: redundant marks stay optional.** A form that is already unique without the mark (a feature stroke makes it so, e.g. `parlai/-t`) should stay writable without it even
  though its lemma `parler` has `*`: both `parlai/-t` and `*parlai/-t` accepted; the trainer would teach the lemma's mark but accept the shorter one (`Drill.alternates` exists for this). The principle above does NOT depend on it: without
  it, the lemma's mark is simply required on every form (consistent, at the cost of extra marks on forms that never needed one). Plover side: see the next entry.

## Branch TODO — Plover: marks optional when redundant (abbreviations branch, 2026-10-06)

- **Need (wish list; the lemma-mark principle above stands without it).** When a form's `*`/`#` is redundant (the outline without it is already unique), Plover should accept the outline with or without the mark, and still require it where it separates homophones.
- **What Plover offers (checked 2026-10-06, web search, standard mode, not exhaustive): no built-in optional keys.** A JSON dictionary maps one outline to one text; two outlines for one text are simply two entries.
  The dictionary-extension API (`StenoDictionary` subclasses, `plover-python-dictionary` with a `lookup(key)` function, our own `stenalgo` extension) can answer any lookup. I found no existing plugin that makes keys optional
  (`ignore_folding` in the dictionary API concerns stroke splitting, not optional keys); not every plugin page was read: re-check the Plover plugin registry before building.
- **Options.** (a) Emit both outlines in `plover_stenalgo_dictionary.json` for every form whose mark is redundant: no plugin change, but about as many extra entries as there are such forms (roughly the kind (1) groups above, about 1,200 lemmas,
  more entries counting every form) and `Dictionary.reverse_lookup` then returns two outlines per word (the hint outline stays the marked one). (b) Teach the plugin's `StenalgoExpressionDictionary` (`plover_stenalgo/dictionary.py`, which already
  answers computed lookups above the stock JSON) a fallback: a lookup that misses is retried with the reserved keys `*`/`#` (and the `-s`-style feature strokes kept) added or removed, accepting only a unique answer; costs lookup time and must never
  override a real entry. (c) Both: the plugin answers, the JSON stays the single-outline theory. Decide after the dry run of the previous entry shows how many forms are involved; keep the fingerprint check between JSON and plugin data.
- **Trainer.** `Drill.PracticeWord.alternates` already accepts other outlines; the exporters would list the unmarked outline as an alternate for those forms (`util/export_practice_words.py`, lesson exporters).

## Branch TODO — clean up the stray MD files (abbreviations branch, 2026-10-05)

- **Inventory.** The repo root holds about 20 working-note files next to the real docs (`README.md`, `CLAUDE.md`, `TODO.md`, `ROADMAP.md`): the dated `RESUME_*`, `PLAN_*`, `RESULTS_*`, `NOTES_*`, `QUESTIONS_*`, `PERF_*` files,
  plus `affix_selection_speedup_notes.md`, `affix_rules_report.md` (a generated report), `Tao.md` and `birds.md`. Others lie in `scratch/` (`affix-H-*.md`) and untracked in `tmp/affix_golden/*_report.md`.
  `docs/history/` already exists for the finished ones (affix work, 2026-09-25 to 10-01) and `docs/specs/` for the living specs.
- **Triage each file** into: (a) still live, referenced by `TODO.md`, `CLAUDE.md` or the docs (e.g. the `RESULTS_`/`RESUME_2026-10-04-decoder-...` files cited under "Expression decoder"): keep, or fold into `docs/` and fix the references;
  (b) finished: `git mv` into `docs/history/`; (c) superseded or generated: delete (`affix_rules_report.md` is rebuilt by `util.build_affix_rules`; check whether it must stay tracked); (d) unrelated (`Tao.md`, `birds.md`): ask the owner.
- **Keep references intact.** `grep -rn` every moved or removed name across `*.md`, `*.py` and tests before touching it, and fix the links; run `pytest src/test/` and `mypy` after, since some tests may read these paths.
- **Untracked clutter** (`tmp/`, `out`, `sorties/`, `notes.txt`, ...) is out of scope except the `*_report.md` files in `tmp/`; list the rest for a separate decision.

## Branch TODO — expression families and selector collapse (abbreviations branch, 2026-10-03)

- Decide the family merge (`FAMILY_MERGE=1` in `scratch/select_expression_rules.py`, opt-in, measured worse): revert, keep `un`/`une` only, or improve
  Stage C's selector-collapse heuristic (try another base/selector per colliding variant before dropping it). See `RESUME_2026-10-03-que-briefs-overlap.md` 0b.
- The collapse drops variants of unmerged families too (`il y`, `ne`, `je me`, `de`...); check whether the baseline loses mass this way, and fix the
  `il y` -> `tine` shadow risk (dropping the `il y` prefix rule exposes the outline (7,13,22)).
- Check `pas`/`dans` exception mass in running text (hostless-token artifact?) before dropping `pas`, `pas le`, `dans ce`.

## Branch TODO — which variants fill a family's four selector slots (abbreviations branch, 2026-10-04)

- Today Stage A absorbs a family's siblings in DESCENDING FREQUENCY until the cap of 4 (the selector count), using the
  optimistic proxy marginal. Found 2026-10-04 with the `il` family: `il n'`, `il y`, `il ne` (marginal 0), `il s'` fill the cap,
  and `il n' y` (frequency 6.4e6, marginal 9.6e6, above `il s'`'s 8.8e6) is never evaluated. Then Stage C collapses `il n'` and
  `il y`, so the cap was spent on variants that do not survive.
- Idea 1 (user, 2026-10-04): pick the cap's four variants by MARGINAL gain instead of by frequency (evaluate every sibling,
  absorb the best). Cheap to try in the sibling loop of `selectExpressionRules`.
- Idea 2 (user, 2026-10-04): pre-select MORE than 4 candidates per family as a reserve. When Stage C collapses a variant
  (selector swallowed by the host's `*`/`#`), it measures the effect and promotes the next reserve into the freed selector
  instead of leaving the slot empty. Needs: a reserve list on the family, a re-run of Stage B/C evaluation for the promoted
  variant, and a stop rule so the loop terminates. Ties to the selector-retry and CP-SAT-permutation options
  (`RESULTS_2026-10-04-slot-budget-sweep.md` 2b/2c).
- MEASURED 2026-10-04 (budget 20): idea 1 (`SIBLING_PICK=marginal`) alone is identical to the committed run (25.7%, 155 exc., md5 of
  `expr-rules.tsv` unchanged); the `il` family has only 3 variants, so the cap of 4 does not bind. With `IL_LONG=1` (every 3+-unit `il`
  run is an attach candidate) the marginal pick lets `il n' y` displace `il s'` (marginal 0), but `pruneRedundantVariants` then removes
  `il n' y` and `il n'` (loss 9.6e6 -> 0 -> 0, order-dependent) and the result is 25.6%, 158 exc. Under `freq` the cap blocks `il n' y`.
  Defaults stay `freq` and no long runs. Still open: what `il n'` covers (loss 7.2e6 in the committed run) that `il` + `n'` / `n' y` does not.
  Idea 2 (reserve) has nothing to promote at budget 20. `STAGE_A_ONLY=1` in the driver prints the `il` candidates' fate and exits.
- Context for both: the proxy marginal ignores exceptions and collisions (`il n'` +1.69e7 in the proxy, -9.6e6 in the final
  pool), so a marginal-based pick should ideally use the exact composed saving, not the proxy.

## Branch TODO — attach keypress reused as a standalone stroke (abbreviations branch, 2026-10-04)

- Today an attach keypress is not reserved for anything else: `deriveBriefStroke` (`src/expressionrules.py`) only
  avoids existing outlines and other briefs, so a brief can land on a chord equal to an attach keypress (the joint
  audit reports it as a collision, nothing prevents it), and a hostless attach keypress is just an exception that
  falls back to the longform strokes (`noNeighbour`).
- Idea (user, 2026-10-04): the attach keypress of an expression should also be the stroke that writes that expression
  standalone when the attach fails. Example: with an attach `bien que`, a writer typing "Bien que bien des gens..."
  tries the `bien que` keypress as an attach first; it fails against `bien` (the host's own stroke collides with the
  attached expression, an evident `bien que` ~ `bien` collision), the writer deletes it and types the longform. Cognitively it is
  far easier to RETYPE the same fresh keypress as a standalone stroke, then type `bien des gens`.
- MEASURED 2026-10-04 (`scratch/measure_attach_standalone.py`, committed run): attach occurrences in the pool: merged 57.9%,
  `noNeighbour` exception 22.4%, `attachCluster` standalone 19.1%, `spanOne` 0.6%; no `keyOverlap`/`illegalChord`/`standaloneTrap`
  fallback ever fires. Standalone-as-fallback would gain only on hostless attaches whose particle spans >= 2 strokes: `avec` 1.1e8 and
  `n' y` 1.1e7 strokes (about 3% of the 3.672e9 attach saving). FIXED the real clash found on the way: forced briefs `après` and
  `depuis` sat on the attach chords of `ce` and `pas` (single keys); the driver now reserves every attach chord and its selector-free
  base before deriving the forced briefs (with briefs 4.288e9 -> 4.297e9, rules unchanged). Selected briefs are not reserved yet (none clash today).
- To investigate:
  1. Decoder behaviour (NOTES section 3): when does a keypress mean "attach" and when "standalone"? A decoding Plover
     plugin must make the fallback deterministic (try attach, else standalone) without a delete-and-retype cycle.
  2. Reserve the attach keypresses against brief derivation (add them to `takenStrokes` in
     `scratch/select_expression_rules.py` / `deriveBriefStroke`), or instead make the standalone meaning a feature:
     each attach rule's keypress doubles as the brief of its own expression. Measure what the 40 forced briefs and the
     selected briefs lose (a family takes up to 4 selector variants, about 20 slots times 3-4 chords).
  3. Which expressions this makes sense for (an attach whose host stroke collides with its own expression: `bien que`
     against `bien`, `pas` against `pas`, `plus`, ...) and whether the collision audit should then treat
     "attach keypress = standalone stroke of the same expression" as legal, not a collision.
  4. Interaction with `*`/`#` selectors: a standalone stroke carries its selector too, so the same selector-order
     question as the `que` collision applies.

## Branch TODO — max-1-key overlap (abbreviations branch, 2026-10-03)

- Study allowing up to 1 shared key between an attach keypress and its host stroke (today `keyOverlap` refuses ANY
  shared key in `src/expressions.py`; main's decided affix mode refuses only a FULL overlap). The decoder would
  test the |K|+1 candidates `S \ K` and `S \ K + k`. Potential gain: fewer exceptions, a bigger pool of eligible
  keypresses, a relaxed attach-attach disjointness. Risks: ambiguity is per (rule, host), shadowing widens, must be
  audited over the whole theory. Not implemented. Full discussion and the 5-step experiment list:
  `NOTES_2026-10-03-attach-overlap-and-plover-decoder.md` (section 4).
- Merge hazard resolved 2026-10-03: the expression layer has its own `attachKeysOverlap` /
  `EXPR_MAX_SHARED_KEYS = 0` in `src/expressions.py` and no longer uses main's `ruleKeysOverlap`; the study only
  changes that constant.
- Also drop the temporary `from __future__ import annotations` in `src/affixes.py` when merging main.
- Driver nondeterminism (found 2026-10-03): `scratch/select_expression_rules.py` Stage C breaks equal-score base ties by
  set/dict iteration order, so results depend on `PYTHONHASHSEED` (21.7% vs 22.3%). FIXED 2026-10-03 (Stage C solver: one worker, fixed seed); baseline `scratch/md5_expr_deterministic.txt`.
- Suffix `le`/`les` bug FIXED 2026-10-03 (prefix twin shadowed the suffix rule at a trailing particle): 23.3% / 123 exceptions.
  Still open: low-mass rules (`je ne`, `je me`, `ce qu' il`, `pas le`) are worth reviewing; Stage C feedback loop is a v1 heuristic (6 rounds).
- Decided 2026-10-03: no que briefs (`QUE_BRIEF_BUDGET` removed); adjacent hostless attaches merge (`attachCluster`);
  a brief-wins-when-attach-fails fallback was measured (+2.9%) and rejected for decodability. See the NOTES file, section 5.

## Suspected bugs (from docs refactor, 2026-09-22)

Found while writing `docs/PIPELINE.md` (full write-ups, evidence and confidence in
`docs/refactor/callgraph/90-findings.md` — kept in git history once the refactor folder is
removed — same B-numbers). **Not yet reviewed by the user.** Tier 1
changes the Plover dictionary (or other exported output) today; tier 2 changes reports or
tracked artifacts; tier 3 is latent (no measured impact). B39/B40 were dropped: their code
was removed in Dead-Code Removal (Pass 5). B1 was dropped 2026-09-24: every reading of a
spelling is already an alternate press-set on the resolved Word, so the unresolved "twin" Word
only adds a redundant route (269 twins: 133 alone on their stroke, 38 on a resolved stroke, 98
losing a tie, 0 hiding another spelling — B47 later removed those redundant routes). B2, B4,
B11, B14, B27, B43, B44, B45, B46 and B47 have since been fixed.

### Tier 1 — affects the Plover output today

- **B47** RESOLVED 2026-09-25 (`findSpellingTwinWords`, src/ambiguitychecker.py:785, dropped by
  `Dictionary.buildDisambiguatedTheory` at dictionary.py:426): the residual bare entry belonged
  to a spelling twin — another Word with the same ortho, `lemmeGramCat` and canonical base
  stroke as the one `_resolveEntryWord` picked for the spelling's resolved press-set entry
  (`affadis` participe m. pl. beside `affadis` indicatif passé 2e sg.). The press-set's
  alternates already realize every reading of the spelling on the resolved Word (the entry's
  parallel "readings" field), but `buildFinalInducedStrokes` still gave the twin its own bare
  primary stroke, since it iterates every theory Word and the twin is in no keypress group.
  The fix drops the 272 twin Words (259 spellings) from the disambiguated theory entirely:
  disambiguated_theory.tsv −272 rows (`affadis` keeps only `a/kpa/pvi/-s` and `a/kpa/pvi/-dt`),
  same-lemma residual collisions 104 → 6 (the six survivors are the `-eter`/`-eler` variant
  conjugations `caquette`/`caquète`…, the spelling-variant follow-up), cross-lemma 0, reform
  doublet 0. Plover: −130 stenos (the twins' phantom bare/star-marked chords), 0 added, 0 owner
  changes, 0 spellings lost (each spelling stays reachable through its resolved Word's
  entries). Trainer: definitions.json −272 stray rows (`affadis` now shows each reading on its
  own chord only); practice-words/practice-sentences unchanged (the phantom chords were outside
  the top-10,000 drill set). In a star/hash cluster a twin even consumed a */# slot for a
  spelling already reachable through its feature strokes — those 138 marked phantoms are gone
  too. Before/after in `scratch/b47-before/`. Original entry: Same-lemma disambiguation leaves a
  residual BARE entry for readings that already have a feature stroke — e.g. `affadir_VER`: the
  disambiguated theory (disambiguated_theory.tsv) held THREE `affadis` rows on the same base
  stroke `a/kpa/pvi`: `a/kpa/pvi` + extraStrokes `17` (participe passé m. pl., realized as the
  `-s` suffix), `a/kpa/pvi` + extraStrokes `19,20` (realized as the `-dt` suffix), and
  `a/kpa/pvi` with EMPTY extraStrokes — a residual unmarked entry for the indicatif passé 2e sg.
  reading, shadowed by `affadi` (which owns the bare chord: `a/kpa/pvi` → `affadi` in
  plover_stenalgo_dictionary.json; `affadis`'s real entries are `a/kpa/pvi/-dt` and
  `a/kpa/pvi/-s`). Expected behavior: once the Realization Phase assigns a reading its
  feature-discriminating stroke, that reading should have NO other entry — the bare placement
  belongs to the group's default reading only. The stray row was invisible in Plover (the
  exporter's entry resolution dropped it) but surfaced in the trainer Definitions page
  (export_definitions iterates the phonetic-theory homophone group), where `affadis` showed as
  "indicatif passé, 2e sg." on BOTH the bare chord and the `-dt` chord.
- **B44** RESOLVED 2026-09-24 (`composeReservedKeyStrokesForEntries`, src/ambiguitychecker.py:424:
  Different-Lemma or Grammatical-Category Disambiguation (S7) now clusters and marks every entry,
  primary and alternate, on its own final stroke; `panse` → `p*@s`, `p*@s/-k`, `p*@s/-R`). Plover:
  +183 stenos, 0 removed, 50 spellings newly reachable (`subits`, `amplis`, `garanties`, `buttent`…),
  none lost; 5 stenos change owner (`ksa/R@/ti/-s` `garantis` → `garanties`, the VER reading moving
  to `ksa/R@/t*i/-s`). Why no tool flagged it: the Realization Phase files these under
  "cross-lemma collisions (out of scope — */# track's job)", S7 never re-checked the final strokes,
  and `export_plover_dictionary` printed its 14,739 "same-steno collisions" as expected, lumping
  same-stroke homographs with real collisions. New final check `findFinalCollisions`: `python -m
  util.build_disambiguated_theory` (so `python dictionary.py`) exits 1 on any cross-lemma collision
  (191 before the fix, 0 after); it reports, without failing, 104 same-lemma residuals and 28
  reform-doublet (R2) collisions. Of the 104, 98 are an unresolved synthetic twin Word on its
  unmarked base stroke (`agis` ind:pas:2s, freq 0, beside `agi` on `a/vti`) — harmless while the
  twin is the rarer, since the attested Word reaches the spelling — and 6 make spellings unreachable
  (`caquette`/`caquète`, `dételle`/`détèle`, `nivelle`/`nivèle`… `-eter`/`-eler` variant
  conjugations of one lemma, for the spelling-variant follow-up); the 28 R2 collisions all hide a
  variant spelling on purpose. Probes: `scratch/b44_collisions.py`, `scratch/b44_residuals.py`;
  pre-fix outputs in `scratch/b44-before/`, diff in `scratch/b44-plover-diff.txt`. The 9 B45
  participles (`promis` → `promises`) and the variant spellings were separate causes of the old
  list: the B45 ones are gone since the B45 fix (probe rerun 2026-09-24); re-check the variant
  spellings after the spelling-variant removal.
- **B45** RESOLVED 2026-09-24 (`spliceParticiplePhon`, src/verbparadigm.py:326, now adds the
  consonant of a consonant-final feminine stem for a feminine slot and drops it for a masculine
  one, `feminineParticipleConsonant` :306; util/completeVerbParadigms.py prefers a same-gender
  donor; `util/fixParticipleGenderPhon.py --apply` added the consonant to 45 feminine rows
  (`découverte`, `cuite`, `feinte`, `jointe`, `méprise`…), dropped it from 17 masculine plurals
  and deleted 17 synthetic rows duplicating an attested one (`promis` m_s, stale since e3b0358)).
  Backtest over 22,168 attested cross-gender pairs: 96.7% → 99.5% exact phon, no regression.
  Rebuild: S2 appended 82 rows (`recuire`, `romancer`, `introduire`), Plover +60 entries
  (`enclos` `@/kmtae` / `enclose` `@/kmtaenl`; `promis` loses its star-marked stroke), no
  spelling lost; clusters 6,703 → 6,707, overflow 8.32% unchanged. Before/after in
  `scratch/b45-before/`, `scratch/b45-plover-diff.txt`. Original entry: synthetic past
  participles copied another gender's phonology — 33 masculine rows carried the feminine's `/z/`
  (`enclos` `@kloz` outranked `enclose` on `@/kmtaenl`), and feminine rows lacked it.
- **B46** RESOLVED 2026-09-25 (`_padSilentUnits`, src/verbparadigm.py, applied by
  `generateMissingParticiple`: appends one silent trailing `_#` per orthographic unit the phonemic
  breakdown is short of, matching the attested convention — `garnis` `g_a_R|n_i_#` beside
  `g_a_r|n_i_s`; `util/fixParticipleSilentUnits.py --apply` repaired the 4,920 existing synthetic
  rows in place — 4,829 one unit short, 91 two (the silent `h` of `inhumées` is its own ortho
  unit), 294 already aligned, 0 errors). Measured at last: the missing `#` never changed any
  stroke — after `rm -f *.pickle` + a full `python dictionary.py` rebuild (S2 converged, 0 rows
  appended), all 10 tracked outputs are byte-identical to the pre-change baseline
  (`scratch/b46-before-md5s.txt`); the fix only makes the rows usable by unit-aligned readers
  (deriveSyllableSplitTable, deriveMidVowelTable, `normalizeSplicedBreakdown`'s boundary copy).
  Original entry: synthetic `discriminées` `…m_i|n_e` / `…m_i|n_é_es`, attested `aimées`
  `E|m_e_#` / `ai|m_é_es`; 4,910 of 5,227 synthetic participle rows, predating the B2 fix.
- **B2** RESOLVED 2026-09-24 (`normalizeSplicedBreakdown`, src/verbparadigm.py:589, applied by
  `generateMissingConjugatedForm`: re-places every syllable boundary from a split table learned from
  the corpus Words, vocalizes a word-final glide after a consonant, and sets mid vowels from their
  spelling; `util/fixSplicedVerbBreakdowns.py --apply` corrected the 14,926 rows spliced before). A
  backtest regenerating the 13,461 attested finite forms the generator can rebuild went from 83.5% to
  98.0% exact on phon/`syll_cv`/`orthosyll_cv` (residue: Lexique's own `e`/`E`, `u`/`w` variation).
  Rebuild: 3,587 spellings got a shorter shortest stroke (none longer), S2 added 167 `sub:pre:3p` rows,
  lemma-homophone clusters 6,552 → 6,703, overflow 8.03% → 8.32%. 64 Plover spellings were reachable
  only through their wrong extra stroke and now lose to a real homophone (`buttent` → `butent`,
  `caquette` → `caquète`): B44 (unmarked feature strokes) and the spelling-variant follow-up. Original
  entry: Synthetic verb forms get a vowel-less trailing syllable — src/verbparadigm.py:561, :611 —
  radical cut by character count keeps the infinitive's syllable boundary (`cannes` sub:pre:2s: 2
  strokes vs NOM 1). 3,843 new Words carry an extra stroke and miss their real homophones.
  The cut also keeps the infinitive's vowel quality: `abonne` sub:pre is `abon` `a|b_o|n_#` (closed
  `o` from `abone`, trailing onset-only `n`) → `a/svae/mR-`, vs the attested `abOn` → `a/sven`.
- **B3** Breakdown built from a LexiqueInfra association that disagrees with the phonology —
  lexique.py:1021, :1033 (with :770-883) — match uses Infra `phono`, `syll_cv` comes from `assoc`
  (`embêter` typed with closed `e`). 132 mixed-lexicon rows; 175 VER synthetic rows inherit it.
- **B4** RESOLVED 2026-09-24 with B44 (alternate entries now carry their own star/hash mark; `subits`
  is reachable as `s@i/sv*i/-s`). Original entry: alternate entries of self-homographs take
  unrelated words' only stroke — src/ambiguitychecker.py:1288 (`buildExtraInducedStrokes`),
  dictionary.py:389 — alternate entry strokes skip the star/hash marks (`subits` loses to `subis`).
- **B5** Frequency ties make star/hash marks depend on input order — src/ambiguitychecker.py:224-232,
  `_starHashCompare` :242-258 — not antisymmetric on equal frequency (`pas`/`pâts`). Shuffling input
  changes marks in 619 of 4,450 lemma-homophone groups (14%); any lexicon row move can flip them.
- **B6** 1990-reform deletion/insertion rules miss inflected forms after lemma normalization —
  lexique.py:224-225 with :1197-1198 — rules keyed under `oldSpelling`, lemma already normalized
  (`balloter` beside `ballottait`). 67 rows over 24 lemmas keep pre-reform spellings in Plover.
- **B7** NOM/ADJ exception override keeps the source word's syllabification —
  util/generateMissingNomAdjForms.py:88, :94 — ortho/phon from the exception table, `syll_cv` from the
  source (`molle(s)` typed like `mou`). Among 12 NOM/ADJ synthetic rows with `syll_cv` ≠ `phon`.
- **B8** Phonetic stroke rule never checks that a stroke is pressable — src/keyboard.py:607-620 with
  dictionary.py:305 — no check against `_possibleKeypress` (`traumatisme` coda `zm` → 3-key
  right-pinky press). 529 Words, 39 distinct illegal strokes in the Plover output.
- **B9** Identity merge discards the later row's frequency and syllabification —
  dictionary.py:113-137 (`readCorpus`) — frequencies not summed, differing `syll_cv` dropped (24
  reform-rewrite identities: `gélinotte`, …). Undercounted frequency feeds the frequency-ratio rule
  (R4) and the Plover "most frequent" pick.
- **B10** Plover export breaks frequency ties by phonetic-theory order — util/export_plover_dictionary.py:56
  — `max(key=frequency)` keeps the first Word (`dégotés`/`dégottés`, both 0.0). Low impact;
  order-dependent like B5.

### Tier 2 — affects reports or tracked artifacts (not the Plover output)

- **B11** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). The realization report is identical under seeds 0, 1 and unset (37 cross-category, 1,326 cross-lemma). Original entry: Residual-collision lists in the realization report change between clean rebuilds —
  src/word.py:94, :155; src/ambiguitychecker.py:739-747, :1248-1257 — salted `hash()` stored in the
  pickles sets `allWords` order and first-seen pairing. Cross-category clashes 34/40/38, cross-lemma
  1,283/1,292 across rebuilds; the disambiguated theory and Plover unaffected (`PYTHONHASHSEED=0` workaround).
- **B12** The precedence-spec checker covers much less than the spec —
  util/check_conjugation_disambiguation_order.py:69-77, :100-126 — "masculine must be free" checked
  for participles only; mandatory impératif/subjonctif and line order unchecked. The validation
  report can be clean while answers contradict the spec.
- **B13** Verb paradigm completion is not idempotent — util/completeVerbParadigms.py:95-97 with
  :324-340 — `--apply` twice without deleting the pickles appends the same rows again to the tracked
  `LexiqueSynthetic.tsv` (duplicates merge by identity; only the file grows).
- **B43** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). The S2.1 dry run now confirms 0 rows under seeds 0, 1 and unset. Kept for the record; the order-insensitive feature-set key / receiving-group restriction below remain optional cleanups. Original entry: The S2.1 appender's "confirmed to cause a new discriminator collision" gating is
  PYTHONHASHSEED-sensitive (found 2026-09-24 via the pipeline-timing test run): on the same
  converged tree and identical pickles, `python -m util.completeVerbParadigms` (dry run) reports
  0 flagged lemmas / 0 candidate rows under `PYTHONHASHSEED=0` but 10 / 84 unpinned, so an
  unpinned `python dictionary.py` (or S2 wrapper) appends 84 rows to the tracked
  `LexiqueSynthetic.tsv` a pinned run wouldn't — and then cascades a pickle rebuild (~95 s)
  plus a full extra S2 round (~330 s at the time): the 726 s S2 step was mostly this cascade.
  (Since the 2026-09-24 S2.1 speedup — `extractDiscriminatingFeatures` 75 s → 14 s,
  `detectUndersampledLemmas` 127 s → 4 s — a pinned S2 step takes ~67 s, so the extra round
  is much cheaper, but the 84 unwanted rows remain.)
  Mechanism (confirmed 2026-09-24 with digest-instrumented dry runs, `scratch/b43_probe.py`
  and `scratch/b43_probe2.py`): every stage through candidate generation is content-identical
  across seeds (same 1,817 structural candidates, identical baseline selection and
  collisions). The seed does NOT enter through candidate order (an earlier hypothesis): the
  augmented pass fed seed-1-ordered candidates under seed 0 gives byte-identical feasible
  options, chosen discriminators and feature-set keys as seed-0 order, once the generated
  Words' cached `_hash` is recomputed. The only seed channel is `Word._hash` itself
  (`src/word.py:94`, a salted `hash()` of an f-string, cached at construction and pickled
  with the Word): `extractDiscriminatingFeatures` returns `dict[WordFeature, set[Word]]`, and
  `set[Word]` iteration order follows those hash values into `buildFeasibleDiscriminatorOptions`
  / `selectSharedDiscriminators` tie-breaks, and from there into `buildDiscriminatorSelection`'s
  word-order feature-set tuples (e.g. `('s','p')` 20,902 lemmas vs `('p','s')` 3,125 are
  distinct keys) that `crossLemmaFeatureSetCollisions` compares literally. Theory Words carry
  the hashes of whatever process built `PhoneticTheory.pickle`; freshly generated candidate
  Words get the current process's — under an unpinned run the two regimes are mixed.
  Related latent bug (unverified impact): `Word.__eq__` (`src/word.py:158`) compares only
  `_hash`, so a pickled Word and an identical freshly constructed Word compare unequal (and
  miss in dict/set lookups) whenever the pickle was built under a different seed. Amplifier: the confirm pass re-runs the global
  shared-discriminator selection on the augmented theory, reshuffling ~2,000 uninvolved
  lemmas' tuples (1,994 flagged under seed 0, 2,004 unpinned) — the gate mostly measures
  set-cover reshuffle noise, and the seed decides whether a candidate lemma lands in it
  (seed 0: none → 0 rows; two independent unpinned draws: 10 → the same 84 rows, so random
  seeds agree and PYTHONHASHSEED=0 is the outlier). Same salted-`hash()` family as B11/B27.
  Workaround: always pin `PYTHONHASHSEED=0` for anything that can run the appenders.
  Candidate fixes: make `Word._hash` seed-independent (e.g. a `hashlib.blake2b` digest of the
  same fields) and `__eq__` compare the fields — removes the whole salted-Word-hash family
  (likely B11/B27 too) but changes every `set[Word]` iteration order, so it needs a
  LexiqueSynthetic.tsv re-convergence and new output baselines; alternatively (or also) make
  the feature-set key order-insensitive (sorted (feature, word) pairs or frozenset — changes
  which collisions are detected, same re-convergence); restricting the augmented
  selection to the receiving stroke groups would also remove the ~2,000-lemma noise and the
  second full-corpus extraction pass.
- **B14** RESOLVED 2026-09-24 (the theory-build extraction into `util.build_phonetic_theory` /
  `util.build_disambiguated_theory`): `phonetic_theory.tsv` is now written on every run (pickle
  hit or miss; a pickle round-trip preserves dict order, so the bytes are stable), and
  `disambiguated_theory.tsv` is only ever written by its own command from the JSONs that exist
  at that moment — the old buildOnly could emit it from stale inputs mid-run.

### Tier 3 — latent (no measured current impact)

- **B15** Pickle caches are never invalidated — dictionary.py:451, :498 — not checked against the
  lexicon TSVs, `excluded_words.txt` or `starboard3h.json`; editing the layout without
  `rm -f *.pickle` yields a silently wrong Plover dictionary. Likelihood low while the layout is frozen.
- **B16** First-seen pairing can hide same-lemmeGramCat collisions — src/ambiguitychecker.py:739-747
  with :1248-1250 — X, Z (same `lemmeGramCat`) and Y on one stroke: if Y is seen first, (X,Z) never
  reaches `residualCollisions`. No instance observed.
- **B17** `buildDisambiguatedTheory` ignores unassigned Keypress Groups and residuals — dictionary.py:380-389
  — an unrealizable group's Words silently lose their feature discriminating stroke in the disambiguated theory and
  Plover. Not triggered (all 7 groups have keys).
- **B18** Trainer legend can disagree with the dictionary — util/export_keyboard_layout.py:128 —
  legend reads the tracked realization report, the dictionary recomputes keys inline; rerunning
  Discriminating-Feature Grouping (Grouping Phase) without the report build shows old keys. Agree today.
- **B19** Null `chosenKeys` crashes the trainer legend — util/export_keyboard_layout.py:133-141, :144
  — an unassigned group raises `TypeError`. Not triggered.
- **B20** `_resolveEntryWord` silently falls back to the first candidate — src/ambiguitychecker.py:800
  — stale resolved discriminating feature sets (lexicon fix without rerunning Discriminating-Feature
  Elicitation (Elicitation Phase)) mark `candidates[0]` instead of failing.
- **B21** Extra alternates of empty-primary spellings are never verified —
  src/ambiguitychecker.py:1227-1241 — only Words in `allWords` get alternates checked; 2,749
  spellings have an empty primary ("abaisse"). 0 collisions with the phonetic theory today.
- **B22** Collision tests compare raw strokes — src/ambiguitychecker.py:1114, :1142, :1243-1247 —
  collisions are physical (canonical) but raw Strokes are compared. 0 cases today.
- **B23** Non-live hard-rule feature raises `KeyError` — src/featuregroupingsat.py:117 with :128-135
  — a feature in `ALONE_KEYS`/`MUST_DIFFER_GROUPS` that stops being live gives `KeyError` instead of
  a clear error.
- **B24** A solver timeout can lock a non-optimal result — src/featuregroupingsat.py:172, :274, :398
  — FEASIBLE is accepted and locked, so tier score/tie-break are neither proven nor reproducible.
- **B25** The frequency-ratio rule (R4) and the category-priority rule (R6) can form a cycle —
  src/ambiguitychecker.py:224 vs :229 — A<B (R6), B<C (R6), C<A (R4) → order-dependent sort. 0
  cycles among live representatives.
- **B26** Doublet merge checks only the representative's lemma — src/ambiguitychecker.py:321-326 —
  a rarer homograph carrying the reform-pair lemma makes the doublet look like a real ambiguity. 0
  instances.
- **B27** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). Word identity is fragile — src/word.py:94, :161 — separator-free `_hash` concatenation and
  `__eq__` on `_hash` only: Words from pickles of different processes never compare equal. Root
  cause of B11.
- **B28** `zip` truncation can leave a syllable unregistered — dictionary.py:177 — 99 Words have
  phonetic/orthographic syllable lists of different lengths; a unique extra syllable would make
  `buildPhoneticTheory` (:310) raise `KeyError`. Not triggered.
- **B29** `lexicalPhonemeAmbiguityScore` looks up a word phonology as a syllable name —
  src/grammar.py:913, :931 — `getSyllable("apodiR")` → `None`, the branch adds 0 for polysyllabic
  words. Affects the fallback keymap only.
- **B30** `optimizeOrder` starts from set order — src/grammar.py:307-320 — the best permutation (and
  the phoneme-order tables in `docs/ARCHITECTURE.md`) can change with the hash seed. Fallback
  keymap only.
- **B31** Multiphoneme frequencies are always 0 — src/grammar.py:566, :574-584 — all 353 values are
  0.0; no reader.
- **B32** The layout solver wipes the layout before solving — src/cpsatsolver.py:422 (not run) —
  an infeasible or timed-out part leaves its bank empty and the next `buildPhoneticTheory` raises `IndexError`.
- **B33** `lexique.py` rebuilds on import — lexique.py:1261-1263 — no `__main__` guard: importing it
  overwrites `LexiqueMixte.tsv`. No importers today.
- **B34** `Lexique` keeps its rows in class-level lists — lexique.py:957-958 — a second `Lexique()`
  in one process doubles every row. Not triggered.
- **B35** The sentence exporter's drill-item gate depends on another process —
  util/export_practice_sentences.py:158 — compares against `practice-words.json` from a separate
  disambiguated-theory recompute; changed inputs between the runs reject valid sentences.

### Added at Interactive Triage (2026-09-23)

- **B36** `baux` carries a comma-joined dual lemma (`bail,bau`) — `resources/LexiqueMixte.tsv` —
  a lexicon data defect: the lemma field holds two lemmas, which confuses lemma-based grouping
  (lemma-homophone detection, doublet merge). Verified still present 2026-09-23.
- **B37** `baud` is phoneticized `bo` (missing the final consonant) — `resources/LexiqueMixte.tsv`
  — a pronunciation/sense defect (the fish vs the unit [bod]). Verified still present 2026-09-23.
- **B38** Suspected mistagged-verb "ghost lemmas" — `pars`, `sert`, `bute`, `mar`, `lack`, `fy`,
  `mise`, `vins` — verb forms catalogued as NOM lemmas; they pollute lemma indexes and cross-lemma
  grouping.
- **B41** 182 nouns have no gender in Lexique383 (`maison`, `voiture`, `main`, …) — the trainer's
  Words mode then has no le/la context word for their singular; a lexicon gender fill would fix it.
- **B42** `régnions`/`régnons` are both `ReN§` in the lexicon (no yod on `-ions`) — a false-homophone
  questionnaire pair, still present in `questionnaire.json`/`elicitation_answers.json`; possibly a
  broader `-ions`/`-iez`-after-[N] pattern worth a systematic check.

## Queued follow-ups (from docs refactor)

- **Code renames for "lemma" names that mean lemma + category** (decision a12; no code change
  yet): `LemmaHomophoneGroupKey` (src/elicitation.py:24) → `HomophoneGroupKey`; `groupWordsByLemme`
  (src/word.py:414) → `groupWordsByLemmeGramCat` (`groupWordsByBareLemme` is correctly named).
  Same pattern, also worth renaming: `buildLemmaHomophoneGroups` (src/elicitation.py:61) and
  `buildWordsByOrthoLemme` (src/ambiguitychecker.py:772, keyed by (ortho, `lemmeGramCat`)).
- ~~**No command regenerates `starboard3h.json`**~~ — done (2026-09-23): `python -m
  util.optimize_keyboard` runs the CP-SAT layout solve, seeds from the committed
  `starboard3h.json` and writes `starboard3h_optimized.json` by default (`--output
  starboard3h.json` to replace the seed deliberately).
- **Realization report vs inline path drift** — the trainer keyboard legend reads the tracked
  `realization_report.json`, while the disambiguated theory and the Plover dictionary recompute the
  Discriminating-Feature Stroke Realization (Realization Phase) inline; nothing compares them
  (B18, B19).
- **`.claude/settings.local.json` still allow-lists the old `build_phase_p_realization`
  commands** — user to update to `util.build_realization_report`.
- **Runtime strings still say "Phase G/P"** — ask the user before changing them (it is a code
  change, not a comment edit): print messages and report keys at dictionary.py:537/539,
  src/featuregrouping.py:316/324, src/featuregroupingsat.py:591, util/build_realization_report.py:111/132,
  and the French questionnaire HTML at util/build_questionnaire_page.py:312. Renaming a report key
  changes the tracked `realization_report.json`.

### Added at Interactive Triage (2026-09-23)

- **Regenerate `MARKING_OVERRIDES` from one canonical run** at the 10× threshold — the current
  ~51-pair list was built from a top-10-by-regret cross-check against 30×/100×, not one clean run
  (the spec's §3 "provisional" note).
- **Confirm (not just assume) that bucket 2 and bucket 3 share one physical marking mechanism** —
  implemented that way (`decideStarHashMark` handles both), but the design question was never
  explicitly re-confirmed; caveat now recorded in `docs/specs/star-hash-marking.md` §8.
- **The `-er`/`-ers` noun wishlist** — reuse the `Infinitif`/`Infinitif:p` atomic features instead
  of a generic star/hash mark for a whole NOM/VER homophone sub-class (raised, not sized or
  verified against real data).
- **Done — Integrate the pipeline steps into one orchestrated entrypoint** — `python
  dictionary.py` now runs the four steady-state S2 appenders (`--apply`), the Elicitation,
  Grouping and Realization phases, the disambiguated-theory refresh and every export, rebuilding the
  pickles itself when its appenders appended rows; the manual-`rm` staleness trap is
  intentionally preserved (see `docs/PIPELINE.md` "How to run a full rebuild").
- **No tests for `cpsatsolver.py`'s ambiguity math** — the layout solver's cost model is untested
  (low urgency while the layout is frozen).
- **Housekeeping: merge or delete the `phase-g-grouping` branch** — it long outgrew the Grouping
  Phase and still exists locally and on origin.
- **Trainer: definition search is exact-spelling only** — no accent-insensitive or prefix fallback
  in Definitions mode.
- **Trainer: hyphenated compounds are drilled as two chords** (`celle-ci`, `là-haut`) in sentence
  mode, while Plover would output them as two words.
- **DONE (2026-09-25): Remove spelling variants from the lexicon** — `resources/spellingVariants.tsv`
  (422 sets: 374 active / 48 veto, human-reviewed against Google Books Ngram 2010–2019 counts in
  `resources/LexiqueGoogleNgram.tsv`) is enforced by `src/spellingvariants.py` at Lexicon Building
  (S1) and the `dictionary.py` load choke point; `util/prune_spelling_variants.py` keeps
  `LexiqueSynthetic.tsv` clean. The canonical may sit on either side of a reform pair (the
  reconcile-back rule), and a dropped spelling that coincides with a conjugated form of a kept verb
  (`boite`/`boiter`, `fritte`/`fritter`) is exempt unless its lemme carries the set's canonical
  (`absout`/`absoudre` drops). Rebuild verified: reform doublets (R2) 28 → 0, cross-lemma 0 → 0.
  Follow-ups: (a) R2/doublet machinery (`doubletPairs`, the reform-doublet exemption in S7) now has
  nothing to handle and can be removed; (b) neologism patch from a future
  `LexiqueGoogleNgramAdditions.tsv` (`python -m util.ngram_data extract-additions`, calibrate the
  threshold on the distribution first); (c) RESOLVED 2026-09-25 (`util/fixRectifiedEConjugations.py`,
  working tree): the 6 residual same-lemma collisions after B47 were the `-eter`/`-eler`
  variant-conjugation doublets — attested rectified forms (`caquète` ind.) beside synthetic
  traditional-doubling subjonctif/future rows (`caquette` subj) from Verbiste's `j:eter`/
  `app:eler` templates; the subjonctif-vs-indicatif cross-spelling opposition was never asked,
  so the Elicitation Phase skipped the whole group and NO reading got a feature stroke. Fix:
  the script remapped the 49 verbs whose LexiqueMixte forms attest the `è` convention
  (caqueter, atteler, renouveler, étiqueter…; only the appeler/jeter family keeps doubling)
  to `ach:eter`/`p:eler` in `resources/verbiste/verbs-fr.xml` and pruned the 330 doubled
  LexiqueSynthetic.tsv rows; S2 regenerated 507 rows with rectified spellings (converged in
  3 rounds). Final-stroke collisions now 0/0/0 (cross-lemma / same-lemma / reform doublet),
  resolved press-set groups 47,838 → 47,911, subjonctif readings live as same-spelling
  alternates (B47 machinery). Plover: +489/−261 stenos, 57 owner changes; the 240 lost
  spellings are ALL doubled spellings (wrong convention per their verb's own lexicon) — 171
  have their `è` counterpart reachable, 69 rare readings (2s futures, 3p forms of ~25
  freq-0 verbs) are unwritable until their regenerated row passes the S2 collision gate.
  Before/after in `scratch/b48-before/`, rebuild log `scratch/b48-rebuild.log`.
- **Audit the 2% of attested finite verb forms the B2 generator does not reproduce** —
  GENERATOR SIDE RESOLVED 2026-09-25 (non-final-syllable vowel laxing in
  `normalizeSplicedBreakdown`/`deriveMidVowelTable`/`_midVowelContexts`, src/verbparadigm.py: the
  new `nonfinal-closed`/`nonfinal-open` contexts are learned and applied after the boundary
  re-placement, only the coarse `e`/`o` units are rewritten — a committed `°`/`E`/`O`/`2`/`9` never
  changes (`devriez` keeps its schwa, `bottèlent` its `O`) — and in the learning the coarse
  counterpart of a lax winner abstains, as do non-mid nuclei like `wa`; the existing 26 rules were
  unchanged, 26 added; `util/fixSplicedVerbBreakdowns.py --apply` corrected the 531 stored synthetic
  rows). Backtest 13,007 → 13,027 exact of 13,269: the `ai`/`ei`/`aî`/`ê`→`E` classes and the
  closed-syllable `e`→`E`/`o`→`O` ones are gone (`affaiblira`, `vieillira`, `fraîchira`,
  `portâtes`); the new `E`→`e`/`O`→`o` entries (66) are the generator being finer than coarse
  attested rows (`aigrirent`), not regressions. Residue, classified per the audit's rule:
  plain-`e` non-final-open (96, `aguerrira` /ɛ/ vs `descend` /e/) is undecidable from spelling or
  the coarse infinitive — a within-lemma lexicon inconsistency, fix-script material (upgrade coarse
  infinitive vowels from the lemma's own committed finite rows); `o` non-final-open (24,
  `délogera` O vs `posera` o) is LexiqueInfra-internal inconsistency — no rule learnable at 89.5%
  share; `u`↔`w` (18) splits within lemmas (`évanouir` w vs `réjouir` u) — lexicon errors;
  `°`↔`E` (6, `jetterez`) needs rewriting a committed schwa in doubling stems — left open;
  `2`/`9`/`°` (≈10), the dropped `n` (5, `enorgueillir`), the malformed `ij#` (3,
  `oublierions`), and the boundary/1-offs stay as noise or small splice bugs. Rebuild verified:
  S2 converged appending 0 rows; final collisions 0/0/0; phonetic theory 446 spellings' stroke
  sets changed, none shorter/longer/gone/new; Plover 167,719 → 167,708 (−478/+467, 6 re-pointed),
  0 spellings lost or gained; definitions.json regrouped (−4 net), practice-words 3,784 rows carry
  the corrected chords, practice-sentences and keyboard-layout byte-identical; lemma-homophone
  clusters 6,551 → 6,555, overflow 8.32% → 8.31%. Before/after `scratch/b2r-before/`, rebuild log
  `scratch/b2r-rebuild.log`, ambiguity log `scratch/b2r-ambiguity.log`, classifier
  `scratch/b2_audit.py`. Follow-ups: the coarse-infinitive vowel upgrade script and the `u`↔`w`
  normalization script (both lexicon halves, like the other `fix*` scripts).
- **Close the B2 residue the audit classified but left open** — the continuation of the entry above,
  now that the generator side is done:
  - the plain-`e` non-final rows — DOUBLED-CONSONANT RULE DONE 2026-09-25 (NON_FINAL_DOUBLED in
    src/verbparadigm.py, learned and applied like the other non-final contexts): a coarse `e`
    before a doubled consonant letter in any syllable but the word's first laxes to E (`aguerrir`
    rr, `assujettir` tt, `pressentir` ss; 38 rows fixed, 0 flipped; backtest 13,027 -> 13,065 of
    13,269; `fixSplicedVerbBreakdowns --apply` corrected 142 more stored rows). The first syllable
    is excluded because the prefix vowels keep their quality there (`dessécher` /deseSe/,
    `effacer` /efase/ — 120 rows), and `sc` is not a doubled `s` because `descendre` attests
    /des@d/ (86 rows). Both widenings of the rule were tested 2026-09-25 and REVERTED: treating
    `sc` as a doubled `s` (flips `descendre`'s 86 correct rows), and admitting the word's first
    syllable for `pressentiez`/`tressaillez` (first-syllable cases, not a detector gap — the
    widened detector changed nothing else on the corpus). Residue, all lexicon-side (per-lemma
    coarse infinitive vs committed finite forms — the upgrade script): `condescendre`/`redescendre` attest E before `sc` (27 rows,
    `k§dEs@`, `R°dEs@`) though `descendre` attests `e`; `essuyer` (`Es8ija`), `blettir`
    (`blEtisE`), `pressentir` (`pREs@tje`) and `tressaillir` (`tREsaje`) attest E from the word's
    first syllable (16 rows). The 12 `élever` rows (`El°va`) are NOT generator gaps: `é` is a
    one-phoneme grapheme (/e/), so the attested E rows are lexicon errors to correct in the
    attested rows, not in the generator. Same heuristic may still unlock the 6 `jetterez` rows
    (the doubled-consonant stem marks the E the committed `°` hides — would need rewriting a
    committed schwa, left open).
  - `u`↔`w` — DONE 2026-09-26 (`util/fixOuGlideConsistency.py --apply`): the 25 lemmas whose
    `ou`+vowel rows split between hiatus /u/ and glide /w/ (`jouez` Z_u|e beside `jouer` Z_w_e,
    `évanouir` 18 u / 17 w, `réjouirai`, `relouer`, `touareg`…) are normalized to /w/ with the
    syllable merge, in all four files (Lexique383 phon/syll/nbsyll/cv-cv/p_cvcv/phonrenv, Infra
    phono/assoc/regTo_GP, Mixte and Synthetic phon/syll_cv/orthosyll_cv): 36 Mixte + 19 Synthetic
    rows. `python lexique.py` regenerates exactly the 36 patched Mixte rows. Uniformly-/u/ lemmas
    (`hindouisme`, `louisianais`, `ouïgour`) and the obstruent+liquid hiatus lemmas (`trouer`,
    `clouer`, /u/ is correct there) are untouched. Rebuild: S2 converged after appending 71 rows
    (3 rounds; the changed strokes moved the collision gate: the whole `sidérer` paradigm (33)
    plus one gap each in 35 hiatus/participle lemmas: `clouer`, `strier`, `suppléer`,
    `individué`, `mosaïqué`…); final collisions 0/0/0; Plover 167,708 → 167,768 (−55/+115
    stenos), 0 spellings lost, 27 gained (23 `sidérer` forms, `individué(es)`, `mosaïqué(es)`);
    keyboard-layout.json identical; 639 tests pass. Before/after `scratch/uw-before/`, log
    `scratch/uw-rebuild.log`.
  - the splice bugs behind the malformed `u#`/`ij#` units — FIXED 2026-09-26 (generator guard +
    `util/fixMalformedSyntheticSplices.py --apply`): the endings are mined by string length, so an
    -ouer/-uer/-éer verb spliced with the -ier donors of `étudi:er` lost its R in the cnd forms
    (`clouerions` `kluj§`) and left an empty/fused unit (`cloue` `k_l_u#`). `repairSpliceUnits`
    turns empty and fused units into a sounded unit + `#`; `isWellFormedSplice` (no empty unit,
    phon == sounded join up to mid vowels) makes `generateMissingConjugatedForm` skip a bad slot;
    the script repaired 281 stored rows (58 phon R restored, 36 lost `n` unit reinserted for
    `enorgueillir`/`enivrer` via `reinsertLostNasalUnit`) and deleted 49. Rebuild: collisions
    0/0/0, Plover 167,768 → 167,747 (34 spellings lost, 13 gained); 649 tests pass. OPEN: the 34
    lost spellings are the cnd `-ierions`/`-ieriez` forms of 15 -ier verbs (`trier`, `crier`,
    `plier`…; the donor ending gives `ij#|R_j_` / phon `jj` — needs a glide-aware ending class,
    e.g. splitting `étudi:er` by infinitive tail), `oublieriez`/`publieriez`, and the
    `désennuie(nt)` forms (unit-count rule vs the `ui` ortho unit); 9 loanword/noun rows
    (`games`, `kreutzers`, `miladys`, `sweepstakes`, `updates`, `molle(s)`, `interviewée(s)`)
    still fail the guard, made by another generator. `enorgueillir`'s dropped `n` is fixed
    (reinserted); `interviewer` stays deleted (its Mixte source is inconsistent).
  - the 34 lost `-ierions`/`-ieriez` spellings — FIXED 2026-09-26 (`endingTemplateKey`,
    src/verbparadigm.py): the ending tables are keyed by template plus the glide class of the
    infinitive (`#ij` when the phon ends `ije`: `crier`, `trier`, `plier`, `oublier`, and the
    `-iller` verbs), so those verbs no longer splice the `étudier` (`d_j_e`) endings; `crierions`
    `k_R_i_#|R_j_§`. Rebuild: S2 converged after 2 rounds appending 2,560 rows (34 back plus the
    full paradigms of ~85 `-iller` verbs, `tiller`… ~30 rows each, previously blocked by the
    well-formedness guard); collisions 0/0/0; Plover 167,747 → 170,098 strokes, 0 spellings
    lost, 1,900 gained; 649 tests pass. Before-state `scratch/ier-before/`, logs
    `scratch/ier-rebuild.log`, `scratch/ier-full.log`. Still open: 9 loanword/noun rows made by
    another generator.
  - the plain-`e` first-syllable residue — DONE 2026-09-26 (`util/fixFirstSyllableE.py --apply`, user-validated
    lemma list): the harmonisation vocalique is ignored (docs/ARCHITECTURE.md decision 6), so every
    form of `essayer`, `essuyer`, `descendre`, `effacer`, `dessiner`, `voir` (`verrons`), `nerver`,
    `dessaper` (`dEsape`, syllable added)… gets `E`; `re-` prefix verbs keep their schwa (`restructurer`
    untouched, `redescendre` `R°dEs@dR`). 586 Mixte + 392 Synthetic rows (Lexique383 577, Infra 603;
    `python lexique.py` regenerates the same Mixte). Rebuild: S2 converged, collisions 0/0/0, Plover
    170,098 → 170,156, 3 spellings lost (`dessoula`, `dessoulais`, `dessoulez`: rare variant-spelling
    rows of `dessouler` the regeneration no longer carries, not regenerated by S2's gate), 0 gained
    spellings. Before-state `scratch/fse-before/`, log `scratch/fse-rebuild.log`. OPEN: the generator's
    first-syllable exclusion in NON_FINAL_DOUBLED now contradicts the corpus (first-syllable `E`
    everywhere) — revisit, and the coarse-infinitive upgrade script is no longer needed for this set.
  - `python lexique.py` stopped reproducing the committed LexiqueMixte.tsv after 0b5eace (found
    and FIXED 2026-09-26): the 49 verbs remapped to `ach:eter`/`p:eler` dropped out of
    `loadElerEterQualifyingVerbs`, so reform rule 5 no longer regularized their Lexique383
    doubled rows (56 rows reverted, `amoncèle` → `amoncelle`). The loader now also accepts those
    two templates (the rewrite only fires on a still-doubled prefix, so regular è verbs are
    untouched); a regeneration is byte-identical to the committed Mixte again.
  - accepted noise, no action: `o` non-final-open (Infra contradicts itself, `posera` `o` vs
    `délogera` `O`), `2`/`9`/`°` variation (~10 rows), the boundary 1-offs.
- **Vowel-harmony standardization, batch 2** — the read-only report (`python -m util.reportVowelHarmony`)
  found 687 within-lemma E/e, O/o, 9/2 disagreements in 663 lemmas; the classified findings, the ~12
  genuine-harmony lemmas (`-ologique`, `coronarien`, `monopoliser`…), the ~40 loi-de-position `-onner`
  verbs awaiting a decision, and the plan are in `docs/VOWEL_HARMONY_CANDIDATES.md`. Follows the first
  batch (`util/fixFirstSyllableE.py`, docs/ARCHITECTURE.md decision 6).
  - Batch 2, family 2 APPLIED 2026-09-26 (`util/fixHarmonyVowels.py --apply`; lemma table checked on
    fr.wiktionary): `O` for `cosmologique`, `radiologique`, `radioscopique`, `étiologique`,
    `troglodytique`, `coronarien`, `ovoïdal`, `philosophal`, `cochonnée`, `corroborer`, `lobotomiser`,
    `monopoliser`, `autographier`; `o` for `rototo`; word-final open vowels (`ovoïdaux`) untouched.
    34 Mixte + 21 Synthetic rows. Rebuild: collisions 0/0/0, 649 tests, Plover 170,156 → 170,321 (0
    spellings lost, +165 gained: S2 appended 164 rows, 156 ADJ — the -ique adjectives' plural/gender
    forms now agree with their exemplars). Before-state `scratch/harm-before/`. Families 1 (~40
    `-onner` loi-de-position verbs) and 3 (suffix-driven pairs) DECIDED 2026-09-26: left as is (real
    positional/suffix alternations). Only the `mixed` rows remain open.
  - The generator's first-syllable exclusion of NON_FINAL_DOUBLED — TESTED AND KEPT 2026-09-26: dropping
    the `any(boundary <= nucleus …)` condition in `_midVowelContexts` (so a first-syllable `e` before a
    doubled consonant laxes too) is a net wash on the backtest (14,376 -> 14,375 of 14,529 exact): the
    `condescend` 23 `e`/`E` rows become 11 `°`/`E`, 18 new `enquête`/`enterre` `e`/`E` misses appear (`e`
    that stays tense before `rr`/`tt` in non-prefix first syllables), 1 `celait` regression. Now that
    `util/fixFirstSyllableE.py` put `E` in the infinitives themselves, the rule has nothing left to add;
    reverted. The `jetterez` 6 rows stay open.
  - Batch 3, the `mixed` rows APPLIED 2026-09-26 (`util/fixMixedHarmonyVowels.py --apply`, targets in
    `util/harmonyVowelTargets.tsv`, candidates by `util/buildMixedHarmonyCandidates.py`, all validated by
    hand against fr.wiktionary, see docs/VOWEL_HARMONY_CANDIDATES.md): `E` before a doubled consonant
    or `sc`, `O`/`o`/`e` per Wiktionary; left alone: the masculine `-o(t)` / feminine `-Ot(te)` pairs,
    `boeuf`/`oeuf`, and the 49 `-oter`/`-onner`/... verbs that only flatten the loi de position
    (`greloter`, `flotter`, `adorer`, `téléphoner`…; `cloner`, `diplômer` stay flattened to `o`);
    `professeur` is `O` in all its forms (homophones). 282 Mixte + 42 Synthetic rows. `lexique.py` learns
    `oo-OO` (coopter); Lexique383 gives `professeur`/`professeurs` genre `m` (it was blank, so the reading
    "s" was a subset of `professeure` "f s" and no press-set group formed). Rebuild: S2 converged, collisions
    0/0/0, 649 tests, Plover 170,321 -> 171,586 strokes, 0 spellings lost, 1,253 gained (S2 regenerated
    forms once the strokes moved). Before-state `scratch/mh-before/`, log `scratch/mh-rebuild4.log`.
    OPEN: `chopper` (no pronunciation); 30 other NOM lemmas have a blank-genre row beside a feminine one
    (`amateur`, `architecte`, `malade`…), not audited; `agressions` NOM row lost its merge with the
    `agresser` VER row (harmless).
- **Pluvier-style TAO prefix/suffix shortcut scan** — go through Pluvier's dictionary rules
  (docs/PRIOR_ART.md; the TAO strokes that emit a whole multi-syllable prefix or suffix from
  one special keystroke), and for each rule measure the payoff in OUR lexicon: the sum of
  word frequencies of Words whose current stroke sequence would be shortened by having that
  shortcut stroke (a positively-affected word is one whose orthography starts/ends with the
  rule's target affix and whose stroke count would drop). Store the scored rules in
  descending order of usefulness in a tracked scratch file (e.g.
  `scratch/pluvier-affix-shortcuts.tsv`) for later human evaluation — do NOT wire any of
  them into the theory; this is measurement only.
- ~~**Resyllabify 5 wrong `-ption` lemmas**~~ — DONE 2026-09-29 (`lexique.py` `fix_p_sj`; Mixte 5 rows, Plover 5 entries, trainer definitions regrouped). Also DONE 2026-09-29: the 5 `-ction` lemmas with an x (`exaction(s)`, `extinction`, `extraction(s)`) — `fix_x_k_s` wrongly moved the k of `-ction` into the last syllable; `-xion`/`-xtion` (genuine x = ks) deliberately left as `ksj§`. Still open: check the `-th` stray anchor. Original note: — `resources/LexiqueMixte.tsv` (source: Lexique383
  syllable columns) — `absorption`, `absorptions`, `réabsorption`, `résorption`, `résorptions`
  are split `…R|p_s_j_§` (the `p` in the onset of the last syllable, phono `psj§`, ortho `ption`).
  Every other `-ption` word (adoption, exception, acception, assomption, exemption, rédemption,
  circonscription, …) is split `p|s_j_§` (`p` in the coda of the previous syllable, last syllable
  `sj§`/`tion`). The five are wrong: they create a stray `psj§ ption` suffix anchor (5 carriers,
  freq 0.6) in the affix scan that can never fuse with `tion`. Fix the split, then rebuild per
  `docs/PIPELINE.md` ("Recomputing after a fix", lexicon change → `rm -f *.pickle`). Afterwards
  check whether other stray anchors (`ction` `ksj§`, 5 carriers; `-th`) are the same kind of
  syllabification artefact. Found 2026-09-29 while comparing affix rules to OQLF/TAO.

- **`ra`-spelled prefix syllables with an `Re` phonology (lexicon, to investigate).** Found 2026-09-30 while
  analysing rank 17 (`ra|rai|raie|re|rhé|ré|réh`, `Re` phonology) of the affix sweep. Besides `ré`, its parts are:
  `rai` (raidir, rainer, rainure(s), rainurer, rainurés; `ai` = é is plausible), `raie` (raiera, raierai, raierais,
  raieras, raierions, raieront), `rhé` (rhétorique, rhésus, rhéostat…) and `ra` carried by a single word,
  `rayâmes` (orthographic syllable `ra` pronounced `Re`, which should not be possible for a syllable spelled `ra`: look
  at its phonology / orthosyll in `Lexique383.tsv` / `LexiqueInfraCorrespondance.tsv`, probably the `ra|yâmes`
  split of `rayer` forms). Decision (user, 2026-09-30): `re` (`R°`) and `ré` (`Re`) stay separate rules, no
  phonology-class merge. Check also the `raie`/`rayer` family for the same split, then rebuild per `docs/PIPELINE.md`.

- **Affix pipeline integration (2026-10-01): DONE and committed on `affix-abbreviation-rules`.** Stage Affix Abbreviation Building (S9) per `docs/history/PLAN_2026-10-01-affix-pipeline-implementation.md` (decisions file, S9a/S9b, self-looping interactive review, per-rule cache; docs in `docs/AFFIX_RULES.md` and `docs/AFFIX_DESIGN.md`); a full rebuild from nothing is byte-identical. Trainer integration done on branch `affix-trainer` (2026-10-02, `util/export_affix_lessons.py`; the learner trial of the 30 rules stays open); the `ra`/`Re` phonology items above; re-review of the verdicts when the lexicon changes (pending items are listed by `util.build_affix_rules`).

- **DONE (2026-10-02): Affix abbreviations carry the conjugation markings.** Records now keep every route of a Word in the disambiguated
  theory (`WordRecord.routes`) and `src/affixabbrev.py` abbreviates each route with its own marks and trailing feature strokes:
  79,715 abbreviations (72,121 primary-route entries and 7,594 for the other routes; TSV column `route`; a shared outline goes to the most frequent spelling whatever its route, which changed 60 of the 72,204 earlier entries to a more frequent word; `util.validate_affix_markings` checks it). The marks (keys 10/15)
  never overlap a keypress; S9a output byte-identical. Not covered: a Word whose primary route has no free abbreviation can still
  get one for another route (by design, each route is settled on its own).

- **Plan a conjugation-engine plugin for Plover (2026-10-02, to plan, not to build yet).** Goal: for all homophones of a word
  stenogram (the outline without conjugation marking) keep ONE entry in the theory, with a reference to a conjugation table
  listing the possible conjugation strokes and endings, so the static dictionary no longer needs one entry per marked form.
  The plan should cover: the table format (shared paradigm data, see [[dual-target architecture]] note: Plover static dict +
  Javelin-style runtime engine), the plugin type (Plover extension / meta or command plugin vs a dictionary-replacing
  engine), how marker strokes resolve to a form at runtime, interaction with the affix layer (S9) and the `*`/`#` homophone
  marks, undo behaviour, and what the Plover dictionary export keeps as a static fallback. Output: a `PLAN_<date>-...md` in
  `docs/history/` or `docs/`.


## Expression decoder (2026-10-04; see RESULTS_2026-10-04-expression-decoder.md and RESUME_2026-10-04-decoder-theory-shadow-elision.md)

- Re-selected 2026-10-04 on the theory with `les`/`des`/`ses`/`mes`/`tes`/`ces` in /E/ (merge of origin/main): same 29 attach rules, a few keypresses shifted (`à`, `il`, `elle`, `ne`, `un`, the `de`/`ne` stacks) and 3 brief strokes reassigned; attach saving 24.1% (3.450e9), 4.006e9 with briefs, 0 pool shadows/collisions; decode round trip 4 mismatches (0.04%, the `ce que ...` pool rows, as before). Rules, briefs and `plover_stenalgo_expressions.stenalgo` regenerated.
- Done: decoder (`src/expressiondecoder.py`), whole-theory shadow/collision audit, Stage B theory-wide shadow term (limit 0.002), pinky-diagonal key conflicts (attach saving 24.8%, `il n'` stacks again).
- Ranking built (`src/expressionranking.py`); no composer `loses` check is needed for attested expressions. The attested table and the unigram probabilities are exported (`util/export_expression_data.py`); look at the 1.6% open-set mis-decodes (`dans` + `et`...).
- Remaining collisions: `n' y`, `il n'`, `je me` (host `*` swallows the selector), `le`, `qui`, `un`.
- Elision pairs are the default now. Open: the shadows of `un`, `le`, `c'`, `qu'` (46 events, 0.23% of host frequency, none a frequent phrase), the remaining collision families (`de`, `j'`, `je`, `il`, `à`, `n' y`, `il n'`, `je me`),
  hostless clusters read with either elision form (fragments only), complete `ASPIRATED_H`/`NO_ELISION` from a lexicon.
- Report hosted-only saving (fragments excluded) next to the pool total in the driver.
- Step 4 leftovers: brief that depends on a failed attach; attach keypress as standalone stroke (parked); overlap max-1; `longest_key` / prefix lookups in the Plover plugin.
- Step 5 (Plover dictionary plugin): DONE and installed in a real Plover 5.4.1 (see "Branch TODO — Plover expression dictionary plugin" at the top and `RESULTS_2026-10-04-expression-decoder.md`, "Plover plugin").
