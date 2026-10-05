"""
Plover "system" plugin for Stenalgo's French Starboard theory: makes Plover's
raw-steno display (and dictionary strokes) use Stenalgo's own key names
instead of the English "Ireland" layout's.

`KEYS`/`IMPLICIT_HYPHEN_KEYS`/`GEMINI_PR_KEYMAP` come from `_generated_keys`
(regenerate with `python -m util.export_plover_system` from the stenalgo repo
whenever `starboard3h.json` changes) -- this module has no dependency on the
solver stack itself, only on this small generated table, so it stays cheap to
install into a real Plover.

No new Plover *machine* plugin is needed: Gemini PR is just a fixed-bit-position
wire format whose built-in machine plugin's internal (Ireland-named) labels get
remapped to these key names by `KEYMAPS["Gemini PR"]`, entirely through Plover's
own config -- see the "one more thing on flickering llama" plan for the research
behind this design.
"""
from ._generated_keys import GEMINI_PR_KEYMAP, IMPLICIT_HYPHEN_KEYS, KEYS

SUFFIX_KEYS: tuple[str, ...] = ()

# No number bar yet -- Stenalgo strokes don't have a dedicated numeral key.
NUMBER_KEY: str | None = None
NUMBERS: dict[str, str] = {}

UNDO_STROKE_STENO = "*"

# Stenalgo strokes already resolve to exact spellings computationally (see
# dictionary.py/writeDisambiguatedTheory); there's no English-style suffix-stacking
# orthography to correct after the fact.
ORTHOGRAPHY_RULES: list[tuple[str, str]] = []
ORTHOGRAPHY_RULES_ALIASES: dict[str, str] = {}
ORTHOGRAPHY_WORDLIST: str | None = None

KEYMAPS: dict[str, dict[str, str | tuple[str, ...]]] = {
    "Gemini PR": dict(GEMINI_PR_KEYMAP),
}

# The theory ships inside this package (`dictionaries/`, copied by `python -m util.export_plover_plugin`). Plover
# uses the default list when a config has no dictionary list of its own for this system, highest priority first:
# the expression data answers merged chords and must sit above the stock dictionary, whose JSON it reads its word
# index from (same folder).
ASSET_PREFIX = "asset:plover_stenalgo:dictionaries/"
DICTIONARIES_ROOT = "asset:plover:assets"
DEFAULT_DICTIONARIES: tuple[str, ...] = (
    "user.json",
    "commands.json",
    ASSET_PREFIX + "plover_stenalgo_expressions.stenalgo",
    ASSET_PREFIX + "plover_stenalgo_dictionary.json",
)
