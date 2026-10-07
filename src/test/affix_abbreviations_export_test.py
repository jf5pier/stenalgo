from util.export_affix_abbreviations import buildIndex, buildRuleIndex


def test_index_maps_spelling_and_long_outline_to_the_first_short_one():
    rows = [
        {"spelling": "arrête", "long": "a/Riet", "short": "Rwiejt"},
        {"spelling": "arrête", "long": "a/Riet/-k", "short": "Rwiejt/-k"},
        {"spelling": "arrête", "long": "a/Riet", "short": "other"},
        {"spelling": "amour", "long": "a/m@eR", "short": "mw@ejR"},
    ]
    assert buildIndex(rows) == {"arrête": {"a/Riet": "Rwiejt", "a/Riet/-k": "Rwiejt/-k"}, "amour": {"a/m@eR": "mw@ejR"}}


def test_rule_index_lists_the_distinct_ranks_of_a_spelling_ascending():
    rows = [
        {"spelling": "arrête", "rank": "3"},
        {"spelling": "arrête", "rank": "1"},
        {"spelling": "arrête", "rank": "3"},
        {"spelling": "amour", "rank": "2"},
    ]
    assert buildRuleIndex(rows) == {"arrête": [1, 3], "amour": [2]}
