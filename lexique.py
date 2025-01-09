#!/usr/bin/python
# coding: utf-8
#
# This class provides functions to read Lexique version 383 [1,2] for its data
# concerning French word ortograph, frequency, grammatical info, phonology and
# phonetic syllable breakdow.  It the corrects the orthographic syllable
# breakdow using the phoneme to graphem association of LexiqueInfra [3].
# The output is a simplified French Lexique with corrected ortographic
# syllables.
#
# 1. New, B., Pallier, C., Brysbaert, M., Ferrand, L. (2004)
#  Lexique 2 : A New French Lexical Database.
#  Behavior Research Methods, Instruments, & Computers, 36 (3), 516-524.
# 2. New, B., Brysbaert, M., Veronis, J., & Pallier, C. (2007).
#  The use of film subtitles to estimate word frequencies.
#  Applied Psycholinguistics, 28(4), 661-677.
# 3. Gimenes, M., Perret, C., & New, B. (2020).
#  Lexique-Infra: grapheme-phoneme, phoneme-grapheme regularity, consistency,
#  and other sublexical statistics for 137,717 polysyllabic French words.
#  Behavior Research Methods. doi.org/10.3758/s13428-020-01396-2
#
import sys
import csv
from copy import deepcopy
from dataclasses import dataclass
from src.grammar import Syllable, SyllableCollection
# from src.word import GramCat
from typing import List

problemList = ["autocritiquer", "fjord", "carter", "cappuccino", "capucino",
               "capuccino", "cappuccinos",  "mamma", "voyouterie",
               "voyoucratie", "jungien", "jungiens", "mails", "fjords",
               "sprinteur", "sprinteurs", "pierreries", "quidams",
               "voyoutisme", "fettucine", "requiems",  "suppliât", "niquait",
               "télétexte", "tangerine", "réattaquait", "chopper",
               "tangerine", "mail"]

foreignList = ["ausweis", "beagle", "beagles", "bintje", "boghei", "borchtch",
               "brainstorming", "breitschwanz", "catgut", "catguts",
               "challenge", "challengers", "cheeseburgers", "chippendale",
               "chippendales", "chorizos", "cinzano", "coache", "coaches",
               "coachs", "conjungo", "conjungos", "crumble", "curant",
               "duces", "foil", "gun", "highlander", "hydrofoil", "guns",
               "highlanders", "interviewer", "jingle", "jingles", "jodler",
               "jonkheer", "kandjar", "kierkegaardienne", "kommandantur",
               "lazzis", "lunches", "lychees", "mailing", "mile", "muchas",
               "nikkei", "palmer", "panzer", "panzers", "people", "pickles",
               "pschent", "quattrocento", "quite", "ranch", "rancher",
               "ranchs", "ranches", "roadster", "rock'n'roll", "sandjak",
               "sandwiches", "sandwichs", "schampooing", "schampooiner",
               "shampooiner", "shampooing", "shampooings", "puzzle",
               "puzzles", "rinforzando", "rough", "rhythm'n'blues", "single",
               "shogun", "shôgun", "skinhead", "skinheads", "smiley",
               "teenager", "training", "trecento", "valpolicella", "wharf",
               "whig", "whigs", "whipcord", "whiskey", "whiskies", "whiskys",
               "whist", "whisky", "wildcat", "winchesters"]

ignoredList = problemList + foreignList


def printVerbose(word: str, msg: list):
    # return
    if word in [""]:  # ["soleil"] :
        print(word, " :\n", " ".join(map(str, msg)))


