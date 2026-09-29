"""The DisambiguatedTheory.pickle envelope of util/_theoryio.py: fingerprint
hit/miss round-trips on tmp files. The real five fingerprint inputs are
multi-MB repo artifacts the unit tests must not depend on, so every test
passes its own `inputs` / `path`."""

from util._theoryio import (
    loadCachedDisambiguatedTheory,
    writeDisambiguatedTheoryPickle,
)


def _writeInputs(tmp_path, contents=(b"lexique", b"layout")):
    inputs = tuple(str(tmp_path / name) for name in ("lexique.tsv", "layout.json"))
    for path, content in zip(inputs, contents):
        with open(path, "wb") as f:
            f.write(content)
    return inputs


def test_round_trip_is_a_hit(tmp_path):
    inputs = _writeInputs(tmp_path)
    cachePath = str(tmp_path / "DisambiguatedTheory.pickle")
    theory = {"ami": [(1, 2), (3,)]}
    wordToStrokes = {}
    wordsByOrthoLemme = {("ami", "VER"): []}
    writeDisambiguatedTheoryPickle(theory, wordToStrokes, wordsByOrthoLemme,
                                    path=cachePath, inputs=inputs)
    assert loadCachedDisambiguatedTheory(path=cachePath, inputs=inputs) \
        == (theory, wordToStrokes, wordsByOrthoLemme)


def test_changed_input_is_a_miss(tmp_path):
    inputs = _writeInputs(tmp_path)
    cachePath = str(tmp_path / "DisambiguatedTheory.pickle")
    writeDisambiguatedTheoryPickle({"ami": [(1, 2)]}, {}, {}, path=cachePath, inputs=inputs)
    with open(inputs[0], "wb") as f:
        f.write(b"lexique-edited")
    assert loadCachedDisambiguatedTheory(path=cachePath, inputs=inputs) is None


def test_deleted_input_is_a_miss(tmp_path):
    # A fingerprint input disappearing (e.g. keypress_groups.json not yet
    # rebuilt) must not load a stale cache.
    inputs = _writeInputs(tmp_path)
    cachePath = str(tmp_path / "DisambiguatedTheory.pickle")
    writeDisambiguatedTheoryPickle({"ami": [(1, 2)]}, {}, {}, path=cachePath, inputs=inputs)
    import os
    os.remove(inputs[1])
    assert loadCachedDisambiguatedTheory(path=cachePath, inputs=inputs) is None


def test_absent_cache_is_a_miss(tmp_path):
    inputs = _writeInputs(tmp_path)
    assert loadCachedDisambiguatedTheory(
        path=str(tmp_path / "DisambiguatedTheory.pickle"), inputs=inputs) is None


def test_truncated_cache_is_a_miss(tmp_path):
    # A corrupt pickle (interrupted write) loads as a miss, never as an error.
    inputs = _writeInputs(tmp_path)
    cachePath = tmp_path / "DisambiguatedTheory.pickle"
    writeDisambiguatedTheoryPickle({"ami": [(1, 2)]}, {}, {}, path=str(cachePath), inputs=inputs)
    with open(cachePath, "r+b") as f:
        f.truncate(17)
    assert loadCachedDisambiguatedTheory(path=str(cachePath), inputs=inputs) is None


def test_format1_envelope_is_a_miss(tmp_path):
    # A round-1 format-1 envelope (no word indexes) must load as a miss, never
    # crash or half-load.
    import pickle
    inputs = _writeInputs(tmp_path)
    cachePath = str(tmp_path / "DisambiguatedTheory.pickle")
    from util._theoryio import disambiguatedTheoryFingerprint
    with open(cachePath, "wb") as f:
        pickle.dump((1, disambiguatedTheoryFingerprint(inputs), {"ami": [(1, 2)]}), f,
                    protocol=pickle.HIGHEST_PROTOCOL)
    assert loadCachedDisambiguatedTheory(path=cachePath, inputs=inputs) is None
