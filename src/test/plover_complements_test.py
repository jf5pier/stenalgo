"""Unit tests for the Plover punctuation and command converter (`util/export_plover_complements.py`): the Ireland stroke
parser, the key-to-key conversion through the Gemini PR buttons, the French spacing and the collision filter."""

import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "plover_stenalgo"))

from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS  # type: ignore[import-not-found]  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util.export_plover_complements import (COMMAND_ALIASES, SPACE, completePluvier, build, buildPluvier, convertOutline, frenchTranslation, parseIreland,  # noqa: E402
                                            phoneticAliases, pressable, starboardKeys)

BUTTON_KEY = starboardKeys(KEYS, GEMINI_PR_KEYMAP)


def row(source: str, outline: str, output: str, note: str = "punctuation: x") -> dict[str, str]:
    return {"source": source, "outline": outline, "output": output, "kind": "position", "status": "reviewed", "note": note}


class TestParseIreland(unittest.TestCase):
    def test_strokes(self) -> None:
        self.assertEqual(parseIreland("TP-PL"), ["T", "P", "-P", "-L"])
        self.assertEqual(parseIreland("KPA*"), ["K", "P", "A", "*"])
        self.assertEqual(parseIreland("STPH*FPLT"), ["S", "T", "P", "H", "*", "-F", "-P", "-L", "-T"])
        self.assertEqual(parseIreland("R*R"), ["R", "*", "-R"])

    def test_number_bar_is_a_key_of_its_own(self) -> None:
        self.assertEqual(parseIreland("#TPH-R"), ["#", "T", "P", "H", "-R"])

    def test_rejects_garbage(self) -> None:
        self.assertIsNone(parseIreland(""))
        self.assertIsNone(parseIreland("PT"))                # out of steno order


class TestConversion(unittest.TestCase):
    def test_period_goes_to_the_keys_on_the_same_gemini_buttons(self) -> None:
        # Ireland T-P-P-L = Gemini T- P- -P -L = Stenalgo p- m- -k -t (docs/PLOVER_COMPLEMENTS.md)
        (outline,) = convertOutline("TP-PL", BUTTON_KEY) or []
        self.assertEqual(outline, ((KEYS.index("p-"), KEYS.index("m-"), KEYS.index("-k"), KEYS.index("-t")),))

    def test_an_ireland_star_is_the_star_key_only(self) -> None:
        outlines = convertOutline("KPA*", BUTTON_KEY)
        assert outlines is not None
        self.assertEqual(len(outlines), 1)                    # no `#` twin: `#` is the number key
        self.assertIn(KEYS.index("*"), outlines[0][0])
        self.assertNotIn(KEYS.index("#"), outlines[0][0])

    def test_number_bar_is_the_hash_key_pressed_with_the_stroke(self) -> None:
        (outline,) = convertOutline("#TPH-R", BUTTON_KEY) or []
        self.assertIn(KEYS.index("#"), outline[0])
        self.assertEqual(set(outline[0]) - {KEYS.index("#")}, set(convertOutline("TPH-R", BUTTON_KEY)[0][0]))  # type: ignore[index]

    def test_a_starred_number_bar_stroke_keeps_only_the_star_key(self) -> None:
        outlines = convertOutline("#TA*B", BUTTON_KEY)
        assert outlines is not None
        self.assertEqual(len(outlines), 1)                    # the `#` spelling of the star is the number bar
        self.assertIn(KEYS.index("*"), outlines[0][0])
        self.assertIn(KEYS.index("#"), outlines[0][0])


