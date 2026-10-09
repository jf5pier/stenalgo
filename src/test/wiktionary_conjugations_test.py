"""Unit tests for util/_wiktionaryconj.py (the page parser) and the file format of util/fetch_wiktionary_conjugations.py.
No network: the HTML is a hand-written excerpt of the structure of Conjugaison:français/créer."""
from util._wiktionaryconj import parseConjugationPage
from util.fetch_wiktionary_conjugations import HEADER, addPage, attestedTags, pruneToMissing, readOutput, writeOutput


def _row(pronoun: str, form: str, pronounIpa: str, ipa: str) -> str:
    return (f'<tr><td align="right">{pronoun}</td><td><a href="./{form}">{form}</a></td>'
            f'<td class="API">\\{pronounIpa}</td><td class="API"><span class="API">{ipa}</span>\\</td></tr>')


PAGE = (
    '<h3>Modes impersonnels</h3><table>'
    '<tr><th>Passé</th></tr>'
    '<tr><td>Infinitif</td><td></td><td>créer</td><td>\\kʁe.e\\</td><td>avoir</td><td>créé</td><td>\\a.vwaʁ kʁe.e\\</td></tr>'
    '<tr><td>Participe</td><td></td><td>créant</td><td>\\kʁe.ɑ̃\\</td><td></td><td>créé</td><td>\\kʁe.e\\</td></tr>'
    '</table><h3>Indicatif</h3><table><tr><th colspan="4">Présent</th></tr>'
    + _row("je", "crée", "ʒə", "kʁe") + _row("nous", "créons", "nu", "kʁe.ɔ̃")
    + '</table><table><tr><th colspan="4">Passé simple</th></tr>' + _row("tu", "créas", "ty", "kʁe.a")
    + '</table><table><tr><th colspan="4">Passé composé</th></tr>'
    '<tr><td>j’ai</td><td>créé</td><td class="API">\\ʒ‿e kʁe.e\\</td></tr></table>'
    '<h3>Subjonctif</h3><table><tr><th colspan="4">Présent</th></tr>' + _row("que je", "crée", "kə ʒə", "kʁe")
    + '</table><h3>Conditionnel</h3><table><tr><th colspan="4">Présent</th></tr>' + _row("nous", "créerions", "nu", "kʁe.ʁjɔ̃")
    + '</table><h3>Impératif</h3><table><tr><th>Présent</th></tr>'
    '<tr><td></td><td>crée</td><td>\\kʁe\\</td></tr><tr><td></td><td>créons</td><td>\\kʁe.ɔ̃\\</td></tr>'
    '<tr><td></td><td>créez</td><td>\\kʁe.e\\</td></tr></table>'
    '<table><tr><th>Masculin</th></tr><tr><td>créé\\kʁe.e\\</td><td>créés\\kʁe.e\\</td></tr></table>'
    '<table><tr><th>Féminin</th></tr><tr><td>créée\\kʁe.e\\</td><td>créées\\kʁe.e\\</td></tr></table>'
    # the pronominal conjugation repeats the headings and must be ignored
    '<h3>Modes impersonnels</h3><table><tr><th>Passé</th></tr>'
    '<tr><td>Infinitif</td><td>se</td><td>créer</td><td>\\sə kʁe.e\\</td><td>s’être</td><td>créé</td><td>\\x\\</td></tr></table>'
    '<h3>Indicatif</h3><table><tr><th colspan="4">Présent</th></tr>' + _row("je me", "crée", "ʒə mə", "WRONG")
)


