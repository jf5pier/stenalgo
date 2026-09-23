# Plover integration — design, build, and hardware verification (2026-09-21)

Written so a fresh (cleared-context) session can pick up without re-deriving context.
**Status as of end of session: fully working end-to-end.** `plover_stenalgo` (a
Plover system plugin) is installed in the user's real Plover, verified against the
real physical Starboard's wiring, and a test word ("rat", keys 8+12) typed correctly
with Stenalgo's own key names showing on the raw-steno paper tape.

## Bottom line

Stenalgo's raw-steno display and dictionary previously had no path into Plover at
all — Plover would show English "Ireland" layout key names regardless of what
Stenalgo's theory actually uses, and there was no word→stroke dictionary file Plover
could load. This session designed and shipped a first cut:

- **`src/keyboard.py`**: `Starboard.keyDisplayName`/`keyDisplayNames`/`strokesToRTFCRE`
  — cosmetic per-key display names (derived from `starboard3h.json`'s phonemes) and a
  renderer that produces Plover-style RTFCRE stroke strings instead of the existing
  `strokesToString`'s bare phoneme concatenation.
- **`plover_stenalgo/`**: a standalone, dependency-free Plover *system* plugin package
  (own `pyproject.toml`, entry point `plover.system`). No custom Plover *machine*
  plugin needed — see "Plover architecture" below for why.
- **`util/export_plover_system.py`**: generates `plover_stenalgo/plover_stenalgo/_generated_keys.py`
  (KEYS, IMPLICIT_HYPHEN_KEYS, the Gemini PR keymap) from `starboard3h.json`, by key
  *position* not name, so it survives future re-optimization.
- **`util/export_plover_dictionary.py`**: reads `FirstTheory.pickle` (base strokes
  only — Realization Phase's star/hash marks aren't wired into a persisted per-word output yet)
  and writes a real Plover JSON dictionary (`plover_stenalgo_dictionary.json`, 87.8k
  strokes, ~47.4k same-steno collisions — expected, see "What's genuinely still open").
- New unit tests in `src/test/keyboard_test.py` for the three new `Starboard` methods.
- **The Gemini PR keymap was verified against the real device**, not just derived from
  documentation/reference firmware — see "The hardware verification saga" below. It
  had to be corrected: the initial guess was wrong for 4 of the 26 keys.

## The original question

User asked how to get Plover to display Stenalgo's own key names (not English's) on
the raw-steno paper tape, and correctly translate strokes into French dictionary
words, given Starboard's RP2040 firmware speaks the Gemini PR / TX Bolt / ProCAT /
Plover HID protocols (via Javelin).

## Plover architecture (why no custom machine plugin is needed)

Researched by reading Plover 5.4.1's actual source (`pip download`, unzip the wheel —
no network install needed to just read files):

- Plover's raw-steno paper tape (`plover/gui_qt/paper_tape.py`) always renders the
  active **system**'s own `KEYS` names — never hardcoded English names:
  `self._all_keys = "".join(key.strip("-") for key in system.KEYS)`.
