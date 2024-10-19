#!/usr/bin/python
# coding: utf-8
#
import sys
from dataclasses import dataclass
from enum import Enum
from itertools import permutations, chain
from copy import deepcopy
from typing import Tuple, List, Dict
from word import Word
import numpy as np


GramCat = Enum("GramCat", ["ADJ", "ADJ:dem", "ADJ:ind", "ADJ:int", "ADJ:num",
                           "ADJ:pos", "ADV", "ART:def", "ART:ind", "AUX", "CON",
                           "LIA", "NOM", "ONO", "PRE", "PRO:dem", "PRO:ind",
                           "PRO:int", "PRO:per", "PRO:pos", "PRO:rel", "VER"])


@dataclass
class Phoneme:
    """
    Representation of the parts of a Syllable

    name : str
        Single char IPA representation of the phoneme
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    """
    name: str
    frequency: float = 0.0

    # There's an argument to have "w" and "j" as part of the vowels
    vowel_phonemes = "aeiE@o°§uy5O9821"
    consonant_phonemes = "RtsplkmdvjnfbZwzSgNG"

    def __post_init__(self):
        # 7 phonemes is the max per syll
        self.posFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.invPosFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def increaseFrequency(self, frequency: float, pos: int = 0, invPos: int = 0):
        self.frequency += frequency
        self.posFrequency[pos] += frequency
        self.invPosFrequency[invPos] += frequency

    def isVowel(self):
        return self.name in self.vowel_phonemes

    def isConsonant(self):
        return self.name in self.consonant_phonemes

    def __eq__(self, other):
        if type(other) is Phoneme:
            return self.name == other.name
        else:
            return self.name == other

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name + ":" + "%.1f" % self.frequency


@dataclass
class Biphoneme:
    """
    Coocurence of two phonemes in a group of phonemes (syllable or other)

    pair : (str, str)
        Pair of phonemes
    frequency :
        Occurence frequency of the pair of phoenemes
    """
    pair: Tuple[str, str]
    frequency: float = 0.0

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency

    def __eq__(self, other):
        return self.pair == other.pair

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __str__(self):
        return "(%s, %s)" % (self.pair[0], self.pair[1])

    def __repr__(self):
        return self.pair[0] + self.pair[1] + ":" + "%.1f" % self.frequency


class PhonemeCollection:
    """
    Collection of Phonemes representing the existing sounds of a lexicon/corpus

    phonemes_names: {str:Phoneme}
    phonemes : [Phoneme]
    """

    def __init__(self):
        self.phoneme_names = {}
        self.phonemes = []

    def getPhonemes(self, phoneme_names: str):
        """ Get phonemes from collection, adding missing ones if needed """
        ret = []
        for phoneme_name in phoneme_names:
            if phoneme_name not in self.phoneme_names:
                p = Phoneme(phoneme_name)
                self.phoneme_names[phoneme_name] = p
                self.phonemes.append(p)

            ret.append(self.phoneme_names[phoneme_name])
        return ret

    def getPhoneme(self, phoneme_name: str):
        return self.getPhonemes(phoneme_name)[0]

    def printTopPhonemes(self, nb: int = -1):
        self.phonemes.sort(reverse=True)
        print("Top phonemes:", self.phonemes[:nb])

    def printTopPhonemesPerPosition(self, nb: int = -1):
        for i in range(7):
            self.phonemes.sort(key=lambda p: p.posFrequency[i], reverse=True)
            print("Phonemes in pos %i" % i, list(map(lambda p: (
                p.name, "%.1f" % p.posFrequency[i]),
                self.phonemes[:nb])), "\n")

    def printTopPhonemesPerInvPosition(self, nb: int = -1):
        for i in range(7):
            self.phonemes.sort(
                key=lambda p: p.invPosFrequency[i], reverse=True)
            print("Phonemes in inverted pos -%i" % (i+1), list(map(lambda p: (
                p.name, "%.1f" % p.invPosFrequency[i]),
                self.phonemes[:nb])), "\n")

    def printBarchart(self, phoneme_order: str, exhaustive_phonemes: str,
                      vsize: int = 10):
        maxFreq = 0.0
        excluded_phonemes = list(
            filter(lambda p: p not in phoneme_order, exhaustive_phonemes))
        for phoneme_name in exhaustive_phonemes:
            maxFreq = max(maxFreq, self.phoneme_names[phoneme_name].frequency)
        for i in range(vsize, 0, -1):
            toPrint = "> "
            for phoneme_name in phoneme_order:
                phoneme = self.phoneme_names[phoneme_name]
                toPrint += phoneme.name \
                    if phoneme.frequency >= i*maxFreq/vsize else " "
            toPrint += " | "
            for phoneme_name in excluded_phonemes:
                phoneme = self.phoneme_names[phoneme_name]
                toPrint += phoneme.name \
                    if phoneme.frequency >= i*maxFreq/vsize else " "
            toPrint += " <"
            print(toPrint)
        print("> " + phoneme_order + " | " + "".join(excluded_phonemes) + " <")
        barsWidth = len(phoneme_order)+3
        barsWidth2 = len(excluded_phonemes) + 3
        print("^"*(barsWidth) + "|" + "^"*(barsWidth2))
        print(" "*(barsWidth-8) + "ordered | floating", "\n")


