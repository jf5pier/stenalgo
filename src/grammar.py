#!/usr/bin/python
# coding: utf-8
#
import sys
from dataclasses import dataclass
from itertools import permutations, chain
from copy import deepcopy
from .word import Word
import numpy as np


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
    vowel_phonemes: str = "aeiE@o°§uy5O9821"
    consonant_phonemes: str = "RtsplkmdvjnfbZwzSgNG"

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

    pair: tuple[str, str]
    frequency: float = 0.0

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency

    def __eq__(self, other) :
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
        self.phoneme_names: dict[str, Phoneme] = {}
        self.phonemes: list[Phoneme] = []

    def getPhonemes(self, phoneme_names: str) -> list[Phoneme]:
        """Get phonemes from collection, adding missing ones if needed"""
        ret: list[Phoneme] = []
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
            print("Phonemes in pos %i" % i,
                list(map(lambda p: (p.name, "%.1f" % p.posFrequency[i]),
                        self.phonemes[:nb],)),
                "\n",
            )

    def printTopPhonemesPerInvPosition(self, nb: int = -1):
        for i in range(7):
            self.phonemes.sort(key=lambda p: p.invPosFrequency[i], reverse=True)
            print("Phonemes in inverted pos -%i" % (i + 1),
                list(map(lambda p: (p.name, "%.1f" % p.invPosFrequency[i]),
                        self.phonemes[:nb],)),
                "\n",
            )

    def printBarchart(self, phoneme_order: str,
                      exhaustive_phonemes: str, vsize: int = 10):
        maxFreq = 0.0
        excluded_phonemes = list(
            filter(lambda p: p not in phoneme_order, exhaustive_phonemes)
        )
        for phoneme_name in exhaustive_phonemes:
            maxFreq = max(maxFreq, self.phoneme_names[phoneme_name].frequency)
        for i in range(vsize, 0, -1):
            toPrint = "> "
            for phoneme_name in phoneme_order:
                phoneme = self.phoneme_names[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " | "
            for phoneme_name in excluded_phonemes:
                phoneme = self.phoneme_names[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " <"
            print(toPrint)
        print("> " + phoneme_order + " | " + "".join(excluded_phonemes) + " <")
        barsWidth = len(phoneme_order) + 3
        barsWidth2 = len(excluded_phonemes) + 3
        print("^" * (barsWidth) + "|" + "^" * (barsWidth2))
        print(" " * (barsWidth - 8) + "ordered | floating", "\n")


class BiphonemeCollection:
    """
    Collection of pairs of phonemes found in syllables

    biphonemes_names: {(str,str):Biphoneme}
    biphonemes : list[Biphoneme]
    """

    def __init__(self):
        self.biphoneme_names: dict[tuple[str, str], Biphoneme] = {}
        self.biphonemes: list[Biphoneme] = []

    def getBiphonemes(self, biphoneme_names: list[tuple[str, str]]) -> list[Biphoneme]:
        """Get biphonemes from collection, adding missing ones if needed"""
        ret: list[Biphoneme] = []
        for biphoneme_name in biphoneme_names:
            if biphoneme_name not in self.biphoneme_names:
                bp = Biphoneme(biphoneme_name)
                self.biphoneme_names[biphoneme_name] = bp
                self.biphonemes.append(bp)

            ret.append(self.biphoneme_names[biphoneme_name])
        return ret

    def getBiphoneme(self, biphoneme_name: tuple[str, str]) -> Biphoneme:
        return self.getBiphonemes([biphoneme_name])[0]

    def printTopBiphonemes(self, nb: int = -1):
        self.biphonemes.sort(reverse=True)
        print(
            "Biphonemes:",
            list(map(lambda bp: (bp.pair, "%.1f" % bp.frequency), self.biphonemes[:nb])
            ), "\n",
        )

    def getPhonemesNames(self):
        """Extract single phonemes names from pairs of phonemes"""
        left = set(map(lambda p: p.pair[0], self.biphonemes))
        right = set(map(lambda p: p.pair[1], self.biphonemes))
        return "".join(set(list(left) + list(right)))

    def optimizeOrder(self):
        """Optimize the order of the phonemes found in the biphonemes
        to reduce the frequency where two phonemes would be types in
        the wrong order to produce a syllable."""
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
                mutatedPermutation[randOrder[i - 1]] = bestPermutation[randOrder[i]]
            mutatedPermutation[randOrder[shuffleSize - 1]] = tmp
            mutatedPermutation = "".join(mutatedPermutation)

            # print("Test perm:", mutatedPermutation, scan)
            for pos in chain(
                range(len(phonemes) - windowSize),
                range(len(phonemes) - windowSize, 0, -1),
            ):
                subPhonemes = mutatedPermutation[pos : pos + windowSize]
                for permutation in permutations(subPhonemes):
                    subp = "".join(permutation)
                    p = (
                        mutatedPermutation[:pos] + subp
                        + mutatedPermutation[pos + windowSize :]
                    )
                    score, negScore, badOrder = self.scorePermutation(p)
                    if score > bestScore:
                        # if score > (bestScore * 1.03) :
                        # print("New order (%0.1f > %0.1f):"%(score,bestScore), p)
                        # print("Biphonemes in wrong order:", badOrder)
                        bestScore = score
                        bestNegScore = negScore
                        bestPermutation = p
                        bestBadOrder = badOrder
        print(
            "\nBest order (ordered score %0.1f, disordered score %0.1f):\n"
            % (bestScore, bestNegScore),
            bestPermutation,
        )
        # print("Disordered:", bestBadOrder)
        return bestPermutation

    def scorePermutation(self, permutation: str):
        score = 0.0
        negScore = 0.0
        badOrder: list[Biphoneme] = []
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
    phono_words : Word
        Dictionnary of words grouped by their phonology from the Lexicon that
        contain that syllable
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
        self.spellings: dict[str, float] = {}
        self.phono_words: dict[str, list[Word]] = {}

        phonemes = Syllable.phonemeCol.getPhonemes(phoneme_names)
        self.name = "".join(list(map(lambda p: p.name, phonemes)))
        self.frequency : float = frequency
        self.spellings[spelling] = frequency


        firstVowelPos = -1
        lastVowelPos = -1
        verbose = True if phoneme_names == "" else False
        for pos, phoneme in enumerate(phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(phonemes) - pos - 1
            )
            if verbose:
                print(phoneme, phoneme.frequency)
            self.phonemes.append(phoneme)
            if firstVowelPos == -1 and not phoneme.isVowel():
                if verbose:
                    print("Left hand consonant", phoneme)
                phoneme_pre = Syllable.preVowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_pre.increaseFrequency(frequency)
                self.phonemes_pre.append(phoneme_pre)
            elif firstVowelPos != -1 and not phoneme.isVowel():
                if verbose:
                    print("Right hand consonant", phoneme)
                phoneme_post = Syllable.postVowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_post.increaseFrequency(frequency)
                self.phonemes_post.append(phoneme_post)
            # Break down the syllable into consonants-vowels-consonants
            if phoneme.isVowel():
                if verbose:
                    print("Vowel", phoneme)
                phoneme_vowel = Syllable.vowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_vowel.increaseFrequency(frequency)
                self.phonemes_vowel.append(phoneme_vowel)

                if firstVowelPos == -1:
                    firstVowelPos = pos
                lastVowelPos = pos

        # Track the cooccurences of phonemes pairs in the first
        # consonnants group
        if firstVowelPos >= 2:
            for pos1, phoneme1 in enumerate(phonemes[: firstVowelPos - 1]):
                for phoneme2 in phonemes[pos1 + 1 : firstVowelPos]:
                    biphoneme = Syllable.preVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Left hand biphoneme", biphoneme)
                    self.biphonemes_pre.append(biphoneme)

        # Track the cooccurences of phonemes pairs in the last
        # consonnants group
        if lastVowelPos <= len(phonemes) - 3:
            for pos1, phoneme1 in enumerate(phonemes[lastVowelPos + 1 : -1]):
                for phoneme2 in phonemes[lastVowelPos + pos1 + 2 :]:
                    biphoneme = Syllable.postVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Right hand biphoneme", biphoneme)
                    self.biphonemes_post.append(biphoneme)

        # Track the cases where multiple vowels are part of the
        # middle (inclue semivowels??)
        if firstVowelPos < lastVowelPos:
            for pos1, phoneme1 in enumerate(phonemes[firstVowelPos:lastVowelPos]):
                for phoneme2 in phonemes[firstVowelPos + pos1 + 1 : lastVowelPos + 1]:
                    biphoneme = Syllable.multiVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Vowel biphoneme", biphoneme)
                    self.biphonemes_vowel.append(biphoneme)

        # print("pho",self.phonemes, "pre",self.phonemes_pre,
        # "post",self.phonemes_post,
        #      "vow",self.phonemes_vowel, "bpre", self.biphonemes_pre, "bpost",
        #      self.biphonemes_post, "bvow",self.biphonemes_vowel)

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos, phoneme in enumerate(self.phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(self.phonemes) - pos - 1
            )
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

    def trackWord(self, word: Word):
        if word.phonology in self.phono_words:
            self.phono_words[word.phonology].append(word)
        else:
            self.phono_words[word.phonology] = [word]

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
        Syllable.preVowelPhonemeCol.printBarchart(order, Phoneme.consonant_phonemes)

        print("Right hand optimization :")
        order = Syllable.postVowelBiphonemeCol.optimizeOrder()
        Syllable.postVowelPhonemeCol.printBarchart(order, Phoneme.consonant_phonemes)

        print("Vowel optimization :")
        order = Syllable.multiVowelBiphonemeCol.optimizeOrder()
        Syllable.vowelPhonemeCol.printBarchart(order, Phoneme.vowel_phonemes)
        print("")

    def replacePhonemeInPos(self, phoneme1: Phoneme|str, phoneme2: Phoneme|str, pos: str):
        """Replace a phoneme in one of 3 positions in a syllable"""
        if pos == "preVowels":
            pre = "".join(map(str, self.phonemes_pre))
            pre = pre.replace(str(phoneme1), str(phoneme2))
            return (
                pre
                + "".join(map(str, self.phonemes_vowel))
                + "".join(map(str, self.phonemes_post))
            )
        elif pos == "postVowels":
            post = "".join(map(str, self.phonemes_post))
            post = post.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemes_pre))
                + "".join(map(str, self.phonemes_vowel))
                + post
            )
        elif pos == "vowels":
            vowel = "".join(map(str, self.phonemes_vowel))
            vowel = vowel.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemes_pre))
                + vowel
                + "".join(map(str, self.phonemes_post))
            )
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
        return ( "".join([str(p) for p in self.phonemes])
            + " > " + ", ".join([
                    str(spel) + ": %.1f" % freq
                    for (spel, freq) in self.sortedSpellings()[:4]
                ])
            + " > SyllFreq " + "%.1f %.1f"
            % ( self.frequency,
                sum([freq for (spel, freq) in self.sortedSpellings()[:4]]),
            )
        )


