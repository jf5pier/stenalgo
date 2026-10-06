# Plover plugins and commands that complement the base theory

DRAFT, first pass (2026-10-05). Sources read: Plover's stock `commands.json` (GitHub, `plover/assets/commands.json`)
and the plugin list at <https://plover.wiki/index.php/Plugins>. Not yet read: each plugin's own page or source,
Lapwing's `commands.json`, popularity figures (PyPI downloads / registry stars). Rows marked `?` are unverified.

## Layout context

Stenalgo keeps Plover's Gemini PR wire format but renames the keys (`plover_stenalgo/_generated_keys.py`):
22 phoneme keys, `*`, `#`, `&`, `%`. There is no number key (`NUMBER_KEY = None`), and the stenotype
letters of the Ireland layout (`STPH`, `-PBLG`...) mean nothing here. Anything that is written as an
*outline* is layout-dependent; anything that only touches the *output* (`{#Return}`) is not.

## Classification of the stock `commands.json` (39 entries)

| Kind | Examples (Ireland outline -> output) | Class |
|---|---|---|
| Output side | `{#Return}{^}`, `{#Tab}{^}`, `{#Control_L(v)}`, `{#Alt_L(Left)}`, `{#Super_L(v)}` | (a) layout-independent; keep |
| Outlines | `SKW-BGS`, `R*R`, `TA*B`, `STPH-R/G/P/B` (arrows), `PW*FP` (BackSpace), `TKPEUL`... | (b) outline-dependent; reassign a Stenalgo stroke |
| Mnemonic | `TA*B` = "TAB", `KHR*F` = "CL(ipboard) paste" | (c) letters carry the meaning; lost in a phonetic French layout |
| Plover commands | `{PLOVER:ADD_TRANSLATION}`, `{PLOVER:SUSPEND}`, `{PLOVER:TOGGLE}` | (a) for output, (b) for the outline |

AZERTY/Bépo caveat to test: `{#Control_L(c)}` sends the *key name* `c`, which Plover maps through the host layout, so a
combo can land on another physical key. Needs a check on the user's host before shipping combos.

## Candidates

| Plugin / file | Adds | Key-position dependent? | Fit |
|---|---|---|---|
| Stock `commands.json` | specials keys, combos, Plover commands | yes (outlines) | convert via generator (see TODO) |
| plover-last-translation (macro; also inside plover-lapwing-aio) | retro-edit of the previous translation (capitalise, repeat...) | no, only the `=macro` entries need an outline | high: needed for French capitals, retro-spacing |
| plover-retro-quotes | retroactive quote insertion | no | medium: guillemets need French-specific variant `?` |
| plover-dict-commands | `PRIORITY_DICT`, `TOGGLE_DICT`: enable, disable, reorder dictionaries | no | medium: lets the expression layer be toggled live |
| plover-system-switcher | run commands / switch system on a stroke | no | low `?` |
| plover-stroke | stroke class used by other plugins | depends on the system | low; Stenalgo already ships `stroke.py` |
| plover-layout-display, plover-wpm-meter, Spectra Lexer, plover-word-tray, plover-clippy | GUI tools: layout viewer, speed, outline lookup/hints | layout display needs the Stenalgo map | medium for learners; not part of the dictionary `?` |
| plover-emoji, plover-number-format | emoji dictionary, number formatting | emoji: outlines; number-format: needs a number mode | `?` not surveyed |
| plover-auto-reconnect-machine, plover-focus-track | machine/convenience extensions | no | optional |

## Minimum gaps (from TODO), mapped

1. Punctuation with French spacing: `{:}`-style attach/glue meta entries; this is a dictionary, not a plugin, but
   retro-quotes/last-translation help for guillemets and non-breaking spaces before `: ; ? !`.
2. Letters, capitals, digits: fingerspelling dictionary and a number mode (no number key; needs a design decision).
3. Special keys and combos: the converted `commands.json` above.

## Punctuation encoding in Plover and Lapwing

Read 2026-10-05 from `plover_lapwing/dictionaries/lapwing-base.json` and `lapwing-commands.json` (repo
`aerickt/plover-lapwing-aio`). Lapwing has no separate punctuation file: its punctuation entries sit in
`lapwing-base.json` (114,885 entries) among the words, and `lapwing-commands.json` (146 entries) holds the spacing
and capitalisation commands. Plover's stock English dictionary was not re-read; it uses the same meta syntax.

**Mechanism (identical in Plover and Lapwing).** Punctuation is a plain dictionary entry whose output is a *meta*
in braces; no plugin is involved. The meta decides spacing and capitalisation:

