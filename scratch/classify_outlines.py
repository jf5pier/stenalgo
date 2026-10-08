"""Writes resources/outlineClassification.tsv: for every punctuation outline and command outline of the stock Plover
English system, Lapwing and Pluvier/TAO, how its outline MEANS what it means, which decides how it converts to the
Stenalgo layout (docs/PLOVER_COMPLEMENTS.md):

  position      the meaning is the key positions (-FPLT = period, STPH-R = Left): convert KEY TO KEY (GEMINI_PR_KEYMAP)
  phonetic-fr   the letters spell the sounds of the French word (STROFL = apostrophe): convert by PHONEME
                (compute the Stenalgo stroke of the pronunciation)
  phonetic-en   the letters spell the sounds of an English word (TA*B = tab, KPA = cap, PHRO*F = plover off): no French
                meaning; re-derive from a French name (or keep key-to-key)
  mnemonic      initials or letter names (R-R = Return, KHR-BG = Ctrl+C): re-derive or keep key-to-key
  unclear       not decided
`status`: reviewed = read by hand, auto = assigned by a prefix rule here, table = the phonetic reading was checked against
Pluvier's sound tables (src/steno.py of github.com/Vermoot/Pluvier: `j` and `ij` -> -LZ, conditional /RE/ -> -RS),
unverified = the reading of the outline's letters is a guess.

Run: python scratch/classify_outlines.py [PLOVER_ASSETS_DIR] [PLOVER_CONFIG_DIR]   (defaults: the Windows install)
"""
import csv
import json
import re
import sys

ASSETS = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/Program Files/Open Steno Project/Plover 5.4.1/data/Lib/site-packages/plover/assets"
CONFIG = sys.argv[2] if len(sys.argv) > 2 else "/mnt/c/Users/jfsp/AppData/Local/plover/plover"
OUT = "resources/outlineClassification.tsv"


