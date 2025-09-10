#!/usr/bin/python
# coding: utf-8
#
import atexit
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
from src.keyboard import Keyboard, Strokes
from src.grammar import Phoneme, Syllable
from src.word import Word, GramCat
from src.cpsatprinter import SolutionPrinter
from tqdm import tqdm
from itertools import combinations

def getAmbiguousMultiphonemes(theory: dict[tuple[tuple[int, ...], ...], list[Word]],
                              keyboard: Keyboard) -> dict[str, list[Word]]:

    ambiguousMultiphonemes: dict[str, list[Word]]= {}
    for strokes, words in theory.items():
        if len(words) > 1:
            phonemesPressed: str = keyboard.strokesToString(strokes)
            ambiguousMultiphonemes[phonemesPressed] = words
    return ambiguousMultiphonemes

def optimizeTheory(theory: dict[Strokes, list[Word]], keyboard: Keyboard) \
        -> dict[Strokes, dict[str, dict[str, list[tuple[Word, list[str]]]]]]:
    """
    Using OR-tools, encode the optimisation rules and objectives to find the best
    disambiguation of homophones.
    """
    SOLVER_TIME = 3600.0  # seconds
    SOLVER_LOG = False
    TWO_FEATURE_SCAN = False
    

    wordFeatures: dict[Word, list[str]] = {}
    lemmes: set[str] = set()
    for lemme in tqdm([word.lemme for words in theory.values() for word in words],
                      desc="Collecting lemmes", unit=" word", ascii=True, ncols=100):
        lemmes.add(lemme)
    hints = ["pers_2", "pers_3:nbr_p", "indicatif:pers_1", "indicatif:nbr_p", "s",
             "pers_3:nbr_s", "présent:pers_1:nbr_s", "indicatif:nbr_s",
             "indicatif:pers_3:nbr_s", "p", "nbr_p"]

    # hints: list[str] = ["s", "pre:3s", "p", "ind", "3s", "ind:1s", "imp:pre", "pre:3p",
    #                     "imp", "3p", "ind:3s", "ind:pre:2p", "ind:3p 2s"]

    allFeatures: set[str] = set()
    for word in tqdm([word for words in theory.values() for word in words],
                      desc="Collecting word features", unit=" word", ascii=True, ncols=100):
        for feature in word.getFeatures():
            allFeatures.add(feature)
            wordFeatures[word] = wordFeatures.get(word, []) + [feature]

    model = cp_model.CpModel()

    # Create BoolVar for each feature that can be seleced to discriminate between homophones
    featuresBoolVar:dict[str, IntVar] = {}

    for feature in tqdm(allFeatures, desc="Creating feature variables",
                        unit=" feature", ascii=True, ncols=100):
        featuresBoolVar[feature] = model.NewBoolVar(f"feature_{feature}")
        if feature in hints:
           _ = model.AddHint(featuresBoolVar[feature], 1)

    # Create BoolVar for each pair of features that can be seleced
    featurePairsBoolVar:dict[tuple[str, str], IntVar] = {}
    if TWO_FEATURE_SCAN :
        for feature1, feature2 in tqdm(combinations(allFeatures, 2),
                            desc="Creating feature pairs variables",
                            unit=" feature", ascii=True, ncols=100):
            featurePairsBoolVar[(feature1, feature2)] = \
                model.NewBoolVar(f"features_{feature1}_{feature2}")

    wordDiscriminatedBy: dict[Word, list[IntVar]] = {
        word:[] for words in theory.values() for word in words}
    wordIsDiscrminated: dict[Word, IntVar] = {}
    orthoDiscriminatedBy: dict[tuple[str, str], list[IntVar]] = {}
    orthoIsDiscrminated: dict[tuple[str, str], IntVar] = {}
        
    for strokes, words in tqdm(theory.items(), desc="Scaning discriminating features",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in words}
        for word in words:
            wordByLemme[word.lemme].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            phonemesPressed: str = keyboard.strokesToString(strokes)
            lemmeWordFeatures = {
                feature: list(filter(lambda w: feature in wordFeatures[w], lemmeWords)) 
                for feature in allFeatures }
            #print(lemmeWordFeatures, "\n\n")
            if len(lemmeWords) > 1:
                for word in lemmeWords:
                    orthoDiscriminatedBy[lemme, word.ortho] = [] 
                    # one-feature discrimination
                    for feature in wordFeatures[word]:
                        if len(lemmeWordFeatures[feature]) == 1:
                            wordDiscriminatedBy[word] += [
                                model.NewBoolVar(
                                    f"{lemme}_{phonemesPressed}_discriminated_by_{feature}")]
                            orthoDiscriminatedBy[lemme, word.ortho] += wordDiscriminatedBy[word][-1:]

                            _ = model.Add(wordDiscriminatedBy[word][-1] == True
                                      ).OnlyEnforceIf(featuresBoolVar[feature])
                            _ = model.Add(wordDiscriminatedBy[word][-1] == False
                                      ).OnlyEnforceIf(featuresBoolVar[feature].Not())
                    # two-features pair discrimination
                    # This is very costly, so it's off by default
                    if TWO_FEATURE_SCAN :
                        for feature1, feature2 in combinations(wordFeatures[word], 2):
                            if len(lemmeWordFeatures[feature1]) == 1 and \
                                len(lemmeWordFeatures[feature2]) == 1:
                                wordDiscriminatedBy[word] += [
                                    model.NewBoolVar(
                                        f"{lemme}_{phonemesPressed}_discriminated_by_{feature1}-{feature2}")]
                                orthoDiscriminatedBy[lemme, word.ortho] += wordDiscriminatedBy[word][-1:]

                                _ = model.Add(wordDiscriminatedBy[word][-1] == featuresBoolVar[feature2]
                                        ).OnlyEnforceIf(featuresBoolVar[feature1])
                                _ = model.Add(wordDiscriminatedBy[word][-1] == featuresBoolVar[feature1]
                                        ).OnlyEnforceIf(featuresBoolVar[feature2])
                                _ = model.Add(wordDiscriminatedBy[word][-1] == False
                                        ).OnlyEnforceIf(featuresBoolVar[feature1].Not())
                                _ = model.Add(wordDiscriminatedBy[word][-1] == False
                                        ).OnlyEnforceIf(featuresBoolVar[feature2].Not())

                    wordIsDiscrminated[word] = \
                        model.NewIntVar(0, len(wordDiscriminatedBy[word]),
                                        f"nb_discrimination_{lemme}_{phonemesPressed}")
                    _ = model.Add(wordIsDiscrminated[word] == \
                                  sum(discBoolVar for discBoolVar in wordDiscriminatedBy[word]))
                orthosOfLemme =list(set(word.ortho for word in lemmeWords))
                for ortho in orthosOfLemme:
                    orthoIsDiscrminated[lemme, ortho] = \
                        model.NewIntVar(0, len(orthoDiscriminatedBy[lemme, ortho]),
                                        f"nb_ortho_discrim_{lemme}_{ortho}_{phonemesPressed}")
                    _ = model.Add(orthoIsDiscrminated[lemme, ortho] == \
                                  sum(discBoolVar for discBoolVar in orthoDiscriminatedBy[lemme, ortho]))

    # We want to maximize the number of discriminated words
    nbWordDiscrminated: IntVar = model.NewIntVar(0, len(wordIsDiscrminated), f"nb_word_discriminated")
    nbOrthoDiscrminated: IntVar = model.NewIntVar(0, len(orthoIsDiscrminated), f"nb_ortho_discriminated")
    _ = model.Add(nbWordDiscrminated == sum(wordIsDiscrminated.values()))
    _ = model.Add(nbOrthoDiscrminated == sum(orthoIsDiscrminated.values()))

    # We want to minimize the number of features used for discrimination
    nbFeatureDiscriminators: IntVar = model.NewIntVar(0, len(featuresBoolVar)+ len(featurePairsBoolVar), f"nb_discriminators")
    _ = model.Add(nbFeatureDiscriminators == (sum(featuresBoolVar.values()) + sum(featurePairsBoolVar.values())))

    totalCost: IntVar = model.NewIntVar(-len(featuresBoolVar), len(wordIsDiscrminated), f"total_cost")
    # _ = model.Add(totalCost == nbWordDiscrminated - nbFeatureDiscriminators)
    _ = model.Add(totalCost == nbOrthoDiscrminated - nbFeatureDiscriminators)

    model.maximize(totalCost)

    # Solve
    print("Solving the model...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME
    solver.parameters.log_search_progress = SOLVER_LOG
    printer = SolutionPrinter(model, 1.0,
            [nbWordDiscrminated, nbOrthoDiscrminated, nbFeatureDiscriminators, totalCost])
    status = solver.Solve(model, printer)

    print(f"Status : {status}")
    print(solver.StatusName(status))
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f'Total penalty = {solver.ObjectiveValue():,}')
        printer.on_solution_callback()
        print("Feature discriminating")
        selectedFeatures = []
        for feature, boolVar in featuresBoolVar.items() :
            if solver.Value(boolVar):
                print(feature)
                selectedFeatures.append(feature)
        for feature, boolVar in featurePairsBoolVar.items() :
            if solver.Value(boolVar):
                print(feature)
                selectedFeatures.append(feature)
        augmentedTheory: dict[Strokes, dict[str, dict[str, list[tuple[Word, list[str]]]]]] = {}
        for strokes, words in tqdm(theory.items(), desc="Scaning discriminating features",
                                unit=" homophones", ascii=True, ncols=100):
            # Split by lemme
            wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in words}
            for word in words:
                wordByLemme[word.lemme].append(word)
            phonemesPressed: str = keyboard.strokesToString(strokes)
            augmentedTheory[strokes] = {}

            # Discriminate homophones words sharing the same lemme
            for lemme, lemmeWords in wordByLemme.items():
                augmentedTheory[strokes][lemme] = {}
                orthosOfLemme =list(set(word.ortho for word in lemmeWords))
                if len(lemmeWords) == 1:
                    print(f"{phonemesPressed}, {lemmeWords[0].ortho} -> (single word for lemme {lemme})")
                    augmentedTheory[strokes][lemme][lemmeWords[0].ortho] = [(lemmeWords[0], [])]
                else :
                    for word in lemmeWords:
                        discrimOfWord = list(filter(lambda feature: solver.Value(feature) == 1, wordDiscriminatedBy[word]))
                        discrimOfWord = [var.Name().split("_discriminated_by_")[-1] for var in discrimOfWord]

                        at = augmentedTheory[strokes][lemme].get(word.ortho, [])
                        at.append((word, discrimOfWord))
                        augmentedTheory[strokes][lemme][word.ortho] = at
                        selectedDiscrim = list(filter(lambda feature: feature in selectedFeatures, discrimOfWord))
                        print(f"{phonemesPressed}, {word.ortho} of lemme {lemme} -> discriminated by {discrimOfWord}, selected {selectedDiscrim}")
        return augmentedTheory

    return {}