| Meta | Effect | Lapwing example (outline -> output) |
|---|---|---|
| `{.}` `{?}` `{!}` | attach to the previous word, capitalise the next | `TP-PL` -> `{.}`, `KW-PL` and `H-F` -> `{?}`, `TP-BG` -> `{!}` |
| `{,}` `{:}` `{;}` | attach, no capitalisation | `KW-BG` -> `{,}`, `STPH-FPLT` -> `{:}`, `STPH*FPLT` -> `{;}` |
| `{^}x{^}` | glue a symbol on both sides | `H-PB` -> `{^}-{^}`, `P-P` -> `{^}.{^}`, `OEU` -> `{^}/{^}`, `K-L` -> `{^}:{^}`, `A*T` -> `{^}@{^}` |
| `{^}...{-|}` | ellipsis, then capitalise | `SKW-BGS` -> `{^}...{-|}`; `SW-BS` -> `{^...}` |
| `{~|"^}` / `{^~|"}` | quote attached on one side, carrying the capitalisation | `KW-GS` -> `{~|"^}`, `KW*GS` -> `{^~|"}`, `KR-RG` -> `{~|'^}` |
| `{(^}` `{^)}` `{[^}` `{^]}` | brackets attached on one side | `STPH-FPLTS` -> `{(^}` / `STPH*FPLTS` -> `{^)}`, `PWR-BGT` -> `{[^}` |
| `{-|}` `{^^}` `{^ ^}` | capitalise next; no space; forced space | `KPA*` -> `{^}{-|}`, `SP`, `TK-LS` -> `{^^}`, `S-P` -> `{^ ^}` (commands file) |
| `{&x}` | glue (fingerspelling, Greek letters) | `S-LGTS` -> `{&σ}`; the `LGTS` ending selects the Greek family |

Patterns worth noting: the `*` form of an outline is the *other side* variant (`KW-GS` opens a quote, `KW*GS`
closes it); the `-S` ending adds the closing partner (`STPH-FPLTS` opens a bracket, `STPH*FPLTS` closes it);
a `#` number prefix duplicates some entries (`#TPH-FPLT` = `{:}`). English spacing is built in: `{:}` and `{;}`
attach with no space before, which is wrong for French (`mot : mot`, `mot ? mot`), so the French theory needs its
own entries whose output carries the (non-breaking) space, for example a `{^}` + ` ` + `:` + `{^}` form
(not yet designed; see the minimum gaps above).

### Ireland keys mapped onto the Stenalgo layout ("same buttons")

Taken from `GEMINI_PR_KEYMAP` in `_generated_keys.py`, read in reverse: the Stenalgo key that sits on the Gemini
button an Ireland letter is wired to.

| Ireland | S | T | K | P | W | H | R | A | O | `*` | E | U | -F | -R | -P | -B | -L | -G | -T | -S | -D | -Z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Stenalgo | `s-` | `p-` | `v-` | `m-` | `t-` | `R-` | `w-` | `@-` | `a-` | `*` or `#` | `-i` | `-e` | `-j` | `-s` | `-k` | `-d` | `-t` | `-R` | `-n` | `-l` | `-Z` | `-m` |

Remarks on the table:
- Ireland has a single `*`; on the Starboard it is the two inner index keys. Stenalgo splits them into `*` and `#`
  (the star/hash homophone marks), so a starred Lapwing outline has two Stenalgo spellings, one with `*` and one with `#`
  (Gemini buttons `#1` and `*4` in `GEMINI_PR_KEYMAP`). Pressing both is a third spelling, not tested here.
- `S1` has no Stenalgo key (only `S2` is mapped).
- The Ireland number bar (`#`) has no counterpart: `NUMBER_KEY` is `None`, and Stenalgo's `&`, `%` and `k-` sit on Gemini's
  `#A`, `#B`, `#C` buttons as ordinary keys. Lapwing entries written with a `#` prefix cannot be mapped.
- Stenalgo's `k-` has no Ireland letter, so no Lapwing outline uses it.

Examples (Stenalgo steno, `-` where Plover needs the hyphen): `TP-PL` (`{.}`) -> `pm-kt`; `KW-BG` (`{,}`) -> `vt-dR`;
`KW-PL` (`{?}`) -> `vt-kt`; `H-F` (`{?}`) -> `R-j`; `TP-BG` (`{!}`) -> `pm-dR`; `STPH-FPLT` (`{:}`) -> `spmR-jktn`;
`H-PB` (`{^}-{^}`) -> `R-kd`; `P-P` (`{^}.{^}`) -> `m-k`; `K-L` (`{^}:{^}`) -> `v-t`; `KW-GS` (open quote) -> `vt-Rl`;
`KW*GS` (close quote) -> `vt*Rl` or `vt#-Rl`.

### Conflicts with the theory

Method: every Lapwing entry whose output is punctuation or a symbol (71 entries, 62 distinct outputs; 66 single-stroke,
5 multi-stroke such as the emoji) was mapped as above and compared, as a key set, with
`plover_stenalgo_dictionary.json` (167k outlines, parsed with `plover_stenalgo.stroke.parseStroke`). Two tests: an
exact outline match, and the stroke being the first stroke of a longer theory outline (a prefix clash). The pinky-square
rule (`KeyConflicts`, no diagonal pairs) was checked as well. The 29 starred entries were checked in both spellings
(`*` and `#`).

