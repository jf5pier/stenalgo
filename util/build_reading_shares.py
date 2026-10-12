"""
Builds the reading-share table (docs/MERGED_FEATURE_KEYS_PLAN.md, iteration 0): for every lexicon
ambiguity class, the observed share of each of its readings, so that a row's single frequency can be
split over its readings (decision D13).

A class is the set of readings of one (ortho, lemme, cgram) row of the theory's lexicons: its deduplicated `infover`
readings for VER/AUX (`imp:pre:2s;ind:pre:1s;ind:pre:2s` for `fais`), its gender/number cells for
NOM/ADJ (`nom:fs;nom:ms` for an epicene singular). Counts are pooled over every row of a class.

Sources, first one with at least --min-tokens tokens for the class wins:
  subtitles  French OpenSubtitles lines (verb classes only), the genre of the film frequency we weight
             by. No tagger handles imperatives (spaCy tags "Regarde !" Ind 3s), so readings come from a
             dialogue heuristic (subtitleLabel): subject clitic -> person, subjectless clause start or
             `-moi`/`-le` -> imperative, auxiliary before -> participle, `que` -> subjunctive possible.
             Ambiguity left by the heuristic (same person, several tenses or moods) is split with the
             UD-fitted reading weights. --validate measures the heuristic against the UD gold tags.
  ud-spoken  UD_French-ParisStories + UD_French-Rhapsodie gold tags.
  ud-all     the four treebanks (+ GSD, Sequoia).
  pooled     a Luce choice model fitted on the classes above: share proportional to a per-reading
             weight, restricted to the class's readings.

Inputs: ud-french/ (git clone --depth 1 of the four UD_French-* repos), opensubtitles-fr/sample.txt
(every 400th line of OPUS OpenSubtitles v2018 mono fr.txt.gz), both gitignored; resources/LexiqueMixte.tsv + LexiqueSynthetic.tsv (the theory's lexicons).
Output: resources/readingShares.tsv (class, reading, count, share, source); attribution in
resources/readingShares.NOTICE.md.

Run: python -m util.build_reading_shares [--ud-dir DIR] [--subtitles PATH] [--lexicons PATH...] [--out PATH]
     [--min-tokens N] [--validate]   (hand-run, rare)
"""
import argparse
import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

LEXICON_DEFAULTS = ["resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv"]
UD_DIR_DEFAULT = "ud-french"
SUBTITLES_DEFAULT = "opensubtitles-fr/sample.txt"
OUTPUT_DEFAULT = "resources/readingShares.tsv"
SPOKEN_TREEBANKS = ("ParisStories", "Rhapsodie")
WRITTEN_TREEBANKS = ("GSD", "Sequoia")
UPOS_TO_CGRAM = {"VERB": "VER", "AUX": "AUX", "NOUN": "NOM", "ADJ": "ADJ"}
VERB_CGRAMS = ("VER", "AUX")
NOMINAL_CGRAMS = ("NOM", "ADJ")

LexiqueKey = tuple[str, str, str]
ReadingClass = frozenset[str]
ReadingCounts = dict[str, float]  # reading -> count, fractional for the subtitles
ClassCounts = dict[ReadingClass, ReadingCounts]


def newClassCounts() -> ClassCounts:
    """An empty class -> reading -> count table that creates its entries on first use."""
    return defaultdict(lambda: defaultdict(float))


@dataclass(frozen=True)
class ReadingShare:
    """One row of the table: a reading's count and share within its class."""
    readingClass: str
    reading: str
    count: float
    share: float
    source: str


@dataclass(frozen=True)
class UdToken:
    """A UD word line: lowercased form, lemma, UPOS and the Lexique reading of its features (or None)."""
    form: str
    lemma: str
    upos: str
    reading: str | None


def classKey(readingClass: Iterable[str]) -> str:
    """The canonical text of a class: its readings sorted and joined by `;`."""
    return ";".join(sorted(readingClass))


