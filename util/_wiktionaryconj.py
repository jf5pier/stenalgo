"""
Parser for the French Wiktionary conjugation pages (https://fr.wiktionary.org/wiki/Conjugaison:français/<verbe>), the
HTML returned by the REST endpoint /api/rest_v1/page/html/. Standard library only.

parseConjugationPage(html) -> list of (tag, ortho, ipa): one entry per SIMPLE form the page prints with its own
pronunciation, tag in the lexicon's infoVerb vocabulary (ind:pre:1s, cnd:pre:3p, imp:pre:2s, par:pas, inf ...).
Compound tenses (passé composé, plus-que-parfait ...) print one combined pronunciation for auxiliary + participle
and are left out. Only the first (non pronominal) group of tables is read.

Content of fr.wiktionary.org is CC BY-SA 4.0 (see resources/wiktionaryVerbPronunciations.NOTICE.md).
"""
import re
from html.parser import HTMLParser

MOOD_CODES = {"Indicatif": "ind", "Subjonctif": "sub", "Conditionnel": "cnd", "Impératif": "imp"}
TENSE_CODES = {
    ("ind", "Présent"): "pre", ("ind", "Imparfait"): "imp", ("ind", "Passé simple"): "pas", ("ind", "Futur simple"): "fut",
    ("ind", "Futur"): "fut", ("sub", "Présent"): "pre", ("sub", "Imparfait"): "imp",
    ("cnd", "Présent"): "pre", ("imp", "Présent"): "pre",
}
PERSON_BY_PRONOUN = {"je": "1s", "j’": "1s", "j'": "1s", "tu": "2s", "il/elle/on": "3s", "il": "3s", "nous": "1p",
                     "vous": "2p", "ils/elles": "3p", "ils": "3p"}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").replace(" ", " ")).strip()


def _personOf(pronounCell: str, mood: str) -> str | None:
    words = _clean(pronounCell).replace("que ", "").replace("qu’", "").replace("qu'", "")
    if mood == "imp":
        return {"tu": "2s", "nous": "1p", "vous": "2p"}.get(words)
    return PERSON_BY_PRONOUN.get(words)


class _Rows(HTMLParser):
    """Collects (section heading h3, last th text, [cell texts], [cell classes]) for every table row."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[str, str, list[str], list[str]]] = []
        self._heading = ""
        self._th = ""
        self._cells: list[str] = []
        self._classes: list[str] = []
        self._buffer: list[str] | None = None
        self._bufferTag = ""
        self._inRow = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("h3", "th", "td"):
            self._buffer, self._bufferTag = [], tag
            self._cellClass = dict(attrs).get("class") or ""
        elif tag == "tr":
            self._inRow, self._cells, self._classes = True, [], []

    def handle_data(self, data: str) -> None:
        if self._buffer is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self._bufferTag and self._buffer is not None:
            text = _clean("".join(self._buffer))
            if tag == "h3":
                self._heading = text
            elif tag == "th":
                self._th = text
            else:
                self._cells.append(text)
                self._classes.append(self._cellClass)
            self._buffer, self._bufferTag = None, ""
        elif tag == "tr" and self._inRow:
            if self._cells:
                self.rows.append((self._heading, self._th, self._cells, self._classes))
            self._inRow = False


def _ipaOf(cell: str) -> str:
    return cell.strip("\\ ").strip()


def parseConjugationPage(html: str) -> list[tuple[str, str, str]]:
    parser = _Rows()
    parser.feed(html)
    out: list[tuple[str, str, str]] = []
    impersonal = 0
    previousHeading = ""
    imperativeRow = 0
    for heading, th, cells, classes in parser.rows:
        if heading == "Modes impersonnels" and previousHeading != heading:
            impersonal += 1
        if heading == "Impératif" and previousHeading != heading:
            imperativeRow = 0
        previousHeading = heading
        if impersonal > 1:
            break  # the second group is the pronominal conjugation
        mood = MOOD_CODES.get(heading)
        if heading == "Modes impersonnels" and len(cells) == 7:
            out.extend(_impersonal(cells))
        elif mood == "imp" and th == "Présent" and len(cells) == 3 and cells[0] == "":
            person = ("2s", "1p", "2p")[imperativeRow] if imperativeRow < 3 else None
            imperativeRow += 1
            if person and cells[1]:
                out.append((f"imp:pre:{person}", cells[1], _ipaOf(cells[2])))
        elif th in ("Masculin", "Féminin") and len(cells) == 2:
            gender = "m" if th == "Masculin" else "f"
            for number, cell in zip("sp", cells):
                match = re.fullmatch(r"(\S+)\\(.+)\\", cell)
                if match:
                    out.append((f"par:pas:{gender}{number}", match.group(1), match.group(2).strip()))
        elif mood is not None and len(cells) == 4 and "API" in classes[3]:
            tense = TENSE_CODES.get((mood, th))
            person = _personOf(cells[0], mood)
            if tense and person and cells[1]:
                out.append((f"{mood}:{tense}:{person}", cells[1], _ipaOf(cells[3])))
    return out


def _impersonal(cells: list[str]) -> list[tuple[str, str, str]]:
    """The seven-cell rows of "Modes impersonnels": label, (preposition), spelling, pronunciation, then the
    compound form (auxiliary, past participle, pronunciation)."""
    label = cells[0]
    if label == "Infinitif" and cells[2]:
        return [("inf", cells[2], _ipaOf(cells[3]))]
    if label == "Participe":
        found = []
        if cells[2]:
            found.append(("par:pre", cells[2], _ipaOf(cells[3])))
        if cells[5]:
            found.append(("par:pas:ms", cells[5], _ipaOf(cells[6])))
        return found
    return []
