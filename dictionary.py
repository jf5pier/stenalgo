#!/usr/bin/env python
# coding: utf-8
#
# This class provides reads a converted Lexique version 383 [1,2] that has its
# syllabification redone using graphen-phonemes pairs from Lexique infra[3].
#
# The output is
#
# 1. New, B., Pallier, C., Brysbaert, M., Ferrand, L. (2004)
#  Lexique 2 : A New French Lexical Database.
#  Behavior Research Methods, Instruments, & Computers, 36 (3), 516-524.
#  doi.org/10.3758/BF03195598
# 2. New, B., Brysbaert, M., Veronis, J., & Pallier, C. (2007).
#  The use of film subtitles to estimate word frequencies.
#  Applied Psycholinguistics, 28(4), 661-677.
#  doi.org/10.1017/S014271640707035X
# 3. Gimenes, M., Perret, C., & New, B. (2020).
#  Lexique-Infra: grapheme-phoneme, phoneme-grapheme regularity, consistency,
#  and other sublexical statistics for 137,717 polysyllabic French words.
#  Behavior Research Methods. doi.org/10.3758/s13428-020-01396-2
#
import csv
import json
import os
import subprocess
import time
from copy import deepcopy

from src.grammar import Phoneme, Syllable, SyllableCollection
from src.word import GramCat, Word
from typing import Any, Callable
from src.keyboard import Keyboard, Strokes
from src.ambiguitychecker import (
    buildExtraInducedStrokes,
    buildFinalInducedStrokes,
    buildKeypressGroupExtraAlternates,
    buildKeypressGroupToWords,
    buildWordsByOrthoLemme,
    buildWordToStrokes,
    composeReservedKeyStrokes,
    loadReform1990DoubletPairs,
    realizeKeypressGroupsAsExtraStroke,
    resolvePreferredKeysByGroup,
)


from tqdm import tqdm
import sys

from util._timing import recordTiming


def printVerbose(word: str, msg: list[Any]):
    # return
    if word in []:  # ["soleil"] :
        print(word, " :\n", " ".join(map(str, msg)))


