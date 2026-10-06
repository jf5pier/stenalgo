"""The Plover dictionary plugin (plover_stenalgo/): vendored decoder copy, stroke parser, dictionary class."""
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any

from src.expressiondata import bundleToDict, legalityFromStarboard
from src.expressionmodel import AttachRule, BriefRule, Rules
from src.keyboard import Starboard, Strokes
from src.keyconflicts import KeyConflicts
from util.export_plover_plugin import EXPRESSIONS, STOCK, exportAssets, generate

REPO = Path(__file__).resolve().parent.parent.parent
PLUGIN = REPO / "plover_stenalgo"


def _pluginImports():
    """`plover_stenalgo` from the plugin folder, with a minimal stand-in for `plover.steno_dictionary`."""
    sys.path.insert(0, str(PLUGIN))
    if "plover.steno_dictionary" not in sys.modules:
        class StenoDictionary:
            readonly = False

            def __init__(self) -> None:
                self._longest_key = 0

            @property
            def longest_key(self) -> int:
                return self._longest_key

            @classmethod
            def load(cls, resource: str):
                d = cls()
                d._load(resource)                                           # type: ignore[attr-defined]
                return d

        plover = types.ModuleType("plover")
        module = types.ModuleType("plover.steno_dictionary")
        module.StenoDictionary = StenoDictionary                            # type: ignore[attr-defined]
        plover.steno_dictionary = module                                    # type: ignore[attr-defined]
        sys.modules.update({"plover": plover, "plover.steno_dictionary": module})
    for name in [n for n in sys.modules if n == "plover_stenalgo" or n.startswith("plover_stenalgo.")]:
        del sys.modules[name]
    import plover_stenalgo.dictionary as dictionary   # type: ignore[import-not-found]
    import plover_stenalgo.stroke as stroke   # type: ignore[import-not-found]
    return dictionary, stroke


