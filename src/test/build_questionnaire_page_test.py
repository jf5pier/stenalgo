"""Unit tests for util/build_questionnaire_page.py: the questionnaire.json read
lives in loadItems()/main(), not at module scope (an import used to require the
file to exist)."""
import json

import util.build_questionnaire_page  # noqa: F401  (import itself is the test)
from util.build_questionnaire_page import loadItems


def test_load_items_round_trips(tmp_path):
    items = [{"atomsA": ["pers_1"], "atomsB": ["pers_2"], "clean": True}]
    path = tmp_path / "q.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    assert loadItems(str(path)) == items