class BiphonemeCollection:
    """
    Collection of pairs of phonemes found in syllables

    biphonemes_names: {(str,str):Biphoneme}
    biphonemes : List[Biphoneme]
    """

    def __init__(self):
        self.biphoneme_names: Dict[Tuple[str, str], Biphoneme] = {}
        self.biphonemes: List[Biphoneme] = []

    def getBiphonemes(self, biphoneme_names: List[Tuple[str, str]]) \
            -> List[Biphoneme]:
        """ Get biphonemes from collection, adding missing ones if needed """
        ret = []
        for biphoneme_name in biphoneme_names:
            if biphoneme_name not in self.biphoneme_names:
                bp = Biphoneme(biphoneme_name)
                self.biphoneme_names[biphoneme_name] = bp
                self.biphonemes.append(bp)

            ret.append(self.biphoneme_names[biphoneme_name])
        return ret

    def getBiphoneme(self, biphoneme_name: Tuple[str, str]) -> Biphoneme:
        return self.getBiphonemes([biphoneme_name])[0]

    def printTopBiphonemes(self, nb: int = -1):
        self.biphonemes.sort(reverse=True)
        print("Biphonemes:", list(map(lambda bp: (
            bp.pair, "%.1f" % bp.frequency), self.biphonemes[:nb])), "\n")

    def getPhonemesNames(self):
        """ Extract single phonemes names from pairs of phonemes"""
        left = set(map(lambda p: p.pair[0], self.biphonemes))
        right = set(map(lambda p: p.pair[1], self.biphonemes))
        return "".join(set(list(left) + list(right)))

    def optimizeOrder(self):
        """ Optimize the order of the phonemes found in the biphonemes
            to reduce the frequency where two phonemes would be types in
            the wrong order to produce a syllable. """
        score = 0
        phonemes = list(self.getPhonemesNames())
        np.random.shuffle(phonemes)
        bestPermutation = "".join(phonemes)
        (bestScore, bestNegScore, _) = self.scorePermutation("".join(phonemes))
        # print("Starting order (%0.1f):"%bestScore, bestPermutation)
        # print("Biphonemes in wrong order:", bestBadOrder)

        # The algorithm moves a window over the phonem string and tests
        # permutations in that window exclusively.  A window scan goes over
        # every phonem substring left to right, then right to left.
        windowSize = 4
        windowScans = 400
        maxShuffleSize = 7
        randOrder = np.array(range(len(phonemes)))
        for scan in range(windowScans):
            np.random.shuffle(randOrder)
            shuffleSize = np.random.randint(2, maxShuffleSize)
            mutatedPermutation = list(deepcopy(bestPermutation))
            tmp = bestPermutation[randOrder[0]]
            for i in range(1, shuffleSize):
                mutatedPermutation[randOrder[i-1]
                                   ] = bestPermutation[randOrder[i]]
            mutatedPermutation[randOrder[shuffleSize-1]] = tmp
            mutatedPermutation = "".join(mutatedPermutation)

            # print("Test perm:", mutatedPermutation, scan)
            for pos in chain(range(len(phonemes) - windowSize),
                             range(len(phonemes) - windowSize, 0, -1)):
                subPhonemes = mutatedPermutation[pos:pos+windowSize]
                for permutation in permutations(subPhonemes):
                    subp = "".join(permutation)
                    p = mutatedPermutation[:pos] + subp + \
                        mutatedPermutation[pos+windowSize:]
                    score, negScore, badOrder = self.scorePermutation(p)
                    if score > bestScore:
                        # if score > (bestScore * 1.03) :
                        # print("New order (%0.1f > %0.1f):"%(score,bestScore), p)
                        # print("Biphonemes in wrong order:", badOrder)
                        bestScore = score
                        bestNegScore = negScore
                        bestPermutation = p
                        bestBadOrder = badOrder
        print("\nBest order (ordered score %0.1f, disordered score %0.1f):\n" %
              (bestScore, bestNegScore), bestPermutation)
        # print("Disordered:", bestBadOrder)
        return bestPermutation

    def scorePermutation(self, permutation: str):
        score = 0.0
        negScore = 0.0
        badOrder = []
        for biphoneme in self.biphonemes:
            left, right = biphoneme.pair
            if permutation.index(left) < permutation.index(right):
                score += biphoneme.frequency
            else:
                score -= biphoneme.frequency
                negScore -= biphoneme.frequency
                badOrder.append(biphoneme)
        return score, negScore, badOrder