def load(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


rows: list[tuple[str, str, str, str, str, str]] = []   # source, outline, output, kind, status, note


def add(source: str, outline: str, output: str, kind: str, status: str, note: str = "") -> None:
    rows.append((source, outline, output.replace("\n", "\\n"), kind, status, note))


# --- punctuation of Plover English and Lapwing: key-position everywhere -------------------------------------------------
PUNCTUATION = ["TP-PL", "KW-BG", "KW-PL", "H-F", "TP-BG", "STPH", "STPH-FPLT", "STPH*FPLT", "SKW-BGS", "SW-BS", "H-PB", "P-P",
               "OEU", "K-L", "KW-GS", "KW*GS", "KR-GS", "KR-RG", "KR*RG", "A*E", "AE", "STPH-FPLTS", "STPH*FPLTS", "PWR-BGT",
               "PWR*BGT", "-PBT", "SKW-T", "SKW*T", "H*PB", "H*PBZ", "A*T", "KPA*", "TK-LS", "S-P", "SP"]
for source, path in (("plover-english", f"{ASSETS}/main.json"), ("lapwing", f"{CONFIG}/lapwing-base.json"),
                     ("lapwing", f"{CONFIG}/lapwing-commands.json")):
    d = load(path)
    for outline in PUNCTUATION:
        # an English word or suffix on the same outline (`STPH` -> "is in", `K-L` -> "{^cal}") is not punctuation
        if outline in d and not re.search(r"[A-Za-z]{2}", d[outline]) \
                and not any(r[0] == source and r[1] == outline for r in rows):
            add(source, outline, d[outline], "position", "reviewed", "punctuation: the letters are not sounds")

# --- Plover English stock commands.json ----------------------------------------------------------------------------------
REVIEWED = {
    "SKWRAEURBGS": ("unclear", "new paragraph"), "SKWRAURBGS": ("unclear", "new paragraph"),
    "SKW-BGS": ("position", "Return"), "SH-FT": ("unclear", "Ctrl+Home"), "SR-RS": ("unclear", "Ctrl+End"),
    "TK*EL": ("phonetic-en", "del"), "TKUPT": ("unclear", "add translation"),
    "TPW-R": ("position", "Alt+Left: TPW prefix + the arrow's R"), "TPW-G": ("position", "Alt+Right"),
    "TPEFBG": ("phonetic-en", "esc"), "TA*B": ("phonetic-en", "tab"), "TA*BT": ("phonetic-en", "alt-tab"),
    "KPH*F": ("mnemonic", "Super+V"), "KPH*BG": ("mnemonic", "Super+K"), "KPH*T": ("mnemonic", "Super+W"),
    "KPH-BG": ("mnemonic", "Super+C"), "KHR*F": ("mnemonic", "Ctrl+V"), "KHR*BG": ("mnemonic", "Ctrl+K"),
    "KHR*T": ("mnemonic", "Ctrl+W"), "KHR-BG": ("mnemonic", "Ctrl+C"),
    "KPA*L": ("phonetic-en", "cap"), "KPAD": ("phonetic-en", "cap'd"), "KA*PD": ("phonetic-en", "cap'd"),
    "PW*FP": ("unclear", "BackSpace"), "PW-FP": ("unclear", "BackSpace"),
    "PHRO*F": ("phonetic-en", "plover off"), "PHRO*PB": ("phonetic-en", "plover on"), "PHROLG": ("phonetic-en", "plover toggle"),
    "R*R": ("mnemonic", "Return: R(eturn) twice"), "R-R": ("mnemonic", "Return"), "*UPD": ("phonetic-en", "up'd"),
}
for outline, output in load(f"{ASSETS}/commands.json").items():
    if outline.startswith("STPH-"):
        add("plover-english", outline, output, "position", "reviewed", "cursor key: STPH + the direction key")
    elif outline in REVIEWED:
        add("plover-english", outline, output, REVIEWED[outline][0], "reviewed", REVIEWED[outline][1])
    else:
        add("plover-english", outline, output, "unclear", "auto", "not reviewed")

# --- Lapwing commands: reviewed number-bar variants, then prefix rules ----------------------------------------------------
# The number bar becomes the Stenalgo `#` key pressed with the stroke (util/export_plover_complements.py), so these convert key
# to key even though their plain bases (Tab, Return) are mnemonic.
LAPWING_REVIEWED = {
    "#TA*B": "Shift+Tab: number-bar variant of TA*B", "#R*R": "Shift+Return: number-bar variant of R*R",
    "#R-R": "Shift+Return: number-bar variant of R-R", "#*": "{*}: number bar + star",
}

# --- Lapwing commands: prefix rules ---------------------------------------------------------------------------------------
for outline, output in load(f"{CONFIG}/lapwing-commands.json").items():
    if outline in LAPWING_REVIEWED:
        add("lapwing", outline, output, "position", "reviewed", LAPWING_REVIEWED[outline])
    elif outline.startswith(("#TPH", "STPH")):
        add("lapwing", outline, output, "position", "auto", "cursor / selection block: prefix + direction keys")
    elif outline.startswith("TPW") and "{#F" in output:
        add("lapwing", outline, output, "phonetic-en", "auto", "F-key: TPW + the English number word")
    elif outline.startswith(("PHRO", "PHR*UP", "PHRUP")):
        add("lapwing", outline, output, "phonetic-en", "auto", "Plover command word (plover ..., lookup)")
    elif outline.startswith(("KPA", "KA*P")):
        add("lapwing", outline, output, "phonetic-en", "auto", "cap")
    elif not any(r[0] == "lapwing" and r[1] == outline for r in rows):
        add("lapwing", outline, output, "unclear", "auto", "not reviewed")

# --- Pluvier = the TAO / LaSalle list (resources/tao_la_salle.json of Pluvier; Tao.md "La ponctuation") ---------------------
TAO = [
    ("-RBGS", ",", "position", "reviewed", "Tao.md: 'les lettres -RBGS signifient la virgule'"),
    ("-FPLT", ".", "position", "reviewed", "Tao.md"),
    ("-FPLT/-FPLT", ":", "position", "reviewed", "Tao.md"),
    ("-FPLT/-RBGS", ";", "position", "reviewed", "period + comma"),
    ("-FPLT/-FPLT/-FPLT", "...", "position", "reviewed", "tao_la_salle.json"),
    ("STPH", "?", "position", "reviewed", "Tao.md"),
    ("STPH-FPLT", "!", "position", "reviewed", "Tao.md"),
    ("*P", "new paragraph", "position", "reviewed", "Tao.md: 'le sténogramme *P'"),
    ("STROFL", "'", "phonetic-fr", "reviewed", "apostrophe /apostRof/"),
    ("TROEUP", "...", "phonetic-fr", "reviewed", "trois points"),
    ("P-RZ", "(", "phonetic-fr", "unverified", "skeleton of parenthèse: p R z"),
    ("P-RZ/P-RZ", ")", "phonetic-fr", "unverified", "the same, twice for the closing one"),
    ("BL-K", "/", "phonetic-fr", "unverified", "skeleton of (ligne) oblique: b l k"),
    ("G-LZ", "«", "phonetic-fr", "table", "guillemet /gij.mE/: G + -LZ = /ij/ (Pluvier: 'ij' -> -LZ), first syllable"),
    ("G-LZ/G-LZ", "»", "phonetic-fr", "table", "the same, twice for the closing one"),
    ("T-RS", "-", "phonetic-fr", "table", "tiret /ti.RE/: T + -RS = /RE/ (Pluvier: conditional ending /RE/ -> -RS)"),
    ("TKEULZ", ": «", "phonetic-fr", "table", "dialogue: TK + EU + -LZ = /d/ + /i/ + /j/ ('dia-'), first syllable"),
    ("OE", "-", "unclear", "unverified", "trait d'union"),
    ("PR-PB", "%", "unclear", "unverified", "in tao_la_salle.json only"),
    ("PWHR-BG", "/", "unclear", "unverified", "in tao_la_salle.json only (the TAO table writes BL-K)"),
]
for outline, output, kind, status, note in TAO:
    add("pluvier-tao", outline, output, kind, status, note)

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["source", "outline", "output", "kind", "status", "note"])
    w.writerows(rows)
counts: dict[tuple[str, str], int] = {}
for r in rows:
    counts[(r[0], r[3])] = counts.get((r[0], r[3]), 0) + 1
print(f"wrote {OUT}: {len(rows)} rows")
for k in sorted(counts):
    print(f"  {k[0]:15} {k[1]:12} {counts[k]}")
