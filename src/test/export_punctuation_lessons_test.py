"""Unit tests for the punctuation and command lessons exporter (`util/export_punctuation_lessons.py`): the chord parser, the
French typing simulation, the command classifier and the built document (both styles, paired marks, coverage)."""

import json
import os
import sys
import unittest
from typing import Any

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "plover_stenalgo"))

from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util.export_punctuation_lessons import (EXAMPLES, LESSON_DATA, PLOVER_FILES, PLUVIER_FILE, PRACTICE_WORDS, build,  # noqa: E402
                                             chordOrder, commandInfo, glyphOf, loadChords, loadWords, parseStroke, typeText)

NBSP = " "


class TestParseStroke(unittest.TestCase):
    def test_strokes_parse_back_to_their_keys(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        from util._stenorender import renderFinalStrokesToRTFCRE
        for text in ["pm-kt", "-jktn", "ks*ij", "ksi#j", "stR*esd", "t*ie#R", "pR-nl", "svmt-k", "*k", "-#k", "mtw-dRn", "vm*@", "@#n",
                     "spmR-R", "R-j", "w*s", "pv*iel", "vw-sR"]:
            keys = parseStroke(text, KEYS)
            self.assertEqual(renderFinalStrokesToRTFCRE(board, (keys,)), text, text)


class TestTypeText(unittest.TestCase):
    def test_marks_attach_and_capitalize(self) -> None:
        self.assertEqual(typeText(["oh", "{^" + NBSP + "!}{-|}"]), "Oh" + NBSP + "!")
        self.assertEqual(typeText(["il", "dit", "{~|«" + NBSP + "^}", "merci", "{^~|" + NBSP + "»}"]), "Il dit «" + NBSP + "merci" + NBSP + "»")
        self.assertEqual(typeText(["super", "{^}-{^}", "avion"]), "Super-avion")
        self.assertEqual(typeText(["cent", "{^%}"]), "Cent%")
        self.assertEqual(typeText(["je", "suis", "{.}", "oui"]), "Je suis. Oui")

    def test_backspace_erases_and_return_starts_a_line(self) -> None:
        self.assertEqual(typeText(["chat", "{#BackSpace}"]), "Cha")
        self.assertEqual(typeText(["bonjour", "{#Return}{^}", "monde"]), "Bonjour\nmonde")

    def test_glyph_is_the_visible_mark(self) -> None:
        self.assertEqual(glyphOf("{^" + NBSP + "?}{-|}"), "?")
        self.assertEqual(glyphOf("{~|“^}"), "“")


class TestCommandInfo(unittest.TestCase):
    def test_families_and_names(self) -> None:
        self.assertEqual(commandInfo("{#BackSpace}")[:3], ("edition", "Retour arrière", "backspace"))
        self.assertEqual(commandInfo("{#Left}{^}{#Left}{^}")[:2], ("fleches", "Flèche gauche ×2"))
        self.assertEqual(commandInfo("{#Control_L(Left)}{^}")[0], "mots")
        self.assertEqual(commandInfo("{#Control_L(Shift(Right))}{^}")[:2], ("selection", "Ctrl+Maj+Flèche droite"))
        self.assertEqual(commandInfo("{#Alt_L(Left)}")[0], "debut_fin")
        self.assertEqual(commandInfo("{#Page_Down}{^}")[0], "debut_fin")

    def test_primary_chord_is_the_own_unmarked_shortest(self) -> None:
        own = {"-jktn", "pm-kt"}
        self.assertLess(chordOrder("-jktn", own), chordOrder("pm-kt", own))
        self.assertLess(chordOrder("pm-kt", own), chordOrder("spmR*jktn", own))
        self.assertLess(chordOrder("ks-ij", {"ks-ij", "ks*ij"}), chordOrder("ks*ij", {"ks-ij", "ks*ij"}))


class TestBuiltDocument(unittest.TestCase):
    document: dict[str, Any]
    examples: list[dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        needed = [LESSON_DATA, EXAMPLES, PRACTICE_WORDS, PLUVIER_FILE, *PLOVER_FILES]
        if not all(os.path.exists(os.path.join(ROOT, p)) for p in needed):
            raise unittest.SkipTest("generated inputs not built")
        os.chdir(ROOT)
        board = Starboard.fromJSONFile("starboard3h.json")
        assert board is not None
        with open(LESSON_DATA, encoding="utf-8") as fh:
            data = json.load(fh)
        with open(EXAMPLES, encoding="utf-8") as fh:
            cls.examples = [json.loads(line) for line in fh if line.strip()]
        cls.document = build(loadChords(PLOVER_FILES), loadChords((PLUVIER_FILE,)), data, cls.examples, loadWords(), board, KEYS)

    def test_both_styles_have_the_same_lessons(self) -> None:
        lessons = self.document["lessons"]
        self.assertEqual([l["id"] for l in lessons["plover"]], [l["id"] for l in lessons["pluvier"]])
        self.assertEqual({l["track"] for l in lessons["plover"]}, {"ponctuation", "commandes"})

    def test_every_entry_is_in_exactly_one_lesson_family(self) -> None:
        for style, entries in self.document["entries"].items():
            self.assertEqual(len({e["primary"] for e in entries}), len(entries), style)      # no two meanings share a primary chord
            self.assertTrue(all(e["family"] for e in entries), style)

    def test_punctuation_entries_appear_in_a_phrase_and_paired_marks_come_together(self) -> None:
        pairs = [("lstraight", "rstraight"), ("lq", "rq"), ("lsq", "rsq"), ("lp", "rp"), ("lb", "rb")]
        used = {t[1:] for ex in self.examples for t in ex["tokens"] if t.startswith("@")}
        for opening, closing in pairs:
            for ex in self.examples:
                tokens = {t[1:] for t in ex["tokens"] if t.startswith("@")}
                opens = opening in tokens or (opening == "lq" and "dialogue" in tokens)     # the dialogue mark opens a «
                self.assertEqual(opens, closing in tokens, ex)
        self.assertTrue({"point", "virgule", "interro", "lq", "rq", "lp", "rp", "espace", "pourcent"} <= used)

    def test_commands_are_bare_chords_with_the_other_spellings_accepted(self) -> None:
        backspace = next(w for l in self.document["lessons"]["plover"] if l["id"] == "commandes-01"
                         for w in l["words"] if w["ortho"] == "Retour arrière")
        self.assertEqual(backspace["steno"], "mt-jk")
        self.assertEqual({a["steno"] for a in backspace["alternates"]}, {"mt*jk"})

    def test_rule_lines_keep_one_order_and_only_the_styles_own_chords(self) -> None:
        def lines(style: str) -> list[str]:
            return [r["text"] for lesson in self.document["lessons"][style] if "parenthèses" in lesson["title"] for r in lesson["rules"][1:]]
        plover, pluvier = lines("plover"), lines("pluvier")
        self.assertEqual([x.split(" :")[0] for x in plover], [x.split(" :")[0] for x in pluvier])      # same names, same order
        self.assertTrue(plover[0].startswith("La parenthèse ouvrante ( ( ) :"))
        self.assertLess([x for x in plover].index(plover[0]), [x for x in plover].index(plover[1]))
        self.assertNotIn("spmR-jktnl", pluvier[0])                                                      # a Plover chord stays out of the Pluvier text

    def test_each_style_offers_only_its_own_chords(self) -> None:
        def chords(style: str, name: str) -> list[str]:
            return next(e["chords"] for e in self.document["entries"][style] if e["name"] == name)
        self.assertEqual(chords("pluvier", "le point"), ["-jktn"])                  # not Plover's pm-kt
        self.assertEqual(chords("plover", "le point"), ["pm-kt"])
        self.assertNotIn("vt-Rl", chords("pluvier", "le guillemet ouvrant «"))
        self.assertEqual(chords("pluvier", "le crochet ouvrant"), ["mtw-dRn"])    # shared by both sets

    def test_the_styles_differ_on_the_period(self) -> None:
        def period(style: str) -> str:
            return next(e["primary"] for e in self.document["entries"][style] if e["name"] == "le point")
        self.assertEqual(period("plover"), "pm-kt")
        self.assertEqual(period("pluvier"), "-jktn")


if __name__ == "__main__":
    unittest.main()