| Result | Count | Detail |
|---|---|---|
| Not pressable (pinky diagonal) | 0 | |
| Exact clash with a word | 1 | `OEU` -> `aie`: Lapwing `{^}/{^}` (slash) vs the theory's `hein` |
| Prefix clash | 1 | the same `aie` stroke starts 4,718 longer outlines (the "in-" family, e.g. `inracontables`), and occurs in 5,018 outlines overall |
| No Stenalgo equivalent | 2 | `#TPH-FPLT`, `#TPH*FPLT` (number-bar duplicates of `{:}` and `{;}`; the non-`#` versions are unaffected) |
| Free | 68 | no theory outline starts with or equals the mapped stroke (the prefix test applies to the 66 single-stroke entries only); this includes all starred entries, with `*` and with `#` |

So transplanting Lapwing's punctuation outlines *as they are* almost never collides, because the theory's words
use phonetic chords while those punctuation chords are mostly unpronounceable ones (`pm-kt`, `vt-dR`, `spmR-jktn`).
Only the slash on `OEU` has to move. The full list follows. Limits of this check:

- It reads only `plover_stenalgo_dictionary.json`; the expression-layer data (`plover_stenalgo_expressions.stenalgo`,
  merged chords) was not compared.
- It covers punctuation, not the rest of `lapwing-commands.json` (arrows, Tab, clipboard).
- "Free" means unused today; every new brief or theory change can take one of these chords, so keep them in the
  collision check (`src/keyconflicts.py`) as reserved.
- Comfort was not assessed: a mapped chord such as `spmR-jktn` is legal but needs six to nine keys at once, a poor fit
  for the most frequent marks (`{.}`, `{,}`); a Stenalgo-specific short outline for those is likely better than a transplant.

### All 71 entries

Sorted by Lapwing output. A starred outline shows both Stenalgo spellings (`*` key or `#` key); the comment is the
same for both unless it says otherwise. `-` = no Stenalgo equivalent. "Glued" means no space at that side (Plover `{^}`);
a bare symbol with no `{^}` is separated by spaces; `{-|}` capitalises the next word; `{~|x}` carries the capitalisation state through.

