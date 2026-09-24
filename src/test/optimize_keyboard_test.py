"""Unit tests for util/optimize_keyboard.py: argument surface and the
never-overwrite-the-seed-silently guarantee."""
from util.optimize_keyboard import DEFAULT_OUTPUT, SEED_PATH, parseArgs


def test_default_output_is_not_the_seed():
    assert DEFAULT_OUTPUT != SEED_PATH


def test_parse_args_defaults():
    assert parseArgs([]).output == DEFAULT_OUTPUT


def test_parse_args_output_override():
    assert parseArgs(["--output", "x.json"]).output == "x.json"
