import xml.etree.ElementTree as ET

from src.keyboard import Starboard
from util.export_keyboard_layout import KEYBOARD_JSON
from util.export_svg_layout import buildSvg


def test_svg_has_one_group_per_key() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    assert starboard is not None
    root = ET.fromstring(buildSvg(starboard))
    ids = [g.get("id") for g in root if g.tag.endswith("}g")]
    assert ids == ["board"] + [f"key-{i:02d}" for i in range(starboard.nbKeys)]