@dataclass
class Word:
    """
    Representation of a Word defined by an orthograph and a pronunciation

    ortho : str
        The word's orthograph
    phonology : str
        Collection of phonemes representing the pronunciation
    lemme : str
        Root of the word
    gram_cat : GramCat
        Grammatical category
    cgramortho : [GramCat]
        All grammatical categories of the words sharing this orthograph
    gender : str
        Gender of the noun or adjectiv
    number : str
        Number (singular or plural) of the noun or adjectiv
    info_verb : str
        Conjugaiton of the verb
    syll : str
        Syllables in phonemes as provided by the Lexique383
    cv-cv : str
        Consonant-Vowel brokendown by syllable
    orthosyll : str
        Orthograph of the syllables (some are mistaken)
    frequency : float
        Frequency of the word in the written chosen corpus
    frequencyFilm : float
        Frequency of the word in the film chosen corpus
    syll_cv : [[str]]
        Syllables in phonemes as provided by the LexicInfra and
        groupped by Lexique383 cv_cv field into list of phonems
    orthosyll_cv : [[str]]
        Orthograph of the syllables as provided by the LexicInfra
        and groupped by Lexique383 cv_cv field into list of phonems' graphems
    """
    ortho: str
    phonology: str
    lemme: str
    gram_cat: str  # GramCat
    ortho_gram_cat: str  # List[GramCat]
    gender: str
    number: str
    info_verb: str
    syll: str
    cv_cv: str
    orthosyll: str
    frequency: float
    frequencyFilm: float

    def __post_init__(self):
        self.syll_cv: list[str] = deepcopy([])
        self.orthosyll_cv: list[str] = deepcopy([])
        self.orig_syll: str = deepcopy(self.syll)
        self.orig_cv_cv: str = deepcopy(self.cv_cv)
        self.fix_x_k_s()
        self.fix_g_dZ()
        self.fix_j_dZ()
        self.fix_ch_tS()

    def fix_x_k_s(self):
        # X sound should not be broken into 2 consonnants (k-s) in 2 syllables
        if (self.isWellFormedCVSyll()
                and "x" in self.ortho and "k-s" in self.syll):
            printVerbose(self.ortho, ["fix_x_k_s"])
            pos = self.syll.index("k-s")
            self.syll = self.syll[0:pos] + "-ks" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_x_k_s()  # recurse if there is more than one

    def fix_g_dZ(self):
        # adagio a-a.d-d.a-a.g-dZ.i-j.o-o a-dad-Zjo V-CVC-CYV
        if (self.isWellFormedCVSyll()
                and "g" in self.ortho and "d-Z" in self.syll):
            printVerbose(self.ortho, ["fix_g_dZ"])
            pos = self.syll.index("d-Z")
            self.syll = self.syll[0:pos] + "-dZ" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_g_dZ()  # recurse if there is more than one

    def fix_j_dZ(self):
        # banjo b-b.an-@.j-dZ.o-o b@d-Zo CVC-CV
        if (self.isWellFormedCVSyll()
                and "j" in self.ortho and "d-Z" in self.syll):
            printVerbose(self.ortho, ["fix_j_dZ"])
            pos = self.syll.index("d-Z")
            self.syll = self.syll[0:pos] + "-dZ" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_j_dZ()  # recurse if there is more than one

    def fix_ch_tS(self):
        # machos m-m.a-a.ch-tS.o-o.s-# mat-So mat-So CVC-CV CVC-C
        if self.isWellFormedCVSyll() and "t-S" in self.syll:
            printVerbose(self.ortho, ["fix_ch_tS"])
            pos = self.syll.index("t-S")
            self.syll = self.syll[0:pos] + "-tS" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_ch_tS()  # recurse if there is more than one

    @staticmethod
    def fixLexiqueInfraGraphPhon(graphem_phonem: str):
        # Apply correction to LexiqueInfra Graphem-Phonem correspondance
        # that are represented by a differente CV-CV in Lexique
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "cc-ks", "c-k.c-s")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "xc-ksk", "x-ks.c-k")  # exclame
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "rr-RR", "r-R.r-R")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "oy-waj", "o-wa.y-j")
        # accastillage a-a.cc-k.a-a.s-s.t-t.ill-ij.a-a.ge-Z
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ill-ij", "i-i.ll-j")
        # acuité a-a.c-k.ui-8i.t-t.é-e
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ui-8i", "u-8.i-i")
        # aiguille ai-e.gu-g8.i-i.ll-j.e-#
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "gu-g8", "g-g.u-8")
        # asseye a-a.ss-s.ey-Ej.e-# a-sEj
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ey-Ej", "e-E.y-j")
        # bienheureuse
        # b-b.i-j.en-5n.h-#.eu-2.r-R.eu-2.s-z.e-# bj5-n2-R2z CYV-CV-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "en-5n", "e-5.n-n")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "enn-@n", "en-@.n-n")  # désennuie
        # This is not the perfect treatment, it creates ortho-syll
        # like e-nivre instead of en-ivre
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "en-@n", "e-@.n-n")  # enamourée
        # coordinateurs c-k.oo-oO.r-R.d-d.i-i.n-n.a-a.t-t.eu-9.r-R.s-#
        # ko-OR-di-na-t9R ko-OR-di-na-t9R CV-VC-CV-CV-CVC CV-VC-CV-CV-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "oo-oO", "o-o.o-O")
        # mezzos m-m.e-E.zz-dz.o-o.s-# mEd-zo mEd-zo CVC-CV CVC-C
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "zz-dz", "z-d.z-z")
        # suggère s-s.u-y.gg-gZ.è-E.r-R.e-# syg-ZER syg-ZER CVC-CVC CVC-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "gg-gZ", "g-g.g-Z")
        # ubiquiste u-y.b-b.i-i.qu-k8.i-i.s-s.t-t.e-#
        # y-bi-k8ist y-bi-k8ist V-CV-CYVCC V-CV-CYVCC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "qu-k8", "q-k.u-8")
        # vieillie v-v.i-j.ei-e.lli-ji.e-# vje-ji vje-ji CYV-YV CYV-YV
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "lli-ji", "ll-j.i-i")
        return graphem_phonem

    @staticmethod
    def fixAssociation(graphem_phoneme: str, badAsso: str,
                       goodAsso: str) -> str:
        if badAsso in graphem_phoneme:
            pos = graphem_phoneme.index(badAsso)
            return graphem_phoneme[0:pos] + goodAsso + \
                graphem_phoneme[pos+len(badAsso):]
        return graphem_phoneme

    def phonemesToSyllables(self, withSilent:bool =True, symbol: str=""):
        if withSilent:
            return [symbol.join(syll) for syll in self.syll_cv]
        else:
            return [symbol.join(syll).replace("#", "")
                    for syll in self.syll_cv]

    def lettersToSyllables(self, symbol: str =""):
        return [symbol.join(map(lambda cv_lett: cv_lett[1], syll))
                for syll in self.orthosyll_cv]

    def syllablesToWord(self):
        return "".join(self.phonemesToSyllables())

    def writeOrthoSyll(self):
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        return "|".join(self.lettersToSyllables(symbol="_"))

    def writePhonoSyll(self):
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        return "|".join(self.phonemesToSyllables(symbol="_"))

    def breakdownSyllables(self, graphem_phoneme: str):
        # Uses the CV-CV breakdown of phonemes from Lexique with the
        # grapheme-phoneme decomposition of LexiqueInfra to find
        # the graphemes parts of each syllable
        printVerbose(self.ortho, ["Breakdown"])
        if self.syll_cv != [] or self.orthosyll_cv != []:
            printVerbose(self.ortho, ["already:", self.syll_cv,
                                      self.orthosyll_cv])
            # print("Word ", self.ortho, "is already already broke down")
            # print(self.syllablesToWord())
            # print(self.syll_cv, self.orthosyll_cv)
            # print(graphem_phoneme)
            return
        syll_phon = []
        syll_graph = []
        skip_next_Y = False
        skip_next_C = False
        # if True:
        graph_phon_pairs = []
        try:
            graphem_phoneme = Word.fixLexiqueInfraGraphPhon(graphem_phoneme)
            graph_phon_pairs = [(gp.split("-")[0], gp.split("-")[1])
                                for gp in graphem_phoneme.split(".")]
            cv_split = self.cv_cv.split("-")
            for syllNb, cv_syll in enumerate(cv_split):
                _ = syllNb == len(cv_syll) - 1
                syll_phon = []
                syll_graph = []
                for cvNb, cv_phoneme in enumerate(cv_syll):
                    printVerbose(self.ortho, [
                        syllNb, cv_syll, cvNb, cv_phoneme, "\n", "g/p:",
                        graph_phon_pairs[0][0], graph_phon_pairs[0][1],
                        "\n", "skip Y/C:", skip_next_Y, skip_next_C])
                    if cv_phoneme == "C":
                        if skip_next_C:
                            skip_next_C = False
                            continue

                        if (graph_phon_pairs[0][0] in ["ch"] and
                                graph_phon_pairs[0][1] in ["tS"]):
                            skip_next_C = True
                        elif (graph_phon_pairs[0][0] in ["x"] and
                                graph_phon_pairs[0][1] in ["ks", "gz"]):
                            # ajax  a.j.a.x a-a.j-Z.a-a.x-ks a-Zaks V-CVCC
                            skip_next_C = True
                            printVerbose(
                                self.ortho, ["x: skip_next_C ", skip_next_C])
                        elif (graph_phon_pairs[0][0] in ["g", "j"]
                              and graph_phon_pairs[0][1] == "dZ"):
                            # adagio a-a.d-d.a-a.g-dZ.i-j.o-o
                            # a-da-dZjo V-CV-CCYV after fix
                            skip_next_C = True
                        elif (graph_phon_pairs[0][0] in ["pp"]
                              and (cvNb == len(cv_syll) - 1 or
                              (cv_syll[cvNb+1] == "C"
                               and graph_phon_pairs[1][0] not in ["l", "r"]))):
                            # appropriation
                            # a-a.pp-p.r-R.o-o.p-p.r-R.i-ij.a-a.t-s.i-j.on-§
                            # a-pRo-pRi-ja-sj§ V-CCV-CCV-YV-CYV
                            skip_next_C = True

                    if cv_phoneme == "V":
                        while graph_phon_pairs[0][1] == "#":
                            printVerbose(self.ortho, ["Pop # in V"])
                            graph_phon = graph_phon_pairs.pop(0)
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                printVerbose(
                                    self.ortho, ["no more graph/phon"])
                                self.syll_cv.append(syll_phon)
                                self.orthosyll_cv.append(syll_graph)
                                return
                        # appropriation
                        # a-a.pp-p.r-R.o-o.p-p.r-R.i-ij.a-a.t-s.i-j.on-§
                        # a-pRo-pRi-ja-sj§ V-CCV-CCV-YV-CYV
                        # balaye b-b.a-a.l-l.ay-Ej.e-# ba-lEj CV-CVY
                        if graph_phon_pairs[0][1] in ["ij", "Ej"]:
                            skip_next_Y = True

                    if cv_phoneme == "Y":
                        while graph_phon_pairs[0][1] == "#":
                            printVerbose(self.ortho, ["Pop # in Y"])
                            # admixtion a-a.d-d.m-m.i-i.x-ks.t-#.i-j.on-§
                            graph_phon = graph_phon_pairs.pop(0)
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                return
                        if graph_phon_pairs[0][0] not in [
                                "i", "ll", "o", "y", "u", "ill",
                                "il", "ou", "l", "lli", "w", "ï"]:
                            printVerbose(
                                self.ortho, ["skip Y of", graph_phon_pairs[0]])
                            skip_next_Y = False
                            continue
                        if skip_next_Y:
                            skip_next_Y = False
                            # Rare english words and other exceptions
                            printVerbose(
                                self.ortho, ["skip next Y of",
                                             graph_phon_pairs[0]])
                            continue

                    if len(graph_phon_pairs) > 0:
                        graph_phon = graph_phon_pairs.pop(0)
                        if (graph_phon[1] == "Ej"
                                and cvNb <= len(cv_syll) - 2
                                and cv_syll[cvNb+1] == "C"):
                            # ace a-Ej.c-s.e-# Ejs VYC englis word
                            skip_next_Y = True
                        elif (graph_phon[1] == "ij"
                              and cvNb == len(cv_syll) - 1):
                            # atrium a-a.t-t.r-R.i-ij.u-O.m-m a-tRi-jOm
                            # V-CCV-YVC
                            skip_next_Y = True
                        # silent phonemes are not matched by a cv_phoneme
                        while graph_phon[1] == "#":
                            printVerbose(self.ortho, ["Pop # at end"])
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                printVerbose(
                                    self.ortho, ["no more graph/phon"])
                                self.syll_cv.append(syll_phon)
                                self.orthosyll_cv.append(syll_graph)
                                return
                            graph_phon = graph_phon_pairs.pop(0)
                        syll_graph.append((cv_phoneme, graph_phon[0]))
                        syll_phon.append(graph_phon[1])
                    printVerbose(
                        self.ortho, ["appended g/p ", syll_graph, syll_phon])
                    if len(graph_phon_pairs) == 0:
                        printVerbose(self.ortho, ["no more graph/phon"])
                        self.syll_cv.append(syll_phon)
                        self.orthosyll_cv.append(syll_graph)
                        return

                self.syll_cv.append(syll_phon)
                self.orthosyll_cv.append(syll_graph)
                # Append silent phonemes to end of previous syllable
                while (len(graph_phon_pairs) > 0
                       and graph_phon_pairs[0][1] == "#"):
                    graph_phon = graph_phon_pairs.pop(0)
                    self.syll_cv[-1].append(graph_phon[1])
                    self.orthosyll_cv[-1].append(("#", graph_phon[0]))
                if len(graph_phon_pairs) == 0:
                    printVerbose(self.ortho, ["no more graph/phon"])
                    return

            if len(graph_phon_pairs) > 0:
                print("Left-over graphem-phoneme not assigned")
                print(self.ortho, graphem_phoneme, self.syll, self.cv_cv)
                print(self.syll_cv)
                print(self.orthosyll_cv, "extra:", graph_phon_pairs)
                sys.exit(1)
        # if False:
        except Exception as e:
            print(e)
            print(self.ortho, graphem_phoneme, self.orig_syll,
                  self.syll, self.orig_cv_cv, self.cv_cv)
            print(self.syll_cv)
            print(self.orthosyll_cv)
            print(syll_phon, syll_graph, "extra:", graph_phon_pairs)
            sys.exit(1)
        return

    def isWellFormedCVSyll(self):
        # Verify cv_cv and syll have the same form
        a = self.cv_cv.split("-")
        b = self.syll.split("-")
        return len(a) == len(b) and list(map(len, a)) == list(map(len, b))

    def isWellFormedCVOrthosyll(self):
        # Verify cv_cv and orthosyll have generally the same form
        a = self.cv_cv.split("-")
        b = self.orthosyll.split("-")
        return len(a) == len(b)

    def isSyllConsensus(self):
        # Verify if the phonologic syll and syll_cv match once silent phonemes
        # are removed
        if self.isWellFormedCVSyll():
            for syll, syll_cv in zip(self.syll.split("-"), self.syll_cv):
                if syll != "".join(syll_cv).replace("#", ""):
                    return False
            return True
        return False

    def isOrthoSyllConsensus(self):
        # Verify if the orthograph of orthosyll and orthosyll_cv match
        if self.isWellFormedCVOrthosyll():
            for orthosyll, orthosyll_cv in zip(self.orthosyll.split("-"),
                                               self.orthosyll_cv):
                if orthosyll != "".join(orthosyll_cv):
                    return False
            return True
        return False