class TestParseConjugationPage:

    def test_simple_forms_get_the_lexicon_tags(self):
        forms = set(parseConjugationPage(PAGE))
        assert ("ind:pre:1s", "crée", "kʁe") in forms
        assert ("ind:pre:1p", "créons", "kʁe.ɔ̃") in forms
        assert ("ind:pas:2s", "créas", "kʁe.a") in forms
        assert ("sub:pre:1s", "crée", "kʁe") in forms
        assert ("cnd:pre:1p", "créerions", "kʁe.ʁjɔ̃") in forms

    def test_imperative_rows_have_no_pronoun_and_are_read_in_order(self):
        forms = set(parseConjugationPage(PAGE))
        assert {("imp:pre:2s", "crée", "kʁe"), ("imp:pre:1p", "créons", "kʁe.ɔ̃"), ("imp:pre:2p", "créez", "kʁe.e")} <= forms

    def test_impersonal_forms_and_participle_tables(self):
        forms = set(parseConjugationPage(PAGE))
        assert ("inf", "créer", "kʁe.e") in forms
        assert ("par:pre", "créant", "kʁe.ɑ̃") in forms
        assert ("par:pas:ms", "créé", "kʁe.e") in forms
        assert {("par:pas:mp", "créés", "kʁe.e"), ("par:pas:fs", "créée", "kʁe.e"), ("par:pas:fp", "créées", "kʁe.e")} <= forms

    def test_compound_tenses_and_the_pronominal_group_are_left_out(self):
        forms = parseConjugationPage(PAGE)
        assert not any(ipa == "WRONG" or "kʁe.e" == ipa and tag == "ind:pas:1s" for tag, _o, ipa in forms)
        assert not any(ortho == "créé" and tag.startswith("ind") for tag, ortho, _i in forms)
        assert len([f for f in forms if f[0] == "inf"]) == 1

    def test_a_page_without_tables_gives_nothing(self):
        assert parseConjugationPage("<html><body><p>Page inexistante</p></body></html>") == []


class TestOutputFile:

    def test_round_trip_merges_homograph_tags_and_sorts(self, tmp_path):
        entries: dict[tuple[str, str, str], set[str]] = {}
        addPage(entries, "créer", [("sub:pre:3s", "crée", "kʁe"), ("ind:pre:1s", "crée", "kʁe"), ("inf", "créer", "kʁe.e")])
        addPage(entries, "aimer", [("inf", "aimer", "ɛ.me")])
        path = tmp_path / "w.tsv"
        assert writeOutput(entries, str(path)) == 3
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == HEADER
        assert lines[1:] == ["aimer\taimer\tinf\tɛ.me", "créer\tcrée\tind:pre:1s;sub:pre:3s\tkʁe", "créer\tcréer\tinf\tkʁe.e"]
        assert readOutput(str(path)) == entries


class TestMissingFormFiltering:

    def test_add_page_keeps_only_the_missing_tags(self):
        entries: dict[tuple[str, str, str], set[str]] = {}
        parsed = [("ind:pre:1s", "crée", "kʁe"), ("sub:pre:1s", "crée", "kʁe"), ("ind:pas:2s", "créas", "kʁe.a")]
        assert addPage(entries, "créer", parsed, {"sub:pre:1s", "ind:pas:2s"}) == 2
        assert entries == {("créer", "crée", "kʁe"): {"sub:pre:1s"}, ("créer", "créas", "kʁe.a"): {"ind:pas:2s"}}

    def test_prune_drops_attested_tags_rows_without_a_missing_tag_and_unknown_lemmas(self):
        entries = {("créer", "crée", "kʁe"): {"ind:pre:1s", "sub:pre:1s"}, ("créer", "créons", "kʁe.ɔ̃"): {"ind:pre:1p"},
                   ("aimer", "aime", "ɛm"): {"ind:pre:1s"}}
        assert pruneToMissing(entries, {"créer": {"sub:pre:1s"}}) == {("créer", "crée", "kʁe"): {"sub:pre:1s"}}

    def test_attested_and_missing_tags_come_from_mixte(self, tmp_path):
        mixte = tmp_path / "m.tsv"
        mixte.write_text("ortho\tphon\tlemme\tcgram\tgenre\tnombre\tinfover\n"
                         "aime\tEm\taimer\tVER\t\t\tind:pre:1s;ind:pre:3s;\n"
                         "aimé\teme\taimer\tVER\tm\ts\tpar:pas;\n"
                         "aimer\teme\taimer\tVER\t\t\tinf;\n"
                         "table\ttabl\ttable\tNOM\tf\ts\t\n", encoding="utf-8")
        assert attestedTags(str(mixte)) == {"aimer": {"ind:pre:1s", "ind:pre:3s", "par:pas:ms"}}
