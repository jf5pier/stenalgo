"""
Keypress search helpers of the affix rules: the legal keypresses (`enumerateKeypresses`), each phoneme's keys
(`PhonemeKeys`) and the phonetic-similarity label of a keypress (`simScore`, a report label only: it never
gates which keys are tried, see `affixrules.chooseRuleKeypress`).
"""
from itertools import combinations

from src.affixes import PREFIX, SimContext
from src.keyboard import Starboard, Stroke

OTHER_BANK_WEIGHT = 0.5
NUCLEUS_VOWEL_WEIGHT = 0.5
UNEXPLAINED_KEY_PENALTY = 0.25
MAX_KEYPRESS_KEYS = 3
SAMPLE_CARRIERS = 2000      # first-pass simulation sample (top frequency); finalists use all
MAX_ALTERNATIVES = 5
SPLIT_MAX_LOSS = 0.02       # a single keypress is kept unless more than this share of frequency collides
FORBIDDEN_KEYS = frozenset({0, 1, 10, 15})   # reserved keys: never used (Decision 2)


# ═══════════════════════════════════════════════════════════════════════════
# Similarity (B1)
# ═══════════════════════════════════════════════════════════════════════════

class PhonemeKeys:
    """Each phoneme's key sets, per bank, read from the layout."""

    def __init__(self, starboard: Starboard) -> None:
        partOf = {k: part for part, keys in starboard.keyIDinSyllabicPart.items() for k in keys}
        self.encodings: dict[str, list[tuple[str, frozenset[int]]]] = {}
        for keyset, phonemes in starboard.phonemesAssignedToStroke.items():
            bank = partOf[keyset[0]]
            for p in phonemes:
                self.encodings.setdefault(p, []).append((bank, frozenset(keyset)))
        self.vowels = {p for p, enc in self.encodings.items() if any(b == "nucleus" for b, _ in enc)}


def naturalBank(position: str) -> str:
    return "onset" if position == PREFIX else "coda"


def salientPhonemes(memberPhonos: list[tuple[str, float]], pk: PhonemeKeys) -> dict[str, float]:
    """Phoneme -> weight: frequency share of the members containing it, vowels x0.5."""
    total = sum(f for _, f in memberPhonos) or 1.0
    share: dict[str, float] = {}
    for phono, f in memberPhonos:
        for p in set(phono.replace(".", "")):
            share[p] = share.get(p, 0.0) + f / total
    return {p: s * (0.5 if p in pk.vowels else 1.0) for p, s in share.items()}


def simScore(keys: frozenset[int], weights: dict[str, float], pk: PhonemeKeys, position: str) -> float:
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    natural = naturalBank(position)
    got = 0.0
    covered: set[int] = set()
    for p, w in weights.items():
        best, bestKeys = 0.0, None
        for bank, ks in pk.encodings.get(p, ()):
            if ks <= keys:
                if bank == natural:
                    bw = 1.0
                elif bank == "nucleus" and p in pk.vowels:
                    bw = NUCLEUS_VOWEL_WEIGHT
                else:
                    bw = OTHER_BANK_WEIGHT
                if bw > best:
                    best, bestKeys = bw, ks
        if bestKeys is not None:
            got += w * best
            covered |= bestKeys
    return (got - UNEXPLAINED_KEY_PENALTY * len(keys - covered)) / total


def phonemeKeys(starboard: Starboard) -> list[int]:
    return sorted(k for ks in starboard.keyIDinSyllabicPart.values() for k in ks if k not in FORBIDDEN_KEYS)


def enumerateKeypresses(starboard: Starboard, ctx: SimContext) -> list[Stroke]:
    keys = phonemeKeys(starboard)
    out: list[Stroke] = []
    for n in range(1, MAX_KEYPRESS_KEYS + 1):
        for combo in combinations(keys, n):
            if ctx.isLegal(combo):
                out.append(combo)
    return out