- A Plover **system** plugin (entry point group `plover.system`, a plain Python
  module) declares `KEYS`, `IMPLICIT_HYPHEN_KEYS`, `SUFFIX_KEYS`, `NUMBER_KEY`,
  `NUMBERS`, `UNDO_STROKE_STENO`, `ORTHOGRAPHY_RULES`/`_ALIASES`/`_WORDLIST`,
  `KEYMAPS`, `DICTIONARIES_ROOT`, `DEFAULT_DICTIONARIES` (`plover/system/__init__.py`'s
  `_EXPORTS` dict is the authoritative list of what's required). `KEYS` can be
  **any** strings — nothing ties them to English letters.
- Gemini PR and TX Bolt (`plover/machine/gemini_pr.py`, `tx_bolt.py`) are just
  fixed-bit-position wire formats. Their `STENO_KEY_CHART` English-looking labels
  (`"S1-"`, `"T-"`, `"*1"`, ...) are the **machine plugin's own internal labels**,
  immediately remapped through `plover/machine/keymap.py`'s `Keymap` class to
  whatever the active system's `KEYS` are — a plain `{system_key: machine_key(s)}`
  dict, fully configurable, no code changes needed per system.
- **Conclusion**: a system plugin + the *existing* Gemini PR machine plugin + a
  `KEYMAPS["Gemini PR"]` binding is sufficient. A custom machine plugin would only be
  needed if Starboard needed more than Gemini PR's 42 bit-positions (it needs 26).
- `plover_stroke` (the compiled stroke-encoding library `plover.steno.Stroke` is
  built on) enforces one real constraint discovered by trial: every system `KEYS`
  name must be **exactly one core character, with an optional single leading or
  trailing hyphen** (e.g. `"k-"`, `"-t"`, `"*"` are valid; `"&0"`, `"S1-"` as a system
  key are not). This killed an initial placeholder-naming idea (see `keyDisplayName`'s
  docstring in `src/keyboard.py`).

## Firmware context (Starboard is genuinely Javelin-based)

Confirmed via local checkouts at `~/javelin-steno` and `~/javelin-steno-pico` (the
user's own — not hypothetical prior art anymore, see [[dual_target_architecture]] auto-memory):

- `javelin-steno-pico/config/starboard_rp2040.h`: `PRODUCT_NAME = "Starboard
  (Javelin)"`, full 28-button direct-wired pin map already defined for this exact
  board (`Andrew Hess`'s design — also has a QMK-firmware equivalent,
  `github.com/AndrewHess/qmk_firmware`, `starboard` branch).
- `pico_bindings.cc:81-84` unconditionally compiles in `StenoGemini`, `StenoTxBolt`,
  `StenoProcat`, `StenoPloverHid` processors — the wire-protocol code already exists.
- Current config has `JAVELIN_USE_EMBEDDED_STENO 1` (Javelin's own onboard-dictionary
  standalone engine, no host Plover). Per the user, that standalone path is a
  **later** goal, gated on shrinking the dictionary to fit RP2040 flash — ties to
  [[dual_target_architecture]]'s runtime rule-engine idea, not this session's scope.
- **Still open, not investigated this session**: whether switching between Gemini PR
  passthrough and `JAVELIN_USE_EMBEDDED_STENO` onboard mode is a runtime toggle (no
  firmware rebuild needed) or compile-time only. This is a `javelin-steno-pico`-repo
  task, out of scope for the `stenalgo` repo.

## The hardware verification saga

The first cut of `GEMINI_PR_KEYMAP` (in `util/export_plover_system.py`) was a
**guess**: I laid out the 26 Gemini PR labels in the conventional steno order
(S1-,S2-,T-,K-,P-,W-,H-,R-,A-,O-,*1-4,-E,-U,-F,-R,-P,-B,-L,-G,-T,-S,-D,-Z) against
Stenalgo's key indices in ascending order, and cross-checked it against Andrew Hess's
published QMK reference keymap (`keyboards/starboard/keymaps/steno_only/keymap.c`,
cloned from GitHub) for the same physical board. 22 of 26 keys matched.

The remaining 4 (Stenalgo keys 0, 1, 2, 10 — three "unused/reserved" slots plus the
onset "k" phoneme key) were ambiguous from documentation alone, so the user tested
the real device:

1. **First test**: pressed all 26 keys in ascending Stenalgo-index order (0→25) with
   stock Plover ("English Stenotype" system + Gemini PR machine) and pasted the
   resulting paper-tape lines. This confirmed 20/26 keys immediately, but the "#"
   column (Plover's English system merges Gemini's 12 separate `#1`-`#C` number-bar
   bits into one display column) couldn't distinguish *which* bit fired for keys 0,
   1, 2, 10 — all four showed as bare `#`.
2. **Infrastructure fight to get an unambiguous read**, roughly in order attempted:
   - A "debug" Plover system plugin exposing all 12 number-bar bits as distinct keys
     — blocked because Plover's own "Plugins Manager → Install from Git repo" dialog
     literally does `pip install "git+" + <text>`, so a plain WSL UNC path doesn't
     work (needs an actual git remote, e.g. `git+file://...`).
   - Installing a full Plover inside WSL2 directly (`pip install plover`) — blocked
     first by `xkbcommon` having no prebuilt Linux wheel at any Python version (needs
     `libxkbcommon-dev` system headers, `sudo apt-get install libxkbcommon-dev` fixed
     it), and even after that, the physical USB device isn't visible inside WSL2
     without `usbipd-win` setup (not attempted — too much one-time setup for a
     one-off diagnostic).
   - **What actually worked**: a standalone raw-serial probe script, first tried in
     Python (blocked: no Python on the user's Windows PATH), then rewritten in
     **PowerShell** (`System.IO.Ports.SerialPort`, built into Windows, zero installs)
     that decodes Gemini PR's 6-byte packets directly using
     `plover/machine/gemini_pr.py`'s own `STENO_KEY_CHART`, bypassing Plover
     entirely. This is the general lesson: **when diagnosing real hardware and the
     user's dev environment is unknown/mismatched (WSL vs. Windows vs. macOS),
     prefer a tool with zero extra dependencies over the "correct" tool that needs
     installation** — it took 4 failed approaches to get here.
3. **Result** (pressing keys 0,1,2,10 with the PowerShell probe, Plover closed):
   `key0 -> #A`, `key1 -> #B`, `key2 -> #C`, `key10 -> #1`. (Also re-confirmed
   key3 -> `S2-` specifically, and key15 -> `*4` specifically, resolving remaining
   minor ambiguities for free.)

**Real finding**: keys 0, 1, 2, and 10 are all wired to Gemini's number-bar bits, not
letters or star bits. Only key 15 (`HASH_KEY` in Stenalgo's own naming) sends an
actual star bit (`*4`). This means, on the currently-flashed firmware:
- Stenalgo's "k" phoneme (key 2) currently cannot be typed via Gemini PR relay at all
  as a plain letter — it would register as a number-bar bit instead.
- `STAR_KEY` (key 10) is not actually a star key on this firmware; only `HASH_KEY`
  (key 15) is.

**Why this turned out to be a non-problem for `plover_stenalgo` specifically**:
Plover's English Stenotype system treats the number bar specially only because *it*
wires `NUMBER_KEY`/`NUMBERS` to reinterpret certain keys as digits when the bar is
held. `plover_stenalgo` never sets those (`NUMBER_KEY = None`), so Gemini's `#A`,
`#B`, `#C`, `#1` bits behave as four perfectly ordinary, independent chordable keys
under our system — no different from binding to any other raw bit. `GEMINI_PR_LABELS`
in `util/export_plover_system.py` was updated to the verified real values and the
generated file regenerated; `plover_stroke` re-validated all 26 keys round-trip
correctly (tested in a throwaway venv).

**Still an open question** (not a Plover problem, a Stenalgo design one): should the
firmware's button-script actually be reassigned so key 2 sends a real letter and key
10 a real star bit, matching the *original* intent of the physical layout? Left for
the user to decide — not touched this session.

## Installing the plugin in a real Windows Plover (from WSL)

Plover's **Tools → Plugins Manager → Install from Git repo** dialog literally runs
`pip install "git+" + <whatever you type>` — it needs an actual git remote, not a
plain path. A `file://` URL to the WSL-side working copy did **not** work (git-over-UNC-path
issues). What worked: pushed `plover_stenalgo/` to a real GitHub repo,
**https://github.com/jf5pier/stenalgo-plover** (public; created with `gh repo create
jf5pier/stenalgo-plover --public --source=. --push`), then installed via
`git+https://github.com/jf5pier/stenalgo-plover.git` in that same dialog. The
dictionary file itself doesn't need to be in git at all for Plover to load it — a
plain WSL UNC path works fine for **Configuration → Dictionaries → Add**
(`\\wsl.localhost\<distro>\home\jfsp\stenalgo\plover_stenalgo_dictionary.json`);
the git requirement is specific to that one "Install from Git repo" plugin dialog,
not to Plover's file-loading in general.

(The `plover_stenalgo/` directory in *this* repo was briefly its own nested git repo
during that push, then had its `.git` removed so it's tracked normally here instead —
the GitHub repo remains the separate copy Plover's installer points at; keep the two
in sync by hand if `plover_stenalgo/`'s source changes again.)

## The "@" red herring — two real stroke-rendering bugs found while loading the dictionary

First real Plover load threw ~6,000 "invalid steno" warnings. The user's hypothesis
was the `@` (schwa) character; that turned out to be a coincidence (all the failing
words happened to also involve a separate bug, not because `@` itself was invalid —
confirmed by testing `@` alone through `plover_stroke` directly, which parses fine).
Reproduced directly against the real `plover_stroke` library (the same one Plover
uses) to find the actual causes, both pre-existing bugs in the theory's stroke
generation (present in `strokesToString`/`theory.tsv` too, not introduced by the
Plover work), now worked around in `strokesToRTFCRE` specifically:

1. **Duplicate keys within one stroke** (~7,238 / 184,524 words, e.g. "rien",
   "besoin"): some syllables combine two phonemes whose key assignments overlap in
   `starboard3h.json` (onset "R" = key 8 alone; onset "j" = the chord (8, 9)) —
   `getStrokeOfSyllableByPart`'s naive per-phoneme concatenation adds key 8 twice.
   A stroke is fundamentally a *set* of pressed keys, so deduplicating in
   `strokesToRTFCRE` is always correct regardless of how/whether the deeper
   phoneme-overlap question ever gets resolved upstream.
2. **Keys out of canonical order within a stroke**: Plover's RTFCRE parser requires
   each stroke's letters in the system's declared `KEYS` order (ascending key index
   here); some multi-consonant coda clusters resolved out of order (e.g. key 21 "-R"
   before key 20 "-t"), which `strokesToString`'s plain concatenation tolerates but
   Plover's stricter parser rejects.

Fix: `strokesToRTFCRE` now iterates `sorted(set(stroke))` instead of the raw
stroke tuple. Verified **zero** parse errors against `plover_stroke` across all
87,506 regenerated dictionary entries (down from 87,840 pre-fix, as a handful of
previously-distinct-looking duplicate-key strings collapsed into genuinely
identical, now-colliding strokes — folded into the existing same-steno collision
count, not a new problem). **Deliberately not touched**: `strokesToString`,
`theory.tsv`, `getStrokeOfSyllableByPart` — the root cause is a core-theory
phonology question (whether "R + j" together should even look different from "j"
alone, physically) well outside this session's Plover-integration scope.

## Files touched

- `src/keyboard.py` — `Starboard.keyDisplayName`, `keyDisplayNames`,
  `strokesToRTFCRE` (dedupes + sorts keys per stroke), `_reservedKeyDisplayNames`.
- `src/test/keyboard_test.py` — `TestKeyDisplayName`, `TestStrokesToRTFCRE`.
- `util/export_plover_system.py` (new) — generator, `GEMINI_PR_LABELS` now reflects
  verified real hardware wiring (see inline comment with the 2026-09-21 provenance
  note).
- `util/export_plover_dictionary.py` (new) — dictionary exporter.
- `plover_stenalgo/` (new, committed here as plain files) — the Plover plugin
  package (`pyproject.toml`, `system.py`, generated `_generated_keys.py`). Also
  mirrored at **github.com/jf5pier/stenalgo-plover** (public) for Plover's
  git-based plugin installer — see "Installing the plugin" above; keep both in
  sync by hand.
- `plover_stenalgo_dictionary.json` (new, committed — 87,506 strokes, same
  convention as this repo's other committed generated artifacts like
  `starboard3h.json`/`realization_report.json`).
- Diagnostic-only, not part of the repo: `~/gemini_raw_probe.py` and
  `~/gemini_raw_probe.ps1` in the user's home directory (kept there in case more
  keys ever need re-verification after a firmware change); a throwaway
  `plover_stenalgo_debug` plugin under `/tmp/.../scratchpad/` (session-scoped,
  will not survive — superseded by the PowerShell probe anyway, safe to ignore/delete).

## What's genuinely still open

- **The ~47.4k same-steno collisions** in `plover_stenalgo_dictionary.json` are
  expected — Realization Phase's star/hash marking (`src/ambiguitychecker.py`) isn't wired into
  `dictionary.py`'s persisted per-word output yet (tracked separately in
  `ROADMAP.md`/`CLAUDE.md`'s pipeline section, item 6). Re-running the exporter once
  that lands should resolve most of them.
- **Firmware button-script fix for keys 2/10** (see above) — a decision for the user,
  not started.
- **Track A (javelin-steno-pico firmware: runtime vs. compile-time protocol
  selection)** — not investigated this session at all, flagged as a separate,
  focused session in that repo.
