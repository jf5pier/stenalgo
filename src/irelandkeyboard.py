"""
The Ireland steno layout (the one Pluvier targets) priced in the same currency as `Starboard`.

Keys, in left-to-right chord order: `S T K P W H R A O * E U -F -R -P -B -L -G -T -S -D -Z` (the number bar `#` is
ignored: Pluvier's dictionary has no `#`). An Ireland chord is a string such as `STAR` or `TSAR`, parsed by
`util.export_plover_complements.parseIreland` semantics (re-implemented here so that `src/` does not import `util/`).

Model: each Ireland key is placed on the Starboard key of the same finger and geometry, so that the finger tables of
`Starboard._possibleKeypress` (the same `FingerWeights` currency) price it:

    S=2  T=4 K=5  P=6 W=7  H=8 R=9  *=10 (15 when only the right index is busy)  A=11 O=12  E=13 U=14
    -F=16 -R=17  -P=18 -B=19  -L=20 -G=21  -T=22 -S=23 -D=24 -Z=25

Assumptions (documented choices, not an ergonomic study):
- the finger assignment is the standard one (left pinky S; ring T K; middle P W; index H R and *; thumbs A O / E U; right
  index -F -R and *; middle -P -B; ring -L -G; pinky -T -S -D -Z);
- `S` is a tall key: it is priced as TWO possible keys, the top (2) and the bottom (3) left pinky key, the cheaper of the two
  choices being kept, shape terms included (it takes the row that avoids a zig-zag with its neighbours; a gap to P/W stays);
- `*` is a tall key as well: one key of its index finger, outside the shape ranges (as on the Starboard);
- `*` is pressed by the left index, unless the right index is already busy and the left one is not;
- the 3 keys of a pinky or a diagonal pinky pair (-T with -Z, -S with -D) are priced as `pinky4keys`: Starboard marks them
  illegal, the Ireland keyboard physically allows them;
- the shape terms (zig-zag, gap, the 3 and 4 key adjustments) are those of `Starboard.getStrokeShapeCost`, computed over
  the left onset block (T K P W H R, the ids 4..9 above) and the right coda block;
- then the same `0.85 ** nbFingers` multi-finger discount.
"""
from __future__ import annotations

from src.keyboard import FingerWeights, PositionWeights, Starboard

LEFT: str = "STKPWHR"
VOWELS: str = "AO*EU"
RIGHT: str = "FRPBLGTSDZ"
# The Ireland keys in chord order ("-F" is the right-hand F).
KEYS: tuple[str, ...] = tuple(LEFT) + tuple(VOWELS) + tuple("-" + c for c in RIGHT)
# Ireland key -> the Starboard key id it is priced as.
STARBOARD_ID: dict[str, int] = {
    "S": 2, "T": 4, "K": 5, "P": 6, "W": 7, "H": 8, "R": 9, "*": 10, "A": 11, "O": 12, "E": 13, "U": 14,
    "-F": 16, "-R": 17, "-P": 18, "-B": 19, "-L": 20, "-G": 21, "-T": 22, "-S": 23, "-D": 24, "-Z": 25,
}
_RIGHT_INDEX_STAR = 15
_PINKY_RIGHT = (22, 23, 24, 25)
_TALL_KEYS = ("S", "*")
_FW = FingerWeights()
_TABLE: PositionWeights = Starboard._possibleKeypress


def parseChord(stroke: str) -> list[str] | None:
    """The Ireland keys of one stroke in chord order ("-F" for a right-hand F), None for text that is not a stroke."""
    if not stroke:
        return None
    i = 0
    left = ""
    while i < len(stroke) and stroke[i] in LEFT:
        left += stroke[i]
        i += 1
    vowels = ""
    while i < len(stroke) and stroke[i] in VOWELS:
        vowels += stroke[i]
        i += 1
    if i < len(stroke) and stroke[i] == "-":
        i += 1
    right = stroke[i:]
    if left != "".join(c for c in LEFT if c in left) or vowels != "".join(c for c in VOWELS if c in vowels) \
            or right != "".join(c for c in RIGHT if c in right) or len(set(left)) != len(left):
        return None
    return list(left) + list(vowels) + ["-" + c for c in right]


