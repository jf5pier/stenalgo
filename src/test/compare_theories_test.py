"""Smoke test of `util/compare_theories.py` on tiny fixture files (no pickle)."""

import json
import os
import tempfile
import unittest

from util import compare_theories

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


class TestCompareTheories(unittest.TestCase):
    def test_smoke_and_determinism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            def write(name: str, content: str) -> str:
                path = os.path.join(tmp, name)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(content)
                return path

            lexicon = write("lex.tsv", "ortho\tsyll\tfreqfilms2\tfreqlivres\n"
                            "star\tsta\t10\t1\ntsar\ttsa\t5\t1\nchat\tSa\t5\t1\nrare\tRa\t0\t0\nfroid\tfRwa\t3\t1\n")
            dicofr = write("dicofr.json", json.dumps({"STA": "star", "TSA": "tsar", "SHA": "chat", "TPROEU": "froid"}))
            dup = write("dup.json", json.dumps({"SHA": ["chat", "chats"]}))
            stenalgo = write("dict.json", json.dumps({"k": "star", "s": "chat"}))
            abbreviations = write("abbr.tsv", "spelling\tshort\nchat\tk/s\n")
            args = compare_theories.argparse.Namespace(
                stenalgo_abbreviations=abbreviations, stenalgo_dict=stenalgo, stenalgo_layout=os.path.join(ROOT, "starboard3h.json"), pluvier_dict=dicofr,
                pluvier_dup=dup, lexicon=lexicon, phoneme_keys=os.path.join(ROOT, "resources", "pluvierPhonemeKeys.tsv"),
                freq="films", out=tmp)
            first = compare_theories.compare(args)
            second = compare_theories.compare(args)
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertEqual(first["coverage"]["universe"]["spellings"], 5)
            self.assertEqual(first["coverage"]["pluvier"]["spellings"], 4)
            self.assertEqual(first["coverage"]["both"]["spellings"], 2)                             # star, chat
            self.assertEqual(first["collisionsOnCommonWords"]["pluvier"]["wordsColliding"], 1)     # chat's outline is claimed twice
            self.assertEqual(first["collisionsOnCommonWords"]["stenalgo"]["wordsColliding"], 0)
            self.assertIn("stenalgoShort", first["fullCoverage"])
            self.assertEqual(first["fullCoverage"]["stenalgoShort"]["abbreviatedWords"], 0)        # k/s is longer than s
            self.assertEqual(first["theories"]["pluvier"]["wordsOnlyInCollisionRecord"], 1)
            order = first["fullCoverage"]["phonemeOrder"]["pluvier"]
            self.assertAlmostEqual(order["shareWithViolation"], 5 / 23)                             # tsar only, of star+tsar+chat+froid
            text = compare_theories.renderMarkdown(first)
            self.assertIn("## 1. Word coverage", text)
            self.assertIn("#### Every claimant takes the stroke", text)

    def test_main_writes_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lexicon = os.path.join(tmp, "lex.tsv")
            with open(lexicon, "w", encoding="utf-8") as handle:
                handle.write("ortho\tsyll\tfreqfilms2\tfreqlivres\nstar\tsta\t10\t1\n")
            for name, content in (("a.json", {"STA": "star"}), ("b.json", {}), ("c.json", {"k": "star"})):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
                    json.dump(content, handle)
            compare_theories.main(["--pluvier-dict", os.path.join(tmp, "a.json"), "--pluvier-dup", os.path.join(tmp, "b.json"),
                                   "--stenalgo-dict", os.path.join(tmp, "c.json"), "--lexicon", lexicon, "--out", tmp])
            self.assertTrue(os.path.exists(os.path.join(tmp, "theory_comparison.json")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "theory_comparison.md")))

    def test_several_pluvier_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lexicon = os.path.join(tmp, "lex.tsv")
            with open(lexicon, "w", encoding="utf-8") as handle:
                handle.write("ortho\tsyll\tfreqfilms2\tfreqlivres\nstar\tsta\t10\t1\nla\tla\t30\t1\nchat\tSa\t5\t1\n")
            files = {"a.json": {"STA": "star", "SHA": "chat"}, "b.json": {"HRA": "la", "SHA": "chats"}, "c.json": {"k": "star"}}
            for name, content in files.items():
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
                    json.dump(content, handle)
            compare_theories.main(["--pluvier-dict", os.path.join(tmp, "a.json"), "--pluvier-dict", os.path.join(tmp, "b.json"),
                                   "--stenalgo-dict", os.path.join(tmp, "c.json"), "--lexicon", lexicon, "--out", tmp])
            with open(os.path.join(tmp, "theory_comparison.json"), encoding="utf-8") as handle:
                report = json.load(handle)
            self.assertEqual([os.path.basename(d["path"]) for d in report["inputs"]["pluvierDicts"]], ["a.json", "b.json"])
            self.assertIsNone(report["inputs"]["pluvierDup"])
            self.assertEqual(report["coverage"]["pluvier"]["spellings"], 2)             # star, la; chat lost SHA to `chats`
            self.assertEqual(report["theories"]["pluvier"]["layerEntries"], [2, 2])


if __name__ == "__main__":
    unittest.main()