| # | Output (Lapwing) | What it does | Lapwing keypress | Stenalgo keypress | Comment |
|---|---|---|---|---|---|
| 1 | `"{^}{-\|}` | opening straight quote: space before, glued to the next word, next word capitalised | `SKWHA*FP` | `svtR*@jk` or `svtR@#jk` | free |
| 2 | `#{^}` | `#` with a space before, glued to the next word (hashtag / number prefix) | `HAERB` | `R@isd` | free |
| 3 | `-` | standalone hyphen with spaces on both sides | `H*PB` | `R*kd` or `R#-kd` | free |
| 4 | `--` | standalone `--` with spaces on both sides | `H*PBZ` | `R*kdm` or `R#-kdm` | free |
| 5 | `--{^}` | `--` with a space before, glued to the next word | `H-PBZ` | `R-kdm` | free |
| 6 | `-{^}` | `-` with a space before, glued to the next word (prefix) | `H-PBS` | `R-kdl` | free |
| 7 | `<{^}` | `<` with a space before, glued to the next word | `AEPBG` | `@ikdR` | free |
| 8 | `@{^}` | `@` with a space before, glued to the next word (handle) | `KWRA*T` | `vtw*@n` or `vtw@#n` | free |
| 9 | `\{{^}` | `\{` with a space before, glued to the next word (opening brace) | `TPR-BGT` | `pmw-dRn` | free |
| 10 | ``{^}` | backtick with a space before, glued to the next word (opens code) | `KH-FG` | `vR-jR` | free |
| 11 | `{!}` | `!` glued to the previous word, next word capitalised | `TP-BG` | `pm-dR` | free |
| 12 | `{!}{?}` | `!?` glued to the previous word, next word capitalised | `TPH-FBG` | `pmR-jdR` | free |
| 13 | `{(^}` | `(` with a space before, glued to the next word (opening bracket) | `STPH-FPLTS` | `spmR-jktnl` | free |
| 14 | `{,}` | `,` glued to the previous word, no capitalisation | `KW-BG` | `vt-dR` | free |
| 15 | `{,} " {^}{-\|}` | `,` glued to the previous word, then a spaced opening `"` glued to the next word, capitalised | `KWR-BGS` | `vtw-dRl` | free |
| 16 | `{,} {~\|"^}` | `,` glued to the previous word, then an opening `"` glued to the next word, capitalisation carried | `KWR-GS` | `vtw-Rl` | free |
| 17 | `{,} {~\|'^}` | `,` glued to the previous word, then an opening `'` glued to the next word, capitalisation carried | `KWR*GS` | `vtw*Rl` or `vtw#-Rl` | free |
| 18 | `{.}` | `.` glued to the previous word, next word capitalised | `TP-PL` | `pm-kt` | free |
| 19 | `{:}` | `:` glued to the previous word, no capitalisation | `#TPH-FPLT` | - | no number key |
| 20 | `{:}` | `:` glued to the previous word, no capitalisation | `STPH-FPLT` | `spmR-jktn` | free |
| 21 | `{;}` | `;` glued to the previous word, no capitalisation | `#TPH*FPLT` | - | no number key |
| 22 | `{;}` | `;` glued to the previous word, no capitalisation | `STPH*FPL` | `spmR*jkt` or `spmR#-jkt` | free |
| 23 | `{;}` | `;` glued to the previous word, no capitalisation | `STPH*FPLT` | `spmR*jktn` or `spmR#-jktn` | free |
| 24 | `{?}` | `?` glued to the previous word, next word capitalised | `H-F` | `R-j` | free |
| 25 | `{?}` | `?` glued to the previous word, next word capitalised | `KW-PL` | `vt-kt` | free |
| 26 | `{[^}` | `[` with a space before, glued to the next word | `PWR-BGT` | `mtw-dRn` | free |
| 27 | `{^)}` | `)` glued to the previous word (closing bracket) | `STPH*FPLTS` | `spmR*jktnl` or `spmR#-jktnl` | free |
| 28 | `{^...}` | `...` glued to the previous word, no capitalisation (trailing off) | `SW-BS` | `st-dl` | free |
| 29 | `{^]}` | `]` glued to the previous word | `PWR*BGT` | `mtw*dRn` or `mtw#-dRn` | free |
| 30 | `{^}#{^}` | `#` glued on both sides (infix) | `HA*ERB` | `R*@isd` or `R@i#sd` | free |
| 31 | `{^}%` | `%` glued to the previous word (suffix) | `P*ERS` | `m*isl` or `mi#sl` | free |
| 32 | `{^}--{^}` | `--` glued on both sides | `H-PBSZ` | `R-kdlm` | free |
| 33 | `{^}-{^}` | `-` glued on both sides (hyphen joining two words) | `H-PB` | `R-kd` | free |
| 34 | `{^}."{-\|}` | `."` glued to the previous word, next word capitalised (closing quote after a full stop) | `KWR*BGS` | `vtw*dRl` or `vtw#-dRl` | free |
| 35 | `{^}...{-\|}` | `...` glued to the previous word, next word capitalised | `SKW-BGS` | `svt-dRl` | free |
| 36 | `{^}.{^}` | `.` glued on both sides (decimal point, domain dot) | `P-P` | `m-k` | free |
| 37 | `{^}/{^}` | `/` glued on both sides | `OEU` | `aie` | clash: word hein; first stroke of 4718 outlines |
| 38 | `{^}:{^}` | `:` glued on both sides (time, ratio) | `K-L` | `v-t` | free |
| 39 | `{^}:{^}` | `:` glued on both sides (time, ratio) | `KHR-PB` | `vRw-kd` | free |
| 40 | `{^}>` | `>` glued to the previous word (suffix) | `A*EPBG` | `*@ikdR` or `@i#kdR` | free |
| 41 | `{^}@{^}` | `@` glued on both sides (e-mail) | `A*T` | `*@n` or `@#n` | free |
| 42 | `{^}\}` | `\}` glued to the previous word (closing brace) | `TPR*BGT` | `pmw*dRn` or `pmw#-dRn` | free |
| 43 | `{^}^{^}` | `^` glued on both sides | `KA*RT` | `v*@sn` or `v@#sn` | free |
| 44 | `{^}_{^}` | `_` glued on both sides | `RUPBD` | `wekdZ` | free |
| 45 | `{^}`` | backtick glued to the previous word (closes code) | `KH*FG` | `vR*jR` or `vR#-jR` | free |
| 46 | `{^}°` | `°` glued to the previous word (suffix) | `TKERG` | `pvisR` | free |
| 47 | `{^}°{^}` | `°` glued on both sides | `TK*ERG` | `pv*isR` or `pvi#sR` | free |
| 48 | `{^}Ω` | `Ω` glued to the previous word (suffix) | `O*EPL` | `*aikt` or `ai#kt` | free |
| 49 | `{^}Ω` | `Ω` glued to the previous word (suffix) | `O*EPLS` | `*aiktl` or `ai#ktl` | free |
| 50 | `{^}–{^}` | en dash glued on both sides (range) | `TPH-RB` | `pmR-sd` | free |
| 51 | `{^}—{^}` | em dash glued on both sides | `PH-RB` | `mR-sd` | free |
| 52 | `{^}‽{-\|}` | `‽` glued to the previous word, next word capitalised | `TRAEPBG` | `pw@ikdR` | free |
| 53 | `{^}‽{-\|}` | `‽` glued to the previous word, next word capitalised | `TRAPBG` | `pw@kdR` | free |
| 54 | `{^}♭` | `♭` glued to the previous word (suffix) | `TPHRA*T` | `pmRw*@n` or `pmRw@#n` | free |
| 55 | `{^~\|"}` | closing `"` glued to the previous word, capitalisation carried to the next word | `KW*GS` | `vt*Rl` or `vt#-Rl` | free |
| 56 | `{^~\|'}` | closing `'` glued to the previous word, capitalisation carried | `KR*RG` | `vw*sR` or `vw#-sR` | free |
| 57 | `{^~\|)}` | `)` glued to the previous word, capitalisation carried | `PR*EPB` | `mw*ikd` or `mwi#kd` | free |
| 58 | `{^™}` | `™` glued to the previous word (suffix) | `TR*PL` | `pw*kt` or `pw#-kt` | free |
| 59 | `{} " {^}{-\|}` | spaced opening `"` glued to the next word, capitalised (drops the previous attachment) | `KW-BGS` | `vt-dRl` | free |
| 60 | `{} ' {^}{-\|}` | spaced opening `'` glued to the next word, capitalised | `KW*BGS` | `vt*dRl` or `vt#-dRl` | free |
| 61 | `{~\|"^}` | opening `"`: space before, glued to the next word, capitalisation carried | `KW-GS` | `vt-Rl` | free |
| 62 | `{~\|'^}` | opening `'`: space before, glued to the next word, capitalisation carried | `KR-RG` | `vw-sR` | free |
| 63 | `{~\|(^}` | `(` with a space before, glued to the next word, capitalisation carried | `PREPB` | `mwikd` | free |
| 64 | `¯\_(ツ)_/¯` | inserts the shrug emoticon as free-standing text (spaces around) | `SHRUG/SHRUG` | `sRweR/sRweR` | free |
| 65 | `Δ{^}` | inserts `Δ` with a space before, glued to the next word (prefix) | `TK*EL/TA` | `pv*it/p@` or `pvi#t/p@` | free |
| 66 | `Δ{^}` | inserts `Δ` with a space before, glued to the next word (prefix) | `TKEL/TA*` | `pvit/p*@` or `pvit/p@#` | free |
| 67 | `Δ{^}` | inserts `Δ` with a space before, glued to the next word (prefix) | `TKO*EULT` | `pv*aietn` or `pvaie#tn` | free |
| 68 | `–` | standalone en dash with spaces on both sides | `TPH*RB` | `pmR*sd` or `pmR#-sd` | free |
| 69 | `—` | standalone em dash with spaces on both sides | `PH*RB` | `mR*sd` or `mR#-sd` | free |
| 70 | `✨` | inserts the emoji as free-standing text | `PHOEPBLG/SPARBG/-L/-S` | `mRaikdtR/sm@sdR/-t/-l` | free |
| 71 | `🤨` | inserts the emoji as free-standing text | `PHOEPBLG/H*U` | `mRaikdtR/R*e` or `mRaikdtR/Re#` | free |

### Stock `commands.json` mapped the same way

Fetched 2026-10-05 from `openstenoproject/plover`, `plover/assets/commands.json`: 37 entries, not the 39 counted in the
classification above (that count is superseded by this one). Same method and key map as the punctuation table: the
Ireland outline is mapped to Stenalgo keys (a starred outline shows its `*` and `#` spellings) and compared with
`plover_stenalgo_dictionary.json`, exact and first-stroke. The output column is layout-independent and can be kept as it is.

| # | Ireland outline | What it does | Output | Stenalgo keypress | Comment |
|---|---|---|---|---|---|
| 1 | `STPH-R` | Left arrow key; no space added | `{#Left}{^}` | `spmR-s` | free |
| 2 | `STPH-RB` | Ctrl+Left (word left) | `{#Control_L(Left)}{^}` | `spmR-sd` | free |
| 3 | `STPH-P` | Up arrow key | `{#Up}{^}` | `spmR-k` | free |
| 4 | `STPH-B` | Down arrow key | `{#Down}{^}` | `spmR-d` | free |
| 5 | `STPH-BG` | Ctrl+Right (word right) | `{#Control_L(Right)}{^}` | `spmR-dR` | free |
| 6 | `STPH-G` | Right arrow key | `{#Right}{^}` | `spmR-R` | free |
| 7 | `SKWRAEURBGS` | two newlines (new paragraph), next word capitalised | `{^\n\n^}{-\|}` | `svtw@iesdRl` | free |
| 8 | `SKWRAURBGS` | two newlines (new paragraph), next word capitalised | `{^\n\n^}{-\|}` | `svtw@esdRl` | free |
| 9 | `SKW-BGS` | Enter key; no space added | `{#Return}{^}` | `svt-dRl` | free; same outline is Lapwing's ellipsis `{^}...{-|}` |
| 10 | `SH-FT` | Ctrl+Home (start of document) | `{#Control_L(Home)}{^}` | `sR-jn` | free |
| 11 | `SR-RS` | Ctrl+End (end of document) | `{#Control_L(End)}{^}` | `sw-sl` | free |
| 12 | `TK*EL` | Delete key | `{#Delete}` | `pv*it` or `pvi#t` | free |
| 13 | `TKUPT` | opens Plover's Add Translation window | `{PLOVER:ADD_TRANSLATION}` | `pvekn` | free |
| 14 | `TPW-R` | Alt+Left (browser back) | `{#Alt_L(Left)}` | `pmt-s` | free |
| 15 | `TPW-G` | Alt+Right (browser forward) | `{#Alt_L(Right)}` | `pmt-R` | free |
| 16 | `TPEFBG` | Escape key | `{#Escape}` | `pmijdR` | free |
| 17 | `TA*B` | Tab key; no space added | `{#Tab}{^}` | `p*@d` or `p@#d` | free; letters TAB lost |
| 18 | `TA*BT` | Alt+Tab twice (previous window) | `{#Alt_L(Tab Tab)}` | `p*@dn` or `p@#dn` | free; letters TAB lost |
| 19 | `KPH*F` | Super+V (clipboard history) | `{#Super_L(v)}` | `vmR*j` or `vmR#-j` | free; mnemonic lost |
| 20 | `KPH*BG` | Super+K | `{#Super_L(k)}` | `vmR*dR` or `vmR#-dR` | free; mnemonic lost |
| 21 | `KPH*T` | Super+W | `{#Super_L(w)}` | `vmR*n` or `vmR#-n` | free; mnemonic lost |
| 22 | `KPH-BG` | Super+C | `{#Super_L(c)}` | `vmR-dR` | free; mnemonic lost |
| 23 | `KPA*L` | upper-case the next word | `{<}` | `vm*@t` or `vm@#t` | free; mnemonic lost |
| 24 | `KPAD` | retro: capitalise the previous word | `{*-\|}` | `vm@Z` | free; mnemonic lost |
| 25 | `KHR*F` | Ctrl+V (paste) | `{#Control_L(v)}` | `vRw*j` or `vRw#-j` | free; mnemonic lost |
| 26 | `KHR*BG` | Ctrl+K | `{#Control_L(k)}` | `vRw*dR` or `vRw#-dR` | free; mnemonic lost |
| 27 | `KHR*T` | Ctrl+W (close tab) | `{#Control_L(w)}` | `vRw*n` or `vRw#-n` | free; mnemonic lost |
| 28 | `KHR-BG` | Ctrl+C (copy) | `{#Control_L(c)}` | `vRw-dR` | free; mnemonic lost |
| 29 | `KA*PD` | retro: capitalise the previous word | `{*-\|}` | `v*@kZ` or `v@#kZ` | free; mnemonic lost |
| 30 | `PW*FP` | BackSpace key | `{#BackSpace}` | `mt*jk` or `mt#-jk` | free |
| 31 | `PW-FP` | BackSpace key | `{#BackSpace}` | `mt-jk` | free |
| 32 | `PHRO*F` | suspend Plover output | `{PLOVER:SUSPEND}` | `mRw*aj` or `mRwa#j` | free |
| 33 | `PHRO*PB` | resume Plover output | `{PLOVER:RESUME}` | `mRw*akd` or `mRwa#kd` | free |
| 34 | `PHROLG` | toggle Plover output on/off | `{PLOVER:TOGGLE}` | `mRwatR` | free |
| 35 | `R*R` | Enter key; no space added | `{#Return}{^}` | `w*s` or `w#-s` | free |
| 36 | `R-R` | newline glued to both sides, capitalisation carried | `{^~\|\n^}` | `w-s` | free |
| 37 | `*UPD` | retro: upper-case the previous word | `{*<}` | `*ekZ` or `e#kZ` | free |

Findings: no outline clashes with the theory, and no pinky diagonal is needed. The 13 outlines with mnemonic
letters (Tab, Super/Ctrl+letter, CAP) keep working as chords but no longer spell what they do. `SKW-BGS` is Enter in this
file and the ellipsis in Lapwing: both sets cannot be loaded with the same outline. Entries 7 and 8 differ only in
the vowel keys (`@ie` vs `@e`), and 30 and 31 are the same BackSpace with and without the star.

## Next steps

1. Finish the survey: read each plugin page, fetch Lapwing's `commands.json`, add popularity figures.
2. Run a classification script over the stock `commands.json` entries into classes (a)/(b)/(c) and list the outlines.
3. Design the Ireland-key -> Stenalgo-key mapping and collision check (`src/keyconflicts.py`), then the generator.

## Programmatic (Python) dictionaries: Jeff's and Emily's

Read 2026-10-05 from the READMEs on GitHub (the `.py` sources themselves were not read, so details of the
lookup code are inferred). All are loaded through `plover-python-dictionary` and decode the stroke by rule
instead of by table. They are a fourth class for the layout analysis: (d) **programmatic**, where the key
letters are baked into the decoder.

| Dictionary | Author / repo | Trigger and decoding | Gap it fills | Fit |
|---|---|---|---|---|
| Emily's Symbols | EPLHREU/emily-symbols | starter `SKHW`; `A`/`O` = space before/after; `*` = capitalise next; `E`/`U` = 4 variants; 2x3 key grid addresses symbols by shape; `-T`/`-S` repeat | punctuation and symbols, whitespace/arrow keys; attachment and capitalisation in one stroke | high: closest model for the French punctuation spacing (`attachmentMethod` variable) |
| Emily's Modifiers | EPLHREU/emily-modifiers | ending `-LTZ`; left hand fingerspells the letter; `FRPB` = Ctrl/Shift/Super/Alt; `*` switches to symbols; `AO` + bottom row = binary digits, `+F` = F1-F12 | any key combo in one stroke | high for specials keys and combos |
| Jeff's Modifiers | jthlim/jeff-modifiers (14 stars) | suffix `-TZ`; `-FRPB` = Ctrl/Shift/Super/Alt; `TKPWHR`+`-LTZ` = navigation; `+U` = symbols; `STKPWR`+`EULTZ` = binary numbers/F-keys (S=8, K=4, W=2, R=1) | same, with navigation block | high; compare with Emily's, pick one |
| Jeff's Numbers | jthlim/jeff-numbers (8 stars) | digits entered through the normal number key, then suffix keys: `EU` reverse, `Z` +"00", `*` decimal point, `*S` comma, `DZ` dollars, `R` Roman, `G` words, `B`/`W` ordinal, `-RB`, `-RG` currency/percent | numbers and formatting | partly: needs a number-entry mode first (no `NUMBER_KEY`); the suffix ideas transfer; French number words, decimal comma and `1er`/`2e` ordinals replace the English parts |
| Jeff's Visual Stroke (the "Show Stroke" asked about) | jthlim/jeff-visual-stroke (5 stars) | trigger `STR*Z`, then the chord to show; outputs an ASCII-art keyboard diagram of the chord | stroke lookup while learning | useful for a Stenalgo learner: needs the Stenalgo board drawn from `_generated_keys.py`; overlaps the trainer and plover-layout-display |
| Jeff's Phrasing | jthlim/jeff-phrasing (45 stars) | starter = subject (`SWR` I, `KWHR` he), `AO*` = auxiliaries and negation, `EUF` word order, middle keys = verbs, `-T` = object; tenses and verb forms matched automatically | common English phrases | low as such (English grammar); the idea overlaps the expression layer: `docs/PIPELINE.md` S8.10; a French analogue (pronoun + auxiliary + verb) is a design option, not a gap |

### What they imply for Stenalgo

- **They cannot be dropped in.** They match Ireland key letters (`SKHW`, `-LTZ`, `-FRPB`) and rely on fingerspelling
  on the left hand, binary digits on the bottom row, and the number key. Stenalgo's keys are named differently
  (`GEMINI_PR_KEYMAP`), its left hand holds phoneme keys, and there is no fingerspelling in the base theory yet.
- **Common design pattern worth copying:** a *unique trigger/ending* that keeps the whole family out of the
  word theory (`SKHW`, `-LTZ`, `-TZ`, `STR*Z`), plus a fixed key-to-role split (character / modifiers / switcher).
  In Stenalgo this is the stroke-budget question: which chords stay free after the words and expression briefs
  (`src/keyconflicts.py`)? The TODO's collision check applies to the trigger.
- **Recommended route:** a generator (`util/export_*`) that writes a Stenalgo-native decoder or a static JSON,
  following the fingerprint pattern of the other exporters, instead of shipping their `.py` files. The static
  JSON route keeps Plover's reverse lookup working, which a Python dictionary does not.
- **Open point:** what the French theory uses for fingerspelling, since Emily's and Jeff's modifiers both
  select the letter through it.
- **Licences:** not checked; read them before reusing code (ideas and key layouts can be cited).

### Fingerspelling: what it is and what it would take here

Fingerspelling writes a word letter by letter, one stroke per letter, for names, acronyms, URLs, codes and anything
outside the dictionary. It is also the letter-selector inside Emily's and Jeff's modifiers, so the question above
(what does the French theory use?) blocks both.

**How it works on a stenotype (Ireland layout, English).** Each letter is one chord, usually the key of that letter
plus `*` for the "spelled" variant (the lower-case letter alone often collides with a word):

| Intent | Strokes | Output |
|---|---|---|
| lower-case `a`, `b`, `c` | `A*`, `PW*`, `KR*` | `a b c` (attached by the `{>}{&a}` glue meta: no spaces between letters) |
| upper-case `A` | `A*P` | `A` (`{&A}`) |
| spell "SNCF" | `S*P`, `TPH*P`, `KR*P`, `TP*P` | `SNCF` |
| spell "Léa" (accent) | `HR*P`, then an accent stroke such as `{^é^}` / a dead-key entry, then `A*` | `Léa` |
| initialism with the French letter names | `S*`, `N*`, `S*`... | `sns` |

Typical outputs use Plover's glue meta `{&x}` (attaches to the previous glued letter) and capital variants
`{&X}`. Emily's Modifiers reuse the same left-hand letter chords with the `-LTZ` ending to send `Ctrl+c`, `Alt+Tab`.

**Why it does not transfer directly.** Stenalgo's left hand holds phoneme keys (`k-`, `s-`, `p-`, `v-`, `m-`, `t-`,
`R-`, `w-`), so `A*` or `PW*` mean nothing, and there are 22 phoneme keys, not 26 letters. French letters also need
accents (`é è ê ë à â ç î ï ô ù û ü œ`) which the English tables do not cover.

**Candidate designs (to decide, none implemented).**

1. *Letter names as phonetics.* Spell a letter by its French name, which the phoneme keys can already write:
   `a` = /a/, `b` = /be/, `c` = /se/, `d` = /de/, `f` = /Ef/, `g` = /Ze/, `h` = /aS/, `j` = /Zi/, `k` = /ka/,
   `w` = /dublave/. One stroke per letter plus the `*` or `#` mark as the "spelled" flag, e.g. `p-`+`-e`+`*` -> `{&b}`.
   Pro: nothing new to learn; con: `*` and `#` already carry homophone marks (`resolved_press_sets.json`), so a
   dedicated flag is needed.
2. *Trigger plus letter index.* A unique trigger (like `SKHW` or `STR*Z`) held with a two-stroke code from the phoneme
   keys: a stroke picks the letter group (`a-e`, `f-j`, ...), the next picks the letter. 26 letters need 2 strokes each.
3. *Reserved keys.* Use the `&` and `%` keys (currently reserved) as a spelling modifier on top of the phoneme keys
   in design 1: `&` = lower-case letter, `%` = capital. Costs no new chord region, only a collision check
   (`src/keyconflicts.py`).
4. *Accents.* Dedicated post-letter strokes that retro-edit the last glued letter (`é`, `è`, `ç`...), using the retro
   macro of `plover-last-translation`; or ship the accented letters as their own entries in the generated JSON.

Expected examples under design 3 (illustrative strokes, spelled from the French letter names):

| Intent | Strokes | Output |
|---|---|---|
| spell "CNRS" | `&`+/se/, `&`+/En/, `&`+/ER/, `&`+/Es/ | `cnrs` |
| capital then lower-case "Léa" | `%`+/El/, `&`+/e/ + accent stroke, `&`+/a/ | `Léa` |
| URL fragment "a-b.fr" | letters as above plus a symbol stroke from the Emily's Symbols model | `a-b.fr` |

Whichever design wins, export it as static JSON from a generator (reverse lookup keeps working) and check the new
chords against the word theory before shipping.

### Programmatic dictionaries vs the stock file and the plugins

Based on the READMEs and the plugin list; items marked (inferred) are not verified against the source.

**Advantages of Emily's and Jeff's dictionaries**
- Coverage: one decoder handles every letter, symbol and key combo, with modifiers combined freely; stock `commands.json` has 39 hand-picked entries.
- Learnability: the key roles (character, modifiers, switcher, trigger) are learned once instead of memorising hundreds of outlines.
- Single-stroke entry: attachment and capitalisation, or a full shortcut, fit in one stroke.
- Collision control: a unique trigger or ending (`SKHW`, `-LTZ`, `-TZ`) keeps the family away from the word theory, which is what the TODO's collision check needs.
- No Plover-side code: plain Python files, no plugin API (unlike the macro and meta plugins).

**Drawbacks**
- Layout lock-in: Ireland key letters are baked into the decoders, so they need a rewrite. The stock `commands.json` is only a table whose output sides are already layout-independent, so it is the easier source for the outline remapping.
- They depend on fingerspelling, a number key and binary digits; Stenalgo has none yet (`NUMBER_KEY = None`).
- No reverse lookup, so no outline suggestions (inferred).
- Each family takes a whole region of the chord space, while the phoneme keys already carry the words.
- Extra dependency: `plover-python-dictionary`; static JSON would not need it.
- Maintenance and licence unchecked; the repositories have 5 to 45 stars.

**Where the plugins still win**
- `plover-last-translation`, `plover-retro-quotes`, `plover-dict-commands`: retro editing, quotes and dictionary priority are not covered by the dictionaries.
- `plover-layout-display` and Spectra Lexer help learners without using strokes; they overlap with Jeff's Visual Stroke.

**Recommendation:** copy the design (trigger, key roles, attachment flags) and generate static Stenalgo JSON; use the plugins for retro editing; use stock `commands.json` only for the output side of special keys.