class Syllable:
    """
    Representation of a unique sound part of a word

    phonemes : [Phoneme]
        List of Phonemes sounding the Syllable
    spellings : {str: float}
        Dict of orthographic spelling that sound the same Syllable
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    phonemeCol : PhonemeCollection
        Collection of Phonemes found in the underlying lexicon/corpus
    preVowelPhonemeCol : PhonemeCollection
        Collection of phonemes found before the vowels of a syllable
    postVowelPhonemeCol : PhonemeCollection
        Collection of phonemes found after the vowels of a syllable
    vowelPhonemeCol : PhonemeCollection
        Collection phonemes found in the vowels part syllable
    preVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found before the vowels of a syllable
    postVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found after the vowels of a syllable
    multiVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found in multi-vowels syllable
    """
    phonemeCol: PhonemeCollection = PhonemeCollection()
    preVowelPhonemeCol: PhonemeCollection = PhonemeCollection()
    postVowelPhonemeCol: PhonemeCollection = PhonemeCollection()
    vowelPhonemeCol: PhonemeCollection = PhonemeCollection()
    preVowelBiphonemeCol: BiphonemeCollection = BiphonemeCollection()
    postVowelBiphonemeCol: BiphonemeCollection = BiphonemeCollection()
    multiVowelBiphonemeCol: BiphonemeCollection = BiphonemeCollection()

    def __init__(self, phoneme_names: str, spelling: str, frequency: float = 0.0):
        self.phonemes: list[Phoneme] = []
        self.name: str = ""
        self.phonemes_pre: list[Phoneme] = []
        self.phonemes_post: list[Phoneme] = []
        self.phonemes_vowel: list[Phoneme] = []
        self.biphonemes_pre: list[Biphoneme] = []
        self.biphonemes_post: list[Biphoneme] = []
        self.biphonemes_vowel: list[Biphoneme] = []
        self.spellings: Dict[str, float] = {}

        phonemes = Syllable.phonemeCol.getPhonemes(phoneme_names)
        self.name = "".join(list(map(lambda p: p.name, phonemes)))

        firstVowelPos = -1
        lastVowelPos = -1
        verbose = True if phoneme_names == "" else False
        for pos, phoneme in enumerate(phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(phonemes)-pos-1)
            if verbose:
                print(phoneme, phoneme.frequency)
            self.phonemes.append(phoneme)
            if firstVowelPos == -1 and not phoneme.isVowel():
                if verbose:
                    print("Left hand consonant", phoneme)
                phoneme_pre = Syllable.preVowelPhonemeCol.getPhoneme(
                    phoneme.name)
                phoneme_pre.increaseFrequency(frequency)
                self.phonemes_pre.append(phoneme_pre)
            elif firstVowelPos != -1 and not phoneme.isVowel():
                if verbose:
                    print("Right hand consonant", phoneme)
                phoneme_post = Syllable.postVowelPhonemeCol.getPhoneme(
                    phoneme.name)
                phoneme_post.increaseFrequency(frequency)
                self.phonemes_post.append(phoneme_post)
            # Break down the syllable into consonants-vowels-consonants
            if phoneme.isVowel():
                if verbose:
                    print("Vowel", phoneme)
                phoneme_vowel = Syllable.vowelPhonemeCol.getPhoneme(
                    phoneme.name)
                phoneme_vowel.increaseFrequency(frequency)
                self.phonemes_vowel.append(phoneme_vowel)

                if firstVowelPos == -1:
                    firstVowelPos = pos
                lastVowelPos = pos

        # Track the cooccurences of phonemes pairs in the first
        # consonnants group
        if firstVowelPos >= 2:
            for pos1, phoneme1 in enumerate(phonemes[:firstVowelPos-1]):
                for phoneme2 in phonemes[pos1+1:firstVowelPos]:
                    biphoneme = Syllable.preVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name))
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Left hand biphoneme", biphoneme)
                    self.biphonemes_pre.append(biphoneme)

        # Track the cooccurences of phonemes pairs in the last
        # consonnants group
        if lastVowelPos <= len(phonemes) - 3:
            for pos1, phoneme1 in enumerate(phonemes[lastVowelPos+1:-1]):
                for phoneme2 in phonemes[lastVowelPos+pos1+2:]:
                    biphoneme = Syllable.postVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name))
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Right hand biphoneme", biphoneme)
                    self.biphonemes_post.append(biphoneme)

        # Track the cases where multiple vowels are part of the
        # middle (inclue semivowels??)
        if firstVowelPos < lastVowelPos:
            for pos1, phoneme1 in enumerate(phonemes[firstVowelPos:lastVowelPos]):
                for phoneme2 in phonemes[firstVowelPos+pos1+1:lastVowelPos+1]:
                    biphoneme = Syllable.multiVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name))
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Vowel biphoneme", biphoneme)
                    self.biphonemes_vowel.append(biphoneme)

        self.frequency = frequency
        self.spellings[spelling] = frequency

        # print("pho",self.phonemes, "pre",self.phonemes_pre,
        # "post",self.phonemes_post,
        #      "vow",self.phonemes_vowel, "bpre", self.biphonemes_pre, "bpost",
        #      self.biphonemes_post, "bvow",self.biphonemes_vowel)

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos, phoneme in enumerate(self.phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(self.phonemes)-pos-1)
        for phoneme in self.phonemes_pre:
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemes_post:
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemes_vowel:
            phoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_pre:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_post:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_vowel:
            biphoneme.increaseFrequency(frequency)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency
        self.increaseFrequency(frequency)

    @staticmethod
    def printTopPhonemesPerPosition(nb: int = -1):
        Syllable.phonemeCol.printTopPhonemesPerPosition(nb)

    @staticmethod
    def printTopPhonemesPerInvPosition(nb: int = -1):
        Syllable.phonemeCol.printTopPhonemesPerInvPosition(nb)

    @staticmethod
    def printTopPhonemes(nb: int = -1):
        print("Whole words phonemes:")
        Syllable.phonemeCol.printTopPhonemes(nb)
        print("Pre-vowel phonemes :")
        Syllable.preVowelPhonemeCol.printTopPhonemes(nb)
        print("Vowel phonemes :")
        Syllable.vowelPhonemeCol.printTopPhonemes(nb)
        print("Post-vowel phonemes :")
        Syllable.postVowelPhonemeCol.printTopPhonemes(nb)

    @staticmethod
    def printTopBiphonemes(nb: int = -1):
        print("Pre-vowels biphonemes")
        Syllable.preVowelBiphonemeCol.printTopBiphonemes(nb)
        print("Vowel biphonemes")
        Syllable.multiVowelBiphonemeCol.printTopBiphonemes(nb)
        print("Post-vowels biphonemes")
        Syllable.postVowelBiphonemeCol.printTopBiphonemes(nb)

    @staticmethod
    def optimizeBiphonemeOrder():
        print("Left hand optimization :")
        order = Syllable.preVowelBiphonemeCol.optimizeOrder()
        Syllable.preVowelPhonemeCol.printBarchart(
            order, Phoneme.consonant_phonemes)

        print("Right hand optimization :")
        order = Syllable.postVowelBiphonemeCol.optimizeOrder()
        Syllable.postVowelPhonemeCol.printBarchart(
            order, Phoneme.consonant_phonemes)

        print("Vowel optimization :")
        order = Syllable.multiVowelBiphonemeCol.optimizeOrder()
        Syllable.vowelPhonemeCol.printBarchart(order, Phoneme.vowel_phonemes)
        print("")

    def replacePhonemeInPos(self, phoneme1: Phoneme,
                            phoneme2: Phoneme, pos: str):
        """ Replace a phoneme in one of 3 positions in a syllable """
        if pos == "preVowels":
            pre = "".join(map(str, self.phonemes_pre))
            pre.replace(str(phoneme1), str(phoneme2))
            return pre + "".join(map(str, self.phonemes_vowel)) + \
                "".join(map(str, self.phonemes_post))
        elif pos == "postVowels":
            post = "".join(map(str, self.phonemes_post))
            post.replace(str(phoneme1), str(phoneme2))
            return "".join(map(str, self.phonemes_pre)) + \
                "".join(map(str, self.phonemes_vowel)) + post
        elif pos == "vowels":
            vowel = "".join(map(str, self.phonemes_vowel))
            vowel.replace(str(phoneme1), str(phoneme2))
            return "".join(map(str, self.phonemes_pre)) + vowel + \
                "".join(map(str, self.phonemes_post))
        else:
            return "".join(map(str, self.phonemes))

    def sortedSpellings(self):
        spel_freq = [(k, v) for k, v in self.spellings.items()]
        spel_freq.sort(key=lambda kv: kv[1], reverse=True)
        return spel_freq

    def __eq__(self, other):
        return self.phonemes == other.phonemes

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __str__(self):
        return "".join([str(p) for p in self.phonemes]) + " > " + \
            ", ".join([str(spel)+": %.1f" % freq for (spel, freq) in
                       self.sortedSpellings()[:4]]) \
            + " > SyllFreq " + "%.1f %.1f" % \
            (self.frequency, sum(
                [freq for (spel, freq) in self.sortedSpellings()[:4]]))


