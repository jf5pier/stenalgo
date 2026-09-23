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
import pickle
from copy import deepcopy

from src.grammar import Phoneme, Syllable, SyllableCollection
from src.word import GramCat, Word
from typing import Any
from src.keyboard import Keyboard, Starboard, Stroke, Strokes
from src.cpsatsolver import optimizeKeyboard
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


#from src.cpsatoptimizer import optimizeTheory
from tqdm import tqdm
import sys

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

    def buildTheory(self, keyboard: Keyboard) -> dict[Strokes, list[Word]]:
        theory: dict[tuple[tuple[int, ...], ...], list[Word]] = {}
        for word in tqdm(self.words, desc="Building theory", unit=" words", ascii=True, ncols=80):
            syllableNames = word.phonemesToSyllableNames(withSilent=False)
            syllableStrokes: tuple[tuple[int, ...], ...] = tuple(keyboard.getStrokeOfSyllableByPart(
                self.syllableCollection.syllable_names[syllableName].phonemeNamesByPart())
                for syllableName in syllableNames)
            if syllableStrokes not in theory:
                theory[syllableStrokes] = []
            theory[syllableStrokes].append(word)
        return theory

    def writeTheory(self, theory: dict[Strokes, list[Word]], keyboard: Keyboard, filename: str) -> None:
        with open(filename, "w") as f:
            _ = f.write("strokes\twords\n")
            maxAmbiguity = 0
            maxAmbiguityWords = []
            maxFrequencyAmbiguity = 0.0
            maxFrequencyAmbiguityWords = []
            maxFrequencyAmbiguityStrokes= ()
            for syllableStrokes, words in theory.items():
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

    def buildFinalTheory(
        self, theory: dict[Strokes, list[Word]], keyboard: Keyboard,
        keypressGroupsPath: str = "keypress_groups.json",
        resolvedPressSetsPath: str = "resolved_press_sets.json",
    ) -> dict[Word, list[Strokes]]:
        """
        Theory 2: every word's final resolved Strokes -- a LIST, since a self-homograph
        spelling (more than one valid reading, e.g. "calmez" = impératif or indicatif
        présent -- see src.elicitation.resolveGroupPressSets) has more than one
        independently-valid stroke, each identifying it without the others. Index 0 is
        always the word's PRIMARY stroke: theory 1 (buildTheory) composed with the
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

        wordToStrokes = buildWordToStrokes(theory)
        wordsByOrthoLemme = buildWordsByOrthoLemme(theory)
        groupToWords = buildKeypressGroupToWords(resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme)
        extraGroupSetsByWord = buildKeypressGroupExtraAlternates(
            resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme
        )
        preferredKeysByGroup = resolvePreferredKeysByGroup(markersByKeypress)
        assignment = realizeKeypressGroupsAsExtraStroke(
            groupToWords, theory, keyboard,
            extraGroupSetsByWord=extraGroupSetsByWord, preferredKeysByGroup=preferredKeysByGroup,
        )
        finalInduced = buildFinalInducedStrokes(theory, groupToWords, assignment)
        primaryComposed = composeReservedKeyStrokes(
            finalInduced, loadReform1990DoubletPairs(),
            phonemeStrokeCounts={word: len(strokes) for word, strokes in wordToStrokes.items()},
        )
        extraByWord = buildExtraInducedStrokes(theory, assignment, extraGroupSetsByWord)
        return {word: [strokes] + extraByWord.get(word, []) for word, strokes in primaryComposed.items()}

    def writeFinalTheory(
        self, theory: dict[Strokes, list[Word]], finalTheory: dict[Word, list[Strokes]],
        keyboard: Keyboard, filename: str,
    ) -> None:
        """
        Writes `filename`: one row per (word, reading) -- a self-homograph word (see
        `buildFinalTheory`) gets one row per independently-valid stroke, all sharing the
        same ortho/lemme/gramCat/base-strokes columns and differing only in
        `extraStrokes`. Those extra strokes use coda-bank and reserved
        (STAR_KEY/HASH_KEY) keys that carry no single assigned phoneme, so
        `strokesToString` (phoneme-layer only) can't render them -- they're written as
        raw key-index tuples instead, same as `build_realization_report.py` already
        reports `chosenKeys`.
        """
        wordToStrokes = buildWordToStrokes(theory)
        with open(filename, "w") as f:
            _ = f.write("ortho\tlemme\tgramCat\tstrokes\textraStrokes\n")
            for word in sorted(finalTheory, key=lambda w: (w.lemme, w.gramCat.name, w.ortho)):
                baseStrokes = wordToStrokes[word]
                strokeString = keyboard.strokesToString(baseStrokes)
                for fullStrokes in finalTheory[word]:
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


if __name__ == "__main__":
    dictionary: Dictionary

    if os.path.exists("Dictionary.pickle"):
        with open("Dictionary.pickle", "rb") as pfile:
            dictionary = pickle.load(pfile)
            Syllable.allPhonemeCol = pickle.load(pfile)
            Syllable.phonemeColByPart = pickle.load(pfile)
            Syllable.biphonemeColByPart = pickle.load(pfile)
            Syllable.multiphonemeColByPart = pickle.load(pfile)
        print("Loaded dictionary from pickle file.")
        print(dictionary.syllableCollection)
    else :
        dictionary = Dictionary()

        dictionary.analyseSyllabification()
        Syllable.optimizeBiphonemeOrder()

        dictionary.analyseAmbiguities()
        with open("Dictionary.pickle", "wb") as pfile:
            pickle.dump(dictionary, pfile)
            pickle.dump(Syllable.allPhonemeCol, pfile)
            pickle.dump(Syllable.phonemeColByPart, pfile)
            pickle.dump(Syllable.biphonemeColByPart, pfile)
            pickle.dump(Syllable.multiphonemeColByPart, pfile)
#        pickle.dump(dictionary.syllableCollection, open("Syllables.pickle", "wb"))

#    print(dictionary.words[0])
#    sys.exit(1)

    #dictionary.printSyllabificationStats()


    #dictionary.writeConstrainFiles()

    #pprint.pprint(dictionary.wordsByOrtho["effraye"])
    #for syllableStrokes, words in theory.items():
    #    strokeString = starboard.strokesToString(syllableStrokes)
    #    print(strokeString, ":", list(map(lambda w: w.ortho, words)))
    keyboardJSON = 'starboard3h.json'
    starboard = Starboard.fromJSONFile(keyboardJSON)
    if starboard is None :
        print("Could not load keyboard from", keyboardJSON, "generating an initial keymap based on phoneme order")
        starboard = Starboard()
        dictionary.generateBaseKeymap(starboard)

    #optimizeKeyboard(starboard, dictionary.syllabicPartAmbiguity, ["onset", "nucleus" ,"coda"])
    starboard.printLayout()
    #starboard.toJSONFile('starboard.json')
    theory: dict[Strokes, list[Word]] = {}
    if os.path.exists("FirstTheory.pickle"):
        with open("FirstTheory.pickle", "rb") as pfile:
            theory = pickle.load(pfile)
    else:
        theory = dictionary.buildTheory(starboard)
        dictionary.writeTheory(theory, starboard, "theory.tsv")
        with open("FirstTheory.pickle", "wb") as pfile:
            pickle.dump(theory, pfile)


    # lemmeOrthoWords: dict[tuple[str, str], list[Word]] = {}
    # for stokes, words in theory.items():
    #     for word in words:
    #         lemmeOrthoWords[(word.lemme, word.ortho)] = lemmeOrthoWords.get((word.lemme, word.ortho), []) + [word]
    # for (lemme, ortho), words in lemmeOrthoWords.items():
    #     if len(words) > 1 :
    #         print(f"Lemme {lemme} ortho {ortho} has {len(words)} words features: ", list(map(lambda w: (w.gramCat.name, w.gender, w.number, w.infoVerb), words)))
    #
    # infoVerbs = []
    # for word in dictionary.words:
    #     if  word.infoVerb is not None:
    #         for iv in word.infoVerb:
    #             if iv not in infoVerbs:
    #                 print(iv)
    #                 infoVerbs.append(iv)
    # sys.exit(1)
    # Theory 2: the Realization Phase's same-lemma coda-bank realization + the star/hash
    # mark track's reserved keys, composed on top of theory 1 (see ROADMAP.md's "What's left to
    # do" -- this retires the superseded solver-picks-features path that used to run
    # here, whose satOptimizeDiscriminator conflict count had gone vestigial).
    keypressGroupsPath = "keypress_groups.json"
    resolvedPressSetsPath = "resolved_press_sets.json"
    finalTheoryPath = "theory2.tsv"
    if os.path.exists(keypressGroupsPath) and os.path.exists(resolvedPressSetsPath):
        finalTheory = dictionary.buildFinalTheory(theory, starboard, keypressGroupsPath, resolvedPressSetsPath)
        dictionary.writeFinalTheory(theory, finalTheory, starboard, finalTheoryPath)
        print(f"\nWrote {finalTheoryPath}: {len(finalTheory)} words with theory 2"
              f" (Phase P + */# track) strokes.")
    else:
        print(f"\nSkipping theory 2 (Phase P + */# track): {keypressGroupsPath} and/or"
              f" {resolvedPressSetsPath} not found. Run `python -m util.build_keypress_groups`"
              f" and `python -m src.elicitation` first, then re-run `python dictionary.py`.")


