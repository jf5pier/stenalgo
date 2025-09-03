#!/usr/bin/python
# coding: utf-8
#
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
import time
from functools import cmp_to_key
from src.keyboard import Keyboard
from src.grammar import Phoneme, Syllable
from src.cpsatprinter import SolutionPrinter
from tqdm import tqdm

def optimizeKeyboard(keyboard: Keyboard,
                     syllabicPartAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]], 
                     syllabicParts: list[str]) -> None:
    """
    Using OR-tools, encode the optimisation rules and objectives to find the best keymap.
    Starting from the theory, tries to optimize the keymap to :
        - minimize the number of ambiguities (strokes that generate more than one word)
        - minimize the strain of typing by assigning frequent phonemes to easier keys.
        - maximize the number of words that can be typed with the right order of strokes from left to right.
        - find alternate strokes to differentiate homonymes
    """
    PARTS: list[str] = syllabicParts
    STROKE_ASSIGNMENT_PENALTY = 1
    AMBIGUITY_PENALTY = 30000
    ORDER_PENALTY= 500
    SOLVER_TIME = 90.0  # seconds
    SOLVER_LOG = False
    MAX_MULTIPHONEMES: int = 2000
    
    phonemesByPart: dict[str, str] = {
        "onset": Phoneme.consonantPhonemes[:],
        "nucleus": Phoneme.nucleusPhonemes[:],
        "coda": Phoneme.consonantPhonemes[:]
    }

    # Initiate the model(s)
    model: dict[str, cp_model.CpModel] = {p: cp_model.CpModel() for p in PARTS}

    keysInPart: dict[str, list[int]] = {p: keyboard.keyIDinSyllabicPart[p][:] for p in PARTS}

    # Generate Symbol Groups
    # The groups are now all possible combinations of 1 to N phonemes found in syllabic part of words.
    multiphonemesInPart: dict[str, list[tuple[str, ...]]] = { }
    for part in PARTS:
        multiphonemesInPart[part] = []
        for (mp1, mp2) in syllabicPartAmbiguity[part]:
            multiphonemesInPart[part].append(mp1)
            multiphonemesInPart[part].append(mp2)
        multiphonemesInPart[part] = list(set(multiphonemesInPart[part]))
        
    sortedMultiphonemeAmbiguity: dict[str, list[tuple[tuple[tuple[str, ...], tuple[str, ...]], float]]] = {p:[] for p in PARTS}
    for part in PARTS:

        for mpi1,mp1 in enumerate(multiphonemesInPart[part][:-1]):
            for mp2 in multiphonemesInPart[part][mpi1+1:]:
                ambiguity: float = syllabicPartAmbiguity[part].get((mp1,mp2), syllabicPartAmbiguity[part].get((mp2,mp1), 0.0))
                sortedMultiphonemeAmbiguity[part].append(((mp1,mp2), ambiguity))
        sortedMultiphonemeAmbiguity[part].sort(key=lambda mp : mp[1], reverse=True) # Sort by ambiguity descending

    selectedMultiphonemesAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]] = {}
    for part in PARTS:
         selectedMultiphonemesAmbiguity[part] =  {mp:cost for mp, cost in sortedMultiphonemeAmbiguity[part][:MAX_MULTIPHONEMES]}

    strokesInPart: dict[str, list[tuple[int, ...]]] = {p: [] for p in PARTS}
    for part in PARTS:
        for strokeLength in range(1, 5):
            strokesInPart[part] += keyboard.getPossibleStrokes(part, strokeLength)
        strokesInPart[part].sort(key=cmp_to_key(keyboard.strokeIsLowerThen))

    strokesContainingKey: dict[str, dict[int, list[tuple[int, ...]]]] = {p:{} for p in PARTS}
    for part in PARTS:
        for stroke in strokesInPart[part]:
            for key in stroke:
                if key not in strokesContainingKey[part]:
                    strokesContainingKey[part][key] = []
                strokesContainingKey[part][key].append(stroke)

    strokeIsAssignedToPhoneme: dict[str, dict[tuple[str, tuple[int, ...]], IntVar]]  = {p: {} for p in PARTS}
    keyIsAssignedToPhoneme: dict[str, dict[tuple[str, int], IntVar]]  = {p:{} for p in PARTS}
    for part in PARTS:
        for phoneme in tqdm(phonemesByPart[part], desc="Linking phonemes to strokes",
                            unit=" phonemes", ascii=True, ncols=100):
            for stroke in strokesInPart[part]:
                strokeIsAssignedToPhoneme[part][(phoneme, stroke)] = \
                    model[part].NewBoolVar(f'x_{part[0]}_{phoneme}_{stroke}')

            for key in keysInPart[part]:
                keyIsAssignedToPhoneme[part][(phoneme, key)] = \
                    model[part].NewBoolVar(f'k_{phoneme}_{key}')
            
            # Each symbol's key set size must be between 1 and maxKeysPerPhoneme.
            _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][phoneme, k]
                    for k in keysInPart[part]) >= 1)

            _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][phoneme, k]
                    for k in keysInPart[part]) <= keyboard.maxKeysPerPhoneme[part])

            for stroke in strokesInPart[part]:
                # Add all the key-phoneme associations of the associated stroke. It's not enough to ensure all the
                # associated keys are part of the stroke
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][(phoneme, key)]
                    for key in stroke) == len(stroke)).OnlyEnforceIf(strokeIsAssignedToPhoneme[part][(phoneme, stroke)])
                
                # Forces phoneme dissociation  of all keys that are not part of the associated stroke.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][(phoneme, k)]
                    for k in keysInPart[part] if k not in stroke) == 0).OnlyEnforceIf(
                    strokeIsAssignedToPhoneme[part][(phoneme, stroke)])

            # Not sure if needed, seems to be implied by the above.
            # for key in keysInPart[part]:
            #     _ = model[part].AddBoolOr(strokeIsAssignedToPhoneme[part][(phoneme, s)]
            #           for s in strokesContainingKey[part][key]).OnlyEnforceIf(keyIsAssignedToPhoneme[part][(phoneme, key)])
            # for stroke in strokesInPart[part]:

                # The only way a key is not associated to a phoneme is if none of the strokes containing this key
                # are assigned to the phoneme.
                for key in keysInPart[part]:
                    _ = model[part].AddBoolOr([strokeIsAssignedToPhoneme[part][phoneme, s2].Not() \
                            for s2 in strokesContainingKey[part][key]]).OnlyEnforceIf( \
                            keyIsAssignedToPhoneme[part][phoneme, key].Not())

            # Force exactly one stroke to be assigned to the phoneme.
            _ = model[part].Add(sum(strokeIsAssignedToPhoneme[part][phoneme, s] for s in strokesInPart[part]) == 1)
            
    ###
    # Add hints based on the provided keyboard layout.
    #
    for part in PARTS:
        for phoneme in phonemesByPart[part]:
            keyboardStrokes = keyboard.getStrokesOfPhoneme(phoneme, part)
            keyHintedPositive = {key:0 for key in keysInPart[part]}
            for stroke in strokesInPart[part]:
                if stroke in keyboardStrokes:
                    _ = model[part].AddHint(strokeIsAssignedToPhoneme[part][(phoneme, stroke)], 1)
                    for key in stroke:
                        _ = model[part].AddHint(keyIsAssignedToPhoneme[part][(phoneme, key)], 1)
                        keyHintedPositive[key] = 1
                else :
                    _ = model[part].AddHint(strokeIsAssignedToPhoneme[part][(phoneme, stroke)], 0)
            for key in keysInPart[part]:
                if keyHintedPositive[key] == 0:
                    _ = model[part].AddHint(keyIsAssignedToPhoneme[part][(phoneme, key)], 0)

    # A boolean variable that is True if key 'k' is in the key set
    # of multiphoneme 'mp' (the union of keys from all phonemes in syllabiic part).
    multiphonemeHasKey: dict[str, dict[tuple[tuple[str, ...], int], IntVar]]  = {p:{} for p in PARTS}
    for part in PARTS:
        for multiphoneme in tqdm(multiphonemesInPart[part], desc="Linking multiphonemes to strokes",
                                 unit=" multiphonemes", ascii=True, ncols=100):

            mp_str = "".join(multiphoneme)
            for k in keysInPart[part]:
                multiphonemeHasKey[part][multiphoneme, k] = \
                    model[part].NewBoolVar(f'multiphonemesKeys_{part[0]}_{mp_str}_{k}')

    # keysetsAreIdentical[g1][g2]: A boolean variable that is True if the key set of
    # multiphoneme mp1 is identical to the key set of multiphoneme mp2.
    keysetsAreIdentical: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], IntVar]] = {}
    for part in PARTS:
        keysetsAreIdentical[part] = {}
        for mp1i,mp1 in enumerate(multiphonemesInPart[part][:-1]):
            for mp2 in multiphonemesInPart[part][mp1i+1:]:
                keysetsAreIdentical[part][mp1, mp2] = \
                    model[part].NewBoolVar(f'is_keyset_identical_{part[0]}_{mp1}_{mp2}')


    # Model the key set of a group of phonemes as the union of its phonemes' key sets.
    # multiphonemesKeys[mp, k] is true if and only if key 'k' is assigned to at least one symbol in multiphoneme'mp'.
    for part in PARTS:
        for multiphoneme in tqdm(multiphonemesInPart[part], desc="Linking multiphoneme to shared keys",
                             unit=" multiphonemes", ascii=True, ncols=100):

            for k in keysInPart[part]:
                # We need a boolean variable to represent the condition: "at least one phoneme in multiphoneme
                # has key k assigned".
                atLeastOnePhonemeHasKey = \
                    model[part].NewBoolVar(f'keyset_has_key{part[0]}_{multiphoneme}_{k}')

                # Add constraints to define the meaning of at_least_one_symbol_has_key. First, one phoneme
                # must be associated to the key.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k]
                        for p in multiphoneme) >= 1).OnlyEnforceIf(atLeastOnePhonemeHasKey)

                # In the negative case, no phoneme in the multiphoneme can be associated to the key.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k]
                        for p in multiphoneme) == 0).OnlyEnforceIf(atLeastOnePhonemeHasKey.Not())

                # Limit the numbers of keys to the number of phonemes in the multiphoneme.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k]
                        for p in multiphoneme) <= len(multiphoneme)).OnlyEnforceIf(atLeastOnePhonemeHasKey)

                # Now, link the multiphonemesKeys variable directly to this condition.
                # multiphonemesKeys[multiphoneme, k] is equivalent to at_least_one_symbol_has_key.
                _ = model[part].Add(multiphonemeHasKey[part][multiphoneme, k] == atLeastOnePhonemeHasKey)

                for phoneme in multiphoneme:
                    # Reciprocaly : if a phoneme of the multiphoneme is associated to a key, then the
                    # multiphoneme must be too.
                    _ = model[part].Add( multiphonemeHasKey[part][multiphoneme, k] == True).OnlyEnforceIf(\
                            keyIsAssignedToPhoneme[part][phoneme, k])

                # These look redundant, retest if a problem arises.
                # _ = model[part].AddBoolOr(keyIsAssignedToPhoneme[part][phoneme, k]
                #         for phoneme in multiphoneme).OnlyEnforceIf(multiphonemeHasKey[part][multiphoneme, k])
                # _ = model[part].AddBoolOr(keyIsAssignedToPhoneme[part][phoneme, k].Not()
                #         for phoneme in multiphoneme).OnlyEnforceIf(multiphonemeHasKey[part][multiphoneme, k].Not())

    # Model the identical keysets relationship:
    #   `mp1`  keyset is identical to `mp2` keyset if and only
    #   if multiphonemeKeys[mp1,k] is equal multiphonemeKeys[mp2,k] for all k.
    mismatch_literals: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], dict[int, IntVar]]] = {
        p:{} for p in PARTS}

    for part in PARTS:
        for mp1i,mp1 in tqdm(list(enumerate(multiphonemesInPart[part][:-1])), desc="Linking multiphoneme to missing keys",
                             unit=" multiphonemes", ascii=True, ncols=100):

            for mp2 in multiphonemesInPart[part][mp1i+1:]:
                mismatch_literals[part][mp1,mp2] = {}
                for k in keysInPart[part]:
                    # Create a temporary boolean variable for each key 'k' that is true if the keys don't match.
                    mismatch_literals[part][mp1,mp2][k] =  model[part].NewBoolVar(f'mismatch_{mp1}_{mp2}_{k}')
                    # Enforce that mismatch_literals[k] is true if multiphonemesKeys[g1, k] != multiphonemesKeys[g2, k]
                    _ = model[part].Add(multiphonemeHasKey[part][mp1, k]
                            != multiphonemeHasKey[part][mp2, k]).OnlyEnforceIf(
                            mismatch_literals[part][mp1,mp2][k])

                    # Negative case, the multiphonemes must have all the same keys associated if there is no mismatch.
                    _ = model[part].Add(multiphonemeHasKey[part][mp1, k]
                            == multiphonemeHasKey[part][mp2, k]).OnlyEnforceIf(
                            mismatch_literals[part][mp1,mp2][k].Not())
                
                # Now, model the `is_group_identical` variable. It's true if and only if there are no mismatches.
                _ = model[part].Add(sum(mismatch_literals[part][mp1,mp2].values()) == 0).OnlyEnforceIf(
                        keysetsAreIdentical[part][mp1, mp2])
                _ = model[part].Add(sum(mismatch_literals[part][mp1,mp2].values()) > 0).OnlyEnforceIf(
                        keysetsAreIdentical[part][mp1, mp2].Not())
                # These are equivalent to the above, test for performance before removing :
                #_ = model[part].AddBoolAnd(mismatch_literals[part][mp1,mp2][k].Not()
                #       for k in keysInPart[part]).OnlyEnforceIf(is_keyset_identical[part][mp1, mp2])
                #_ = model[part].AddBoolOr(mismatch_literals[part][mp1,mp2][k] 
                #       for k in keysInPart[part]).OnlyEnforceIf(is_keyset_identical[part][mp1, mp2].Not())

    # Model the left to right order of phonemes on the keyboard.
    # Strokes are ordered by keyboard.strokeIsLowerThen(stroke1, stroke2), start by giving them an index.
    strokeIndex: dict[str, dict[tuple[int, ...], int]] = {
        part: {stroke: i for i, stroke in enumerate(strokesInPart[part])} for part in PARTS
    }

    # Add the relationship "phoneme1 is before phoneme2".
    phonemePosition: dict[str, dict[str, IntVar]] = {p:{} for p in PARTS}
    phoneme1IsBefore2: dict[str, dict[tuple[str, str], IntVar]] = {p:{} for p in PARTS}
    phonemeSharePosition: dict[str, dict[tuple[str, str], IntVar]] = {p:{} for p in PARTS}
    for part in PARTS:
        for phoneme in phonemesByPart[part]:
            # Establish a link between phonemes, strokes and index of stroke
            phonemePosition[part][phoneme] = \
                model[part].NewIntVar(0, len(strokesInPart[part])-1, f'position_{phoneme}_{part}')
            for stroke in strokesInPart[part]:
                _ = model[part].Add(
                phonemePosition[part][phoneme] == strokeIndex[part][stroke]).OnlyEnforceIf(
                    strokeIsAssignedToPhoneme[part][(phoneme, stroke)])
                _ = model[part].Add(
                phonemePosition[part][phoneme] != strokeIndex[part][stroke]).OnlyEnforceIf(
                    strokeIsAssignedToPhoneme[part][(phoneme, stroke)].Not())

        #_ = model[part].AddAllDifferent(list(phonemePosition[part].values()))

        for p1i, p1 in enumerate(phonemesByPart[part][:-1]):
            for p2 in phonemesByPart[part][p1i+1:]:

                # Define the order relationship of variables
                phoneme1IsBefore2[part][p1, p2] = model[part].NewBoolVar(f'pos_{p1}_before_{p2}_{part}')
                phonemeSharePosition[part][p1, p2] = model[part].NewBoolVar(f'pos_shared_{p1}_{p2}_{part}')
                
                _ = model[part].Add(phonemePosition[part][p1] < phonemePosition[part][p2]).OnlyEnforceIf(
                    phoneme1IsBefore2[part][p1, p2])
                _ = model[part].Add(phonemePosition[part][p1] >= phonemePosition[part][p2]).OnlyEnforceIf(
                    phoneme1IsBefore2[part][p1, p2].Not())

                _ = model[part].Add(phonemePosition[part][p1] == phonemePosition[part][p2]).OnlyEnforceIf(
                    phonemeSharePosition[part][p1, p2])
                _ = model[part].Add(phonemePosition[part][p1] != phonemePosition[part][p2]).OnlyEnforceIf(
                    phonemeSharePosition[part][p1, p2].Not())

    ######
    # --- Define the Objective Function ---
    # The total cost is defined by 3 metrics :
    # - The amount of ambiguity of overlapping keyset representing multiphonemes that are ambiguous.
    # - The complexity/ergonomy of strokes assigned to each phoneme times their respecting frequency.
    # - The order of phonemes on the keyboard respecting phoneme order in words.
    #
    maxAmbiguity: dict[str, int] = {}
    overlapCosts: dict[str, IntVar] = {}
    for part in PARTS:
        maxAmbiguity[part] = int(sum(selectedMultiphonemesAmbiguity[part].values()) * AMBIGUITY_PENALTY )
        overlapCosts[part] = model[part].NewIntVar(0, maxAmbiguity[part], f'multiphoneme_ambiguity_cost_{part}')

    ###
    # Define multiphoneme overlap costs
    #
    multiphonemeAmbiguityCost: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], IntVar ]] = {
            p:{} for p in PARTS}
    for part in PARTS:
        for (mp1,mp2) in selectedMultiphonemesAmbiguity[part]:
            multiphonemeAmbiguityCost[part][mp1, mp2] = \
                model[part].NewIntVar(0, maxAmbiguity[part], 
                                        f'multiphoneme_overlap_cost_{part[0]}_{mp1}_{mp2}')

            # Define de Ovelap cost (ambiguity penalty) for each pair of multiphonemes
            _ = model[part].Add(multiphonemeAmbiguityCost[part][mp1, mp2]
                        == int(selectedMultiphonemesAmbiguity[part][mp1, mp2]
                                * AMBIGUITY_PENALTY)).OnlyEnforceIf(keysetsAreIdentical[part][mp1, mp2])
            _ = model[part].Add(multiphonemeAmbiguityCost[part][mp1, mp2]
                        == 0).OnlyEnforceIf(keysetsAreIdentical[part][mp1, mp2].Not())
        
        # Get the total overlap cost for the part
        _ = model[part].Add(overlapCosts[part] == sum(multiphonemeAmbiguityCost[part][mp1, mp2]
                     for (mp1,mp2) in selectedMultiphonemesAmbiguity[part] ))

    ###
    # Define the stroke penalty cost based on stroke complexity and phoneme frequency.
    #
    strokeCosts: dict[str, dict[tuple[int, ...], int]] = {p: {
        stroke: int(keyboard.getStrokeCost(stroke, p)) for stroke in strokesInPart[p]}
        for p in PARTS}
    maxStrokeCost = {part: max(strokeCosts[part].values()) for part in PARTS}

    phonemeFrequency: dict[str, dict[str, int]] = {part: {
        p: int(Syllable.phonemeColByPart[part].phonemeNames[p].frequency)
        for p in phonemesByPart[part]} for part in PARTS}

    maxStrokesPenalty: dict[str, int] = {
        part: maxStrokeCost[part] * sum(phonemeFrequency[part][p] for p in phonemesByPart[part])
            * STROKE_ASSIGNMENT_PENALTY for part in PARTS }

    allStrokesPenaltyCost: dict[str, IntVar] = {}
    strokePenaltyCost: dict[str, dict[tuple[int, ...], IntVar]] = {p:{} for p in PARTS}
    for part in PARTS:
        for stroke in strokesInPart[part]:
            # Per-stroke penalty cost
            strokePenaltyCost[part][stroke] = model[part].NewIntVar(0, maxStrokesPenalty[part], f'stroke_{stroke}_cost')
            _ = model[part].Add(strokePenaltyCost[part][stroke] == sum(
                strokeIsAssignedToPhoneme[part][p, stroke] * STROKE_ASSIGNMENT_PENALTY
                * phonemeFrequency[part][p] * strokeCosts[part][stroke] for p in phonemesByPart[part] ))

        allStrokesPenaltyCost[part] = model[part].NewIntVar(0, maxStrokesPenalty[part], f'strokes_penalty_cost_{part}')
        _ = model[part].Add(allStrokesPenaltyCost[part] == sum(
            strokePenaltyCost[part][stroke] for stroke in strokesInPart[part]))

    ###
    # Define the phoneme pair order penalty cost based on phoneme order matrix.
    #
    phonemePairsOrderPenaltyCost: dict[str, dict[tuple[str, str], IntVar]] = {p:{} for p in PARTS}
    allPhonemePairsOrderPenaltyCost: dict[str,  IntVar] = {}
    minScore: dict[str, dict[str, int]] = {part:{p: 0 for p in phonemesByPart[part]} for part in PARTS}
    maxScore: dict[str, dict[str, int]] = {part:{p: 0 for p in phonemesByPart[part]} for part in PARTS}
    for part in PARTS:
        pairwiseScore = {biphoneme: int(score) * ORDER_PENALTY
            for biphoneme, score in Syllable.biphonemeColByPart[part].pairwiseBiphonemeOrderScore.items()}
        for p1 in phonemesByPart[part]:
            for p2 in phonemesByPart[part]:
                if (p1, p2) not in pairwiseScore:
                    pairwiseScore[p1, p2] = 0

        for p1i, p1 in enumerate(phonemesByPart[part][:-1]):
            for p2 in phonemesByPart[part][p1i+1:]:
                minScore[part][p1] += min(pairwiseScore[p1, p2], pairwiseScore[p2, p1])
                maxScore[part][p1] += max(pairwiseScore[p1, p2], pairwiseScore[p2, p1])
                minScore[part][p2] += min(pairwiseScore[p1, p2], pairwiseScore[p2, p1])
                maxScore[part][p2] += max(pairwiseScore[p1, p2], pairwiseScore[p2, p1])

        for p1i, p1 in enumerate(phonemesByPart[part][:-1]):
            for p2 in phonemesByPart[part][p1i+1:]:
                # if not(pairwiseScore[p1, p2] == 0 and pairwiseScore[p2, p1] == 0):
                #     print(f'Pairwise order score for {part} {p1},{p2}: {pairwiseScore[p1, p2]}, {p2},{p1}: {pairwiseScore[p2, p1]}')

                phonemePairsOrderPenaltyCost[part][p1, p2] = \
                    model[part].NewIntVar(minScore[part][p1], maxScore[part][p2],
                                          f'order_penalty_{p1}_{p2}_{part}')

                _ = model[part].Add(phonemePairsOrderPenaltyCost[part][p1, p2] == \
                    pairwiseScore[p1, p2] * phoneme1IsBefore2[part][p1, p2] + \
                    pairwiseScore[p2, p1] * phoneme1IsBefore2[part][p1, p2].Not()).OnlyEnforceIf(
                    phonemeSharePosition[part][p1, p2].Not())

                # If the phoneme are sharing a stroke, take half of the order penalty
                _ = model[part].Add(phonemePairsOrderPenaltyCost[part][p1, p2] == \
                    int((pairwiseScore[p1, p2] + pairwiseScore[p2, p1])/2)).OnlyEnforceIf(
                    phonemeSharePosition[part][p1, p2])

        allPhonemePairsOrderPenaltyCost[part] = model[part].NewIntVar(
                sum(minScore[part].values()), sum(maxScore[part].values()), f'phoneme_order_penalty_cost_{part}')
        _ = model[part].Add(allPhonemePairsOrderPenaltyCost[part] == \
                            sum(phonemePairsOrderPenaltyCost[part].values()))

    ###
    # Define the total cost of all 3 constraints
    #
    total_cost: dict[str, IntVar] = {}
    for part in PARTS:
        print(f'Part {part}, Max Multiphoneme Ambiguity: {maxAmbiguity[part]:,},' +
            f' Max Strokes penalty: {maxStrokesPenalty[part]:,}' +
            f' Max order penalty: {sum(maxScore[part].values()):,}')
        total_cost[part] = model[part].NewIntVar(sum(minScore[part].values()), 
                                maxAmbiguity[part] + maxStrokesPenalty[part] + sum(maxScore[part].values()),
                                'total_cost')

        # Define the total cost to optimize.
        _ = model[part].Add(total_cost[part] == \
                            overlapCosts[part] + allStrokesPenaltyCost[part] \
                            + allPhonemePairsOrderPenaltyCost[part])

        model[part].Minimize(total_cost[part])

    # Solve
    print("Solving the models...")
    solver = {p: cp_model.CpSolver() for p in PARTS}
    keyboard.clearLayout()
    for part in PARTS:
        solver[part].parameters.max_time_in_seconds = SOLVER_TIME
        solver[part].parameters.log_search_progress = SOLVER_LOG
        print(f"Solving for {part} model...")
        printer = SolutionPrinter(model[part], 1.0,
              [overlapCosts[part], allStrokesPenaltyCost[part],
              allPhonemePairsOrderPenaltyCost[part]])
        status = solver[part].Solve(model[part],
              printer,)

        # Output
        print(f"Status for {part}: {status}")
        print(solver[part].StatusName(status))
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Total penalty = {solver[part].ObjectiveValue():,}')
            printer.on_solution_callback()
            strokesAssignedToPhoneme: dict[str, list[tuple[int, ...]]] = {p: [] for p in phonemesByPart[part]}
            keysAssignedToPhoneme: dict[str, list[int]] = {p: [] for p in phonemesByPart[part]}
            phonemesAssignedToStroke: dict[tuple[int, ...], list[str]] = {s: [] for s in strokesInPart[part]}
            phonemesAssignesToKey: dict[int, list[str]] = {k: [] for k in keysInPart[part]}

            # Extract key-phoneme and stroke-phoneme associations from the solution
            for stroke in strokesInPart[part]:
                for phoneme in phonemesByPart[part]:
                    if solver[part].Value(strokeIsAssignedToPhoneme[part][(phoneme, stroke)]) == 1:
                        strokesAssignedToPhoneme[phoneme].append(stroke)
                        phonemesAssignedToStroke[stroke].append(phoneme)
                        keyboard.addToLayout(stroke, phoneme, Syllable.getSortedPhonemesNames(part))
            for k in keysInPart[part]:
                for phoneme in phonemesByPart[part]:
                    if solver[part].Value(keyIsAssignedToPhoneme[part][(phoneme, k)]) == 1:
                        keysAssignedToPhoneme[phoneme].append(k)
                        phonemesAssignesToKey[k].append(phoneme)

            # Print the solution
            print("Phonemes:")
            orderedPhonemes = sorted(phonemesByPart[part], key=lambda p: solver[part].Value(phonemePosition[part][p]))
            for phoneme in orderedPhonemes:
                print(f' Part {part}, Phoneme {phoneme}: ' +
                    f'Strokes {strokesAssignedToPhoneme[phoneme]}, ' +
                    f'Keys {keysAssignedToPhoneme[phoneme]} ' +
                    f'Order position: {solver[part].Value(phonemePosition[part][phoneme])}' +
                    f''  )
            print("Keys:")
            for key in keysInPart[part]:
                print(f' Part {part}, Key {key}: Phonemes {phonemesAssignesToKey[key]}')
            print("Strokes:")
            for stroke in strokesInPart[part]:
                if len(phonemesAssignedToStroke[stroke]) > 0:
                    print(f' Part {part}, Stroke: {stroke}, Phonemes: {phonemesAssignedToStroke[stroke]},'
                        + f' stroke cost: {strokeCosts[part][stroke]} (frequency weighted cost: '
                        + f' {solver[part].Value(strokePenaltyCost[part][stroke]):,})')

            print("Multiphonemes ambiguity:")
            multiphonemesKeysAssigned:dict[tuple[str, ...], list[int]] = {}
            for multiphoneme in multiphonemesInPart[part]:
                multiphonemesKeysAssigned[multiphoneme] = []
                for k in keysInPart[part]:
                    if solver[part].Value(multiphonemeHasKey[part][multiphoneme, k]) == 1:
                        multiphonemesKeysAssigned[multiphoneme].append(k)

            for mp1,mp2 in selectedMultiphonemesAmbiguity[part]:
                if solver[part].Value(keysetsAreIdentical[part][mp1, mp2]) == 1 \
                        and solver[part].Value(multiphonemeAmbiguityCost[part][(mp1, mp2)]) > 0:
                    print(f'  Part {part}, Multiphonemes {mp1} and {mp2}' +
                          f' share the same keys: {multiphonemesKeysAssigned[mp1]}'+
                          f' cost {solver[part].Value(
                        multiphonemeAmbiguityCost[part][(mp1, mp2)]):,} ')

                elif sorted(multiphonemesKeysAssigned[mp1]) == sorted(multiphonemesKeysAssigned[mp2]) \
                    and set(mp1) != set(mp2) \
                    and (solver[part].Value(multiphonemeAmbiguityCost[part][(mp1, mp2)]) > 0 or \
                         selectedMultiphonemesAmbiguity[part][mp1,mp2] > 0.0):
                    # This should only happen if there is a bug, can probably be removed.
                    print(f'** Bug ambiguity: **')
                    print(f'  Part {part}, Multiphonemes {mp1} and {mp2} have keys : {multiphonemesKeysAssigned[mp1]}' +
                          f' and : {multiphonemesKeysAssigned[mp2]} strokes: ')
                    print(f'  {mp1} ambiguity to {mp2} cost {solver[part].Value(
                          multiphonemeAmbiguityCost[part][(mp1, mp2)]):,}' +
                          f' should be : {int(selectedMultiphonemesAmbiguity[part][mp1,mp2] * AMBIGUITY_PENALTY):,}')
                    print(f'  keysetsAreIdentical[{part}][{mp1}, {mp2}] == {solver[part].Value(
                          keysetsAreIdentical[part][mp1, mp2])}')
                    for k in keysInPart[part]:
                        if solver[part].Value(mismatch_literals[part][mp1,mp2][k]) == 1:
                            print(f'  mismatch_literals[{part}][{mp1},{mp2}][{k}] is a mismatch '+
                                    f'{k in multiphonemesKeysAssigned[mp1]} {k in multiphonemesKeysAssigned[mp2]}')

                elif set(multiphonemesKeysAssigned[mp1]) == set(multiphonemesKeysAssigned[mp2]):
                    if selectedMultiphonemesAmbiguity[part][mp1, mp2] > 0.0:
                        print(f'Identical phoneme set ambiguity:')
                        print(f'  Part {part}, Multiphonemes {mp1} and {mp2} have keys : {multiphonemesKeysAssigned[mp1]}' +
                              f' and : {multiphonemesKeysAssigned[mp2]} strokes: ')
                        print(f'  {mp1} ambiguity to {mp2} cost {solver[part].Value(
                              multiphonemeAmbiguityCost[part][(mp1, mp2)]) * AMBIGUITY_PENALTY:,}' +
                              f' should be : {int(selectedMultiphonemesAmbiguity[part][mp1,mp2] * AMBIGUITY_PENALTY):,}')

        else:
            print('No solution found.')
