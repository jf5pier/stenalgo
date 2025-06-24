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

def printVerbose(word: str, msg: list[Any]):
    # return
    if word in []:  # ["soleil"] :
        print(word, " :\n", " ".join(map(str, msg)))


class Dictionary:
    words = []
    words_by_ortho: dict[str, list[Word]] = {}
    frequent_word: list[str] = []
    nb_frequent_words: int = 200
    totalFrequencies: float = 0.0
    frequent_word_frequencies: float = 0.0
    word_source: str = "resources/LexiqueMixte.tsv"
    frequent_word_file: str = "resources/top500_film.txt"
    sylCol: SyllableCollection = SyllableCollection()

    def __init__(self):
        self.words: list[Word]= self.read_corpus()

    def read_corpus(self) -> list[Word]:
        with open(self.frequent_word_file) as fw:
            self.totalFrequencies = float(
                fw.readline().strip().split("\t")[-1])
            for line in fw.readlines()[:self.nb_frequent_words]:
                ls = line.strip().split("\t")
                self.frequent_word.append(ls[0])
                self.frequent_word_frequencies += float(ls[1])

        with open(self.word_source) as f:
            corpus = csv.DictReader(f, delimiter='\t')

            for corpus_word in corpus:
                if corpus_word["ortho"] is not None \
                        and corpus_word["ortho"][0] != "#":
                    word: Word = Word(ortho=corpus_word["ortho"],
                                phonology=corpus_word["phon"],
                                lemme=corpus_word["lemme"],
                                gram_cat=GramCat[corpus_word["cgram"]]
                                    if corpus_word["cgram"] != '' else None,
                                ortho_gram_cat=[GramCat[gc] for gc in
                                    corpus_word["cgramortho"].split(",")],
                                # gram_cat = corpus_word["cgram"],
                                # ortho_gram_cat = corpus_word["cgramortho"],
                                gender=corpus_word["genre"],
                                number=corpus_word["nombre"],
                                info_verb=corpus_word["infover"],
                                raw_syll_cv=corpus_word["syll_cv"],
                                raw_orthosyll_cv=corpus_word["orthosyll_cv"],
                                frequencyBook=float(corpus_word["freqlivres"]),
                                frequencyFilm=float(corpus_word["freqfilms2"])
                                )
                    self.words.append(word)
                    same_ortho = self.words_by_ortho.get(corpus_word["ortho"],
                                                         deepcopy([])) + [word]
                    self.words_by_ortho[corpus_word["ortho"]] = same_ortho
        return self.words

    def analyseSyllabification(self):
        self.words.sort(key=lambda x: x.frequency, reverse=True)
        for word in self.words:
            # Remove the frequent words from syllable frequency statistics
            frequency = word.frequency if word.ortho not in self.frequent_word else 0.0
            syllable_names = word.phonemesToSyllableNames(withSilent=False)
            spellings = word.graphemsToSyllables(withSilent=False)
            for (syllable_name, spelling) in zip(syllable_names, spellings):
                _ = self.sylCol.updateSyllable(
                    syllable_name, spelling, frequency, word)

        Syllable.sortCollections()

    def printSyllabificationStats(self):
        Syllable.printTopPhonemes()
#        self.sylCol.printTopSyllables(20)
#        Syllable.printTopPhonemesPerPosition()
#        Syllable.printTopPhonemesPerInvPosition()
        Syllable.printTopBiphonemes(20)
        Syllable.printOptimizedBiphonemeOrder()
        syll_onset, syll_nucleus, syll_coda = self.sylCol.analysePhonemSyllabicAmbiguity()
        self.sylCol.printSyllacbicAmbiguityStats(
            syll_onset, syll_nucleus, syll_coda, nb=15)
        lexical_onset, lexical_nucleus, lexical_coda = self.sylCol.analysePhonemLexicalAmbiguity()
        self.sylCol.printLexicalAmbiguityStats(
            lexical_onset, lexical_nucleus, lexical_coda, nb=15)


dictionary = Dictionary()

#from src.grammar import Phoneme
#print (Phoneme.nucleusPhonemesIPA, len(Phoneme.nucleusPhonemesIPA))
#print (Phoneme.nucleusPhonemes, len(Phoneme.nucleusPhonemes))
#for i in Phoneme.nucleusPhonemesIPA :
#    print(i)
dictionary.analyseSyllabification()
dictionary.printSyllabificationStats()