class SyllableCollection:
    """
    Collection of all Syllables found in a lexicon/corpus

    syllable_names: {str : Syllable}
    syllables : [Syllable]
    """
    syllable_names = {}
    syllables = []

    def updateSyllable(self, syllable_name: str, spelling: str,
                       addedfrequency: float, word: Word | None = None):
        """ Updates syllable from collection, adding missing ones if needed """
        if syllable_name not in self.syllable_names:
            s = Syllable(syllable_name, spelling)
            self.syllable_names[syllable_name] = s
            self.syllables.append(s)
        # Adds the spelling if it is missing
        self.syllable_names[syllable_name].increaseSpellingFrequency(
            spelling, addedfrequency)

    def getSyllable(self, syllable_name: str, spelling: str,
                    frequency: float = 0.0):
        """ Get syllable from collection, adding missing ones if needed """
        self.updateSyllable(syllable_name, spelling, frequency)
        return self.syllable_names[syllable_name]

    def getFrequency(self, syllable: Syllable | str):
        if type(syllable) is Syllable:
            name = syllable.name
        elif type(syllable) is str:
            name = syllable
        else:
            print("Type syllable|str not found", syllable)
            sys.exit(1)

        if name not in self.syllable_names:
            print("Not found syllable", name)
            return 0.0
        else:
            # print("Found", name, self.syllable_names[name].frequency )
            return self.syllable_names[name].frequency

    def ambiguityScore(self, phoneme1: str, phoneme2: str, pos: str):
        """ Ambiguity is defined by the existance of two syllables that are
            different by only one phoneme, or that contain a pair of phonemes.
            If a single key is assigned to those different single phonemes or
            to that pair of phonemes or, then using that key will be ambigous.
            The score is defined by the frequency of the least frequent
            ambigous syllable of the pair. """

        def phonemesByPos(syllable: Syllable, pos: str):
            """ Helper function """
            if pos == "preVowels":
                return syllable.phonemes_pre
            elif pos == "postVowels":
                return syllable.phonemes_post
            elif pos == "vowels":
                return syllable.phonemes_vowel
            else:
                return ""

        p1_syll = list(filter(lambda s: phoneme1 in phonemesByPos(s, pos),
                              self.syllables))

        score = 0.0
        for syll1 in p1_syll:
            if phoneme2 in phonemesByPos(syll1, pos):
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                shortSyll1 = syll1.replacePhonemeInPos(phoneme1, "", pos)
                shortSyll2 = syll1.replacePhonemeInPos(phoneme2, "", pos)

                # shortSyll1.pop( syll1.index(phoneme2) )
                score += self.getFrequency(syll1.name) \
                    + self.getFrequency(shortSyll1) \
                    + self.getFrequency(shortSyll2)  \
                    - max(self.getFrequency(syll1.name),
                          self.getFrequency(shortSyll1),
                          self.getFrequency(shortSyll2))
