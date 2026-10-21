"""Unit tests for the remote-solve tooling: the solver settings, the per-part run with its incumbent and report files, and util/merge_layouts.py."""
import json
from typing import Any

import pytest

from src.cpsatsolver import SolverSettings, optimizeKeyboard
from src.grammar import Phoneme, Syllable
from src.keyboard import Starboard
from src.layoutstatistics import buildSyllableStatistics
from src.word import GramCat, Word
from util.merge_layouts import merge
from util.optimize_keyboard import DEFAULT_OUTPUT, main as optimizeMain, parseArgs


def _seed() -> Starboard:
    board = Starboard.fromJSONFile("starboard3h.json")
    assert board is not None
    return board


def _partFile(tmp_path: Any, board: Starboard, part: str, name: str) -> str:
    """A layout file holding only the strokes of one part, as `optimize_keyboard --parts PART` writes it."""
    keys = set(board.keyIDinSyllabicPart[part])
    only = _seed()
    only.clearLayout()
    for stroke, phonemes in board.phonemesAssignedToStroke.items():
        if set(stroke) <= keys:
            for phoneme in phonemes:
                only.addToLayout(stroke, phoneme)
    path = str(tmp_path / name)
    only.toJSONFile(path)
    return path


class TestArguments:
    def test_the_defaults_are_the_historical_run(self) -> None:
        args = parseArgs([])
        assert args.parts == ["onset", "nucleus", "coda"] and args.time == 90.0 and args.workers == 0
        assert args.seed is None and not args.log and args.incumbent_dir is None and args.report is None
        assert args.output == DEFAULT_OUTPUT

    def test_a_subset_of_parts_and_the_run_settings_parse(self) -> None:
        args = parseArgs(["--parts", "onset", "coda", "--time", "3600", "--workers", "64", "--seed", "7", "--incumbent-dir", "d", "--report", "r.json"])
        assert args.parts == ["onset", "coda"] and args.time == 3600.0 and args.workers == 64 and args.seed == 7

    def test_the_seed_layout_defaults_to_the_committed_seed(self) -> None:
        assert parseArgs([]).seed_layout == "starboard3h.json"
        assert parseArgs(["--seed-layout", "resume.json"]).seed_layout == "resume.json"

    def test_an_unknown_part_is_refused(self) -> None:
        with pytest.raises(SystemExit):
            parseArgs(["--parts", "vowel"])

    def test_a_partial_run_cannot_overwrite_the_seed(self) -> None:
        with pytest.raises(SystemExit):
            optimizeMain(["--parts", "onset", "--output", "starboard3h.json", "--statistics", "does-not-matter.pickle"])


class TestMerge:
    def test_the_three_parts_of_the_seed_merge_back_into_the_seed(self, tmp_path: Any) -> None:
        seed = _seed()
        files = {part: _partFile(tmp_path, seed, part, f"{part}.json") for part in ("onset", "nucleus", "coda")}
        merged = merge(_seed(), files)
        assert merged.phonemesAssignedToStroke == seed.phonemesAssignedToStroke

    def test_a_missing_part_keeps_the_seed(self, tmp_path: Any) -> None:
        seed = _seed()
        swapped = _seed()
        swapped.clearLayout()
        for stroke, phonemes in seed.phonemesAssignedToStroke.items():
            for phoneme in phonemes:
                swapped.addToLayout(stroke, {"a": "e", "e": "a"}.get(phoneme, phoneme))
        nucleusFile = _partFile(tmp_path, swapped, "nucleus", "nucleus.json")
        merged = merge(_seed(), {"nucleus": nucleusFile})
        assert merged.getStrokesOfPhoneme("a", "nucleus") == seed.getStrokesOfPhoneme("e", "nucleus")
        assert merged.getStrokesOfPhoneme("b", "onset") == seed.getStrokesOfPhoneme("b", "onset")

    def test_a_part_with_a_missing_phoneme_is_refused(self, tmp_path: Any) -> None:
        broken = _seed()
        stroke = broken.getStrokesOfPhoneme("a", "nucleus")[0]
        broken.removeFromLayout(stroke, "a")
        with pytest.raises(ValueError, match="missing"):
            merge(_seed(), {"nucleus": _partFile(tmp_path, broken, "nucleus", "n.json")})

    def test_a_file_holding_another_part_is_refused(self, tmp_path: Any) -> None:
        seed = _seed()
        with pytest.raises(ValueError, match="not made of nucleus keys"):
            merge(_seed(), {"nucleus": _partFile(tmp_path, seed, "onset", "wrong.json")})


def _toyNucleusSolve(tmp_path: Any, board: Starboard, settings: SolverSettings) -> None:
    """A nucleus-only solve on a small made-up statistics set (every vowel has a weight, four of them are ambiguous with one another)."""
    def word(ortho: str, phon: str, freq: float) -> Word:
        return Word(ortho=ortho, phonology=phon, lemme=ortho, gramCat=GramCat.NOM, orthoGramCat=[GramCat.NOM], gender=None, number=None,
                    infoVerb=None, rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho), frequencyBook=freq, frequencyFilm=freq)
    saved = (Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart)
    try:
        vowels = Phoneme.nucleusPhonemes
        buildSyllableStatistics([word("p" + v, "p" + v, 100.0 - 5.0 * i) for i, v in enumerate(vowels)], set())
        Syllable.optimizeBiphonemeOrder()
        nucleus = [(v,) for v in vowels[:4]]
        ambiguity: dict[str, dict[Any, float]] = {
            "onset": {}, "coda": {},
            "nucleus": {(nucleus[i], nucleus[j]): 10.0 * (i + j + 1) for i in range(4) for j in range(i + 1, 4)},
        }
        optimizeKeyboard(board, ambiguity, ["nucleus"], settings)
    finally:
        Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart = saved


