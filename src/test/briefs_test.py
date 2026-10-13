"""The brief generator (src/briefs.py): matching, stems and expansion, boundary risk, families, pins. Keyboard-light:
the stems and the risk work on bare stroke tuples, the scoring and the generator on the real Starboard layout."""

import json
from pathlib import Path
from typing import Any

import pytest

from src.affixes import SimContext
from src.briefs import (BoundaryRisk, BriefGenerator, BriefInputs, FamilyIndex, Outline, PinnedBrief, expandBrief, expressionSubject,
                        loadPinnedBriefs, pinnedRows, prefixMatch, stemsOf, wordSubject)
from src.keyboard import Starboard
from src.theorycompare import Lexicon

CODA = {16, 17, 18, 19, 20}
STAR, HASH = 10, 15


def legalAll(stroke: tuple[int, ...]) -> bool:
    return True


class TestStems:
    # petit p@a/ti -> (3, 13) / (5, 14); petite (3, 13) / (5, 14, 16); travail (3, 13)/(5, 14, 17)
    petit = ((3, 13), (5, 14))

    def test_stems_start_at_two_strokes(self) -> None:
        stems = stemsOf(self.petit, [self.petit], CODA)
        assert stems == {(2, frozenset({5, 14}))}

    def test_stem_keeps_the_coda_a_form_shares(self) -> None:
        travail = ((3, 13), (5, 14, 17))
        travaille = ((3, 13), (5, STAR, 14, 17, 18))
        stems = stemsOf(travail, [travail, travaille], CODA)
        assert (2, frozenset({5, 14, 17})) in stems

    def test_prefix_match_ignores_marks(self) -> None:
        assert prefixMatch(((3, 13, STAR), (5, 14, 16)), self.petit, 2, CODA)
        assert not prefixMatch(((3, 13), (6, 14)), self.petit, 2, CODA)


class TestExpansion:
    petit = ((3, 13), (5, 14))
    forms: dict[str, list[Outline]] = {"petit": [petit], "petite": [((3, 13), (5, 14, 16))],
                                       "petits": [((3, 13), (5, 14), (18,))]}

    def test_marks_and_extra_coda_carry_over(self) -> None:
        out = expandBrief(self.forms, self.petit, 2, frozenset({5, 14}), (7, 21), CODA, legalAll)
        assert out["petit"] == [((7, 21),)]
        assert out["petite"] == [((7, 16, 21),)]              # coda-only extra key
        assert out["petits"] == [((7, 21), (18,))]           # the tail strokes follow

    def test_marks_of_the_stem_strokes_are_all_kept(self) -> None:
        marked: dict[str, list[Outline]] = {"petit": [((3, 13, STAR), (5, 14, HASH))]}
        out = expandBrief(marked, self.petit, 2, frozenset({5, 14}), (7, 21), CODA, legalAll)
        assert out["petit"] == [((STAR, HASH, 7, 21),)] or out["petit"] == [(tuple(sorted({STAR, HASH, 7, 21})),)]

    def test_illegal_and_taken_outlines_are_dropped(self) -> None:
        out = expandBrief(self.forms, self.petit, 2, frozenset({5, 14}), (7, 21), CODA, lambda s: 16 not in s)
        assert "petite" not in out
        out = expandBrief(self.forms, self.petit, 2, frozenset({5, 14}), (7, 21), CODA, legalAll,
                          lambda form, outline: form != "petit")
        assert "petit" not in out and "petits" in out


class TestBoundaryRisk:
    def test_tail_direction_counts_the_last_stroke(self) -> None:
        a, b = (1,), (2,)
        risk = BoundaryRisk({(a,), (a, b)})
        assert risk.of(b) == 1        # a/b with a live: the word a before b swallows it
        assert risk.of(a) == 0

    def test_head_direction_counts_the_first_stroke(self) -> None:
        a, b = (1,), (2,)
        risk = BoundaryRisk({(a, b), (b,)})
        assert risk.of(a) == 1        # a/b with b live: a would swallow the next word b

    def test_add_updates_the_counts(self) -> None:
        a, b = (1,), (2,)
        risk = BoundaryRisk({(a,)})
        assert risk.of(b) == 0
        risk.add((a, b))
        assert risk.of(b) == 1