class Lexique:

    #picked = []
    words: list[Word] = []
    words_by_ortho: dict[str, list[Word]] = {}
    word_source: str = "resources/Lexique383.tsv"
    graphem_phoneme_source: str = "resources/LexiqueInfraCorrespondance.tsv"
    sylCol: SyllableCollection = SyllableCollection()

    def __init__(self):
        self.words = self.read_corpus()

    def read_corpus(self):
        with open(self.word_source) as f:
            corpus = csv.DictReader(f, delimiter='\t')

            for corpus_word in corpus:
                if (corpus_word["ortho"] is not None
                    and corpus_word["ortho"][0] != "#"
                        and corpus_word["ortho"] not in ignoredList):
                    printVerbose(corpus_word["ortho"], ["Creating word"])
                    word = Word(ortho=corpus_word["ortho"],
                                phonology=corpus_word["phon"],
                                lemme=corpus_word["lemme"],
                                # gram_cat = GramCat[corpus_word["cgram"]] if \
                                #        corpus_word["cgram"] != '' else None,
                                # ortho_gram_cat = [GramCat[gc] for gc in \
                                #        corpus_word["cgramortho"].split(",")],
                                gram_cat=corpus_word["cgram"],
                                ortho_gram_cat=corpus_word["cgramortho"],
                                gender=corpus_word["genre"],
                                number=corpus_word["nombre"],
                                info_verb=corpus_word["infover"],
                                syll=corpus_word["syll"],
                                cv_cv=corpus_word["cv-cv"],
                                orthosyll=corpus_word["orthosyll"],
                                frequency=float(corpus_word["freqlivres"]),
                                frequencyFilm=float(corpus_word["freqfilms2"])
                                )
                    self.words.append(word)
                    same_ortho = self.words_by_ortho.get(corpus_word["ortho"],
                                                         deepcopy([])) + [word]
                    self.words_by_ortho[corpus_word["ortho"]] = same_ortho
        self.breakdownSyllables()
        return self.words

    @staticmethod
    def associationToPhonology(asso: str) -> str:
        asso_split = map(lambda s:  s.split("-"), asso.split("."))
        phono = list(map(lambda s: s[1], asso_split))
        return "".join(phono).replace("#", "")

    def breakdownSyllables(self):
        with open(self.graphem_phoneme_source) as f:
            graph_phon_asso = csv.DictReader(f, delimiter='\t')
            for asso_word in graph_phon_asso:
                printVerbose(asso_word["item"], ["BreakdownSyllables"])
                if (asso_word["item"][0] != "#"
                        and asso_word["item"] not in ignoredList):
                    corpus_words = self.words_by_ortho[asso_word["item"]]
                    foundInLexicon = False
                    for word in corpus_words:
                        printVerbose(
                            word.ortho,
                            ["corpus_words found, phono:", word.phonology,
                             asso_word["phono"]])
                        if word.phonology == asso_word["phono"]:
                            foundInLexicon = True
                            word.breakdownSyllables(asso_word["assoc"])

                    if not foundInLexicon:
                        # Some words in LexiqueInfra have the wrong phology,
                        # but the association seems right. We get the phonology
                        # from the association and try a second time to find a
                        # matching word.
                        asso_word["phono"] = Lexique.associationToPhonology(
                            asso_word["assoc"])
                        for word in corpus_words:
                            if word.phonology == asso_word["phono"]:
                                foundInLexicon = True
                                word.breakdownSyllables(asso_word["assoc"])

                    if not foundInLexicon:
                        # Problem.
                        lexicalPhono = list(
                            map(lambda w: w.phonology,
                                filter(lambda w: w.ortho ==
                                       asso_word["item"], corpus_words)))
                        print("Not found in Lexique383",
                              asso_word["item"], asso_word["phono"],
                              Lexique.associationToPhonology(
                                  asso_word["assoc"]),
                              lexicalPhono)
        return

    @staticmethod
    def isVowel(char: str):
        return char in "aeiouy2589OE§@°"

    @staticmethod
    def moveDualPhonem(syllables: list[str]) -> list[str]:
        # Move dual-phonems representation ij and gz to better compare
        # to Lexique383
        # This function is only used to compare the analysis to Lexique383.
        # Its result is currently not kept

        if (len(syllables) <= 1):
            return syllables
        ret: list[str] = []
        semivowelToMove = ""
        for i, syllOrig in enumerate(syllables):
            s = deepcopy(syllOrig)
            if semivowelToMove != "":
                s = semivowelToMove + s
                semivowelToMove = ""
            if i+1 < len(syllables):
                if s[-1] == "j":  # ['prié', ['pRi', 'je'], ['pRij', 'e']]
                    if Lexique.isVowel(syllables[i+1][0]):  # not bouilloire
                        ret.append(s[:-1])
                        semivowelToMove = "j"
                    else:
                        ret.append(s)
                elif len(s) > 2 and s[-2:] == "gz":
                    # ['exigé', ['Eg', 'zi', 'Ze'], ['Egz', 'i', 'Ze']]
                    ret.append(s[:-1])
                    semivowelToMove = "z"
                else:
                    ret.append(s)
            else:
                ret.append(s)
        return ret

    def printTopWordsFilm(self, nb=500):
        print("Somme\t%f" % sum(map(lambda w: w.frequencyFilm, self.words)))
        for w in self.words[:nb]:
            print("%s\t%f" % (w.ortho, w.frequencyFilm))

    def printTopWordsBooks(self, nb=500):
        print("Somme\t%f" % sum(map(lambda w: w.frequency, self.words)))
        for w in self.words[:nb]:
            print("%s\t%f" % (w.ortho, w.frequency))

    def printSyllabificationStats(self):
        self.mismatchSyllableSpelling: list[Word] = []
        self.mismatchSyllableAssociation = []
        self.matchSyllableAssociation = []
        self.words.sort(key=lambda x: x.frequencyFilm, reverse=True)
        for word in self.words:
            syllable_names = word.syll.split("-")
            spellings = word.orthosyll.split("-")
            if len(syllable_names) != len(spellings):
                self.mismatchSyllableSpelling.append(word)
            if len(syllable_names) == len(word.phonemesToSyllables()):
                # if syllable_names != word.phonemesToSyllables(False) :
                if syllable_names != Lexique.moveDualPhonem(
                        word.phonemesToSyllables(False)):
                    self.mismatchSyllableAssociation.append(
                        [word.ortho, syllable_names, Lexique.moveDualPhonem(
                            word.phonemesToSyllables(False)),
                         word.lettersToSyllables()])
                else:
                    self.matchSyllableAssociation.append(
                        [word.ortho, syllable_names,
                         word.phonemesToSyllables()])

            else:
                for (syllable_name, spelling) in zip(syllable_names,
                                                     spellings):
                    _ = self.sylCol.updateSyllable(
                        syllable_name, spelling, word.frequency)

        Syllable.printTopPhonemes(5)
        self.sylCol.printTopSyllables(5)
        print("Nb Mismatched syll/orthosyll",
              len(self.mismatchSyllableSpelling))
        print("Nb Mismatched syll/infrasyll",
              len(self.mismatchSyllableAssociation))
        print("Nb Matched syll/infrasyll", len(self.matchSyllableAssociation))
        print("Nb broken down", len(
            list(filter(lambda w: w.orthosyll_cv != [], self.words))))
        missing = [w.ortho for w in filter(
            lambda w: w.orthosyll_cv == [], self.words)]
        for m in missing:
            printVerbose(m, ["orthosyll_cv is missing"])
        print("Nb missing", len(missing))
        print("\n".join(map(str, self.mismatchSyllableAssociation)))

    def outputMixedLexique(self, filename: str):
        with open(filename, "w") as f:
            fieldnames = ["ortho", "phon", "lemme", "cgram", "cgramortho",
                          "genre", "nombre", "infover", "syll_cv",
                          "orthosyll_cv", "freqlivres", "freqfilms2"]

            corpus = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            corpus.writeheader()

            for word in sorted(self.words, key=lambda w: w.ortho):
                if word.orthosyll_cv != []:
                    printVerbose(word.ortho, ["Writing to", filename])
                    corpus.writerow({
                        "ortho": word.ortho,
                        "phon": word.phonology,
                        "lemme": word.lemme,
                        "cgram": word.gram_cat,
                        "cgramortho": word.ortho_gram_cat,
                        "genre": word.gender,
                        "nombre": word.number,
                        "infover": word.info_verb,
                        "syll_cv": word.writePhonoSyll(),
                        "orthosyll_cv": word.writeOrthoSyll(),
                        "freqlivres": word.frequency,
                        "freqfilms2": word.frequencyFilm
                    })


lexique = Lexique()
lexique.printSyllabificationStats()
# lexique.outputMixedLexique("resources/LexiqueMixte.tsv")
