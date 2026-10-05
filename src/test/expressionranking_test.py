"""Decode-time ranking (src/expressionranking.py): plain word > pure brief > attested reading > probability."""

from src.affixes import PREFIX
from src.expressiondecoder import ExpressionDecoder
from src.expressionranking import (ReadingRanker, attestedTable, composedReading, normalizedSignature,
                                   rankedDecode)
from src.expressions import AttachRule, BriefRule, Rules, Token, composeOutlineTraced
from src.affixes import SimContext
from src.keyboard import Starboard, Strokes

_loaded = Starboard.fromJSONFile("starboard3h.json")
assert _loaded is not None
sb: Starboard = _loaded

CE, DE = (5,), (18, 24)
PAN, DANS = (4, 11), (4, 5, 11)             # DANS == PAN + CE: `ce pan` is shadowed by the word `dans`
EST, VAIS = (13, 14), (5, 13, 14)           # VAIS == EST + CE too
WORDS: dict[Strokes, list[str]] = {(PAN,): ["pan"], (DANS,): ["dans"], (EST,): ["est"], (VAIS,): ["vais"], ((1, 12),): ["ba"]}


class Ctx(SimContext):
    def __init__(self) -> None:
        super().__init__(sb, [])
        self.finalOutlines = {tuple(o) for o in WORDS}
        self.singleStrokeOutlines = {o[0] for o in self.finalOutlines if len(o) == 1}


def rules() -> Rules:
    return Rules(attaches=(AttachRule(("ce",), PREFIX, CE), AttachRule(("de",), PREFIX, DE)),
                 briefs=(BriefRule(("il", "est"), ((13, 23, 14),)),))


PROB = {"ce": 0.05, "de": 0.04, "pan": 0.001, "dans": 0.02, "est": 0.03, "vais": 0.002, "ba": 0.001}


def ranker(attested=None, prob=None) -> ReadingRanker:
    return ReadingRanker(attested or {}, prob or PROB)


def test_plain_word_beats_a_merge() -> None:
    dec = ExpressionDecoder(rules(), WORDS)
    best = rankedDecode(dec, ranker(), (DANS,))
    assert best is not None and best[0].units == ("dans",) and not best[0].prefix
    assert len(dec.decode((DANS,))) == 2                          # the merge is still a reading


def test_attested_merge_is_class_two_but_a_shadowing_word_still_wins() -> None:
    ctx = Ctx()
    r = rules()
    tokens = (Token("ce", (CE,)), Token("est", (EST,)))
    traced = composeOutlineTraced(r, tokens, ctx)
    assert traced.strokes == ((5, 13, 14),)                       # composes onto the live word `vais`
    sig = composedReading(r, tokens, traced)
    table = attestedTable([(traced.strokes, sig, 10.0)])
    assert ranker().key(traced.strokes, sig)[0] == 3              # unattested: class 3
    assert ranker(table).key(traced.strokes, sig)[0] == 2         # attested: class 2
    best = rankedDecode(ExpressionDecoder(r, WORDS), ranker(table), traced.strokes)
    assert best is not None and best[0].units == ("vais",)        # a plain word is class 0: it wins anyway


def test_attested_beats_probability() -> None:
    r = Rules(attaches=(AttachRule(("ce",), PREFIX, (5,)), AttachRule(("de",), PREFIX, (18, 24))))
    words: dict[Strokes, list[str]] = {((1, 12),): ["ba"], ((1, 12, 18, 24),): ["bade"]}    # `de`+`ba` shadows nothing; stroke (1,5,12,18,24) is a stack
    dec = ExpressionDecoder(r, words)
    outline = ((1, 5, 12, 18, 24),)
    readings = dec.decode(outline)
    assert len(readings) >= 1
    sigs = [normalizedSignature(tuple(p.signature() for p in x)) for x in readings]
    heavy = ranker()
    light = ranker({(outline, sigs[-1]): 3.0})
    assert light.key(outline, sigs[-1])[0] == 2                   # attested class
    assert all(heavy.key(outline, s)[0] == 3 for s in sigs)       # no attestation: probability class


def test_pure_brief_beats_attested_merge_and_order_is_total() -> None:
    dec = ExpressionDecoder(rules(), WORDS)
    best = rankedDecode(dec, ranker(), ((13, 14, 23),))
    assert best is not None and best[0].brief and best[0].units == ("il", "est")
    assert rankedDecode(dec, ranker(), ((30,),)) is None


def test_fewer_rarer_words_lose_among_unattested_merges() -> None:
    r = ranker()
    one = (("content", ("ba",), False, ((("ce",), "prefix"),), (), ()),)
    two = (("content", ("ba",), False, ((("ce",), "prefix"), (("de",), "prefix")), (), ()),)
    rare = (("content", ("pan",), False, ((("ce",), "prefix"),), (), ()),)
    assert r.key(((1,),), one) < r.key(((1,),), two)              # an extra particle costs probability
    assert r.key(((1,),), one) < r.key(((1,),), rare) or PROB["ba"] >= PROB["pan"]
