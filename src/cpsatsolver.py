
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
import time
from functools import cmp_to_key
from src.keyboard import Keyboard
from src.grammar import Phoneme, Syllable


def optimizeTheory(keyboard: Keyboard,
                   syllabicPartAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]], 
                   syllabicParts: list[str]) -> None:
    """
    Using OR-tools, encode the optimisation rules and objectives to find the best keymap.
    """
    class _SolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Callback to print intermediate solutions."""

        def __init__(self, model:cp_model.CpModel, print_interval_seconds:float=2.0,
                     variables: list[cp_model.IntVar]|None = None) -> None:
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.__model = model
            self.__solution_count = 0
            self.__first_print_time = time.time()
            self.__last_print_time = self.__first_print_time
            self.__print_interval = print_interval_seconds
            self.__variables = [] if variables == None else variables

        def on_solution_callback(self) -> None:
            """Called by the solver when a new solution is found."""
            current_time = time.time()
            self.__solution_count += 1
            elapsed_time = current_time - self.__first_print_time
            if current_time - self.__last_print_time >= self.__print_interval:
                print(f'Solution {self.__solution_count}:'
                      + f' objective = {self.ObjectiveValue()}, elapsed = {elapsed_time:.2f} s')
                print("Number of variables =", len(self.__variables))
                for v in self.__variables:
                    print(f'  {v.Name()} = {self.Value(v)}')
                self.__last_print_time = current_time

    
    PARTS: list[str] = syllabicParts
    STROKE_ASSIGNMENT_PENALTY = 1
    KEY_ASSIGNMENT_PENALTY = 1
    OVERLAP_PENALTY = 3000
    SOLVER_TIME = 60.0  # seconds
    SOLVER_LOG = False
    MAX_MULTIPHONEMES: int = 500
    
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
    multiphonemesInPart: dict[str, list[tuple[str, ...]]] = { }
    for part in PARTS:
        multiphonemesInPart[part] = []
        for (mp1, mp2) in syllabicPartAmbiguity[part]:
            multiphonemesInPart[part].append(mp1)
            multiphonemesInPart[part].append(mp2)
        multiphonemesInPart[part] = list(set(multiphonemesInPart[part]))
        
    sortedMultiphonemeAmbiInPart: dict[str, list[tuple[tuple[tuple[str, ...], tuple[str, ...]], float]]] = {p:[] for p in PARTS}
    for part in PARTS:
        for mpi1,mp1 in enumerate(multiphonemesInPart[part][:-1]):
            for mp2 in multiphonemesInPart[part][mpi1+1:]:
                ambiguity: float = syllabicPartAmbiguity[part].get((mp1,mp2), syllabicPartAmbiguity[part].get((mp2,mp1), 0.0))
                sortedMultiphonemeAmbiInPart[part].append(((mp1,mp2), ambiguity))
        sortedMultiphonemeAmbiInPart[part].sort(key=lambda mp : mp[1], reverse=True)

    selectedMultiphonemesAmbiguity: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], float]] = {}
    for part in PARTS:
         selectedMultiphonemesAmbiguity[part] =  {mp:cost for mp, cost in sortedMultiphonemeAmbiInPart[part][:MAX_MULTIPHONEMES]}

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
        for phoneme in phonemesByPart[part]:
            for stroke in strokesInPart[part]:
                strokeIsAssignedToPhoneme[part][(phoneme, stroke)] = \
                    model[part].NewBoolVar(f'x_{part[0]}_{phoneme}_{stroke}')

            for key in keysInPart[part]:
                keyIsAssignedToPhoneme[part][(phoneme, key)] = \
                    model[part].NewBoolVar(f'k_{phoneme}_{key}')
            
            # Constraint 1: Each symbol's key set size must be between 1 and maxKeysPerPhoneme.
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
            

    # A boolean variable that is True if key 'k' is in the key set
    # of multiphoneme 'mp' (the union of keys from all phonemes in syllabiic part).
    multiphonemeHasKey: dict[str, dict[tuple[tuple[str, ...], int], IntVar]]  = {p:{} for p in PARTS}
    for part in PARTS:
        for multiphoneme in multiphonemesInPart[part]:
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
                mp1_str = "".join(mp1)
                mp2_str = "".join(mp2)
                keysetsAreIdentical[part][mp1, mp2] = \
                    model[part].NewBoolVar(f'is_keyset_identical_{part[0]}_{mp1_str}_{mp2_str}')


    # Constraint 2: Model the key set of a group of phonemes as the union of its phonemes' key sets.
    # multiphonemesKeys[mp, k] is true if and only if key 'k' is assigned to at least one symbol in multiphoneme'mp'.
    for part in PARTS:
        for multiphoneme in multiphonemesInPart[part]:
            for k in keysInPart[part]:
                # We need a boolean variable to represent the condition: "at least one phoneme in multiphoneme
                # has key k assigned".
                mp_str = "".join(multiphoneme)
                atLeastOnePhonemeHasKey = model[part].NewBoolVar(f'keyset_has_key{part[0]}_{mp_str}_{k}')

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

    # Constraint 3: Model the identical key set relationship.
    # `mp1` is identical to `mp2` if and only if multiphonemeKeys[mp1,k] is equal multiphonemeKeys[mp2,k] for all k.
    mismatch_literals: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], dict[int, IntVar]]] = {p:{} for p in PARTS}
    for part in PARTS:
        for mp1i,mp1 in enumerate(multiphonemesInPart[part][:-1]):
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


    # --- Define the Objective Function ---
    # The total cost is defined by 3 metrics :
    # - The amount of ambiguity of overlapping keyset representing multiphonemes that are ambiguous.
    # - The complexity/ergonomy of strokes assigned to each phoneme times their respecting frequency.
    # - Todo: The order of phonemes on the keyboard respecting phoneme order in words.
    maxAmbiguity: dict[str, int] = {}
    overlapCosts: dict[str, IntVar] = {}
    for part in PARTS:
        maxAmbiguity[part] = int(sum(selectedMultiphonemesAmbiguity[part].values()) * OVERLAP_PENALTY )
        overlapCosts[part] = model[part].NewIntVar(0, maxAmbiguity[part], 'overlap_cost_{part}')

    # Define multiphoneme overlap costs
    multiphonemeOverlapCost: dict[str, dict[tuple[tuple[str, ...], tuple[str, ...]], IntVar ]] = {
            p:{} for p in PARTS}
    for part in PARTS:
        for mp1i,mp1 in enumerate(multiphonemesInPart[part][:-1]):
            for mp2 in multiphonemesInPart[part][mp1i+1:]:
                if mp1 != mp2 and (mp1,mp2) in selectedMultiphonemesAmbiguity[part]:
                    multiphonemeOverlapCost[part][mp1, mp2] = \
                        model[part].NewIntVar(0, maxAmbiguity[part], 
                                              f'multiphonemeOverlapCost_{part[0]}_{mp1}_{mp2}')

                    # Define de Ovelap cost (ambiguity penalty) for each pair of multiphonemes
                    _ = model[part].Add(multiphonemeOverlapCost[part][mp1, mp2]
                                == int(selectedMultiphonemesAmbiguity[part][mp1, mp2])
                                        * keysetsAreIdentical[part][mp1, mp2])
        
        # Get the total overlap cost for the part
        _ = model[part].Add(overlapCosts[part] == sum(multiphonemeOverlapCost[part][mp1, mp2]
                    * OVERLAP_PENALTY for (mp1,mp2) in selectedMultiphonemesAmbiguity[part] ))

    # Define the stroke penalty cost based on stroke complexity and phoneme frequency.
    strokeCosts: dict[tuple[int, ...], int] = {
        stroke: int(keyboard.getStrokeCost(stroke)) for p in PARTS for stroke in strokesInPart[p]}
    maxStrokeCost = max(strokeCosts.values())

    phonemeFrequency: dict[str, dict[str, int]] = {part: {
        p: int(Syllable.phonemeColByPart[part].phonemeNames[p].frequency)
        for p in phonemesByPart[part]} for part in PARTS}
    #print("Phoneme frequencies:", phonemeFrequency)

    maxStrokesPenalty: dict[str, int] = {
        part: maxStrokeCost * sum(phonemeFrequency[part][p] for p in phonemesByPart[part])
            * STROKE_ASSIGNMENT_PENALTY for part in PARTS }

    # for part in PARTS:
    #     print(f'Phoneme frequencies: ', {p: phonemeFrequency[part][p]
    #          for p in phonemesByPart[part]})

    allStrokesPenaltyCost: dict[str, IntVar] = {}
    strokePenaltyCost: dict[str, dict[tuple[int, ...], IntVar]] = {p:{} for p in PARTS}
    for part in PARTS:
        for stroke in strokesInPart[part]:
            # Per-stroke penalty cost
            strokePenaltyCost[part][stroke] = model[part].NewIntVar(0, maxStrokesPenalty[part], f'stroke_{stroke}_cost')
            _ = model[part].Add(strokePenaltyCost[part][stroke] == sum(
                strokeIsAssignedToPhoneme[part][p, stroke] * STROKE_ASSIGNMENT_PENALTY
                * phonemeFrequency[part][p] * strokeCosts[stroke] for p in phonemesByPart[part] ))

        allStrokesPenaltyCost[part] = model[part].NewIntVar(0, maxStrokesPenalty[part], 'strokes_penalty_cost')
        _ = model[part].Add(allStrokesPenaltyCost[part] == sum(
            strokePenaltyCost[part][stroke] for stroke in strokesInPart[part]))
        
    # key_penalty_cost: dict[str, IntVar] = {}
    # maxNbKeyPenalty: dict[str, int] = {}
    # for part in PARTS:
    #     maxNbKeyPenalty[part] = int( keyboard.maxKeysPerPhoneme[part] * KEY_ASSIGNMENT_PENALTY 
    #         * sum(p.frequency for p in Syllable.phonemeColByPart[part].phonemes))
    #     key_penalty_cost[part] = model[part].NewIntVar(0, maxNbKeyPenalty[part], 'key_penalty_cost')
    #
    #     # Define the penalty associated to the average number of keys assigned to each phoneme 
    #     # Used to keep the keysets small.
    #     _ = model[part].Add(key_penalty_cost[part] == sum(
    #         keyIsAssignedToPhoneme[part][p, k] * KEY_ASSIGNMENT_PENALTY
    #         * int(Syllable.phonemeColByPart[part].phonemeNames[p].frequency)
    #         for p in phonemesByPart[part] for k in keysInPart[part]))

    for part in PARTS:
        print("Max Multiphoneme Ambiguity:", maxAmbiguity[part], "Max Strokes penalty:", maxStrokesPenalty[part])
        total_cost: IntVar = model[part].NewIntVar(0, maxAmbiguity[part] + maxStrokesPenalty[part] , 'total_cost')

        # Define the total cost to optimize.
        _ = model[part].Add(total_cost == (overlapCosts[part] + allStrokesPenaltyCost[part])  )
        model[part].Minimize(total_cost)

    # Solve
    print("Solving the model...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME
    solver.parameters.log_search_progress = SOLVER_LOG
    for part in PARTS:
        status = solver.Solve(model[part],
                              _SolutionPrinter(model[part],
                                               1.0,
                                               [overlapCosts[part], allStrokesPenaltyCost[part]]))

        # Output
        print(f"Status for {part}: {status}")
        print(solver.StatusName(status))
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f'Total penalty = {solver.ObjectiveValue()}')
            for part in PARTS:
                strokesAssignedToPhoneme: dict[str, list[tuple[int, ...]]] = {p: [] for p in phonemesByPart[part]}
                keysAssignedToPhoneme: dict[str, list[int]] = {p: [] for p in phonemesByPart[part]}
                phonemesAssignedToStroke: dict[tuple[int, ...], list[str]] = {s: [] for s in strokesInPart[part]}
                phonemesAssignesToKey: dict[int, list[str]] = {k: [] for k in keysInPart[part]}

                # Extract key-phoneme and stroke-phoneme associations from the solution
                for stroke in strokesInPart[part]:
                    for phoneme in phonemesByPart[part]:
                        if solver.Value(strokeIsAssignedToPhoneme[part][(phoneme, stroke)]) == 1:
                            strokesAssignedToPhoneme[phoneme].append(stroke)
                            phonemesAssignedToStroke[stroke].append(phoneme)
                for k in keysInPart[part]:
                    for phoneme in phonemesByPart[part]:
                        if solver.Value(keyIsAssignedToPhoneme[part][(phoneme, k)]) == 1:
                            keysAssignedToPhoneme[phoneme].append(k)
                            phonemesAssignesToKey[k].append(phoneme)

                # Print the solution
                print("Phonemes:")
                for phoneme in phonemesByPart[part]:
                    print(f' Part {part}, Phoneme {phoneme}: Strokes {strokesAssignedToPhoneme[phoneme]}, Keys {keysAssignedToPhoneme[phoneme]}')
                print("Keys:")
                for key in keysInPart[part]:
                    print(f' Part {part}, Key {key}: Phonemes {phonemesAssignesToKey[key]}')
                print("Strokes:")
                for stroke in strokesInPart[part]:
                    if len(phonemesAssignedToStroke[stroke]) > 0:
                        print(f' Part {part}, Stroke: {stroke}, Phonemes: {phonemesAssignedToStroke[stroke]},'
                            + f' stroke cost: {strokeCosts[stroke]} (frequency weighted cost: '
                            + f' {solver.Value(strokePenaltyCost[part][stroke])})')
                            # + f' expected : {strokeCosts[stroke] * sum(phonemeFrequency[part][p]
                            #                  * STROKE_ASSIGNMENT_PENALTY for p in phonemesAssignedToStroke[stroke])})')

                multiphonemesKeysAssigned:dict[tuple[str, ...], list[int]] = {}
                for multiphoneme in multiphonemesInPart[part]:
                    multiphonemesKeysAssigned[multiphoneme] = []
                    for k in keysInPart[part]:
                        if solver.Value(multiphonemeHasKey[part][multiphoneme, k]) == 1:
                            multiphonemesKeysAssigned[multiphoneme].append(k)

                for mp1,mp2 in selectedMultiphonemesAmbiguity[part]:
                    if solver.Value(keysetsAreIdentical[part][mp1, mp2]) == 1 :
                        print(f'(1) Part {part}, Ambiguous Multiphonemes {mp1} and {mp2} share the same keys: {multiphonemesKeysAssigned[mp1]}')
                        print(f'{mp1} ambiguity to {mp2} cost {solver.Value(multiphonemeOverlapCost[part][(mp1, mp2)]) * OVERLAP_PENALTY} ')

                    elif sorted(multiphonemesKeysAssigned[mp1]) == sorted(multiphonemesKeysAssigned[mp2]) and set(mp1) != set(mp2):
                        # This should only happen if there is a bug, can probably be removed.
                        print(f'(2) Part {part}, Multiphonemes {mp1} and {mp2} have keys : {multiphonemesKeysAssigned[mp1]}' +
                            f' and : {multiphonemesKeysAssigned[mp2]} strokes: ')
                        print(f'{mp1} ambiguity to {mp2} cost {solver.Value(multiphonemeOverlapCost[part][(mp1, mp2)]) * OVERLAP_PENALTY}' +
                            f' should be : {selectedMultiphonemesAmbiguity[part][mp1,mp2] * OVERLAP_PENALTY}')
                        for k in keysInPart[part]:
                            if k in multiphonemesKeysAssigned[mp1] and k in multiphonemesKeysAssigned[mp2]:
                                print(f'Key {k} is shared')
                            if solver.Value(mismatch_literals[part][mp1,mp2][k]) == 1:
                                print(f'mismatch_literals[{part}][{mp1},{mp2}][{k}] is a mismatch '+
                                        f'{k in multiphonemesKeysAssigned[mp1]} {k in multiphonemesKeysAssigned[mp2]}')
                    elif len(mp1)+len(mp2) >= 2:
                        if set(multiphonemesKeysAssigned[mp1]) == set(multiphonemesKeysAssigned[mp2]):
                            if selectedMultiphonemesAmbiguity[part].get((mp1,mp2), selectedMultiphonemesAmbiguity[part].get((mp2,mp1), 0.0)) > 0.0: 
                                print(f'(3) Part {part}, Multiphonemes {mp1} and {mp2} have keys : {multiphonemesKeysAssigned[mp1]}' +
                                    f' and : {multiphonemesKeysAssigned[mp2]} strokes: ')
                                print(f'{mp1} ambiguity to {mp2} cost {solver.Value(multiphonemeOverlapCost[part][(mp1, mp2)]) * OVERLAP_PENALTY }' +
                                    f' should be : {selectedMultiphonemesAmbiguity[part][mp1,mp2] * OVERLAP_PENALTY}')

        else:
            print('No solution found.')
