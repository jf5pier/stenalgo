#!/usr/bin/python
# coding: utf-8
#
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
from src.keyboard import Keyboard
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

def optimizeTheory(theory:dict[tuple[tuple[int, ...], ...], list[Word]], keyboard: Keyboard, syllabicParts: list[str])-> None:
    """
    Using OR-tools, encode the optimisation rules and objectives to find the best disambiguation of homophones.
    """
    SOLVER_TIME = 1200.0  # seconds
    SOLVER_LOG = False
    TWO_FEATURE_SCAN = False
    

    wordFeatures: dict[Word, list[str]] = {}
    lemmes: set[str] = set()
    for lemme in tqdm([word.lemme for words in theory.values() for word in words],
                      desc="Collecting lemmes", unit=" word", ascii=True, ncols=100):
        lemmes.add(lemme)
    hints: list[str] = ["s", "pre:3s", "p", "ind", "3s", "ind:1s", "imp:pre", "pre:3p",
                        "imp", "3p", "ind:3s", "ind:pre:2p", "ind:3p 2s"]

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
                    # one-feature discrimination
                    for feature in wordFeatures[word]:
                        if len(lemmeWordFeatures[feature]) == 1:
                            wordDiscriminatedBy[word] += [
                                model.NewBoolVar(
                                    f"{lemme}_{phonemesPressed}_discriminated_by_{feature}")]
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

    # We want to maximize the number of discriminated words
    nbWordDiscrminated: IntVar = model.NewIntVar(0, len(wordIsDiscrminated), f"nb_discriminated")
    _ = model.Add(nbWordDiscrminated == sum(wordIsDiscrminated.values()))

    # We want to minimize the number of features used for discrimination
    nbFeatureDiscriminators: IntVar = model.NewIntVar(0, len(featuresBoolVar)+ len(featurePairsBoolVar), f"nb_discriminators")
    _ = model.Add(nbFeatureDiscriminators == (sum(featuresBoolVar.values()) + sum(featurePairsBoolVar.values())))

    totalCost: IntVar = model.NewIntVar(-len(featuresBoolVar), len(wordIsDiscrminated), f"total_cost")
    _ = model.Add(totalCost == nbWordDiscrminated - nbFeatureDiscriminators)

    model.maximize(totalCost)

    # Solve
    print("Solving the model...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME
    solver.parameters.log_search_progress = SOLVER_LOG
    printer = SolutionPrinter(model, 1.0,
            [nbWordDiscrminated, nbFeatureDiscriminators, totalCost])
    status = solver.Solve(model, printer)

    print(f"Status : {status}")
    print(solver.StatusName(status))
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f'Total penalty = {solver.ObjectiveValue():,}')
        printer.on_solution_callback()
        print("Feature discriminating")
        for feature, boolVar in featuresBoolVar.items() :
            if solver.Value(boolVar):
                print(feature)
        for feature, boolVar in featurePairsBoolVar.items() :
            if solver.Value(boolVar):
                print(feature)
        for strokes, words in tqdm(theory.items(), desc="Scaning discriminating features",
                                unit=" homophones", ascii=True, ncols=100):
            # Split by lemme
            wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in words}
            for word in words:
                wordByLemme[word.lemme].append(word)

            # Discriminate homophones words sharing the same lemme
            for lemme, lemmeWords in wordByLemme.items():
                phonemesPressed: str = keyboard.strokesToString(strokes)
                if len(lemmeWords) == 1:
                    print(f"{phonemesPressed}, {lemmeWords[0].ortho} -> (single word for lemme {lemme})")
                else :
                    for word in lemmeWords:
                        discrimOfWord = list(filter(lambda feature: solver.Value(feature) == 1, wordDiscriminatedBy[word]))
                        discrimOfWord = [var.Name().split("_discriminated_by_")[-1] for var in discrimOfWord]
                        print(f"{phonemesPressed}, {word.ortho} of lemme {lemme} -> discriminated by {discrimOfWord}")

    return
