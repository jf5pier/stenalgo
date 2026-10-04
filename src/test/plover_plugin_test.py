"""The Plover dictionary plugin (plover_stenalgo/): vendored decoder copy, stroke parser, dictionary class."""
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from src.expressiondata import bundleToDict, legalityFromStarboard
from src.expressionmodel import AttachRule, BriefRule, Rules
from src.keyboard import Starboard
from src.keyconflicts import KeyConflicts
from util.export_plover_plugin import generate

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
                d._load(resource)
                return d

        plover = types.ModuleType("plover")
        module = types.ModuleType("plover.steno_dictionary")
        module.StenoDictionary = StenoDictionary                            # type: ignore[attr-defined]
        plover.steno_dictionary = module                                    # type: ignore[attr-defined]
        sys.modules.update({"plover": plover, "plover.steno_dictionary": module})
    for name in [n for n in sys.modules if n == "plover_stenalgo" or n.startswith("plover_stenalgo.")]:
        del sys.modules[name]
    import plover_stenalgo.dictionary as dictionary
    import plover_stenalgo.stroke as stroke
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
    @classmethod
    def setUpClass(cls) -> None:
        legality = legalityFromStarboard(Starboard.fromJSONFile("starboard3h.json"))
        rules = Rules(attaches=(AttachRule(("de",), "prefix", (3,), "", "base"),
                                AttachRule(("d'",), "prefix", (3,), "", "elided")),
                      briefs=(BriefRule(("a", "b"), ((8,),)),))
        doc = bundleToDict(rules, {((5,),): ["mot"], ((6,),): ["arbre"]}, {"mot": 1, "arbre": 1}, {}, {},
                           KeyConflicts(), legality)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / "test.stenalgo"
        cls.path.write_text(json.dumps(doc), encoding="utf-8")
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
