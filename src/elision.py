"""
French elision as a decoder-side rule (user decision 2026-10-04, experiment `ELISION_PAIRS=1`
in scratch/select_expression_rules.py).

An elision pair (`que`/`qu'`, `de`/`d'`, `ne`/`n'`, `ce`/`c'`, `le`/`l'`, `je`/`j'`...) is
written by ONE attach keypress: the written form is fixed by the host that follows. Before a
vowel sound the elided form is obligatory, before a consonant sound the base form is, so the
stroke needs no `*`/`#` selector to tell them apart and the decoder, which knows the host,
reads exactly one of the two. `AttachRule.elision` marks the base ("base") and the elided
("elided") form; both carry the SAME keypress. The composer refuses a merge whose host
disagrees with the form (an exception, longform kept) and the decoder drops the disagreeing
reading. `le`/`la`/`l'`: `l'` shares `le`'s chord (and is also what `la` writes before a
vowel), see `ELISION_PAIRS`.

Elision depends on the SOUND of the host's first letter, not its spelling alone: a mute `h`
elides (l'homme), an aspirated `h` does not (le haricot); a few vowel-initial words refuse it
(le onze, le oui, le yaourt). `ASPIRATED_H` and `NO_ELISION` are short explicit lists, enough
for the experiment, to be completed from a lexicon flag if the experiment is adopted.
"""

from __future__ import annotations

# elided surface -> base surface (the chord's name)
ELISION_PAIRS: dict[str, str] = {
    "qu'": "que", "d'": "de", "n'": "ne", "c'": "ce", "s'": "se", "l'": "le",
    "j'": "je", "m'": "me", "t'": "te",
}
ELISION_BASES = frozenset(ELISION_PAIRS.values())

BASE = "base"
ELIDED = "elided"

_VOWELS = frozenset("aàâäæeéèêëiîïoôöœuùûüyÿ")

# words whose initial h is aspirated (no elision, no liaison); matched on the word, its plural
# and its feminine (s, e, es stripped)
ASPIRATED_H = frozenset("""
ha hache hachis haddock haie haillon haine hair haïr halage hale hâle haleter hall halo halte
hamac hameau hamburger hamster hanche handicap hangar hanter happer haras harasser harceler
hardi harem hareng hargne haricot harnais harpe harpon hasard hâte hausse haut hautain hautbois
havre havresac hein hennir hérisser hérisson héron héros hernie hêtre heurter hibou hic hideux
hiérarchie hippie hisser hobby hocher hockey hold-up hollande hollandais homard hongre honte hop
hoquet horde hors hotte houblon houle houppe hourra housse houx hublot huche huer huit hululer
humer hurler huron husky hutte hyène hé
""".split())

# vowel-initial words that refuse elision
NO_ELISION = frozenset("""
onze oui ouistiti yaourt yogourt yoga yacht yen yéti yeti yiddish uhlan ukase yucca
""".split())


def _stems(unit: str) -> tuple[str, ...]:
    return (unit, unit[:-1], unit[:-2])


def startsWithVowelSound(unit: str) -> bool:
    """True when `unit` (a word-unit surface) begins with a vowel sound, i.e. a preceding
    particle elides. Case and a leading elision apostrophe are ignored."""
    word = unit.lower().lstrip("'")
    if not word:
        return False
    if any(s in NO_ELISION for s in _stems(word)):
        return False
    if word[0] == "h":
        return not any(s in ASPIRATED_H for s in _stems(word))
    return word[0] in _VOWELS


def elisionAgrees(form: str, hostUnit: str) -> bool:
    """Does the written form (BASE / ELIDED) fit the host that follows? An empty form
    (a rule outside any pair) always agrees."""
    if form == ELIDED:
        return startsWithVowelSound(hostUnit)
    if form == BASE:
        return not startsWithVowelSound(hostUnit)
    return True


def orderingExists(rules: "list[tuple[str, str]]", hostUnit: str | None) -> bool:
    """Can a set of attach particles, written in SOME order before `hostUnit`, all be French?
    `rules`: (elision form, first unit of the particle's expression). The order of attaches
    merged into one stroke is lost (the union is commutative), so the decoder accepts a stack
    when one permutation makes every elision-pair form agree with the word written after it
    (`ce n' est`: `ce` before `n'` and `n'` before `est`). `hostUnit` None: nothing follows."""
    from itertools import permutations
    for order in permutations(rules):
        ok = True
        for i, (form, _unit) in enumerate(order):
            nxt = order[i + 1][1] if i + 1 < len(order) else hostUnit
            if form and nxt is not None and not elisionAgrees(form, nxt):
                ok = False
                break
        if ok:
            return True
    return False