def rowClass(cgram: str, genre: str, nombre: str, infover: str) -> ReadingClass | None:
    """The readings of one lexicon row, or None for a row outside VER/AUX/NOM/ADJ or without readings."""
    if cgram in VERB_CGRAMS:
        verbReadings = frozenset(r for r in infover.split(";") if r)
        return verbReadings or None
    if cgram in NOMINAL_CGRAMS:
        genders = [genre] if genre else ["m", "f"]
        numbers = [nombre] if nombre else ["s", "p"]
        return frozenset(f"nom:{g}{n}" for g in genders for n in numbers)
    return None


def loadLexiqueClasses(lexiconPaths: Iterable[str]) -> tuple[dict[LexiqueKey, ReadingClass], dict[LexiqueKey, float]]:
    """
    (lowercased ortho, lemme, cgram) -> class, the rows of one key united across the lexicons, and the film
    frequency (freqfilms2) of every key, all categories included. With the theory's lexicons (Mixte +
    Synthetic) the classes are the theory's reading sets: Lexique383's infover misses readings (`importe`
    lacks sub:pre:1s/3s, which Synthetic adds as rows of their own).
    """
    classes: dict[LexiqueKey, ReadingClass] = {}
    frequencies: dict[LexiqueKey, float] = defaultdict(float)
    for lexiconPath in lexiconPaths:
        loadLexiconRows(lexiconPath, classes, frequencies)
    return classes, dict(frequencies)


