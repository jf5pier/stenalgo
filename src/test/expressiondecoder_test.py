"""Offline expression decoder (src/expressiondecoder.py): inverts composeOutlineTraced on a tiny
hand-built theory. Chords: est=(13,14) il=(13,23) a=(10,12)... host strokes avoid the keypress keys."""

from src.affixes import PREFIX, SUFFIX, SimContext
from src.expressiondecoder import ExpressionDecoder
from src.expressions import (MERGED, STANDALONE, AttachRule, BriefRule, Rules, Token,
                             composeOutlineTraced)
from src.keyboard import Starboard

sb = Starboard.fromJSONFile("starboard3h.json")
assert sb is not None

EST, IL, Y, A = (13, 14), (13, 23), (13,), (12, 10)
CAFE = ((1, 12), (2, 14))             # a two-stroke word
DE, DEL, PAS = (4, 5), (4, 5, 10), (9,)

WORDS = {(EST,): ["est"], (IL,): ["il"], (Y,): ["y"], (A,): ["a"], CAFE: ["cafe"],
         ((4, 5, 11, 12),): ["de"], ((6, 7),): ["l'"], ((20, 21),): ["que"]}


class Ctx(SimContext):
    def __init__(self):
        super().__init__(sb, [])
        self.finalOutlines = {tuple(o) for o in WORDS}
        self.singleStrokeOutlines = {o[0] for o in self.finalOutlines if len(o) == 1}


def rules(*extra: object, order=frozenset()):
    attaches = (AttachRule(("de",), PREFIX, DE, "de"), AttachRule(("d'",), PREFIX, DEL, "de"),
                AttachRule(("pas",), SUFFIX, PAS, "pas"))
    return Rules(briefs=tuple(b for b in extra if isinstance(b, BriefRule)),
                 attaches=attaches, orderBan=order)


def decoder(r: Rules, ctx: Ctx) -> ExpressionDecoder:
    return ExpressionDecoder(r, WORDS, {"de": 2, "d'": 1, "pas": 2, "est": 1}, ctx.isLegal)


def tok(unit, *strokes):
    return Token(unit, tuple(strokes))


def test_plain_word_and_brief_decode_exactly() -> None:
    ctx = Ctx()
    dec = decoder(rules(BriefRule(("il", "est"), ((13, 23, 14),))), ctx)
    assert [tuple(p.units for p in r) for r in dec.decode((EST,))] == [(("est",),)]
    readings = dec.decode(((13, 14, 23),))
    assert [(r[0].units, r[0].brief) for r in readings] == [(("il", "est"), True)]
    assert dec.decode(((30,),)) == []


def test_prefix_merge_round_trips() -> None:
    ctx = Ctx()
    r = rules()
    traced = composeOutlineTraced(r, (tok("de", (4, 5, 11, 12)), tok("est", EST)), ctx)
    assert [s.outcome for s in traced.segments if s.kind == "attach"] == [MERGED]
    readings = decoder(r, ctx).decode(traced.strokes)
    assert any(len(x) == 1 and x[0].units == ("est",) and
               [a.expression for a in x[0].prefix] == [("de",)] for x in readings)


def test_suffix_merge_lands_on_last_stroke() -> None:
    ctx = Ctx()
    r = rules()
    traced = composeOutlineTraced(r, (tok("cafe", *CAFE), tok("pas", (8,), (9,))), ctx)
    assert traced.strokes is not None and len(traced.strokes) == 2
    readings = decoder(r, ctx).decode(traced.strokes)
    assert any(x[0].units == ("cafe",) and [a.expression for a in x[0].suffix] == [("pas",)]
               for x in readings)


def test_prefix_and_suffix_stack_on_one_stroke() -> None:
    ctx = Ctx()
    r = rules()
    traced = composeOutlineTraced(
        r, (tok("de", (4, 5, 11, 12)), tok("est", EST), tok("pas", (8,), (9,))), ctx)
    assert traced.strokes == ((4, 5, 9, 13, 14),)
    readings = decoder(r, ctx).decode(traced.strokes)
    pieces = [x[0] for x in readings if len(x) == 1 and x[0].units == ("est",)]
    assert pieces and [a.expression for a in pieces[0].prefix] == [("de",)]
    assert [a.expression for a in pieces[0].suffix] == [("pas",)]


def test_selector_swallowed_by_host_mark_gives_both_readings() -> None:
    # host il* with the d' keypress (4,5,10): the star is both a selector and the host mark
    ctx = Ctx()
    r = Rules(attaches=(AttachRule(("d'",), PREFIX, DEL, "de"),))
    words = {((13, 23, 10),): ["il*"], ((13, 23),): ["il"]}
    dec = ExpressionDecoder(r, words, {}, ctx.isLegal)
    readings = dec.decode(((4, 5, 10, 13, 23),))
    assert {x[0].units for x in readings} == {("il",), ("il*",)}


def test_standalone_and_cluster() -> None:
    ctx = Ctx()
    r = rules()
    dec = decoder(r, ctx)
    assert [x[0].kind for x in dec.decode((DE,))] == ["standalone"]      # "de" spans 2 strokes
    assert dec.decode((DEL,)) == []                                      # "d'" spans 1: no standalone
    cluster = dec.decode(((4, 5, 9),))
    assert [x[0].kind for x in cluster] == ["cluster"]


def test_multi_stroke_outline_reads_left_to_right() -> None:
    ctx = Ctx()
    dec = decoder(rules(), ctx)
    readings = dec.decode((EST,) + CAFE)
    assert [tuple(p.units for p in x) for x in readings] == [(("est",), ("cafe",))]
