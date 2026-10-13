"""Unit tests for the Pluvier rule matching of `util/find_pluvier_shorter_words.py` (no Pluvier clone needed)."""

from util.find_pluvier_shorter_words import AffixRule, matchRule, ruleChords, syllables

RULES = sorted([AffixRule("ci", "-RB", False, "steno.py"), AffixRule("comm", "KPH", True, "steno.py"),
                AffixRule("er", "-R", False, "verb ending", verbOnly=True),
                AffixRule("m@", "-PLT", False, "steno.py SUFFIXES", sound=True)],
               key=lambda r: (r.sound, -len(r.spelling)))


def test_rule_chords() -> None:
    assert ruleChords("-/BGS") == ["-BGS"]
    assert ruleChords("KOEPB/|KOPB") == ["KOEPB", "KOPB"]
    assert ruleChords("-/") == []


def test_suffix_as_own_stroke_or_fused() -> None:
    assert matchRule("merci", "mERsi", "PH-R/-RB", RULES, False) == RULES[[r.spelling for r in RULES].index("ci")]
    rule = matchRule("ici", "isi", "EURB", RULES, False)
    assert rule is not None and rule.spelling == "ci"
    assert matchRule("ici", "isi", "EUS", RULES, False) is None          # the spelling alone is not enough


def test_prefix_sound_and_verb_only() -> None:
    rule = matchRule("comment", "kOm@", "KPHA", RULES, False)
    assert rule is not None and rule.label() == "comm- = KPH (steno.py)"
    sound = matchRule("maman", "mam@", "PHAPLT", RULES, False)
    assert sound is not None and sound.label() == "-/m@/ = -PLT (steno.py SUFFIXES)"
    assert matchRule("super", "sypER", "SP-R", RULES, False) is None     # -er = -R is for verb forms only
    verb = matchRule("aller", "ale", "HR-R", RULES, True)
    assert verb is not None and verb.source == "verb ending"


def test_syllables() -> None:
    assert syllables("a-le") == 2
    assert syllables("") == 0