#                print("Score1",score)
            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInPos(phoneme1, phoneme2, pos)
                score += min(self.getFrequency(syll1.name),
                             self.getFrequency(p1_to_p2))
#                print("Score2",score)
        return score

    def analysePhonemAmbiguity(self):
        """ Determines how ambigous would the replacement of a pair of phonemes
            by a variable phoneme meaning Either of these Phonemes be over the
            collection of syllables. Low ambiguity mean a key can be assigned
            to two phonemes and the other keys will give enough context to
            resolve the right syllable."""
        print("Left hand ambiguity optimization")
        pre_vowel_inter_syll_ambiguity = {}
        post_vowel_inter_syll_ambiguity = {}
        vowel_inter_syll_ambiguity = {}
        for p1 in Phoneme.consonant_phonemes[:-1]:
            p1i = Phoneme.consonant_phonemes.index(p1)
            for p2 in Phoneme.consonant_phonemes[p1i+1:]:
                conflict = self.ambiguityScore(p1, p2, "preVowels")
                pre_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Right hand ambiguity optimization")
        for p1 in Phoneme.consonant_phonemes[:-1]:
            p1i = Phoneme.consonant_phonemes.index(p1)
            for p2 in Phoneme.consonant_phonemes[p1i+1:]:
                conflict = self.ambiguityScore(p1, p2, "postVowels")
                post_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Vowel ambiguity optimization")
        for p1 in Phoneme.vowel_phonemes[:-1]:
            p1i = Phoneme.vowel_phonemes.index(p1)
            for p2 in Phoneme.vowel_phonemes[p1i+1:]:
                conflict = self.ambiguityScore(p1, p2, "vowels")
                vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("")
        return pre_vowel_inter_syll_ambiguity, \
            post_vowel_inter_syll_ambiguity, \
            vowel_inter_syll_ambiguity

    def printAmbiguityStats(self, nb: int = -1):
        pre, post, vowels = self.analysePhonemAmbiguity()
        sorted_pre = {(k1, k2): v for (k1, k2), v in
                      sorted(pre.items(), key=lambda item: item[1])}
        sorted_post = {(k1, k2): v for (k1, k2), v in
                       sorted(post.items(), key=lambda item: item[1])}
        sorted_vowels = {(k1, k2): v for (k1, k2), v in
                         sorted(vowels.items(), key=lambda item: item[1])}

        print("Left hand minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_pre.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Right hand minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_post.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Vowels minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_vowels.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

    def printTopSyllables(self, nb: int = -1):
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb]:
            print("Syllable:", str(syl))
