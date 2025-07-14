#!/usr/bin/python
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
import os
import pickle
from pprint import PrettyPrinter
from copy import deepcopy
from src.grammar import Phoneme, Syllable, SyllableCollection
from src.word import GramCat, Word
from typing import Any
from src.keyboard import Keyboard, Starboard
from tqdm import tqdm
import sys

def printVerbose(word: str, msg: list[Any]):
    # return
    if word in []:  # ["soleil"] :
        print(word, " :\n", " ".join(map(str, msg)))


class Dictionary:
    words: list[Word]
    wordsByOrtho: dict[str, list[Word]]
    frequentWords: list[str]
    nbFrequentWords: int = 200
    totalFrequencies: float = 0.0
    frequentWordsFrequencies: float = 0.0
    wordSource: str = "resources/LexiqueMixte.tsv"
    frequentWordsFile: str = "resources/top500_film.txt"
    syllableCollection: SyllableCollection
    syllabicAmbiguity: dict[str, dict[tuple[str, str], float]]
    lexicalAmbiguity: dict[str, dict[tuple[str, str], float]]

    def __init__(self) -> None:
        self.syllableCollection = SyllableCollection()
        self.wordsByOrtho = {}
        self.frequentWords = []
        self.syllableClass: type = Syllable
        self.syllabicAmbiguity = {
        "onset": {}, "nucleus": {}, "coda": {}}
        self.lexicalAmbiguity = {
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

        with open(self.wordSource) as f:
            corpus = csv.DictReader(f, delimiter='\t')

            for corpusWord in tqdm(corpus, desc="Reading corpus", unit=" words"):
                if corpusWord["ortho"] is not None \
                        and corpusWord["ortho"][0] != "#":
                    word: Word = Word(ortho=corpusWord["ortho"],
                                phonology=corpusWord["phon"],
                                lemme=corpusWord["lemme"],
                                gramCat=GramCat[corpusWord["cgram"]]
                                    if corpusWord["cgram"] != '' else None,
                                orthoGramCat=[GramCat[gc] for gc in
                                    corpusWord["cgramortho"].split(",")],
                                # gram_cat = corpus_word["cgram"],
                                # ortho_gram_cat = corpus_word["cgramortho"],
                                gender=corpusWord["genre"],
                                number=corpusWord["nombre"],
                                infoVerb=corpusWord["infover"],
                                rawSyllCV=corpusWord["syll_cv"],
                                rawOrthosyllCV=corpusWord["orthosyll_cv"],
                                frequencyBook=float(corpusWord["freqlivres"]),
                                frequencyFilm=float(corpusWord["freqfilms2"])
                                )
                    words.append(word)
                    same_ortho = self.wordsByOrtho.get(corpusWord["ortho"],
                                                         deepcopy([])) + [word]
                    self.wordsByOrtho[corpusWord["ortho"]] = same_ortho
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
        print("Analyzing lexical ambiguities...")
        self.lexicalAmbiguity["onset"], self.lexicalAmbiguity["nucleus"], self.lexicalAmbiguity["coda"] = \
            self.syllableCollection.analysePhonemLexicalAmbiguity()

    def printSyllabificationStats(self) -> None:
        Syllable.printTopPhonemes()
#        self.sylCol.printTopSyllables(20)
#        Syllable.printTopPhonemesPerPosition()
#        Syllable.printTopPhonemesPerInvPosition()
        Syllable.printTopBiphonemes(5)
        Syllable.printOptimizedBiphonemeOrder()
        self.syllableCollection.printAmbiguityStats(self.syllabicAmbiguity, "Syllabic")
        self.syllableCollection.printAmbiguityStats(self.lexicalAmbiguity, "Lexical")

    def generateBaseKeymap(self, keyboard: Keyboard) -> None:
        """ 
        Generates a keymap of the differen phonemes by trying to minimize ambiguities and 
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
                    keyboard.addToLayout(singleKeys.pop(0), phoneme)


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
                        if maxUse >= MaxOveruse +2*(len(multikeys[0])-2): #NOTE: This makes it so that all thumb key pairs are not assignable
                            _ = multikeys.pop(0)
                        else:
                            for key in multikeys[0]:
                                keyOveruse[key] = keyOveruse.get(key, 0) + 1
                            #print("Assigning", phoneme, "to", multikeys[0])
                            keyboard.addToLayout(multikeys.pop(0), phoneme)
                            assigned = True
                            break

                    if not assigned:
                        unassignedPhonemes.append(phoneme)
            return unassignedPhonemes[:]


        # Start by assigning greedily the most frequent phonemes to the most accessible keys which
        # are the single keys per phoneme.
        for syllabicPart in ["onset", "nucleus", "coda"]:
            unassigned = _greadyAssignKeymapPartition(keyboard, syllabicPart)
            print("Unassigned phonemes in", syllabicPart, ":", unassigned)
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

    def buildTheory(self, keyboard: Keyboard) -> dict[tuple[tuple[int, ...], ...], list[Word]]:
        theory: dict[tuple[tuple[int, ...], ...], list[Word]] = {}
        for word in tqdm(self.words, desc="Building theory", unit=" words", ascii=True, ncols=80):
            syllableNames = word.phonemesToSyllableNames(withSilent=False)
            try: 
                syllableStrokes: tuple[tuple[int, ...], ...] = tuple(keyboard.getStrokeOfSyllableByPart(
                    self.syllableCollection.syllable_names[syllableName].phonemeNamesByPart())
                    for syllableName in syllableNames)
            except IndexError as e:
                print(f"{word.ortho} {syllableNames}", e)
                raise IndexError(f"{word.ortho} {syllableNames}", e)
            if syllableStrokes not in theory:
                theory[syllableStrokes] = []
            theory[syllableStrokes].append(word)
        return theory
        


if __name__ == "__main__":
    starboard = Starboard()
    dictionary: Dictionary

    if os.path.exists("Dictionary.pickle"):
        with open("Dictionary.pickle", "rb") as pfile:
            dictionary = pickle.load(pfile)
            Syllable.allPhonemeCol = pickle.load(pfile)
            Syllable.phonemeColByPart = pickle.load(pfile)
            Syllable.biphonemeColByPart = pickle.load(pfile)
            dictionary: Dictionary = pickle.load(open("Dictionary.pickle", "rb"))
#        dictionary.syllableCollection = pickle.load(open("Syllables.pickle", "rb"))
        #del dictionary.words  # Remove the words to save memory
        pp = PrettyPrinter(indent=4)
        pp.pprint("Loaded dictionary from pickle file.")
#        pp.pprint(dictionary.__dict__)
        pp.pprint(dictionary.syllableCollection)
    else :
        dictionary = Dictionary()

        dictionary.analyseSyllabification()
        Syllable.optimizeBiphonemeOrder()

        dictionary.analyseAmbiguities()
        pp = PrettyPrinter(indent=4)
        pp.pprint(dictionary.syllableCollection)
        with open("Dictionary.pickle", "wb") as pfile:
            pickle.dump(dictionary, pfile)
            pickle.dump(Syllable.allPhonemeCol, pfile)
            pickle.dump(Syllable.phonemeColByPart, pfile)
            pickle.dump(Syllable.biphonemeColByPart, pfile)
#        pickle.dump(dictionary.syllableCollection, open("Syllables.pickle", "wb"))

#    sys.exit(1)
    dictionary.printSyllabificationStats()

#   Create a default starboard keyboard and assign the keymap
    dictionary.generateBaseKeymap(starboard)
    theory = dictionary.buildTheory(starboard)
    with open("theory.tsv", "w") as f:
        _ = f.write("strokes\twords\n")
        maxAmbiguity = 0
        maxAmbiguityWords = []
        for syllableStrokes, words in theory.items():
            strokeString = starboard.strokesToString(syllableStrokes)
            wordOrthos = sorted(list(set(map(lambda w: w.ortho, words))))
            if len(wordOrthos) > maxAmbiguity:
                maxAmbiguity = len(wordOrthos)
                maxAmbiguityWords = wordOrthos
            _ = f.write(f"{strokeString}\t{','.join(wordOrthos)}\n")
        
        print("Max ambiguity:", maxAmbiguity, "for words", maxAmbiguityWords)
    #for syllableStrokes, words in theory.items():
    #    strokeString = starboard.strokesToString(syllableStrokes)
    #    print(strokeString, ":", list(map(lambda w: w.ortho, words)))

