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
from copy import deepcopy
from src.grammar import Syllable, SyllableCollection
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
    wordsByOrtho: dict[str, list[Word]] = {}
    frequentWords: list[str] = []
    nbFrequentWords: int = 200
    totalFrequencies: float = 0.0
    frequentWordsFrequencies: float = 0.0
    wordSource: str = "resources/LexiqueMixte.tsv"
    frequentWordsFile: str = "resources/top500_film.txt"
    syllableCollection: SyllableCollection = SyllableCollection()
    onsetSyllabicAmbiguity: dict[tuple[str, str], float] = {}
    nucleusSyllabicAmbiguity: dict[tuple[str, str], float] = {}
    codaSyllabicAmbiguity: dict[tuple[str, str], float] = {}
    onsetLexicalAmbiguity: dict[tuple[str, str], float] = {}
    nucleusLexicalAmbiguity: dict[tuple[str, str], float] = {}
    codaLexicalAmbiguity: dict[tuple[str, str], float] = {}

    def __init__(self) -> None:
        self.words: list[Word]= self.readCorpus()

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
        self.onsetSyllabicAmbiguity, self.nucleusSyllabicAmbiguity, self.codaSyllabicAmbiguity = \
            self.syllableCollection.analysePhonemSyllabicAmbiguity()
        print("Analyzing lexical ambiguities...")
        self.onsetLexicalAmbiguity, self.nucleusLexicalAmbiguity, self.codaLexicalAmbiguity = \
            self.syllableCollection.analysePhonemLexicalAmbiguity()

    def printSyllabificationStats(self) -> None:
        Syllable.printTopPhonemes()
#        self.sylCol.printTopSyllables(20)
#        Syllable.printTopPhonemesPerPosition()
#        Syllable.printTopPhonemesPerInvPosition()
        Syllable.printTopBiphonemes(20)
        Syllable.printOptimizedBiphonemeOrder()
        self.syllableCollection.printSyllacbicAmbiguityStats(
            self.onsetSyllabicAmbiguity,
            self.nucleusSyllabicAmbiguity,
            self.codaSyllabicAmbiguity, nb=15)
        self.syllableCollection.printLexicalAmbiguityStats(
            self.onsetLexicalAmbiguity,
            self.nucleusLexicalAmbiguity,
            self.codaLexicalAmbiguity, nb=15)

    def generateKeymap(self, keyboard: Keyboard) -> None:
        """ 
        Generates a keymap of the differen phonemes by trying to minimize ambiguities and 
        maximize the number of keystrokes that are in the right order to spell the words phonetically.
        """
        # Start by assigning greedily the most frequent phonemes to the most accessible keys which
        # are the single keys per phoneme.
        onsetSingleKeys, nucleusSingleKeys, codaSingleKeys = keyboard.getSingleKeys(["onset", "nucleus", "coda"])
        sortedOnsetPhonems = sorted(Syllable.onsetPhonemCol.phonemes, reverse=True)
        topOnsetPhonems = sortedOnsetPhonems[:len(onsetSingleKeys)]
        sortedNucleusPhonems = sorted(Syllable.nucleusPhonemCol.phonemes, reverse=True)
        topNucleusPhonems = sortedNucleusPhonems[:len(nucleusSingleKeys)]
        sortedCodaPhonems = sorted(Syllable.codaPhonemCol.phonemes, reverse=True)
        topCodaPhonems = sortedCodaPhonems[:len(codaSingleKeys)]






if __name__ == "__main__":
    dictionary = Dictionary()

    dictionary.analyseSyllabification()
    Syllable.optimizeBiphonemeOrder()

    dictionary.analyseAmbiguities()
#    sys.exit(1)
    dictionary.printSyllabificationStats()

#   Create a default starboard keyboard and assign the keymap
    starboard = Starboard()
    dictionary.generateKeymap(starboard)