def loadLexiconRows(lexiconPath: str, classes: dict[LexiqueKey, ReadingClass],
                    frequencies: dict[LexiqueKey, float]) -> None:
    """Adds one Lexique-format TSV's rows to the classes and frequencies (see loadLexiqueClasses)."""
    with open(lexiconPath, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        col = {name: header.index(name)
               for name in ("ortho", "lemme", "cgram", "genre", "nombre", "infover", "freqfilms2")}
        for line in f:
            fields = line.rstrip("\n").split("\t")
            key = (fields[col["ortho"]].lower(), fields[col["lemme"]], fields[col["cgram"]])
            frequencies[key] += float(fields[col["freqfilms2"]] or 0)
            readingClass = rowClass(fields[col["cgram"]], fields[col["genre"]], fields[col["nombre"]],
                                    fields[col["infover"]])
            if readingClass is not None:
                classes[key] = classes.get(key, frozenset()) | readingClass


def parseFeats(feats: str) -> dict[str, str]:
    """UD FEATS `Key=Val|Key=Val` (or `_`) as a dict."""
    if feats == "_":
        return {}
    return dict(pair.split("=", 1) for pair in feats.split("|"))


UD_IND_TENSES = {"Pres": "pre", "Imp": "imp", "Past": "pas", "Fut": "fut"}
UD_SUB_TENSES = {"Pres": "pre", "Imp": "imp"}
UD_NUMBERS = {"Sing": "s", "Plur": "p"}
UD_GENDERS = {"Masc": "m", "Fem": "f"}


def udReading(upos: str, feats: str) -> str | None:
    """The Lexique reading of a UD token (`ind:pre:1s`, `par:pas`, `nom:fp`...), None when underspecified."""
    featMap = parseFeats(feats)
    if upos in ("VERB", "AUX"):
        verbForm = featMap.get("VerbForm", "")
        if verbForm == "Inf":
            return "inf"
        if verbForm == "Part":
            return {"Past": "par:pas", "Pres": "par:pre"}.get(featMap.get("Tense", ""))
        if verbForm != "Fin":
            return None
        person = featMap.get("Person", "")
        number = UD_NUMBERS.get(featMap.get("Number", ""), "")
        if person not in ("1", "2", "3") or not number:
            return None
        mood = featMap.get("Mood", "")
        tense = featMap.get("Tense", "Pres")
        if mood == "Ind" and tense in UD_IND_TENSES:
            return f"ind:{UD_IND_TENSES[tense]}:{person}{number}"
        if mood == "Sub" and tense in UD_SUB_TENSES:
            return f"sub:{UD_SUB_TENSES[tense]}:{person}{number}"
        if mood == "Cnd":
            return f"cnd:pre:{person}{number}"
        if mood == "Imp":
            return f"imp:pre:{person}{number}"
        return None
    if upos in ("NOUN", "ADJ"):
        gender = UD_GENDERS.get(featMap.get("Gender", ""), "")
        nominalNumber = UD_NUMBERS.get(featMap.get("Number", ""), "")
        return f"nom:{gender}{nominalNumber}" if gender and nominalNumber else None
    return None


def readUdSentences(conlluPath: Path) -> Iterator[list[UdToken]]:
    """The sentences of a CoNLL-U file as word lines (multiword ranges and empty nodes skipped)."""
    sentence: list[UdToken] = []
    with open(conlluPath, encoding="utf-8") as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 6:
                if not line.strip() and sentence:
                    yield sentence
                    sentence = []
                continue
            if "-" in fields[0] or "." in fields[0]:
                continue
            sentence.append(UdToken(fields[1].lower(), fields[2], fields[3], udReading(fields[3], fields[5])))
    if sentence:
        yield sentence


VERB_DOMINANCE = 0.8


class ClassIndex:
    """
    Lexique classes by (form, lemma, cgram), with a by-form fallback for an unknown lemma; and, for the
    untagged subtitles, the multi-reading verb classes of the forms whose film frequency is at least
    VERB_DOMINANCE that of a single verb lemma (`juge`, a noun first, and `suis`, être first, are left out).
    """

    def __init__(self, classes: dict[LexiqueKey, ReadingClass], frequencies: dict[LexiqueKey, float]) -> None:
        self.classes = classes
        self.byFormCgram: dict[tuple[str, str], set[ReadingClass]] = defaultdict(set)
        multiVerbLemmas: dict[str, set[str]] = defaultdict(set)
        for (ortho, lemme, cgram), readingClass in classes.items():
            self.byFormCgram[(ortho, cgram)].add(readingClass)
            if cgram in VERB_CGRAMS and len(readingClass) > 1:
                multiVerbLemmas[ortho].add(lemme)
        formTotals: dict[str, float] = defaultdict(float)
        for (ortho, _lemme, _cgram), frequency in frequencies.items():
            formTotals[ortho] += frequency
        self.verbClassesByForm: dict[str, set[ReadingClass]] = {}
        for ortho, lemmas in multiVerbLemmas.items():
            if len(lemmas) != 1:
                continue
            lemme = next(iter(lemmas))
            verbFrequency = sum(frequencies.get((ortho, lemme, cgram), 0.0) for cgram in VERB_CGRAMS)
            if verbFrequency >= VERB_DOMINANCE * formTotals[ortho]:
                self.verbClassesByForm[ortho] = {classes[(ortho, lemme, cgram)] for cgram in VERB_CGRAMS
                                                 if len(classes.get((ortho, lemme, cgram), frozenset())) > 1}

    def udClass(self, token: UdToken) -> ReadingClass | None:
        """The class of a UD token: exact lemma first, else the form's single class in that category."""
        cgram = UPOS_TO_CGRAM.get(token.upos)
        if cgram is None:
            return None
        exact = self.classes.get((token.form, token.lemma, cgram))
        if exact is not None:
            return exact
        candidates = self.byFormCgram.get((token.form, cgram), set())
        return next(iter(candidates)) if len(candidates) == 1 else None


# --- the subtitle heuristic -----------------------------------------------------------------------

TOKEN_RE = re.compile(
    r"(?:jusqu|lorsqu|puisqu|qu|[jtlmnsdc])'"
    r"|(?<=\w)-t-(?:il|elle|on|ils|elles)\b"
    r"|(?<=\w)-(?:je|tu|il|elle|on|nous|vous|ils|elles|moi|toi|le|la|les|lui|leur|en|y)\b"
    r"|(?<=\w)-[mt]'"
    r"|\w+"
    r"|[^\w\s]")
SUBJECT_PERSONS = {"je": "1s", "j'": "1s", "tu": "2s", "il": "3s", "elle": "3s", "on": "3s", "ça": "3s",
                   "cela": "3s", "ce": "3s", "c'": "3s", "ils": "3p", "elles": "3p", "qui": "3"}
INVERTED_SUBJECTS = {"-je": "1s", "-tu": "2s", "-il": "3s", "-elle": "3s", "-on": "3s", "-t-il": "3s",
                     "-t-elle": "3s", "-t-on": "3s", "-ils": "3p", "-elles": "3p", "-t-ils": "3p", "-t-elles": "3p"}
IMPERATIVE_OBJECTS = {"-moi", "-toi", "-le", "-la", "-les", "-lui", "-leur", "-en", "-y", "-m'", "-t'"}
PREVERBAL_CLITICS = {"ne", "n'", "me", "m'", "te", "t'", "se", "s'", "le", "la", "les", "l'", "lui", "leur", "y",
                     "en", "nous", "vous"}
CLAUSE_OPENERS = {"et", "mais", "alors", "donc", "puis", "ou", "oh", "ah", "eh", "hé", "hey", "bon", "oui", "non",
                  "ok", "okay", "si", "enfin", "allez", "tiens", "maintenant", "vite", "s'il", "plait", "plaît",
                  "chéri", "chérie", "maman", "papa", "monsieur", "madame"}
PARTICIPLE_ADVERBS = {"pas", "plus", "jamais", "rien", "déjà", "tout", "bien", "encore", "toujours", "vraiment",
                      "même", "trop", "presque", "aussi", "beaucoup", "mal", "juste", "enfin"}
AUXILIARY_FORMS = set(
    "ai as a avons avez ont avais avait avions aviez avaient aurai auras aura aurons aurez auront aurais aurait "
    "aurions auriez auraient aie aies ait ayons ayez aient eu avoir ayant suis es est sommes êtes sont étais "
    "était étions étiez étaient serai seras sera serons serez seront serais serait serions seriez seraient "
    "sois soit soyons soyez soient été être étant".split())


def tokenizeSubtitle(line: str) -> list[str]:
    """Lowercased tokens split like UD French: elisions, `-moi`/`-t-il` suffixes and punctuation apart."""
    return TOKEN_RE.findall(line.lower().replace("’", "'"))


COORDINATORS = {",", "et", "mais", "puis", "ou", "donc", "alors"}


def isBoundary(token: str) -> bool:
    """A clause start: punctuation (dialogue dash included) or an interjection/conjunction."""
    return token in CLAUSE_OPENERS or not (token[0].isalnum() or token.endswith("'"))


def coordinatedSubject(tokens: list[str], j: int) -> str | None:
    """
    After a coordinator or comma at tokens[j], the person of the nearest earlier subject clitic of the same
    sentence (`il entre et regarde`), None when the sentence has none before a strong boundary (`Bon, regarde`).
    """
    if tokens[j] not in COORDINATORS:
        return None
    for k in range(j - 1, -1, -1):
        if tokens[k] in SUBJECT_PERSONS and tokens[k] != "qui":
            return SUBJECT_PERSONS[tokens[k]]
        if isBoundary(tokens[k]) and tokens[k] not in COORDINATORS:
            return None
    return None


def subtitleLabel(tokens: list[str], i: int) -> str | None:
    """
    The heuristic reading label of the verb form tokens[i]: `imp`, `par`, a person (`1s`...`3p`, or `3` for a
    noun or `qui` subject), prefixed `que:` when a `que` precedes the subject; None when undecidable.
    """
    following = tokens[i + 1] if i + 1 < len(tokens) else ""
    if following in INVERTED_SUBJECTS:
        return INVERTED_SUBJECTS[following]
    if following in IMPERATIVE_OBJECTS:
        return "imp"
    j = i - 1
    while j >= 0 and tokens[j] in PARTICIPLE_ADVERBS:
        j -= 1
    if j >= 0 and tokens[j] in AUXILIARY_FORMS:
        return "par"
    j = i - 1
    while j >= 0 and tokens[j] in PREVERBAL_CLITICS:
        j -= 1
    leftmostClitic = tokens[j + 1] if j + 1 < i else ""
    if leftmostClitic in ("nous", "vous") and (j < 0 or isBoundary(tokens[j]) or tokens[j] in ("que", "qu'")):
        person = "1p" if leftmostClitic == "nous" else "2p"
    elif j < 0 or isBoundary(tokens[j]):
        return (coordinatedSubject(tokens, j) if j >= 0 else None) or "imp"
    elif tokens[j] in SUBJECT_PERSONS:
        person = SUBJECT_PERSONS[tokens[j]]
        j -= 1
    elif tokens[j] in ("que", "qu'"):
        return None
    else:
        person = "3"
        j -= 1
    return f"que:{person}" if j >= 0 and tokens[j] in ("que", "qu'") else person


def personOf(reading: str) -> str:
    """`ind:pre:3s` -> `3s`; empty for a non-finite reading."""
    parts = reading.split(":")
    return parts[2] if len(parts) == 3 else ""


def labelCandidates(label: str, readingClass: ReadingClass) -> list[str]:
    """The readings of the class a heuristic label allows."""
    if label == "imp":
        return sorted(r for r in readingClass if r.startswith("imp:"))
    if label == "par":
        return sorted(r for r in readingClass if r == "par:pas")
    afterQue = label.startswith("que:")
    person = label.removeprefix("que:")
    finite = [r for r in readingClass if not r.startswith(("imp:", "par:", "inf"))
              and personOf(r).startswith(person)]
    indicative = [r for r in finite if r.startswith(("ind:", "cnd:"))]
    return sorted(finite if afterQue or not indicative else indicative)


def splitByWeights(candidates: list[str], weights: dict[str, float]) -> dict[str, float]:
    """One token split over its candidate readings in proportion to the reading weights."""
    total = sum(weights.get(r, 0.0) for r in candidates)
    if total <= 0:
        return {r: 1.0 / len(candidates) for r in candidates}
    return {r: weights.get(r, 0.0) / total for r in candidates}


@dataclass(frozen=True)
class SplitWeights:
    """Reading weights that split a heuristic label's candidates: one set after `que`, one elsewhere."""
    plain: dict[str, float]
    afterQue: dict[str, float]

    def forLabel(self, label: str) -> dict[str, float]:
        """The weights for a label (`que:3s` -> afterQue)."""
        return self.afterQue if label.startswith("que:") else self.plain


def countSubtitles(subtitlePath: str, index: ClassIndex, weights: SplitWeights
                   ) -> tuple[ClassCounts, Counter[str]]:
    """Fractional reading counts per verb class from the subtitle lines, and a label tally."""
    counts = newClassCounts()
    tally: Counter[str] = Counter()
    with open(subtitlePath, encoding="utf-8") as f:
        for line in f:
            tokens = tokenizeSubtitle(line)
            for i, token in enumerate(tokens):
                verbClasses = index.verbClassesByForm.get(token)
                if not verbClasses:
                    continue
                label = subtitleLabel(tokens, i)
                if label is None:
                    tally["undecided"] += 1
                    continue
                tally[label.removeprefix("que:") if label in ("imp", "par") else "person"] += 1
                for readingClass in verbClasses:
                    candidates = labelCandidates(label, readingClass)
                    if not candidates:
                        tally["outside class"] += 1
                        continue
                    for reading, part in splitByWeights(candidates, weights.forLabel(label)).items():
                        counts[readingClass][reading] += part
    return counts, tally


# --- UD counts, the pooled model, the table -------------------------------------------------------

def udSentences(udDir: str, treebanks: Iterable[str]) -> Iterator[list[UdToken]]:
    """Every sentence of the named UD_French treebanks (a missing clone is skipped)."""
    for treebank in treebanks:
        for conllu in sorted(Path(udDir).glob(f"UD_French-{treebank}/*.conllu")) or sorted(
                Path(udDir).glob(f"{treebank}/*.conllu")):
            yield from readUdSentences(conllu)


def countUd(sentences: Iterable[list[UdToken]], index: ClassIndex
            ) -> tuple[ClassCounts, Counter[str]]:
    """Gold reading counts per class, and a tally of used / mismatched / unknown tokens."""
    counts = newClassCounts()
    tally: Counter[str] = Counter()
    for sentence in sentences:
        for token in sentence:
            if token.reading is None:
                continue
            readingClass = index.udClass(token)
            if readingClass is None:
                tally["unknown"] += 1
            elif token.reading not in readingClass:
                tally["mismatched"] += 1
            else:
                tally["used"] += 1
                counts[readingClass][token.reading] += 1
    return counts, tally


def fitLuceWeights(counts: ClassCounts, pseudoCount: float = 0.5,
                   iterations: int = 200) -> dict[str, float]:
    """
    Per-reading weights of a Luce choice model (share of reading r in class c = w_r / sum of w over c), fitted
    by minorization-maximization on the observed classes; every (class, reading) gets a pseudo-count.
    """
    observed = {c: n for c, n in counts.items() if len(c) > 1 and sum(n.values()) > 0}
    readings = sorted({r for c in observed for r in c})
    wins: dict[str, float] = defaultdict(float)
    for readingClass, classCounts in observed.items():
        for reading in readingClass:
            wins[reading] += classCounts.get(reading, 0.0) + pseudoCount
    weights = {r: 1.0 for r in readings}
    for _ in range(iterations):
        denominators: dict[str, float] = defaultdict(float)
        for readingClass, classCounts in observed.items():
            classTotal = sum(classCounts.values()) + pseudoCount * len(readingClass)
            classWeight = sum(weights[r] for r in readingClass)
            for reading in readingClass:
                denominators[reading] += classTotal / classWeight
        weights = {r: wins[r] / denominators[r] for r in readings}
        norm = sum(weights.values())
        weights = {r: w / norm for r, w in weights.items()}
    return weights


def buildTable(allClasses: Iterable[ReadingClass], tiers: list[tuple[str, ClassCounts]],
               minTokens: int) -> list[ReadingShare]:
    """The first tier with --min-tokens tokens per class, else the Luce model fitted on the chosen tiers."""
    chosen: dict[ReadingClass, tuple[str, ReadingCounts]] = {}
    for readingClass in allClasses:
        for source, tierCounts in tiers:
            classCounts = tierCounts.get(readingClass)
            if classCounts is not None and sum(classCounts.values()) >= minTokens:
                chosen[readingClass] = (source, classCounts)
                break
    pooled = fitLuceWeights({c: n for c, (_source, n) in chosen.items()})
    table: list[ReadingShare] = []
    for readingClass in sorted(set(allClasses), key=classKey):
        if readingClass in chosen:
            source, classCounts = chosen[readingClass]
            total = sum(classCounts.values())
            shares = {r: classCounts.get(r, 0.0) / total for r in readingClass}
        else:
            source = "pooled"
            classCounts = {}
            shares = splitByWeights(sorted(readingClass), pooled)
        for reading in sorted(readingClass):
            table.append(ReadingShare(classKey(readingClass), reading, classCounts.get(reading, 0.0), shares[reading], source))
    return table


def writeTable(table: list[ReadingShare], outputPath: str) -> None:
    """The TSV: class, reading, count (fractional for subtitles), share, source."""
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write("class\treading\tcount\tshare\tsource\n")
        for row in table:
            f.write(f"{row.readingClass}\t{row.reading}\t{row.count:.1f}\t{row.share:.6f}\t{row.source}\n")


def labelKind(reading: str) -> str:
    """Coarse kind of a gold reading for the validation table: imp, par, or ind/sub/cnd + person."""
    if reading.startswith(("imp:", "par:")):
        return reading[:3]
    return f"{reading[:3]}:{personOf(reading)}"


def labelledUdTokens(sentences: Iterable[list[UdToken]], index: ClassIndex
                     ) -> Iterator[tuple[UdToken, ReadingClass, str | None]]:
    """The UD verb tokens of multi-reading classes whose gold reading is in the class, with the heuristic label."""
    for sentence in sentences:
        forms = [t.form for t in sentence]
        for i, token in enumerate(sentence):
            readingClass = index.udClass(token)
            if token.reading is None or readingClass is None or len(readingClass) < 2 \
                    or token.upos not in ("VERB", "AUX") or token.reading not in readingClass:
                continue
            yield token, readingClass, subtitleLabel(forms, i)


def fitSplitWeights(sentences: Iterable[list[UdToken]], index: ClassIndex,
                    allCounts: ClassCounts) -> SplitWeights:
    """Luce weights on every UD token, and on the UD tokens the heuristic labels `que:` (the mood is open there)."""
    queCounts = newClassCounts()
    for token, readingClass, label in labelledUdTokens(sentences, index):
        if label is not None and label.startswith("que:") and token.reading is not None:
            queCounts[readingClass][token.reading] += 1
    return SplitWeights(fitLuceWeights(allCounts), fitLuceWeights(queCounts))


def validateHeuristic(sentences: Iterable[list[UdToken]], index: ClassIndex, weights: SplitWeights) -> None:
    """Runs subtitleLabel on UD sentences and prints, per gold kind, how the heuristic labelled it."""
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    for token, readingClass, label in labelledUdTokens(sentences, index):
        assert token.reading is not None
        if label is None:
            verdict = "undecided"
        else:
            candidates = labelCandidates(label, readingClass)
            verdict = ("right" if token.reading in candidates else f"wrong:{label.removeprefix('que:')}") \
                if candidates else "outside"
        confusion[labelKind(token.reading)][verdict] += 1
    print("\nHeuristic on UD gold (verb tokens of multi-reading classes): gold kind -> verdicts")
    for kind in sorted(confusion, key=lambda k: -sum(confusion[k].values())):
        row = confusion[kind]
        total = sum(row.values())
        detail = ", ".join(f"{v} {n}" for v, n in row.most_common(5))
        print(f"  {kind:10} {total:6}  right {row['right'] / total:6.1%}  ({detail})")


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ud-dir", default=UD_DIR_DEFAULT)
    parser.add_argument("--subtitles", default=SUBTITLES_DEFAULT)
    parser.add_argument("--lexicons", nargs="+", default=LEXICON_DEFAULTS)
    parser.add_argument("--out", default=OUTPUT_DEFAULT)
    parser.add_argument("--min-tokens", type=int, default=20)
    parser.add_argument("--validate", action="store_true", help="measure the subtitle heuristic on UD gold tags")
    args = parser.parse_args()

    index = ClassIndex(*loadLexiqueClasses(args.lexicons))
    spokenCounts, spokenTally = countUd(udSentences(args.ud_dir, SPOKEN_TREEBANKS), index)
    allCounts, allTally = countUd(udSentences(args.ud_dir, SPOKEN_TREEBANKS + WRITTEN_TREEBANKS), index)
    udWeights = fitSplitWeights(udSentences(args.ud_dir, SPOKEN_TREEBANKS + WRITTEN_TREEBANKS), index, allCounts)
    if args.validate:
        validateHeuristic(udSentences(args.ud_dir, SPOKEN_TREEBANKS), index, udWeights)
        validateHeuristic(udSentences(args.ud_dir, WRITTEN_TREEBANKS), index, udWeights)
    subtitleCounts, subtitleTally = countSubtitles(args.subtitles, index, udWeights)

    allClasses = set(index.classes.values())
    table = buildTable(allClasses, [("subtitles", subtitleCounts), ("ud-spoken", spokenCounts),
                                    ("ud-all", allCounts)], args.min_tokens)
    writeTable(table, args.out)

    multi = {row.readingClass: row.source for row in table if ";" in row.readingClass}
    print(f"\nUD tokens (spoken): {dict(spokenTally)}; (all): {dict(allTally)}")
    print(f"Subtitle verb tokens: {dict(subtitleTally)}")
    print(f"Classes: {len(allClasses)}, multi-reading {len(multi)} by source {dict(Counter(multi.values()))}")
    print(f"Wrote {len(table)} rows to {args.out}")
    for form, lemma in (("dis", "dire"), ("fais", "faire"), ("regarde", "regarder"), ("finis", "finir"),
                        ("sois", "être"), ("viens", "venir"), ("finit", "finir"), ("petite", "petit")):
        cgram = "ADJ" if form == "petite" else "VER"
        readingClass = index.classes.get((form, lemma, cgram))
        if readingClass is None:
            continue
        rows = [row for row in table if row.readingClass == classKey(readingClass)]
        print(f"  {form:8} [{rows[0].source}] " + "  ".join(f"{r.reading} {r.share:.3f}" for r in rows))


if __name__ == "__main__":
    main()