class Dictionary:
    words: list[Word]
    wordsByOrtho: dict[str, list[Word]]
    wordsByLemme: dict[str, list[Word]]
    stemmOfLemme: dict[str, list[tuple[str, int]]]
    frequentWords: list[str]
    nbFrequentWords: int = 200
    totalFrequencies: float = 0.0
    frequentWordsFrequencies: float = 0.0
    wordSources: list[str] = [
        "resources/LexiqueMixte.tsv",
        "resources/LexiqueSynthetic.tsv",
    ]
    frequentWordsFile: str = "resources/top500_film.txt"
    syllableCollection: SyllableCollection
    syllabicAmbiguity: dict[str, dict[tuple[str, str], float]]
    lexicalAmbiguity: dict[str, dict[tuple[str, str], float]]
    syllabicPartAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]]

    def __init__(self) -> None:
        self.syllableCollection = SyllableCollection()
        self.wordsByOrtho = {}
        self.wordsByLemme = {}
        self.stemmOfLemme = {}
        self.frequentWords = []
        self.syllableClass: type = Syllable
        self.syllabicAmbiguity = {
        "onset": {}, "nucleus": {}, "coda": {}}
        self.lexicalAmbiguity = {
        "onset": {}, "nucleus": {}, "coda": {}}
        self.syllabicPartAmbiguity = {
        "onset": {}, "nucleus": {}, "coda": {}}

        self.words = self.readCorpus()

    def readCorpus(self) -> list[Word]:
        words : list[Word] = []
        with open(self.frequentWordsFile) as fw:
            self.totalFrequencies = float(
                fw.readline().strip().split("\t")[-1])
            for line in fw.readlines()[:self.nbFrequentWords]:
                ls = line.strip().split("\t")
                self.frequentWords.append(ls[0])
                self.frequentWordsFrequencies += float(ls[1])
        excludedWords: list[str] = []
        if os.path.exists("excluded_words.txt"):
            with open("excluded_words.txt") as ef:
                excludedWords = [l.strip() for l in ef.readlines()
                                            if l.strip() != '' and l.strip()[0] != '#']

        # Same identity as Word.__post_init__'s _hash (ortho, phonology, lemme, gramCat,
        # gender, number): a later source row (e.g. a LexiqueSynthetic paradigm-completion
        # row) matching an already-loaded Word is the SAME homograph, just with a reading
        # the earlier source's row didn't have -- it gets folded into that Word's infoVerb
        # (Word.mergeInfoVerb) instead of becoming a second, separate Word instance, exactly
        # how Lexique383 already represents a common verb's several readings in one row.
        wordByIdentity: dict[tuple[str, str, str, str, str | None, str | None], Word] = {}
        mergeCount = 0

        for wordSource in self.wordSources:
            if not os.path.exists(wordSource):
                continue
            with open(wordSource) as f:
                corpus = csv.DictReader(f, delimiter='\t')

                for corpusWord in tqdm(corpus, desc=f"Reading {wordSource}", unit=" words"):
                    if corpusWord["ortho"] is not None \
                            and corpusWord["ortho"][0] != "#" \
                            and corpusWord["ortho"] not in excludedWords :
                        gender = corpusWord["genre"] if corpusWord["genre"] != '' else None
                        number = corpusWord["nombre"] if corpusWord["nombre"] != '' else None
                        infoVerb = corpusWord["infover"] if corpusWord["infover"] != '' else None

                        identity = (corpusWord["ortho"], corpusWord["phon"], corpusWord["lemme"],
                                    corpusWord["cgram"], gender, number)
                        existingWord = wordByIdentity.get(identity)
                        if existingWord is not None:
                            if infoVerb is not None:
                                existingWord.mergeInfoVerb(infoVerb)
                                mergeCount += 1
                            continue

                        word: Word = Word(
                            ortho = corpusWord["ortho"],
                            phonology = corpusWord["phon"],
                            lemme = corpusWord["lemme"],
                            gramCat = GramCat[corpusWord["cgram"]],
                                # if corpusWord["cgram"] != '' else None,
                            orthoGramCat = [GramCat[gc] for gc in
                                corpusWord["cgramortho"].split(",")],
                            gender = gender,
                            number = number,
                            infoVerb = infoVerb,
                            rawSyllCV = corpusWord["syll_cv"],
                            rawOrthosyllCV = corpusWord["orthosyll_cv"],
                            frequencyBook = float(corpusWord["freqlivres"]),
                            frequencyFilm = float(corpusWord["freqfilms2"])
                            )
                        words.append(word)
                        wordByIdentity[identity] = word

                        lemmeGroup = self.wordsByLemme.get(word.lemme,
                                                           deepcopy([])) + [word]
                        self.wordsByLemme[word.lemme] = lemmeGroup

                        sameOrtho = self.wordsByOrtho.get(corpusWord["ortho"],
                                                             deepcopy([])) + [word]
                        self.wordsByOrtho[corpusWord["ortho"]] = sameOrtho
        print(f"readCorpus: {mergeCount} infoVerb merges fired (identity-dedup, "
              f"Word.mergeInfoVerb) across {len(words)} distinct Word instances.")
        return words

    def analyseSyllabification(self) -> None:
        print("Analyzing syllabification...")
        self.words.sort(key=lambda x: x.frequency, reverse=True)
        for word in tqdm(self.words, unit=" words", ascii=True, ncols=80):
            # Remove the frequent words from syllable frequency statistics
            frequency = word.frequency if word.ortho not in self.frequentWords else 0.0
            syllable_names = word.phonemesToSyllableNames(withSilent=False)
            spellings = word.graphemsToSyllables(withSilent=False)
            for (syllable_name, spelling) in zip(syllable_names, spellings):
                _ = self.syllableCollection.updateSyllable(
                    syllable_name, spelling, frequency, word)

        Syllable.sortPhonemesCollections()

    def analyseAmbiguities(self) -> None:
        """
        Analyse the syllabic ambiguities in the syllable collection.
        """
        print("Analyzing syllabic ambiguities...")
        self.syllabicAmbiguity["onset"], self.syllabicAmbiguity["nucleus"], self.syllabicAmbiguity["coda"] = \
            self.syllableCollection.analysePhonemSyllabicAmbiguity()

        print("Analyzing lexical ambiguities at the phoneme level...")
        self.lexicalAmbiguity["onset"], self.lexicalAmbiguity["nucleus"], self.lexicalAmbiguity["coda"] = \
            self.syllableCollection.analysePhonemeLexicalAmbiguity()

        print("Analyzing lexical ambiguities at the syllabic part level...")
        self.syllabicPartAmbiguity["onset"], self.syllabicPartAmbiguity["nucleus"], self.syllabicPartAmbiguity["coda"] = \
            self.syllableCollection.analyseMultiphonemeLexicalAmbiguity_serial()

    def printSyllabificationStats(self) -> None:
        Syllable.printTopPhonemes()