class TestVendoredCore(unittest.TestCase):
    def test_copy_is_up_to_date(self) -> None:
        for path, text in generate().items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_text(encoding="utf-8"), text,
                             f"{path.name} is stale: run python -m util.export_plover_plugin")

    def test_core_needs_only_the_standard_library(self) -> None:
        code = ("import sys; sys.path.insert(0, sys.argv[1]);"
                "import plover_stenalgo._core.expressiondata;"
                "bad = [m for m in sys.modules if m == 'src' or m.startswith(('src.', 'numpy', 'ortools'))];"
                "sys.exit(1 if bad else 0)")
        done = subprocess.run([sys.executable, "-I", "-c", code, str(PLUGIN)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)


class TestMachineKeymaps(unittest.TestCase):
    """`system.KEYMAPS` names a machine's keys for every supported protocol."""

    HID_KEYS = {"S1-", "T-", "K-", "P-", "W-", "H-", "R-", "A-", "O-", "*1", "-E", "-U", "-F", "-R", "-P", "-B", "-L",
                "-G", "-T", "-S", "-D", "-Z", "#1", "S2-", "*2", "*3", "*4", "#2", "#3", "#4", "#5", "#6", "#7", "#8",
                "#9", "#A", "#B", "#C"} | {f"X{i}" for i in range(1, 27)}     # plover-machine-hid STENO_KEY_CHART

    def test_gemini_pr_and_plover_hid_cover_every_key_once(self) -> None:
        sys.path.insert(0, str(PLUGIN))
        try:
            import importlib
            system = importlib.import_module("plover_stenalgo.system")
        finally:
            sys.path.remove(str(PLUGIN))
        for machine in ("Gemini PR", "Plover HID"):
            keymap = system.KEYMAPS[machine]
            self.assertEqual(set(keymap), set(system.KEYS), machine)
            labels = list(keymap.values())
            self.assertEqual(len(labels), len(set(labels)), f"{machine}: a machine key is mapped twice")
        self.assertLessEqual(set(system.KEYMAPS["Plover HID"].values()), self.HID_KEYS)


class TestPackagedAssets(unittest.TestCase):
    """The data travels inside the plugin package: system.DEFAULT_DICTIONARIES names it as asset URIs."""

    def test_default_dictionaries_name_the_packaged_pair_in_priority_order(self) -> None:
        sys.path.insert(0, str(PLUGIN))
        try:
            import importlib
            system = importlib.import_module("plover_stenalgo.system")
        finally:
            sys.path.remove(str(PLUGIN))
        names = [d for d in system.DEFAULT_DICTIONARIES if d.startswith("asset:plover_stenalgo:")]
        self.assertEqual([n.rsplit("/", 1)[1] for n in names], [EXPRESSIONS, STOCK])   # expressions above the stock

    def test_export_refuses_data_built_against_another_stock_dictionary(self) -> None:
        stock, expressions = REPO / STOCK, REPO / EXPRESSIONS
        if not (stock.exists() and expressions.exists()):
            self.skipTest("generated data not built")
        with tempfile.TemporaryDirectory() as tmp:
            repo, assets = Path(tmp) / "repo", Path(tmp) / "assets"
            repo.mkdir()
            (repo / EXPRESSIONS).write_bytes(expressions.read_bytes())
            (repo / STOCK).write_text(json.dumps({"v-": "mot"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                exportAssets(repo, assets)
            (repo / STOCK).write_bytes(stock.read_bytes())
            copied = exportAssets(repo, assets)
            self.assertEqual(sorted(p.name for p in copied), sorted([EXPRESSIONS, STOCK]))
            for p in copied:
                self.assertEqual(p.read_bytes(), (repo / p.name).read_bytes())

    def test_export_names_the_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                exportAssets(Path(tmp), Path(tmp) / "assets")


class TestStrokeParser(unittest.TestCase):
    def test_parse(self) -> None:
        _dictionary, stroke = _pluginImports()
        self.assertEqual(stroke.parseStroke("k-"), (2,))
        self.assertEqual(stroke.parseStroke("vt-"), (5, 7))
        self.assertEqual(stroke.parseStroke("@isnZ"), (11, 13, 17, 22, 24))
        self.assertIsNone(stroke.parseStroke(""))
        self.assertIsNone(stroke.parseStroke("zzz"))
        self.assertEqual(stroke.parseOutline(("k-", "vt-")), ((2,), (5, 7)))
        self.assertIsNone(stroke.parseOutline(("", "k-")))


class TestDictionary(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory[str]
    path: Path
    dictionary: Any

    @classmethod
    def setUpClass(cls) -> None:
        legality = legalityFromStarboard(Starboard.fromJSONFile("starboard3h.json"))
        rules = Rules(attaches=(AttachRule(("de",), "prefix", (3,), "", "base"),
                                AttachRule(("d'",), "prefix", (3,), "", "elided")),
                      briefs=(BriefRule(("a", "b"), ((8,),)),))
        words: dict[Strokes, list[str]] = {((5,),): ["mot"], ((6,),): ["arbre"]}
        doc = bundleToDict(rules, words, {"mot": 1, "arbre": 1}, {}, {}, KeyConflicts(), legality,
                           wordsFile="stock.json")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / "test.stenalgo"
        cls.path.write_text(json.dumps(doc), encoding="utf-8")
        (Path(cls.tmp.name) / "stock.json").write_text(json.dumps({"v-": "mot", "m-": "arbre"}), encoding="utf-8")
        dictionary, _stroke = _pluginImports()
        cls.dictionary = dictionary.StenalgoExpressionDictionary.load(str(cls.path))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_merged_attach_and_elision(self) -> None:
        self.assertEqual(self.dictionary.get(("sv-",)), "de mot")
        self.assertEqual(self.dictionary.get(("sm-",)), "d'arbre")

    def test_brief(self) -> None:
        self.assertEqual(self.dictionary.get(("R-",)), "a b")

    def test_misses(self) -> None:
        self.assertIsNone(self.dictionary.get(("v-",)))           # a plain word: the stock dictionary's
        self.assertIsNone(self.dictionary.get(("", "v-")))        # Plover's prefix stroke
        self.assertIsNone(self.dictionary.get(("zzz",)))
        self.assertEqual(self.dictionary.get(("zzz",), "x"), "x")
        with self.assertRaises(KeyError):
            self.dictionary[("v-",)]

    def test_longest_key_and_readonly(self) -> None:
        self.assertTrue(self.dictionary.readonly)
        self.assertEqual(self.dictionary.longest_key, 1)

    def test_wrong_or_missing_stock_dictionary_is_refused(self) -> None:
        dictionary, _stroke = _pluginImports()
        stock = Path(self.tmp.name) / "stock.json"
        good = stock.read_text(encoding="utf-8")
        try:
            stock.write_text(json.dumps({"v-": "mot", "m-": "autre"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                dictionary.StenalgoExpressionDictionary.load(str(self.path))
            stock.write_text(json.dumps({"zzz": "mot"}), encoding="utf-8")     # not this system's strokes
            with self.assertRaises(ValueError):
                dictionary.StenalgoExpressionDictionary.load(str(self.path))
            stock.unlink()
            with self.assertRaises(OSError):
                dictionary.StenalgoExpressionDictionary.load(str(self.path))
        finally:
            stock.write_text(good, encoding="utf-8")
