#!/usr/bin/python
# coding: utf-8
#
from ortools.sat.python import cp_model
import time

class SolutionPrinter(cp_model.CpSolverSolutionCallback):
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
        self.__print_count = 0

    def on_solution_callback(self) -> None:
        """Called by the solver when a new solution is found."""
        current_time = time.time()
        self.__solution_count += 1
        self.__print_count += 1
        nbLines = len(self.__variables) + 1
        elapsed_time = current_time - self.__first_print_time
        if self.__solution_count == 1 \
                or current_time - self.__last_print_time >= self.__print_interval:
            # Clear before printing
            if self.__print_count > 3:
                for _ in range(nbLines):
                    print("\033[1A", end="")
                    print("\033[2K", end="")
            print(f'Solution {self.__solution_count}:'
                + f' objective = {self.ObjectiveValue():,}, elapsed = {elapsed_time:.2f} s')
            for v in self.__variables:
                print(f'  {v.Name():>32} = {self.Value(v):,}')
            self.__last_print_time = current_time
