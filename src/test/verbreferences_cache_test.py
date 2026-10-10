"""loadVerbReferences' cache: served only while the source files and the parser are what it was built from."""
from typing import Any

import pytest

from util import _verbreferences
from util._verbreferences import loadVerbReferences


def _sources(tmp_path: Any, ipa: str = "a.ʁe") -> tuple[str, str]:
    wiktionary = tmp_path / "wik.tsv"
    wiktionary.write_text("lemme\tortho\ttags\tipa\naimer\taime\tind:pre:1s\t" + ipa + "\n", encoding="utf-8")
    glaff = tmp_path / "glaff.txt"
    glaff.write_text("", encoding="utf-8")  # no verb line: only the Wiktionary side is filled
    return str(wiktionary), str(glaff)


def test_second_call_reads_the_cache_and_a_changed_source_invalidates_it(tmp_path: Any, monkeypatch: Any) -> None:
    wiktionary, glaff = _sources(tmp_path)
    cache = str(tmp_path / "refs.pickle")
    first = loadVerbReferences(wiktionary, glaff, cachePath=cache)
    assert first.get("aimer", "aime", "ind:pre:1s") is not None

    def mustNotParse(*args: Any) -> None:
        raise AssertionError("served from the cache: no parse")

    monkeypatch.setattr(_verbreferences, "_parseVerbReferences", mustNotParse)
    again = loadVerbReferences(wiktionary, glaff, cachePath=cache)
    assert again.get("aimer", "aime", "ind:pre:1s") is not None

    _sources(tmp_path, ipa="b.ʁe")  # the source changes: the cache no longer matches it
    with pytest.raises(AssertionError, match="no parse"):
        loadVerbReferences(wiktionary, glaff, cachePath=cache)


def test_no_cache_when_a_source_is_missing_or_cachepath_is_none(tmp_path: Any) -> None:
    wiktionary, _ = _sources(tmp_path)
    cache = tmp_path / "refs.pickle"
    loadVerbReferences(wiktionary, str(tmp_path / "absent.txt"), cachePath=str(cache))
    assert not cache.exists()
    wiktionary, glaff = _sources(tmp_path)
    loadVerbReferences(wiktionary, glaff, cachePath=None)
    assert not cache.exists()
