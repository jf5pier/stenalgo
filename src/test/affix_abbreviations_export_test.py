from util.export_affix_abbreviations import buildIndex


def test_index_maps_spelling_and_long_outline_to_the_first_short_one():
    rows = [
        {"spelling": "arrête", "long": "a/Riet", "short": "Rwiejt"},
        {"spelling": "arrête", "long": "a/Riet/-k", "short": "Rwiejt/-k"},
        {"spelling": "arrête", "long": "a/Riet", "short": "other"},
        {"spelling": "amour", "long": "a/m@eR", "short": "mw@ejR"},
    ]
    assert buildIndex(rows) == {"arrête": {"a/Riet": "Rwiejt", "a/Riet/-k": "Rwiejt/-k"}, "amour": {"a/m@eR": "mw@ejR"}}