def lexicon() -> Lexicon:
    return Lexicon(
        freq={"petit": 5.0, "petite": 3.0, "petits": 2.0, "travail": 4.0, "travailler": 2.0, "travaille": 1.0, "accord": 1.0,
              "accorder": 1.0, "chat": 1.0},
        syll={"petit": "p@-ti", "petite": "p@-tit", "chat": "Sa", "travail": "tRa-vaj"},
        lemmaForms={("petit", "ADJ"): {"petit", "petite", "petits"}, ("travail", "NOM"): {"travail"},
                    ("travailler", "VER"): {"travailler", "travaille"}, ("accord", "NOM"): {"accord"},
                    ("accorder", "VER"): {"accorder"}, ("chat", "NOM"): {"chat"}})


class TestFamilies:
    def test_related_pairs_a_noun_with_its_verb(self) -> None:
        index = FamilyIndex(lexicon())
        assert index.familyForms("travail") == {"travail", "travailler", "travaille"}
        assert index.familyForms("accord") == {"accord", "accorder"}
        assert index.familyForms("petit") == {"petit", "petite", "petits"}

    def test_short_lemmas_are_not_related(self) -> None:
        assert FamilyIndex(lexicon()).familyForms("chat") == {"chat"}


@pytest.fixture(scope="module")
def board() -> Starboard:
    loaded = Starboard.fromJSONFile("starboard3h.json")
    assert loaded is not None
    return loaded


def generator(board: Starboard, outlinesOf: dict[str, list[Any]], owner: dict[str, set[str]] | None = None,
              reserved: dict[str, str] | None = None, live: list[Any] | None = None) -> BriefGenerator:
    ctx = SimContext(board, [])
    ctx.finalOutlines = {o for outs in outlinesOf.values() for o in outs}
    ctx.singleStrokeOutlines = {o[0] for o in ctx.finalOutlines if len(o) == 1}
    render = lambda outline: "/".join(",".join(map(str, s)) for s in outline)  # noqa: E731
    return BriefGenerator(BriefInputs(board, ctx, render, lexicon(), outlinesOf, owner or {}, reserved or {}, set(),
                                      live or []))


class TestScoring:
    def test_phoneme_match_is_disjoint(self, board: Starboard) -> None:
        gen = generator(board, {"chat": [((14, 18),)]})
        for strokeKeys, phonemes in board.phonemesAssignedToStroke.items():
            if len(phonemes) > 1:        # one key stroke standing for two phonemes: it reads as only one
                held, explained, _inv, reading = gen.phonemeMatch(tuple(sorted(strokeKeys)), "".join(phonemes))
                assert held == 1 and explained == len(strokeKeys) and len(reading) == 1
                break

    def test_order_inversions_are_counted(self, board: Starboard) -> None:
        gen = generator(board, {"chat": [((14, 18),)]})
        keys = {ph: min(sorted(k)) for k, phs in board.phonemesAssignedToStroke.items() if len(k) == 1 for ph in phs}
        pair = [(a, b) for a in keys for b in keys if a != b and keys[a] < keys[b]][:1]
        assert pair
        a, b = pair[0]
        chord = tuple(sorted({keys[a], keys[b]}))
        straight = gen.phonemeMatch(chord, a + b)
        reversed_ = gen.phonemeMatch(chord, b + a)
        assert straight[2] == 0 and reversed_[2] == -1

    def test_score_prefers_held_phonemes(self, board: Starboard) -> None:
        gen = generator(board, {"chat": [((14, 18),)]})
        single = {ph: tuple(sorted(k)) for k, phs in board.phonemesAssignedToStroke.items() if len(k) == 1 for ph in phs}
        ph, chord = next(iter(single.items()))
        assert gen.chordScore(chord, ph)[1] == 1
        assert gen.chordScore(chord, "")[1] == 0


