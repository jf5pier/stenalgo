
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
import time
from functools import cmp_to_key
from src.keyboard import Keyboard
from src.grammar import Phoneme


def optimizeTheory(keyboard: Keyboard,
                   syllabicPartAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]], 
                   syllabicParts: list[str]) -> None:
    """
    Using OR-tools, encode the optimisation rules and objectives to find the best keymap.
    """
    PARTS = syllabicParts 
    class _SolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Callback to print intermediate solutions."""

        def __init__(self, model:cp_model.CpModel, print_interval_seconds:float=2.0) -> None:
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.__model = model
            self.__solution_count = 0
            self.__last_print_time = time.time()
            self.__print_interval = print_interval_seconds

        def on_solution_callback(self) -> None:
            """Called by the solver when a new solution is found."""
            current_time = time.time()
            self.__solution_count += 1
            if current_time - self.__last_print_time >= self.__print_interval:
                print(f'Solution {self.__solution_count}: objective = {self.ObjectiveValue()}')
                self.__last_print_time = current_time

    
    phonemesByPart: dict[str, str] = {
        "onset": Phoneme.consonantPhonemes[:],
        "nucleus": Phoneme.nucleusPhonemes[:],
        "coda": Phoneme.consonantPhonemes[:]
    }
    # Initiate the model(s)
    model: dict[str, cp_model.CpModel] = {p: cp_model.CpModel() for p in PARTS}

    keysInPart: dict[str, list[int]] = {p: keyboard.keyIDinSyllabicPart[p][:] for p in PARTS}

    # --- 2. Generate Symbol Groups ---
    # The groups are now all possible combinations of 1 to N phonemes found in syllabic part of words.
    multiphonemesInPart: dict[str, set[tuple[str, ...]]] = { }
    for part in PARTS:
        multiphonemesInPart[part] = set()
        for (mp1, mp2) in syllabicPartAmbiguity[part]:
            multiphonemesInPart[part].add(mp1)
            multiphonemesInPart[part].add(mp2)
        
    sortedMultiphonemeAmbiInPart: dict[str, list[tuple[tuple[tuple[str, ...], tuple[str, ...]], float]]] = {p:[] for p in PARTS}
    for part in PARTS:
        mplist = list(multiphonemesInPart[part])
        for mpi1,mp1 in enumerate(mplist[:-1]):
            for mp2 in mplist[mpi1+1:]:
                ambiguity: float = syllabicPartAmbiguity[part].get((mp1,mp2), syllabicPartAmbiguity[part].get((mp2,mp1), 0.0))
                sortedMultiphonemeAmbiInPart[part].append(((mp1,mp2), ambiguity))
        sortedMultiphonemeAmbiInPart[part].sort(key=lambda mp : mp[1], reverse=True)

    # sortedMultiphonemeAmbiInPart: dict[str, list[tuple[tuple[tuple[str, ...], tuple[str, ...]], float]]] = {}
    # for part in PARTS:
    #     sortedMultiphonemeAmbiInPart[part] = sorted(list(syllabicPartAmbiguity[part].items()) +
    #                         [((mp2,mp1),cost) for ((mp1, mp2), cost) in syllabicPartAmbiguity[part].items()],
    #                         key=lambda mp : mp[1], reverse=True)
        
    maxMultiphonemeToOptimize: int = 200
    selectedMultiphonemesAmbiInPart: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]] = {}
    for part in PARTS:
         selectedMultiphonemesAmbiInPart[part] =  {mp:cost for mp, cost in sortedMultiphonemeAmbiInPart[part][:maxMultiphonemeToOptimize]}
    print("Selected multiphoneme ambiguities in onset:", list(selectedMultiphonemesAmbiInPart[PARTS[0]].items())[:20])

    keyIsActive: dict[str, dict[int, IntVar]] = {"onset": {}, "nucleus": {}, "coda": {}}
    strokesInPart: dict[str, list[tuple[int, ...]]] = {
        "onset": [], "nucleus": [], "coda": []
    }
    for part in PARTS:
        for strokeLength in range(1, 5):
            strokesInPart[part] += keyboard.getPossibleStrokes(part, strokeLength)
        strokesInPart[part].sort(key=cmp_to_key(keyboard.strokeIsLowerThen))
        for key in keysInPart[part]:
            keyIsActive[part][key] = model[part].NewBoolVar(f'key_{part[0]}_{key}')

    phonemeAssignedToStroke: dict[str, dict[tuple[str, tuple[int, ...]], IntVar]]  = {"onset": {}, "nucleus": {}, "coda": {}}
    keyIsAssignedToPhoneme: dict[str, dict[tuple[str, int], IntVar]]  = {"onset": {}, "nucleus": {}, "coda": {}}
    for part in PARTS:
        for phoneme in phonemesByPart[part]:
            for stroke in strokesInPart[part]:
                phonemeAssignedToStroke[part][(phoneme, stroke)] = model[part].NewBoolVar(f'x_{part[0]}_{phoneme}_{stroke}')
            for key in keysInPart[part]:
                keyIsAssignedToPhoneme[part][(phoneme, key)] = model[part].NewBoolVar(f'k_{phoneme}_{key}')
            for stroke in strokesInPart[part]:
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][(phoneme, key)] for key in stroke) == len(stroke)).OnlyEnforceIf(phonemeAssignedToStroke[part][(phoneme, stroke)])

    # A boolean variable that is True if key 'k' is in the key set
    # of multiphoneme 'mp' (the union of keys from all phonemes in syllabiic part).
    multiphonemesKeys: dict[str, dict[tuple[tuple[str, ...], int], IntVar]]  = {"onset": {}, "nucleus": {}, "coda": {}}
    for part in PARTS:
        for multiphoneme in multiphonemesInPart[part]:
            mp_str = "".join(multiphoneme)
            for k in keysInPart[part]:
                multiphonemesKeys[part][multiphoneme, k] = model[part].NewBoolVar(f'multiphonemesKeys_{part[0]}_{mp_str}_{k}')

    # is_group_identical[g1][g2]: A boolean variable that is True if the key set of
    # multiphoneme mp1 is identical to the key set of multiphoneme mp2.
    is_keyset_identical: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], IntVar]] = {}
    for part in PARTS:
        is_keyset_identical[part] = {}
        mplist = list(multiphonemesInPart[part])
        for mp1i,mp1 in enumerate(mplist[:-1]):
            for mp2 in mplist[mp1i+1:]:
                if mp1 != mp2:
                    mp1_str = "".join(mp1)
                    mp2_str = "".join(mp2)
                    is_keyset_identical[part][mp1, mp2] = model[part].NewBoolVar(f'is_keyset_identical_{part[0]}_{mp1_str}_{mp2_str}')

    # Constraint 1: Each symbol's key set size must be between 1 and maxKeysPerPhoneme.
    for part in PARTS:
        for p in phonemesByPart[part]:
            _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k] for k in keyboard.keyIDinSyllabicPart[part]) >= 1)
            _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k] for k in keyboard.keyIDinSyllabicPart[part]) <= keyboard.maxKeysPerPhoneme[part])

    strokesContainingKey: dict[str, dict[int, list[tuple[int, ...]]]] = {p:{} for p in PARTS}
    for part in PARTS:
        for stroke in strokesInPart[part]:
            for key in stroke:
                if key not in strokesContainingKey[part]:
                    strokesContainingKey[part][key] = []
                strokesContainingKey[part][key].append(stroke)

    # New Try to force key-stroke relationship to affected to phoneme keys and strokes.
    strokeIsAssignedToPhoneme: dict[str, dict[tuple[str, tuple[int, ...]], IntVar]] = {p:{} for p in PARTS}
    for part in PARTS:
        for phoneme in phonemesByPart[part]:
            for stroke in strokesInPart[part]:
                strokeIsAssignedToPhoneme[part][phoneme, stroke] = model[part].NewBoolVar(f'phoneme_{phoneme}_stroke_{stroke}')
                _ = model[part].AddBoolAnd([keyIsAssignedToPhoneme[part][phoneme, key] for key in stroke]).OnlyEnforceIf(strokeIsAssignedToPhoneme[part][phoneme, stroke])
                #_ = model[part].AddBoolOr([keyIsAssignedToPhoneme[part][phoneme, key].Not() for key in stroke]).OnlyEnforceIf(strokeIsAssignedToPhoneme[part][phoneme, stroke].Not())
        # Needed because the above AddBoolOr is too strick and prevents associating a key
        # from a different stroke if it is also part of the current stroke.
        for phoneme in phonemesByPart[part]:
            for stroke in strokesInPart[part]:
                for key in stroke:
                    #The only way a key is not associated to a phoneme is if none of the strokes containing this key are assigned to the phoneme.
                    _ = model[part].AddBoolOr([strokeIsAssignedToPhoneme[part][phoneme, s2].Not() \
                        for k in stroke for s2 in strokesContainingKey[part][k]]).OnlyEnforceIf(keyIsAssignedToPhoneme[part][phoneme, key].Not())

    # Constraint 2: Model the key set of a group as the union of its symbols' key sets.
    # multiphonemesKeys[g, k] is true if and only if key 'k' is assigned to at least one symbol in group 'g'.
    for part in PARTS:
        for multiphoneme in multiphonemesInPart[part]:
            for k in keysInPart[part]:
                # We need a boolean variable to represent the condition: "at least one phoneme in multiphoneme
                # has key k assigned".
                mp_str = "".join(multiphoneme)
                at_least_one_phonem_has_key = model[part].NewBoolVar(f'union_has_key_{part[0]}_{mp_str}_{k}')

                # Add constraints to define the meaning of at_least_one_symbol_has_key.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k] for p in multiphoneme) >= 1).OnlyEnforceIf(at_least_one_phonem_has_key)
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k] for p in multiphoneme) == 0).OnlyEnforceIf(at_least_one_phonem_has_key.Not())
                # Limit the numbers of keys to the number of phonemes in the multiphoneme.
                _ = model[part].Add(sum(keyIsAssignedToPhoneme[part][p, k] for p in multiphoneme) <= len(multiphoneme)).OnlyEnforceIf(at_least_one_phonem_has_key)

                # Now, link the multiphonemesKeys variable directly to this condition.
                # multiphonemesKeys[multiphoneme, k] is equivalent to at_least_one_symbol_has_key.
                _ = model[part].Add(multiphonemesKeys[part][multiphoneme, k] == at_least_one_phonem_has_key)

    # Constraint 3: Model the identical key set relationship.
    # `mp1` is identical to `mp2` if and only if multiphonemeKeys[mp1,k] is equal multiphonemeKeys[mp2,k] for all k.
    for part in PARTS:
        mplist = list(multiphonemesInPart[part])
        for mp1i,mp1 in enumerate(mplist[:-1]):
            for mp2 in mplist[mp1i+1:]:
                if mp1 != mp2:
                    mismatch_literals: dict[int, IntVar] = {}
                    for k in keysInPart[part]:
                        # Create a temporary boolean variable for each key 'k' that is true if the keys don't match.
                        mismatch_literals[k] =  model[part].NewBoolVar(f'mismatch_{mp1}_{mp2}_{k}')
                        # Enforce that mismatch_literals[k] is true if multiphonemesKeys[g1, k] != multiphonemesKeys[g2, k]
                        _ = model[part].Add(multiphonemesKeys[part][mp1, k] != multiphonemesKeys[part][mp2, k]).OnlyEnforceIf(mismatch_literals[k])
                        _ = model[part].Add(multiphonemesKeys[part][mp1, k] == multiphonemesKeys[part][mp2, k]).OnlyEnforceIf(mismatch_literals[k].Not())
                    
                    # Now, model the `is_group_identical` variable. It's true if and only if there are no mismatches.
                    _ = model[part].Add(sum(mismatch_literals.values()) == 0).OnlyEnforceIf(is_keyset_identical[part][mp1, mp2])
                    _ = model[part].Add(sum(mismatch_literals.values()) > 0).OnlyEnforceIf(is_keyset_identical[part][mp1, mp2].Not())
                    # force recipocity :
                    #_ = model[part].Add(is_keyset_identical[part][mp1, mp2] == is_keyset_identical[part][mp2, mp1])

    # old Only usefull to detect strokes and associated keys that are affected to any phoneme, but not to which phoneme.
    strokeIsActive: dict[str, dict[tuple[int, ...], IntVar]] = {p: {} for p in PARTS}
    for part in PARTS:
        for stroke in strokesInPart[part]:
            strokeIsActive[part][stroke] = model[part].NewBoolVar(f'stroke_{stroke}')
            _ = model[part].AddBoolAnd([keyIsActive[part][key] for key in stroke]).OnlyEnforceIf(strokeIsActive[part][stroke])
            #_ = model[part].Add(strokeIsActive[stroke] == True).OnlyEnforceIf([keyIsActive[part][key] for key in stroke])
            _ = model[part].AddBoolOr([keyIsActive[part][key].Not() for key in stroke]).OnlyEnforceIf(strokeIsActive[part][stroke].Not())

    #old
    nbPhonemesToStroke: dict[str, dict[tuple[int, ...], IntVar]] = {}
    for part in PARTS:
        nbPhonemesToStroke[part] = { t: model[part].NewIntVar(0, len(phonemesByPart[part]), f'y_{part[0]}_{t}')
        for t in strokesInPart[part] }

    # old
    # Constraints: phoneme assignment
    for part in PARTS:
        for phoneme in phonemesByPart[part]:
            #Constraint: each phoneme is assigned to exactly one stroke in its part
            _ = model[part].Add(sum(phonemeAssignedToStroke[part][(phoneme, stroke)] for stroke in strokesInPart[part]) == 1)
            for stroke in strokesInPart[part]:
                # Reciprocal relationship between phonemeAssignedToStroke and strokeIsAssignedToPhoneme
                _ = model[part].Add(strokeIsAssignedToPhoneme[part][(phoneme, stroke)] == phonemeAssignedToStroke[part][(phoneme, stroke)])

    # old
    for part in PARTS:
        for stroke in strokesInPart[part]:
            #Constraint: each stroke has zero or more phonemes assigned to it
            _ = model[part].Add(nbPhonemesToStroke[part][stroke] == sum(phonemeAssignedToStroke[part][(phoneme, stroke)]
                for phoneme in phonemesByPart[part]))
            _ = model[part].Add(nbPhonemesToStroke[part][stroke] >= 1).OnlyEnforceIf(strokeIsActive[part][stroke])
            _ = model[part].Add(nbPhonemesToStroke[part][stroke] == 0).OnlyEnforceIf(strokeIsActive[part][stroke].Not())
        

    # --- 6. Define the Objective Function ---
    # The total cost is the sum of `is_group_identical` variables multiplied by their cost,
    # plus a penalty for each key assigned to a symbol.
    maxAmbiguity: dict[str, int] = {}
    overlapCosts: dict[str, IntVar] = {}
    for part in PARTS:
        maxAmbiguity[part] = int(sum(selectedMultiphonemesAmbiInPart[part].values()))
        overlapCosts[part] = model[part].NewIntVar(0, maxAmbiguity[part], 'overlap_cost_{part}')

    multiphonemeOverlapCost: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], IntVar ]] = {p:{} for p in PARTS}
    for part in PARTS:
        mplist = list(multiphonemesInPart[part])
        for mp1i,mp1 in enumerate(mplist[:-1]):
            for mp2 in mplist[mp1i+1:]:
                if mp1 != mp2 and (mp1,mp2) in selectedMultiphonemesAmbiInPart[part]:
                    multiphonemeOverlapCost[part][mp1, mp2] =  model[part].NewIntVar(0, maxAmbiguity[part], f'multiphonemeOverlapCost_{part[0]}_{mp1}_{mp2}')
                    _ = model[part].Add(multiphonemeOverlapCost[part][mp1, mp2] == int(selectedMultiphonemesAmbiInPart[part][mp1, mp2]) * is_keyset_identical[part][mp1, mp2])
        _ = model[part].Add(overlapCosts[part] == sum(multiphonemeOverlapCost[part][g1, g2] for (g1,g2) in selectedMultiphonemesAmbiInPart[part] ))

    key_penalty_cost: dict[str, IntVar] = {}
    KEY_ASSIGNMENT_PENALTY = 1
    maxNbKeyPenalty: dict[str, int] = {}
    for part in PARTS:
        maxNbKeyPenalty[part] = len(phonemesByPart[part]) * len(keysInPart[part]) * KEY_ASSIGNMENT_PENALTY
        key_penalty_cost[part] = model[part].NewIntVar(0, maxNbKeyPenalty[part], 'key_penalty_cost')
        _ = model[part].Add(key_penalty_cost[part] == sum(keyIsAssignedToPhoneme[part][p, k] * KEY_ASSIGNMENT_PENALTY \
            for p in phonemesByPart[part] for k in keysInPart[part]))

    print("Max Multiphoneme Ambiguity:", maxAmbiguity, "Max Nb Key penalty:", maxNbKeyPenalty)
    for part in PARTS:
        total_cost: IntVar = model[part].NewIntVar(0, maxAmbiguity[part] + maxNbKeyPenalty[part] , 'total_cost')
        _ = model[part].Add(total_cost == overlapCosts[part] + key_penalty_cost[part] )
        model[part].Minimize(total_cost)

    # Solve
    print("Solving the model...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.log_search_progress = False
    for part in PARTS:
        status = solver.Solve(model[part], _SolutionPrinter(model[part], 2.0))

        # Output
        print(f"Status for {part}: {status}")
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Total penalty = {solver.ObjectiveValue()}')
            for part in PARTS:
                strokesAssignedToPhoneme: dict[str, list[tuple[int, ...]]] = {phoneme: [] for phoneme in phonemesByPart[part]}
                keysAssignedToPhoneme: dict[str, list[int]] = {phoneme: [] for phoneme in phonemesByPart[part]}
                for stroke in strokesInPart[part]:
                    phonemes: list[str] = []
                    for phoneme in phonemesByPart[part]:
                        if solver.Value(phonemeAssignedToStroke[part][(phoneme, stroke)]) == 1:
                            strokesAssignedToPhoneme[phoneme].append(stroke)
                            phonemes.append(phoneme)
                    #if phonemes:
                    #    print(f'Part {part}, Stroke {stroke}: phonemes {phonemes}')
                for k in keysInPart[part]:
                    phonemes = []
                    for phoneme in phonemesByPart[part]:
                        if solver.Value(keyIsAssignedToPhoneme[part][(phoneme, k)]) == 1:
                            keysAssignedToPhoneme[phoneme].append(k)
                            phonemes.append(phoneme)
                    #if phonemes:
                    #    print(f'Part {part}, Key {k}: Phonemes {phonemes}')
                for phoneme in phonemesByPart[part]:
                    print(f'Part {part}, Phoneme {phoneme}: Strokes {strokesAssignedToPhoneme[phoneme]}, Keys {keysAssignedToPhoneme[phoneme]}')

                multiphonemesKeysAssigned:dict[tuple[str, ...], list[int]] = {}
                multiphonemesStrokesAssigned:dict[tuple[str, ...], list[tuple[int, ...]]] = {}
                for multiphoneme in multiphonemesInPart[part]:
                    multiphonemesKeysAssigned[multiphoneme] = []
                    for k in keysInPart[part]:
                        if solver.Value(multiphonemesKeys[part][multiphoneme, k]) == 1:
                            multiphonemesKeysAssigned[multiphoneme].append(k)
                    #print(f'Part {part}, Multiphoneme {multiphoneme}: Keys {multiphonemesKeysAssigned[multiphoneme]}')
                for mp1,mp2 in selectedMultiphonemesAmbiInPart[part]:
                    if len(mp1) == 1 and len(mp2) == 1:
                        if solver.Value(is_keyset_identical[part][mp1, mp2]) == 1 :
                            print(f'Part {part}, Ambiguous Multiphonemes {mp1} and {mp2} share the same keys: {multiphonemesKeysAssigned[mp1]}')
                            print(f'{mp1} ambiguity to {mp2} cost {solver.Value(multiphonemeOverlapCost[part][(mp1, mp2)])} ')
                        elif selectedMultiphonemesAmbiInPart[part][mp1,mp2] > 0.0:
                            print(f'Part {part}, Multiphonemes {mp1} and {mp2} have keys : {multiphonemesKeysAssigned[mp1]}' +
                                f' and : {multiphonemesKeysAssigned[mp1]} strokes: ')
                            print(f'{mp1} ambiguity to {mp2} cost {solver.Value(multiphonemeOverlapCost[part][(mp1, mp2)])}' +
                                f' should be : {selectedMultiphonemesAmbiInPart[part][mp1,mp2]}')

        else:
            print('No solution found.')
