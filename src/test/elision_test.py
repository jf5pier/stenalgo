"""Elision pairs (src/elision.py): the host decides between the base and the elided form, which share
one chord; the composer refuses a disagreeing merge and the decoder drops the disagreeing reading."""

from src.affixes import PREFIX, SimContext
from src.elision import BASE, ELIDED, elisionAgrees, orderingExists, startsWithVowelSound
from src.expressiondecoder import ExpressionDecoder
from src.expressions import EXCEPTION, MERGED, AttachRule, Rules, Token, composeOutlineTraced
from src.keyboard import Starboard, Strokes

_loaded = Starboard.fromJSONFile("starboard3h.json")
assert _loaded is not None
sb: Starboard = _loaded


def test_vowel_sound_rules() -> None:
    assert startsWithVowelSound("il") and startsWithVowelSound("homme") and startsWithVowelSound("été")
    assert not startsWithVowelSound("haricot") and not startsWithVowelSound("hautes")
    assert not startsWithVowelSound("onze") and not startsWithVowelSound("tout")
    assert elisionAgrees(ELIDED, "il") and not elisionAgrees(ELIDED, "je")
    assert elisionAgrees(BASE, "je") and not elisionAgrees(BASE, "il")
    assert elisionAgrees("", "anything")


def test_ordering_accepts_some_permutation() -> None:
    # `ce n' est`: ce(base) before n'(elided) before est; the union does not keep the order
    assert orderingExists([(BASE, "ce"), (ELIDED, "n'")], "est")
    assert not orderingExists([(BASE, "que")], "il")
    assert orderingExists([(ELIDED, "qu'")], "il")
    assert orderingExists([(ELIDED, "qu'"), (BASE, "de")], None)


class Ctx(SimContext):
    def __init__(self) -> None:
        super().__init__(sb, [])
        self.finalOutlines = set()
        self.singleStrokeOutlines = set()


QUE = (5, 9, 17)


def rules() -> Rules:
    return Rules(attaches=(AttachRule(("que",), PREFIX, QUE, "que", BASE),
                           AttachRule(("qu'",), PREFIX, QUE, "que", ELIDED)))


def test_composer_merges_only_the_agreeing_form() -> None:
    ctx = Ctx()
    ok = composeOutlineTraced(rules(), (Token("qu'", ((1,), (2,))), Token("il", ((13, 23),))), ctx)
    assert [s.outcome for s in ok.segments if s.kind == "attach"] == [MERGED]
    bad = composeOutlineTraced(rules(), (Token("que", ((1,), (2,))), Token("il", ((13, 23),))), ctx)
    attach = [s for s in bad.segments if s.kind == "attach"][0]
    assert (attach.outcome, attach.reason) == (EXCEPTION, "elision")


def test_decoder_reads_one_form_from_the_host() -> None:
    ctx = Ctx()
    words: dict[Strokes, list[str]] = {((13, 23),): ["il"], ((14, 21),): ["ca"]}
    dec = ExpressionDecoder(rules(), words, {}, None)
    forms = lambda strokes: [[a.expression for a in r[0].prefix] for r in dec.decode(strokes)]  # noqa: E731
    assert forms(((5, 9, 13, 17, 23),)) == [[("qu'",)]]       # vowel host: elided form only
    assert forms(((5, 9, 14, 17, 21),)) == [[("que",)]]       # consonant host: base form only