#        self.sylCol.printTopSyllables(20)
#        Syllable.printTopPhonemesPerPosition()
#        Syllable.printTopPhonemesPerInvPosition()
        Syllable.printTopBiphonemes(5)
        Syllable.printOptimizedBiphonemeOrder()
        Syllable.printOptimizedBiphonemeOrderScore()

        self.syllableCollection.printAmbiguityStats(self.syllabicAmbiguity, "Syllabic")
        self.syllableCollection.printAmbiguityStats(self.lexicalAmbiguity, "Lexical")
        self.syllableCollection.printSyllabicAmbiguityStats(self.syllabicPartAmbiguity, "Lexical")

    def generateBaseKeymap(self, keyboard: Keyboard) -> None:
        """ 
        Generates a keymap of the different phonemes by trying to minimize ambiguities and 
        maximize the number of keystrokes that are in the right order to spell the words phonetically.
        """
        
        def _greadyAssignKeymapPartition(keyboard: Keyboard, syllabicPart: str) -> list[str]:
            phonemeCol = Syllable.phonemeCollectionByPart(syllabicPart)
            biphonemeCol = Syllable.biphonemeCollectionByPart(syllabicPart)
            singleKeys  = keyboard.getPossibleStrokes(syllabicPart, 1)
            nbSingleKeys = len(singleKeys)
            sortedPhonemes = sorted(phonemeCol.phonemes, reverse=True)
            #print("syllabicPart", syllabicPart, "sortedPhonemes", sortedPhonemes, "default", 
            #      Phoneme.phonemesByPart[syllabicPart], "bestPermutation", biphonemeCol.bestPermutation)
            singleKeyTopPhonemes = sortedPhonemes[:nbSingleKeys]
            
            excludedPhonemes: str = "".join(list(map(lambda p: p.name,
                filter(lambda p: p.name not in biphonemeCol.bestPermutation, sortedPhonemes)))
            )

            # Assign single keys to the most frequent phonemes, in the order of the best permutation
            for phoneme in biphonemeCol.bestPermutation + excludedPhonemes:
                if phoneme in singleKeyTopPhonemes:
                    keyboard.addToLayout(singleKeys.pop(0), phoneme, Syllable.getSortedPhonemesNames(syllabicPart))
                    #keyboard.addToLayout(singleKeys.pop(0), phoneme)


            # Keys not assigned to a single-key strope
            multiKeyPhonemes = sortedPhonemes[nbSingleKeys:]
            multikeys = keyboard.getPossibleStrokes(syllabicPart, 2) + \
                                keyboard.getPossibleStrokes(syllabicPart, 3) +  \
                                keyboard.getPossibleStrokes(syllabicPart, 4)

            keyOveruse: dict[int, int] = {} # Try to prevent overusing some keys
            MaxOveruse = 2  # Maximum number of times a key can be used for a phoneme in a multi-key assignment
            unassignedPhonemes: list[str] = []
            for phoneme in biphonemeCol.bestPermutation + excludedPhonemes:
                if phoneme in multiKeyPhonemes:
                    assigned = False
                    while len(multikeys) > 0:
                        maxUse = max(list(map(lambda k : keyOveruse.get(k, 0), multikeys[0])))
                        if maxUse >= MaxOveruse +2*(len(multikeys[0])-2):
                            _ = multikeys.pop(0)
                        else:
                            for key in multikeys[0]:
                                keyOveruse[key] = keyOveruse.get(key, 0) + 1
                            #print("Assigning", phoneme, "to", multikeys[0])
                            keyboard.addToLayout(multikeys.pop(0), phoneme, Syllable.getSortedPhonemesNames(syllabicPart))
                            #keyboard.addToLayout(multikeys.pop(0), phoneme)
                            assigned = True
                            break

                    if not assigned:
                        unassignedPhonemes.append(phoneme)
            return unassignedPhonemes[:]


        # Start by assigning greedily the most frequent phonemes to the most accessible keys which
        # are the single keys per phoneme.
        for syllabicPart in ["onset", "nucleus", "coda"]:
            unassigned = _greadyAssignKeymapPartition(keyboard, syllabicPart)
            if len(unassigned) > 0:
                print(f"Unassigned phonemes in {syllabicPart= }:", "".join(unassigned))

            # get low ambiguity phonemes to pair with unassigned phonemes
            for phonemeName in unassigned:
                lowAmbiguityPhonemes = self.getLowAmbiguityPhonemes(
                    phonemeName, syllabicPart, self.lexicalAmbiguity)
                phonemeIsAssigned = False
                for phonemePair in lowAmbiguityPhonemes:
                    # find if the low ambiguity phonemes are already paired to avoid having more than 2 phonemes per stroke
                    otherPhoneme = phonemePair[0][1] if phonemePair[0][0] == phonemeName else phonemePair[0][0]
                    for otherStrokeOfPhoneme in keyboard.getStrokesOfPhoneme(otherPhoneme, syllabicPart):
                        phonemeSharingStroke = keyboard.getPhonemesOfStroke(otherStrokeOfPhoneme)
                        if len(phonemeSharingStroke) == 1 : # Not over-sharing the stroke
                            print("Assigning", phonemeName, "to", otherStrokeOfPhoneme, "already assigned to", otherPhoneme)
                            keyboard.addToLayout(otherStrokeOfPhoneme, phonemeName)
                            phonemeIsAssigned = True
                            break
                    if phonemeIsAssigned:
                        break
        
        keyboard.printLayout()

    def getLowAmbiguityPhonemes(self, phonemeName: str, syllabicPart: str,
                                ambiguity: dict[str, dict[tuple[str, str], float]]) -> list[tuple[tuple[str, str], float]]:
        """
        Returns a list of phoneme pairs sorted by lowest ambiguity containing a given phoneme name.
        """
        biphonemeAmbiguity = list(filter(lambda p: p[0][0] == phonemeName or p[0][1] == phonemeName, 
                                          ambiguity[syllabicPart].items()))
        return sorted(biphonemeAmbiguity, key=lambda x: x[1], reverse=False)

    def buildPhoneticTheory(self, keyboard: Keyboard) -> dict[Strokes, list[Word]]:
        phoneticTheory: dict[tuple[tuple[int, ...], ...], list[Word]] = {}
        for word in tqdm(self.words, desc="Building the phonetic theory", unit=" words", ascii=True, ncols=80):
            syllableNames = word.phonemesToSyllableNames(withSilent=False)
            syllableStrokes: tuple[tuple[int, ...], ...] = tuple(keyboard.getStrokeOfSyllableByPart(
                self.syllableCollection.syllable_names[syllableName].phonemeNamesByPart())
                for syllableName in syllableNames)
            if syllableStrokes not in phoneticTheory:
                phoneticTheory[syllableStrokes] = []
            phoneticTheory[syllableStrokes].append(word)
        return phoneticTheory

    def writePhoneticTheory(self, phoneticTheory: dict[Strokes, list[Word]], keyboard: Keyboard, filename: str) -> None:
        with open(filename, "w") as f:
            _ = f.write("strokes\twords\n")
            maxAmbiguity = 0
            maxAmbiguityWords = []
            maxFrequencyAmbiguity = 0.0
            maxFrequencyAmbiguityWords = []
            maxFrequencyAmbiguityStrokes= ()
            for syllableStrokes, words in phoneticTheory.items():
                strokeString = keyboard.strokesToString(syllableStrokes)
                wordOrthos = sorted(list(set(map(lambda w: w.ortho, words))))
                sumFrequencies: float = sum(map(lambda w: w.frequency, words))
                if len(wordOrthos) > maxAmbiguity:
                    maxAmbiguity = len(wordOrthos)
                    maxAmbiguityWords = wordOrthos
                if sumFrequencies > maxFrequencyAmbiguity:
                    maxFrequencyAmbiguity = sumFrequencies
                    maxFrequencyAmbiguityWords = wordOrthos
                    maxFrequencyAmbiguityStrokes = syllableStrokes
                _ = f.write(f"{strokeString}\t{','.join(wordOrthos)}\n")
            
            print("Max nb word ambiguity:", maxAmbiguity, "for words", maxAmbiguityWords)
            print("Max frequency ambiguity:", maxFrequencyAmbiguity, "for words",
                  maxFrequencyAmbiguityWords, "\n strokes: ", maxFrequencyAmbiguityStrokes)

    def buildDisambiguatedTheory(
        self, phoneticTheory: dict[Strokes, list[Word]], keyboard: Keyboard,
        keypressGroupsPath: str = "keypress_groups.json",
        resolvedPressSetsPath: str = "resolved_press_sets.json",
    ) -> dict[Word, list[Strokes]]:
        """
        The disambiguated theory: every word's final resolved Strokes -- a LIST, since
        a self-homograph spelling (more than one valid reading, e.g. "calmez" =
        impératif or indicatif présent -- see src.elicitation.resolveGroupPressSets)
        has more than one independently-valid stroke, each identifying it without the
        others. Index 0 is always the word's PRIMARY stroke: the phonetic theory
        (buildPhoneticTheory) composed with the
        same-lemma coda-bank realization of Discriminating-Feature Stroke Realization
        (Realization Phase) (src.ambiguitychecker.realizeKeypressGroupsAsExtraStroke)
        and the star/hash mark reserved keys of Different-Lemma or Grammatical-Category
        Disambiguation (S7) (src.ambiguitychecker.composeReservedKeyStrokes) on top, its
        first mark key pressed together with the word's last phoneme stroke. Any further
        entries are the word's OTHER readings (src.ambiguitychecker.buildExtraInducedStrokes),
        reusing whatever physical keys the primary pass already decided -- NOT run
        through S7 (that stage isn't wired into a self-homograph's alternates yet, the
        same scope boundary ROADMAP.md already notes for the star/hash mark track
        generally). Requires `keypressGroupsPath` (Discriminating-Feature Grouping
        (Grouping Phase), `python -m util.build_keypress_groups`) and
        `resolvedPressSetsPath` (Discriminating-Feature Elicitation (Elicitation Phase),
        `python -m src.elicitation`) to already exist.
        """
        with open(keypressGroupsPath, encoding="utf-8") as f:
            keypressGroups = json.load(f)
        markersByKeypress = {
            int(groupId): frozenset(markers) for groupId, markers in keypressGroups["markersByKeypress"].items()
        }
        with open(resolvedPressSetsPath, encoding="utf-8") as f:
            resolvedGroups = json.load(f)

        wordToStrokes = buildWordToStrokes(phoneticTheory)
        wordsByOrthoLemme = buildWordsByOrthoLemme(phoneticTheory)
        groupToWords = buildKeypressGroupToWords(resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        extraGroupSetsByWord = buildKeypressGroupExtraAlternates(
            resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme
        )
        preferredKeysByGroup = resolvePreferredKeysByGroup(markersByKeypress)
        assignment = realizeKeypressGroupsAsExtraStroke(
            groupToWords, phoneticTheory, keyboard,
            extraGroupSetsByWord=extraGroupSetsByWord, preferredKeysByGroup=preferredKeysByGroup,
        )
        finalInduced = buildFinalInducedStrokes(phoneticTheory, groupToWords, assignment)
        primaryComposed = composeReservedKeyStrokes(
            finalInduced, loadReform1990DoubletPairs(),
            phonemeStrokeCounts={word: len(strokes) for word, strokes in wordToStrokes.items()},
        )
        extraByWord = buildExtraInducedStrokes(phoneticTheory, assignment, extraGroupSetsByWord)
        return {word: [strokes] + extraByWord.get(word, []) for word, strokes in primaryComposed.items()}

    def writeDisambiguatedTheory(
        self, phoneticTheory: dict[Strokes, list[Word]], disambiguatedTheory: dict[Word, list[Strokes]],
        keyboard: Keyboard, filename: str,
    ) -> None:
        """
        Writes `filename`: one row per (word, reading) -- a self-homograph word (see
        `buildDisambiguatedTheory`) gets one row per independently-valid stroke, all sharing the
        same ortho/lemme/gramCat/base-strokes columns and differing only in
        `extraStrokes`. Those extra strokes use coda-bank and reserved
        (STAR_KEY/HASH_KEY) keys that carry no single assigned phoneme, so
        `strokesToString` (phoneme-layer only) can't render them -- they're written as
        raw key-index tuples instead, same as `build_realization_report.py` already
        reports `chosenKeys`.
        """
        wordToStrokes = buildWordToStrokes(phoneticTheory)
        with open(filename, "w") as f:
            _ = f.write("ortho\tlemme\tgramCat\tstrokes\textraStrokes\n")
            for word in sorted(disambiguatedTheory, key=lambda w: (w.lemme, w.gramCat.name, w.ortho)):
                baseStrokes = wordToStrokes[word]
                strokeString = keyboard.strokesToString(baseStrokes)
                for fullStrokes in disambiguatedTheory[word]:
                    # A */# mark's first symbol is pressed with the last phoneme stroke
                    # (composeReservedKeyStrokes): written as a leading "+keys" element.
                    mergedKeys = sorted(set(fullStrokes[len(baseStrokes) - 1]) - set(baseStrokes[-1]))
                    extraStrokes = fullStrokes[len(baseStrokes):]
                    extraString = "/".join(
                        ([f"+{','.join(str(key) for key in mergedKeys)}"] if mergedKeys else [])
                        + [",".join(str(key) for key in stroke) for stroke in extraStrokes]
                    )
                    _ = f.write(f"{word.ortho}\t{word.lemme}\t{word.gramCat.name}\t{strokeString}\t{extraString}\n")

    def writeConstrainFiles(self, phonemesOrderFile: str = "phoneme_order.csv",
                            multiPhonemeAmbiguityFile: str = "multi_phoneme_ambiguity.csv") -> None:

        with open(phonemesOrderFile, "w") as f:
            for phonemes, part in [(Phoneme.consonantPhonemes, "onset"),
                                   (Phoneme.nucleusPhonemes, "nucleus"),
                                   (Phoneme.consonantPhonemes, "coda")]:
                pairwisescore = Syllable.biphonemeColByPart[part].pairwiseBiphonemeOrderScore
                for p1 in phonemes:
                    for p2 in phonemes:
                        writeLine = ",".join([part, p1, p2, "%.1f"%pairwisescore.get((p1, p2), 0.0)])
                        _ = f.write(writeLine + "\n")
        

        with open(multiPhonemeAmbiguityFile, "w") as f:
            for part in ["onset", "nucleus", "coda"]:
                multiphonemes = self.syllableCollection.getMultiphonemeNames(part)
                for m1i, m1 in enumerate(multiphonemes[:-1]):
                    for m2 in multiphonemes[m1i + 1:]:
                        conflict = self.syllabicPartAmbiguity[part].get((m1, m2),
                                   self.syllabicPartAmbiguity[part].get((m2, m1), 0.0))
                        writeLine = ",".join([part, "".join(m1), "".join(m2), "%.1f"%conflict])
                        _ = f.write(writeLine + "\n")


def runStep(description: str, args: list[str]) -> None:
    """Run one pipeline step as a subprocess; abort the pipeline on failure.

    Stdio is inherited (the step's output streams live) and the environment passes
    through unchanged. Requires the repo root as cwd (runPipeline chdirs there first).
    Each step's wall time is appended to pipeline_timings.log (util/_timing.py).
    """
    print(f"\n=== stenalgo pipeline: {description} ===\n$ {' '.join(args)}", flush=True)
    start = time.monotonic()
    completed = subprocess.run(args)
    seconds = time.monotonic() - start
    recordTiming("step", description, seconds,
                 "ok" if completed.returncode == 0 else f"exit {completed.returncode}")
    if completed.returncode != 0:
        print(f"\nPipeline step FAILED: {description}\n  command: {' '.join(args)}\n"
              f"  exit code: {completed.returncode}\n"
              "Fix the problem above, then re-run `python dictionary.py` (completed "
              "steps are idempotent and will simply re-run).",
              file=sys.stderr, flush=True)
        raise SystemExit(completed.returncode or 1)


def runPipeline() -> None:
    """Orchestrate the whole chain in one `python dictionary.py` execution.

    Synthetic Lexicon Building (S2) (converged, via util/build_synthetic_lexicon.py),
    the phonetic theory, the Elicitation, Grouping and Realization phases, the
    disambiguated-theory refresh, and every Plover + steno-trainer export, in
    dependency order. Every phase runs as a subprocess (`python -m ...`), because the
    Dictionary must never be built twice in one process: Syllable's class-level
    phoneme collections (src/grammar.py) accumulate frequencies across builds -- which
    is also why the S3+S5 build lives in its own module (util.build_phonetic_theory),
    not as a function of this file. The run's and every step's wall times are
    appended to pipeline_timings.log (util/_timing.py).
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    startedAt = time.monotonic()

    def module(label: str, mod: str) -> None:
        runStep(label, [sys.executable, "-m", mod])

    try:
        _runSteps(module)
    finally:
        recordTiming("pipeline", "orchestrated run",
                     time.monotonic() - startedAt)


def _runSteps(module: "Callable[[str, str], None]") -> None:
    """The step sequence itself, in dependency order (runPipeline's `module` helper)."""

    # Pass 1: the plain `python dictionary.py` run's first half. The pickle cache is
    # trusted (manual-rm policy); this step writes the phonetic theory only.
    module("Dictionary loading + phonetic theory (S3-S5), pass 1", "util.build_phonetic_theory")

    # Synthetic Lexicon Building (S2), converged: the wrapper reruns the four
    # steady-state appenders (--apply) until a full round appends nothing, and after
    # any round that appended rows it deletes the pickles and reruns the build above
    # itself. Hand-made lexicon or layout edits outside this run remain the caller's
    # responsibility: rm -f the pickles first (the cache is never checked for
    # staleness).
    module("Synthetic Lexicon Building (S2), converged", "util.build_synthetic_lexicon")

    # Elicitation Phase: non-interactive; unresolved oppositions warn and continue
    # (watch the output -- the docs/PIPELINE.md rebuild step 4h human loop fixes
    # them). Without elicitation_answers.json it writes only questionnaire.json and
    # nothing downstream can proceed.
    if not os.path.exists("elicitation_answers.json") and os.path.exists("resolved_press_sets.json"):
        print("WARNING: elicitation_answers.json is absent but resolved_press_sets.json "
              "exists; the Elicitation Phase will not rewrite it. Continuing with the "
              "existing file.", file=sys.stderr, flush=True)
    module("Discriminating-Feature Elicitation (Elicitation Phase)", "src.elicitation")
    if not os.path.exists("resolved_press_sets.json"):
        raise SystemExit(
            "resolved_press_sets.json was not produced: elicitation_answers.json is "
            "missing, so the Elicitation Phase wrote only questionnaire.json. Run the "
            "human loop (docs/PIPELINE.md, rebuild step 4h): `python -m "
            "util.build_questionnaire_page`, answer it, copy the answers into "
            "elicitation_answers.json, then re-run `python dictionary.py`.")

    module("Discriminating-Feature Grouping (Grouping Phase)", "util.build_keypress_groups")

    # Disambiguated-theory refresh (S7). Nothing reads disambiguated_theory.tsv, but
    # the tracked-output verification protocol compares it.
    module("Disambiguated theory refresh (S7 -> disambiguated_theory.tsv)",
           "util.build_disambiguated_theory")

    module("Realization Phase report build", "util.build_realization_report")

    module("Theory Export (S8): Plover dictionary", "util.export_plover_dictionary")
    module("Theory Export (S8): Plover key table", "util.export_plover_system")
    module("Theory Export (S8): trainer keyboard layout", "util.export_keyboard_layout")
    module("Theory Export (S8): trainer word drills", "util.export_practice_words")
    module("Theory Export (S8): trainer sentences", "util.export_practice_sentences")
    module("Theory Export (S8): trainer definitions", "util.export_definitions")

    print("\nstenalgo pipeline complete: phonetic theory (pickles + phonetic_theory.tsv), "
          "LexiqueSynthetic.tsv, resolved_press_sets.json, keypress_groups.json, "
          "realization_report.json, disambiguated_theory.tsv, the Plover outputs and "
          "the four steno-trainer exports are up to date.", flush=True)


if __name__ == "__main__":
    runPipeline()