class TestGenerator:
    def outlines(self, board: Starboard) -> dict[str, list[Any]]:
        # three words sharing a first stroke: petit and its feminine, built from real onset/nucleus/coda keys
        onset = sorted(board.keyIDinSyllabicPart["onset"])[:2]
        nucleus = sorted(board.keyIDinSyllabicPart["nucleus"])[:2]
        coda = sorted(board.keyIDinSyllabicPart["coda"])[:2]
        first, second = (onset[0], nucleus[0]), (onset[1], nucleus[1])
        return {"petit": [(first, second)], "petite": [(first, tuple(sorted(second + (coda[0],))))],
                "petits": [(first, second, (coda[1],))], "chat": [((onset[0], nucleus[1]),)]}

    def test_family_brief_covers_the_forms(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        gen = generator(board, outlines)
        subject = wordSubject("petit", "family", outlines, lexicon())
        derived = gen.derive(subject)
        assert derived is not None
        assert set(derived.news) >= {"petit", "petite", "petits"}
        assert all(len(o) <= 2 for outs in derived.news.values() for o in outs)
        assert gen.coveredBy["petite"] == "petit"
        assert gen.derive(wordSubject("petite", "family", outlines, lexicon())) is None      # covered

    def test_scope_word_leaves_the_family_alone(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        derived = generator(board, outlines).derive(wordSubject("petit", "word", outlines, lexicon()))
        assert derived is not None and set(derived.news) == {"petit"}

    def test_a_live_owner_blocks_the_outline(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        free = generator(board, outlines).derive(wordSubject("petit", "word", outlines, lexicon()))
        assert free is not None
        text = lambda o: "/".join(",".join(map(str, s)) for s in o)  # noqa: E731
        gen = generator(board, outlines, owner={text((free.chord,)): {"autre"}})
        again = gen.derive(wordSubject("petit", "word", outlines, lexicon()))
        assert again is not None and again.chord != free.chord

    def test_expression_subject(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        gen = generator(board, outlines)
        subject = expressionSubject(("petit", "chat"), [outlines["petit"][0], outlines["chat"][0]], lexicon(), 100.0)
        assert len(subject.target) == 3 and subject.kind == "expression"
        derived = gen.derive(subject)
        assert derived is not None and derived.news == {"petit chat": [(derived.chord,)]}
        assert derived.stem() == ()
        assert derived.gain == 100.0 * 2

    def test_pin_validation_keeps_a_valid_pin_and_excludes_an_invalid_one(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        derived = generator(board, outlines).derive(wordSubject("petit", "family", outlines, lexicon()))
        assert derived is not None
        pin = derived.pin()
        subject = wordSubject("petit", "family", outlines, lexicon())
        ok, why = generator(board, outlines).check(pin, subject)
        assert ok is not None and why == "" and ok.chord == pin.chord and set(ok.news) == set(derived.news)
        text = lambda o: "/".join(",".join(map(str, s)) for s in o)  # noqa: E731
        bad, why = generator(board, outlines, reserved={text((pin.chord,)): "punctuation"}).check(pin, subject)
        assert bad is None and "taken" in why

    def test_a_risky_pin_is_invalid(self, board: Starboard) -> None:
        outlines = self.outlines(board)
        derived = generator(board, outlines).derive(wordSubject("petit", "word", outlines, lexicon()))
        assert derived is not None
        chord = derived.chord
        other = outlines["chat"][0][0]
        gen = generator(board, outlines, live=[(chord, other), (other,)])      # chord/other with other live: chord swallows it
        ok, why = gen.check(derived.pin(), wordSubject("petit", "word", outlines, lexicon()))
        assert ok is None and why.startswith("boundary risk")


def test_pinned_file_round_trip(tmp_path: Path) -> None:
    render = lambda outline: "/".join(",".join(map(str, s)) for s in outline)  # noqa: E731
    parse = lambda text: tuple(tuple(int(k) for k in part.split(",")) for part in text.split("/"))  # noqa: E731
    pins = [PinnedBrief("petit", "word", "family", ((3, 13), (5, 14)), (7, 21), "pt", 2, 0, 180),
            PinnedBrief("dans la", "expression", "word", (), (4, 9), "dl", 2, 0, 200)]
    path = tmp_path / "briefs.json"
    path.write_text(json.dumps(pinnedRows(pins, render)), encoding="utf-8")
    assert loadPinnedBriefs(str(path), parse) == pins
    assert loadPinnedBriefs(str(tmp_path / "absent.json"), parse) == []
    assert pins[1].units == ("dans", "la")


def test_pins_on_disk_use_rtfcre_and_never_change_by_reading(tmp_path: Path, board: Starboard) -> None:
    from util._briefpins import loadPins, writePins
    pins = [PinnedBrief("avec", "word", "family", ((3, 13), (5, 14)), (4, STAR, 20), "vk", 2, 0, 180)]
    path = str(tmp_path / "briefs.json")
    writePins(board, pins, path)
    before = Path(path).read_text(encoding="utf-8")
    assert loadPins(board, path) == pins
    assert Path(path).read_text(encoding="utf-8") == before
    assert loadPins(board, str(tmp_path / "absent.json")) == []