class TestPressable(unittest.TestCase):
    def setUp(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        self.board = board

    def test_reserved_keys_may_join_a_chord(self) -> None:
        # Ireland H*PB = R- * -k -d: R- and * share the left index finger, a legal pair (8, 10)
        outlines = convertOutline("H*PB", BUTTON_KEY)
        assert outlines is not None
        self.assertTrue(all(pressable(self.board, stroke) for o in outlines for stroke in o))

    def test_a_pinky_diagonal_is_not_pressable(self) -> None:
        self.assertFalse(pressable(self.board, (0, 3)))          # & + s-: diagonal of the left pinky square
        self.assertTrue(pressable(self.board, (0, 1)))
        self.assertFalse(pressable(self.board, (99,)))           # a key no finger owns


class TestFrench(unittest.TestCase):
    def test_spacing_before_double_punctuation_and_in_guillemets(self) -> None:
        self.assertEqual(frenchTranslation("{:}"), "{^" + SPACE + ":}")
        self.assertEqual(frenchTranslation("{?}"), "{^" + SPACE + "?}{-|}")
        self.assertEqual(frenchTranslation('{~|"^}'), "{~|«" + SPACE + "^}")
        self.assertEqual(frenchTranslation('{^~|"}'), "{^~|" + SPACE + "»}")

    def test_comma_and_period_unchanged_and_single_quotes_become_the_inner_quotes(self) -> None:
        self.assertEqual(frenchTranslation("{,}"), "{,}")
        self.assertEqual(frenchTranslation("{.}"), "{.}")
        self.assertEqual(frenchTranslation("{~|'^}"), "{~|\u201c^}")
        self.assertEqual(frenchTranslation("{^~|'}"), "{^~|\u201d}")


class TestBuild(unittest.TestCase):
    def setUp(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        self.board = board

    def test_sources_priority_kinds_and_filters(self) -> None:
        rows = [row("plover-english", "TP-PL", "{.}"), row("lapwing", "TP-PL", "{.} (lapwing)"),
                row("lapwing", "STPH-R", "{#Left}{^}", note="cursor key"), row("lapwing", "#TPH-R", "{#Left}{^}", note="x"), row("lapwing", "#TA*B", "{#Shift(Tab)}", note="x"),
                row("lapwing", "KW-BG", "{,}"), row("lapwing", "A*E", "{~|'^}")]
        result = build(rows, self.board, BUTTON_KEY, {"vt-dR"}, set())
        self.assertEqual(sorted(result["punctuation"].values()), sorted(["{.} (lapwing)", "{~|\u201c^}"]))   # A*E has the `*` spelling only; lapwing wins; KW-BG is a theory word
        self.assertEqual(sorted(result["commands"].values()), ["{#Left}{^}", "{#Shift(Tab)}"])   # #TPH-R is the twin of STPH-R
        reasons = dict(result["dropped"])
        self.assertIn("redundant", reasons["#TPH-R"])
        self.assertIn("KW-BG", reasons)

    def test_first_stroke_of_a_theory_outline_is_dropped(self) -> None:
        result = build([row("lapwing", "TP-PL", "{.}")], self.board, BUTTON_KEY, set(), {"pm-kt"})
        self.assertEqual(result["punctuation"], {})
        self.assertIn("first stroke", result["dropped"][0][1])


class TestPhoneticAliases(unittest.TestCase):
    def setUp(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        self.board = board

    def test_aliases_join_the_punctuation_beside_the_converted_chords(self) -> None:
        rows = [row("lapwing", "H-PB", "{^}-{^}"), row("lapwing", "TP-PL", "{.}"), row("lapwing", "KW-BG", "{,}")]
        result = build(rows, self.board, BUTTON_KEY, set(), set(), phoneticAliases(KEYS))
        glued = {outline for outline, translation in result["punctuation"].items() if translation == "{^}-{^}"}
        self.assertEqual(glued, {"R-kd", "t-d"})                       # Ireland H-PB and the phonetic trait d'union
        self.assertEqual(result["punctuation"]["svmt-k"], "{^}/{^}")
        self.assertEqual(result["punctuation"]["svmt*k"], "{^\\^}")      # never `\{`: it would escape the brace
        # the period and the comma keep their 4-key Plover chords and get no phonetic alias
        self.assertEqual([o for o, v in result["punctuation"].items() if v == "{.}"], ["pm-kt"])
        self.assertEqual([o for o, v in result["punctuation"].items() if v == "{,}"], ["vt-dR"])
        self.assertNotIn("p-t", result["punctuation"])
        self.assertEqual(result["punctuation"]["v-l"], "{^},{^}")      # the glued comma: phonetic only, no Plover chord

    def test_an_alias_on_a_theory_outline_is_dropped(self) -> None:
        result = build([], self.board, BUTTON_KEY, {"t-d"}, set(), phoneticAliases(KEYS))
        self.assertNotIn("t-d", result["punctuation"])
        self.assertIn(("alias t-d", "equals a theory outline"), result["dropped"])


def pluvierRow(outline: str, kind: str = "position") -> dict[str, str]:
    return {"source": "pluvier-tao", "outline": outline, "output": "x", "kind": kind, "status": "reviewed", "note": ""}


class TestCommandAliases(unittest.TestCase):
    def test_backspace_return_and_delete_are_commands_with_a_star_chord_and_no_hash_twin(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        commands = build([], board, BUTTON_KEY, set(), set(), None, phoneticAliases(KEYS, COMMAND_ALIASES))["commands"]
        self.assertEqual(commands["mt-jk"], "{#BackSpace}")
        self.assertEqual(commands["mt*jk"], "{#BackSpace}")
        self.assertEqual(commands["w*s"], "{#Return}{^}")
        self.assertEqual(commands["pv*iel"], "{#Delete}")
        self.assertFalse([chord for chord in commands if "#" in chord])


class TestCompletePluvier(unittest.TestCase):
    def test_the_pluvier_file_carries_the_plover_symbols_and_the_pluvier_meaning_wins(self) -> None:
        built = {"punctuation": {"s-k": "{^ ^}", "spmR-jktn": "{^ :}"}, "commands": {"mt-jk": "{#BackSpace}"}}
        pluvier = {"punctuation": {"spmR-jktn": "{^ !}", "pR-n": "{^%}"}}
        merged, overridden = completePluvier(built, pluvier)
        self.assertEqual(merged, {"s-k": "{^ ^}", "mt-jk": "{#BackSpace}", "spmR-jktn": "{^ !}", "pR-n": "{^%}"})
        self.assertEqual(overridden, [("spmR-jktn", "{^ :}", "{^ !}")])


class TestPluvier(unittest.TestCase):
    def setUp(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        self.board = board

    def test_position_rows_convert_key_to_key_with_french_spacing(self) -> None:
        rows = [pluvierRow("-FPLT"), pluvierRow("-FPLT/-FPLT"), pluvierRow("STPH")]
        result = buildPluvier(rows, self.board, BUTTON_KEY, KEYS, set(), set())["punctuation"]
        self.assertEqual(result["-jktn"], "{.}")                                    # Ireland -FPLT = -j -k -t -n
        self.assertEqual(result["-jktn/-jktn"], "{^" + SPACE + ":}")               # the colon: no space before, no-break space
        self.assertEqual(result["spmR-"], "{^" + SPACE + "?}{-|}")

    def test_phonetic_rows_use_the_phoneme_keys(self) -> None:
        result = buildPluvier([], self.board, BUTTON_KEY, KEYS, set(), set())
        self.assertEqual(result["punctuation"]["svmt-k"], "{^}/{^}")               # BL-K: b = s+v, l = m+t, then k
        self.assertEqual(result["punctuation"]["tRwajk"], "{^...}")                # trois points: tR + wa + p (-j+-k)
        self.assertEqual(result["punctuation"]["pvij"], "{^" + SPACE + ":}{~|\u00ab" + SPACE + "^}")

    def test_the_pluvier_glued_comma_and_period_are_key_to_key(self) -> None:
        result = buildPluvier([], self.board, BUTTON_KEY, KEYS, set(), set())
        self.assertEqual(result["punctuation"]["-jsdRl"], "{^},{^}")             # -FRBGS (Tao.md Lesson 24)
        self.assertEqual(result["punctuation"]["-skdRl"], "{^}.{^}")             # -RPBGS

    def test_a_chord_that_starts_a_theory_outline_is_dropped(self) -> None:
        result = buildPluvier([], self.board, BUTTON_KEY, KEYS, set(), {"ks*ij"})
        self.assertNotIn("ks*ij", result["punctuation"])
        self.assertTrue(any(name == "G-LZ" for name, _reason in result["dropped"]))
        self.assertNotIn("ksi#j", result["punctuation"])                              # no `#` twin: `#` is the number key

    def test_the_settled_pluvier_rows_have_a_chord_and_the_rest_are_covered(self) -> None:
        result = buildPluvier([], self.board, BUTTON_KEY, KEYS, set(), set())
        punctuation = result["punctuation"]
        self.assertEqual(punctuation["stR*esd"], "{^'^}")                              # STROFL: "strophe" + the star
        self.assertEqual(punctuation["ks*ij"], "{~|\u00ab" + SPACE + "^}")
        self.assertEqual(punctuation["ks*ij/ks*ij"], "{^~|" + SPACE + "\u00bb}")
        self.assertEqual(punctuation["pR-nl/pR-nl"], "{^)}")
        self.assertEqual(punctuation["pR-n"], "{^%}")
        self.assertEqual(sorted(name for name, _reason in result["covered"]), ["OE", "PWHR-BG"])
