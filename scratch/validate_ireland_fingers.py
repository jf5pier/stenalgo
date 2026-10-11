"""Validate src/irelandkeyboard.py's key placement against keyboard.py (Starboard fingers/rows) and the Gemini conversion."""
import sys, os
sys.path.insert(0, "plover_stenalgo")
from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS
from util.export_plover_complements import GEMINI, starboardKeys
from src.keyboard import Starboard
from src.irelandkeyboard import STARBOARD_ID

fa = Starboard._fingerAssignments
buttonKey = starboardKeys(KEYS, GEMINI_PR_KEYMAP)
# real steno machine: finger and row (T=top, B=bottom, W=tall/both) of each Ireland key
REAL = {"S": ("lp", "W"), "T": ("lr", "T"), "K": ("lr", "B"), "P": ("lm", "T"), "W": ("lm", "B"), "H": ("li", "T"), "R": ("li", "B"),
        "*": ("li|ri", "W"), "A": ("lt", ""), "O": ("lt", ""), "E": ("rt", ""), "U": ("rt", ""),
        "-F": ("ri", "T"), "-R": ("ri", "B"), "-P": ("rm", "T"), "-B": ("rm", "B"), "-L": ("rr", "T"), "-G": ("rr", "B"),
        "-T": ("rp", "T"), "-S": ("rp", "B"), "-D": ("rp", "T"), "-Z": ("rp", "B")}
print(f"{'key':4} {'model id':>8} {'finger':>6} {'row':>3} | {'gemini id':>9} {'finger':>6} {'row':>3} | real finger/row | ok")
for k, (rf, rrow) in REAL.items():
    mid = STARBOARD_ID[k]
    g = GEMINI.get(k.replace("-", "") if k.startswith("-") else k)
    gk = None
    gid = None
    # GEMINI maps Ireland key names (right side with '-' prefix?) to Gemini buttons
    gname = GEMINI.get(k) or GEMINI.get(k.lstrip("-")) or GEMINI.get("-" + k.lstrip("-"))
    gid = buttonKey.get(gname) if gname else None
    row = lambda i: "-" if i is None else ("T" if i % 2 == 0 else "B") if i not in (10, 15) else "W"
    mf = fa[mid]; gf = fa[gid] if gid is not None else "-"
    ok = (mf in rf.split("|")) and (rrow in ("", "W") or row(mid) == rrow or mid in (2, 3))
    print(f"{k:4} {mid:8} {mf:>6} {row(mid):>3} | {str(gid):>9} {gf:>6} {row(gid):>3} | {rf:>5} {rrow:>2}  | {'ok' if ok else 'DIFF'}  gemini={gname}")