class TestIncumbent:
    def test_the_best_solution_is_written_at_the_end_whatever_the_write_interval(self, tmp_path: Any) -> None:
        # a poor hint (the most frequent vowels on the worst chords, swapped pairwise) so that the search improves on it, and an interval so long that
        # only the first solution is written during the search: the file must still end up holding the final layout
        poor = _seed()
        order = list(Phoneme.nucleusPhonemes)
        strokes = {v: poor.getStrokesOfPhoneme(v, "nucleus")[0] for v in order}
        for v in order:
            poor.removeFromLayout(strokes[v], v)
        for v, other in zip(order, reversed(order)):
            poor.addToLayout(strokes[other], v)
        board = _seed()
        board.phonemesAssignedToStroke = dict(poor.phonemesAssignedToStroke)
        settings = SolverSettings(timeSeconds=10.0, workers=2, seed=1, incumbentPath=str(tmp_path / "inc_{part}.json"), incumbentInterval=1e9)
        _toyNucleusSolve(tmp_path, board, settings)
        incumbent = Starboard.fromJSONFile(str(tmp_path / "inc_nucleus.json"))
        assert incumbent is not None
        assert incumbent.phonemesAssignedToStroke == board.phonemesAssignedToStroke
        assert incumbent.phonemesAssignedToStroke != poor.phonemesAssignedToStroke  # the search did improve on the hint

    def test_a_layout_write_leaves_no_temporary_file_and_a_failed_one_keeps_the_old_file(self, tmp_path: Any) -> None:
        board = _seed()
        path = tmp_path / "layout.json"
        board.toJSONFile(str(path))
        assert [f.name for f in tmp_path.iterdir()] == ["layout.json"]
        before = path.read_text()
        broken = _seed()
        broken.phonemesAssignedToStroke = {(1,): [object()]}  # type: ignore[list-item]  # not JSON serializable
        with pytest.raises(TypeError):
            broken.toJSONFile(str(path))
        assert path.read_text() == before and [f.name for f in tmp_path.iterdir()] == ["layout.json"]


class TestSolve:
    def test_a_one_part_solve_writes_its_incumbent_and_its_report(self, tmp_path: Any) -> None:
        def word(ortho: str, phon: str, freq: float) -> Word:
            return Word(ortho=ortho, phonology=phon, lemme=ortho, gramCat=GramCat.NOM, orthoGramCat=[GramCat.NOM], gender=None, number=None,
                        infoVerb=None, rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho), frequencyBook=freq, frequencyFilm=freq)
        saved = (Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart)
        try:
            vowels = Phoneme.nucleusPhonemes
            buildSyllableStatistics([word("p" + v, "p" + v, 100.0 - 5.0 * i) for i, v in enumerate(vowels)], set())
            Syllable.optimizeBiphonemeOrder()
            nucleus = [(v,) for v in vowels[:4]]
            ambiguity: dict[str, dict[Any, float]] = {
                "onset": {}, "coda": {},
                "nucleus": {(nucleus[i], nucleus[j]): 10.0 * (i + j + 1) for i in range(4) for j in range(i + 1, 4)},
            }
            board = _seed()
            settings = SolverSettings(timeSeconds=10.0, workers=2, seed=3, incumbentPath=str(tmp_path / "inc_{part}.json"),
                                      incumbentInterval=0.0, reportPath=str(tmp_path / "report.json"))
            optimizeKeyboard(board, ambiguity, ["nucleus"], settings)
        finally:
            Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart = saved
        report = json.loads((tmp_path / "report.json").read_text())
        assert set(report) == {"nucleus"} and report["nucleus"]["status"] in ("OPTIMAL", "FEASIBLE")
        assert report["nucleus"]["workers"] == 2 and report["nucleus"]["seed"] == 3 and "bestBound" in report["nucleus"]
        incumbent = Starboard.fromJSONFile(str(tmp_path / "inc_nucleus.json"))
        assert incumbent is not None and incumbent.phonemesAssignedToStroke
        keys = set(board.keyIDinSyllabicPart["nucleus"])
        assert all(set(stroke) <= keys for stroke in incumbent.phonemesAssignedToStroke)
        assert all(set(stroke) <= keys for stroke in board.phonemesAssignedToStroke)  # only the solved part is in the output layout


class TestPackage:
    def test_the_remote_commands_import_no_lexicon_side_module(self) -> None:
        from util.package_remote_solve import importedRepoFiles
        files = importedRepoFiles()
        assert "src/cpsatsolver.py" in files and "util/optimize_keyboard.py" in files and "util/merge_layouts.py" in files
        forbidden = {"dictionary.py", "lexique.py", "src/ambiguitychecker.py", "util/_theoryio.py"}
        assert not forbidden & set(files), f"the remote package would need {sorted(forbidden & set(files))}"

    def test_the_remote_requirements_are_the_pins_of_the_repo(self) -> None:
        from util.package_remote_solve import pinnedRequirements
        pins = pinnedRequirements()
        assert sorted(pin.split("==")[0] for pin in pins) == ["ortools", "rich", "tqdm"] and all("==" in pin for pin in pins)


class TestRunScript:
    def test_the_run_script_is_valid_bash_and_passes_the_seed_layout(self, tmp_path: Any) -> None:
        import subprocess
        from util.package_remote_solve import RUN_SCRIPT
        path = tmp_path / "run_remote.sh"
        path.write_text(RUN_SCRIPT)
        assert subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True).returncode == 0
        assert '--seed-layout "$SEED_LAYOUT"' in RUN_SCRIPT and "RESUME" not in RUN_SCRIPT
