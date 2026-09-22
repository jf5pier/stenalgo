import pytest

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE


@pytest.fixture(scope="module")
def starboard() -> Starboard:
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


# Expected strings are what Plover's own `plover_stroke` produces for these key sets
# under plover_stenalgo's KEYS/IMPLICIT_HYPHEN_KEYS (checked 2026-09-22).
@pytest.mark.parametrize("stroke, expected", [
    ((13, 14, 23, 10), "*iel"),
    ((13, 14, 23, 15), "ie#l"),
    ((13, 14, 23, 10, 15), "*ie#l"),
    ((3, 9, 12, 15), "swa#"),
    ((4, 5, 8, 10), "pvR*"),
    ((4, 5, 8, 15), "pvR-#"),
    ((20, 10), "*t"),
    ((15, 23), "-#l"),
])
def test_mark_merged_into_phoneme_stroke_renders_like_plover(starboard, stroke, expected):
    assert renderFinalStrokesToRTFCRE(starboard, (stroke,)) == expected


def test_bare_mark_and_plain_strokes_keep_their_rendering(starboard):
    assert renderFinalStrokesToRTFCRE(starboard, ((3, 9, 12), (15,), (10, 15))) == "swa/#/*#"
