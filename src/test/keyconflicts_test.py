"""Pinky-diagonal key conflicts (src/keyconflicts.py): derived from the layout, and equal to
`SimContext.isLegal` for every pair of key sets on every finger."""

from itertools import combinations

from src.affixes import SimContext
from src.keyboard import Starboard
from src.keyconflicts import KeyConflicts

_loaded = Starboard.fromJSONFile("starboard3h.json")
assert _loaded is not None
sb: Starboard = _loaded
conflicts = KeyConflicts.fromStarboard(sb)


def test_partners_are_the_pinky_diagonals() -> None:
    assert conflicts.partners == {22: {25}, 25: {22}, 23: {24}, 24: {23},
                                  0: {3}, 3: {0}, 1: {2}, 2: {1}}
    assert conflicts.conflict((24,), (23,)) and conflicts.conflict((22,), (22,))
    assert not conflicts.conflict((24,), (22,)) and not conflicts.conflict((24,), (25,))
    assert not conflicts.conflict((7, 16, 19), (8, 17, 22))
    assert conflicts.conflict((7, 16, 24), (8, 20, 23))       # the il / n' pair of the 2026-10-04 default run
    assert conflicts.expandMask(1 << 24) == (1 << 24) | (1 << 23)


def test_footprint_disjointness_equals_legality() -> None:
    """For every pair of legal keypresses of one finger: the union is a legal keypress exactly when the
    sets do not conflict (all-four press excepted: legal, but counted as a conflict)."""
    table = sb._possibleKeypress
    for finger in table.fingers:
        legal = {c for c in table[finger] if c}
        keys = sorted(c[0] for c in table[finger] if len(c) == 1)
        for ra in range(1, len(keys) + 1):
            for a in combinations(keys, ra):
                for rb in range(1, len(keys) + 1):
                    for b in combinations(keys, rb):
                        if a not in legal or b not in legal:
                            continue                    # each set is itself a legal keypress
                        if set(a) & set(b):
                            assert conflicts.conflict(a, b)
                            continue
                        union = tuple(sorted(set(a) | set(b)))
                        if union in legal and len(union) == 4:
                            continue
                        assert (union in legal) == (not conflicts.conflict(a, b)), (finger, a, b)


def test_context_union_legality_agrees_on_syllabic_keys() -> None:
    ctx = SimContext(sb, [])
    assert not ctx.isLegal((16, 20, 23, 24)) and conflicts.conflict((16, 24), (20, 23))
    assert ctx.isLegal((16, 17, 20)) and not conflicts.conflict((16,), (17, 20))