def renderChord(keys: set[str] | list[str]) -> str:
    """The canonical text of a set of Ireland keys (hyphen only when there is no vowel key and a right-hand key)."""
    present = set(keys)
    left = "".join(k for k in LEFT if k in present)
    vowels = "".join(k for k in VOWELS if k in present)
    right = "".join(k[1:] for k in KEYS if k.startswith("-") and k in present)
    return left + (vowels if vowels else ("-" if right else "")) + right


def _shapeCost(ids: tuple[int, ...]) -> int:
    """`Starboard.getStrokeShapeCost` on sorted key ids (parity = row, even = top)."""
    cost = 0
    if len(ids) == 2:
        s1, s2 = ids
        if (s1 % 2 == 0 and s2 % 2 == 1 and s2 - s1 == 3) or (s1 % 2 == 1 and s2 % 2 == 0 and s2 - s1 == 1):
            cost += 100
        if (s1 % 2 == 0 and s2 - s1 >= 4) or (s1 % 2 == 1 and s2 - s1 >= 3):
            cost += 100
    elif len(ids) >= 3:
        cost += _shapeCost(ids[0:2]) + _shapeCost(ids[1:])
        s1, s2, s3 = ids[:3]
        if s1 % 2 == 0 and s3 - s1 == 2:
            cost -= 50
        elif s1 % 2 == 0 and s3 - s1 == 3:
            cost += 50
        elif s1 % 2 == 1 and s3 - s1 == 2:
            cost += 50
        if len(ids) >= 4 and s1 % 2 == 0 and ids[3] - s1 == 3:
            cost -= 100
    return cost


class IrelandKeyboard:
    """Prices Ireland chords in the Starboard currency (see the module docstring for the model)."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, ...], int | None] = {}

    def getChordCost(self, keys: tuple[str, ...] | list[str]) -> int | None:
        """The cost of one chord given as Ireland keys; None for an unknown key. Every combination of keys is
        pressable on this keyboard."""
        memo = tuple(sorted(set(keys), key=lambda k: KEYS.index(k) if k in KEYS else -1))
        if memo in self._cache:
            return self._cache[memo]
        result = self._cost(memo)
        self._cache[memo] = result
        return result

    def getStrokeCost(self, stroke: str) -> int | None:
        """The cost of one chord given as text (`STAR`); None when it is not a chord."""
        keys = parseChord(stroke)
        return None if keys is None else self.getChordCost(keys)

    def getOutlineCost(self, outline: str) -> int | None:
        """The summed cost of a `/`-joined outline; None when a stroke is not a chord."""
        total = 0
        for stroke in outline.split("/"):
            cost = self.getStrokeCost(stroke)
            if cost is None:
                return None
            total += cost
        return total

    @staticmethod
    def _cost(keys: tuple[str, ...]) -> int | None:
        if any(k not in STARBOARD_ID for k in keys):
            return None
        ids = {STARBOARD_ID[k] for k in keys}
        if "S" in keys:                                  # a tall key: the cheaper of its two Starboard keys
            return min(IrelandKeyboard._costOfIds(keys, ids - {2} | {row}) for row in (2, 3))
        return IrelandKeyboard._costOfIds(keys, ids)

    @staticmethod
    def _costOfIds(keys: tuple[str, ...], ids: set[int]) -> int:
        if "*" in keys:
            ids.discard(10)
            rightBusy = any(16 <= i <= 17 for i in ids)
            leftBusy = any(8 <= i <= 9 for i in ids)
            ids.add(_RIGHT_INDEX_STAR if rightBusy and not leftBusy else 10)
        cost = 0
        fingersInUse = 0
        for finger in _TABLE.fingers:
            table = _TABLE[finger]
            combo = tuple(sorted(i for i in ids if (i,) in table))
            if not combo:
                continue
            fingersInUse += 1
            cost += table.get(combo, _FW.pinky4keys)       # only the right pinky can hold an unlisted combination
        onset = tuple(sorted(i for i in ids if 2 <= i <= 9))
        coda = tuple(sorted(i for i in ids if 16 <= i <= 25))
        cost += _shapeCost(onset) + _shapeCost(coda)
        return int(cost * 0.85 ** fingersInUse)


def keyOrder(key: str) -> int:
    """The chord-order position of an Ireland key (0 for S ... 21 for -Z)."""
    return KEYS.index(key)
