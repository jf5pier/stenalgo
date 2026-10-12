from pathlib import Path

from src.keyboard import Starboard
from util._outlines import AffixShorts, taggedOutlines
from util._stenorender import renderFinalStrokesToRTFCRE


def starboard() -> Starboard:
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    assert keyboard is not None
    return keyboard


def test_word_without_merge() -> None:
    hint, alternates = taggedOutlines(starboard(), ((14,), (18,)), [], None)
    assert hint["kind"] == "long" and hint["strokes"] == [[14], [18]] and alternates == []


def test_merged_word_hints_the_long_outline(tmp_path: Path) -> None:
    keyboard = starboard()
    long = renderFinalStrokesToRTFCRE(keyboard, ((14,), (18,)))
    short = renderFinalStrokesToRTFCRE(keyboard, ((2, 14, 18),))
    path = tmp_path / "abbreviations.tsv"
    path.write_text(f"spelling\tlong\tshort\tsaved\trank\tanchor\tk\tfrequency\troute\nai\t{long}\t{short}\t1\t4\tx\t1\t1\t0\n",
                    encoding="utf-8")
    hint, alternates = taggedOutlines(keyboard, ((14, 18),), [((14,), (18,))], AffixShorts(keyboard, str(path)))
    assert hint["steno"] == long and hint["kind"] == "long"
    assert [(a["kind"], a.get("rule")) for a in alternates] == [("merged", None), ("affix", 4)]
    assert alternates[1]["strokes"] == [[2, 14, 18]]
