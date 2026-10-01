"""Tests for src/affixbinding.py."""
from src.affixbinding import PhonemeKeys, enumerateKeypresses, simScore
from src.affixes import PREFIX, SUFFIX, SimContext
from src.keyboard import Starboard


def _sb():
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


class TestSim:
    def test_prefers_natural_bank(self):
        sb = _sb()
        pk = PhonemeKeys(sb)
        w = {"k": 1.0}
        onset = simScore(frozenset({2}), w, pk, PREFIX)   # k onset = key 2
        coda = simScore(frozenset({18}), w, pk, PREFIX)   # k coda = key 18
        assert onset > coda > 0
        assert simScore(frozenset({18}), w, pk, SUFFIX) > simScore(frozenset({2}), w, pk, SUFFIX)


class TestKeypresses:
    def test_every_enumerated_keypress_is_legal_and_avoids_reserved_keys(self):
        sb = _sb()
        ctx = SimContext(sb, [])
        presses = enumerateKeypresses(sb, ctx)
        assert presses and all(ctx.isLegal(k) and 1 <= len(k) <= 3 for k in presses)
        assert not any({0, 1, 10, 15} & set(k) for k in presses)