class SyllableCollection:
    """
    Collection of all Syllables found in a lexicon/corpus

    syllable_names: dict[str, Syllable]
    syllables : [Syllable]
    """

    syllable_names: dict[str, Syllable] = {}
    syllables: list[Syllable] = []

    def updateSyllable(self, syllable_name: str, spelling: str,
                       addedfrequency: float, word: Word | None = None,):
        """Updates syllable from collection, adding missing ones if needed"""
        if syllable_name not in self.syllable_names:
            s = Syllable(syllable_name, spelling)
            self.syllable_names[syllable_name] = s
            self.syllables.append(s)
        # Adds the spelling if it is missing
        self.syllable_names[syllable_name].increaseSpellingFrequency(
            spelling, addedfrequency
        )
        # Keep track of words using syllable
        if word is not None:
            self.syllable_names[syllable_name].trackWord(word)

    #def getSyllable(self, syllable_name: str, spelling: str | None = None,
    #                frequency: float = 0.0) -> Syllable:
    #    """Get syllable from collection, adding missing ones if needed"""
    def getSyllable(self, syllable_name: str) -> Syllable | None:
        """Get syllable from collection, or None"""
        #if spelling is not None:
        #    self.updateSyllable(syllable_name, spelling, frequency)
        return self.syllable_names[syllable_name] \
            if syllable_name in self.syllable_names else None

    def getFrequency(self, syllable: Syllable | str) -> float:
        if type(syllable) is Syllable:
            name = syllable.name
        elif type(syllable) is str:
            name = syllable
        else:
            print("Type syllable|str not found", syllable)
            sys.exit(1)

        if name not in self.syllable_names:
            #print("Not found syllable", name)
            return 0.0
        else:
            # print("Found", name, self.syllable_names[name].frequency )
            return self.syllable_names[name].frequency

    #def getWordsByPhono(self, phono: str) -> list[Word]:
    #    # return list(filter(lambda w: w.phonology == phono, self.words))
    #    return self.phono_words[phono]

    def syllabicAmbiguityScore(self, phoneme1: str, phoneme2: str, pos: str) -> float:
        """Ambiguity is defined by the existance of two syllables that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes or, then using that key will be ambigous.
        The score is defined by the frequency of the least frequent
        ambigous syllable of the pair."""

        def phonemesByPos(syllable: Syllable, pos: str):
            """Helper function"""
            if pos == "preVowels":
                return syllable.phonemes_pre
            elif pos == "postVowels":
                return syllable.phonemes_post
            elif pos == "vowels":
                return syllable.phonemes_vowel
            else:
                return ""

        phoneme1_syllables = list(
            filter(lambda s: phoneme1 in phonemesByPos(s, pos), self.syllables)
        )

        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in phonemesByPos(syll1, pos):
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                short_syllable1 = syll1.replacePhonemeInPos(phoneme1, "", pos)
                short_syllable2 = syll1.replacePhonemeInPos(phoneme2, "", pos)

                # short_syllable1.pop( syll1.index(phoneme2) )
                score += (
                    self.getFrequency(syll1.name)
                    + self.getFrequency(short_syllable1)
                    + self.getFrequency(short_syllable2)
                    - max(
                        self.getFrequency(syll1.name),
                        self.getFrequency(short_syllable1),
                        self.getFrequency(short_syllable2),
                    )
                )
            #                print("Score1",score)
            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInPos(phoneme1, phoneme2, pos)
                score += min(self.getFrequency(syll1.name), self.getFrequency(p1_to_p2))
        #                print("Score2",score)
        return score

    def lexicalAmbiguityScore(self, phoneme1: str, phoneme2: str, pos: str) -> float:
        """Ambiguity is defined by the existance of two words that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes, then using that key will be ambigous.
        The score is defined by the frequnecy of the sum of least frequent
        ambgious words."""

        def phonemesByPos(syllable: Syllable, pos: str):
            """Helper function"""
            if pos == "preVowels":
                return syllable.phonemes_pre
            elif pos == "postVowels":
                return syllable.phonemes_post
            elif pos == "vowels":
                return syllable.phonemes_vowel
            else:
                return ""

        phoneme1_syllables = list(
            filter(lambda s: phoneme1 in phonemesByPos(s, pos), self.syllables)
        )
        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in phonemesByPos(syll1, pos):
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                base_score_short1 = 0.0
                base_score_short2 = 0.0
                short_syllable1 = syll1.replacePhonemeInPos(phoneme1, "", pos)
                short_syllable2 = syll1.replacePhonemeInPos(phoneme2, "", pos)
                for phono_word1 in syll1.phono_words:
                    base_score1 = sum(map(lambda w: w.frequency, syll1.phono_words[phono_word1]))
                    word: Word = syll1.phono_words[phono_word1][0]
                    phono_short_word1 = word.replaceSyllables(
                        syll1.name, short_syllable1
                    )
                    phono_short_syll1 = self.getSyllable(phono_short_word1)
                    if phono_short_syll1 is not None:
                        phono_short_words1 = phono_short_syll1.phono_words
                        base_score_short1 = (
                            sum(map(lambda w: w.frequency, phono_short_words1[phono_short_word1]))
                            if phono_short_word1 in phono_short_words1
                            else 0.0
                        )

                    phono_short_word2 = word.replaceSyllables(
                        syll1.name, short_syllable2)
                    phono_short_syll2 = self.getSyllable(phono_short_word2)
                    if phono_short_syll2 is not None:
                        phono_short_words2 = phono_short_syll2.phono_words
                        base_score_short2 = (
                            sum(map(lambda w: w.frequency, phono_short_words2[phono_short_word2]))
                            if phono_short_word2 in phono_short_words2
                            else 0.0
                        )
                    least_scores = sum(sorted(
                        [base_score1, base_score_short1, base_score_short2])[:-1])
                    score += least_scores
            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInPos(phoneme1, phoneme2, pos)
                for phono_word1 in syll1.phono_words:
                    base_score1 = sum(map(lambda w: w.frequency, syll1.phono_words[phono_word1]))
                    word = syll1.phono_words[phono_word1][0]
                    phono_word2 = word.replaceSyllables(syll1.name, p1_to_p2)
                    phono_syll2= self.getSyllable(p1_to_p2)
                    if phono_syll2 is not None :
                        phono_words2 = phono_syll2.phono_words
                        if phono_word2 in phono_words2:
                            base_score2 = sum(map(lambda w: w.frequency, phono_words2[phono_word2]))
                            score += min(base_score1, base_score2)
        return score

    def analysePhonemSyllabicAmbiguity(self):
        """Determines how ambigous would the replacement of a pair of phonemes
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
            for p2 in Phoneme.consonant_phonemes[p1i + 1 :]:
                conflict = self.syllabicAmbiguityScore(p1, p2, "preVowels")
                pre_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Right hand ambiguity optimization")
        for p1 in Phoneme.consonant_phonemes[:-1]:
            p1i = Phoneme.consonant_phonemes.index(p1)
            for p2 in Phoneme.consonant_phonemes[p1i + 1 :]:
                conflict = self.syllabicAmbiguityScore(p1, p2, "postVowels")
                post_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Vowel ambiguity optimization")
        for p1 in Phoneme.vowel_phonemes[:-1]:
            p1i = Phoneme.vowel_phonemes.index(p1)
            for p2 in Phoneme.vowel_phonemes[p1i + 1 :]:
                conflict = self.syllabicAmbiguityScore(p1, p2, "vowels")
                vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("")
        return (
            pre_vowel_inter_syll_ambiguity,
            post_vowel_inter_syll_ambiguity,
            vowel_inter_syll_ambiguity,
        )

    def analysePhonemLexicalAmbiguity(self):
        """Similairly to the Syllabic Ambiguity, but over the whole lexicon:
        determines if a key assigned  to two phonemes will create
        ambiguities when typing a full word. Low ambiguity means that the
        other keys in the syllable and the other syllables of the word
        provide enough context."""
        print("Left hand ambiguity optimization")
        pre_vowel_inter_syll_ambiguity = {}
        post_vowel_inter_syll_ambiguity = {}
        vowel_inter_syll_ambiguity = {}
        for p1 in Phoneme.consonant_phonemes[:-1]:
            p1i = Phoneme.consonant_phonemes.index(p1)
            for p2 in Phoneme.consonant_phonemes[p1i + 1 :]:
                conflict = self.lexicalAmbiguityScore(p1, p2, "preVowels")
                pre_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Right hand ambiguity optimization")
        for p1 in Phoneme.consonant_phonemes[:-1]:
            p1i = Phoneme.consonant_phonemes.index(p1)
            for p2 in Phoneme.consonant_phonemes[p1i + 1 :]:
                conflict = self.lexicalAmbiguityScore(p1, p2, "postVowels")
                post_vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("Vowel ambiguity optimization")
        for p1 in Phoneme.vowel_phonemes[:-1]:
            p1i = Phoneme.vowel_phonemes.index(p1)
            for p2 in Phoneme.vowel_phonemes[p1i + 1 :]:
                conflict = self.lexicalAmbiguityScore(p1, p2, "vowels")
                vowel_inter_syll_ambiguity[(p1, p2)] = conflict

        print("")
        return (
            pre_vowel_inter_syll_ambiguity,
            post_vowel_inter_syll_ambiguity,
            vowel_inter_syll_ambiguity,
        )

    def printSyllacbicAmbiguityStats(self, nb: int = -1):
        pre, post, vowels = self.analysePhonemSyllabicAmbiguity()
        sorted_pre = {
            (k1, k2): v for (k1, k2), v in sorted(pre.items(), key=lambda item: item[1])
        }
        sorted_post = {
            (k1, k2): v
            for (k1, k2), v in sorted(post.items(), key=lambda item: item[1])
        }
        sorted_vowels = {
            (k1, k2): v
            for (k1, k2), v in sorted(vowels.items(), key=lambda item: item[1])
        }

        print("Left hand syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_pre.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Right hand syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_post.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Vowels syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_vowels.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

    def printLexicalAmbiguityStats(self, nb: int = -1):
        pre, post, vowels = self.analysePhonemLexicalAmbiguity()
        sorted_pre = {
            (k1, k2): v for (k1, k2), v in sorted(pre.items(), key=lambda item: item[1])
        }
        sorted_post = {
            (k1, k2): v
            for (k1, k2), v in sorted(post.items(), key=lambda item: item[1])
        }
        sorted_vowels = {
            (k1, k2): v
            for (k1, k2), v in sorted(vowels.items(), key=lambda item: item[1])
        }

        print("Left hand lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_pre.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Right hand lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_post.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Vowels lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_vowels.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

    def printTopSyllables(self, nb: int = -1):
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb]:
            print("Syllable:", str(syl))
