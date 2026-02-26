#!/usr/bin/env python3
import sys
import random
import time


class WalkSAT:

    #Constructor
    def __init__(self, clauses, num_vars, max_flips=10000, noise=0.5):
        self.clauses = clauses      #List of clauses to satisfy
        self.num_vars = num_vars    #Total num of variables
        self.max_flips = max_flips  #Maximum number of attempts to find solution
        self.noise = noise          #Probability of making a random change
        self.assignment = None      #Variable value assignment
        self.unsat_clauses = None   #Unsatisfied clauses


    # Method to assign random True or False values to all variables
    def initialize_assignment(self):
        self.assignment = [random.choice([True, False]) for _ in range(self.num_vars + 1)]
        self.assignment[0] = None  # variables start at 1

    # Method that checks if a clause is satisfied with the current variable assignment
    # If the clause contains a true assignment for a variable the clause is true
    def evaluate_clause(self, clause):
        for lit in clause:
            var = abs(lit)
            value = self.assignment[var]
            if (lit > 0 and value) or (lit < 0 and not value):
                return True
        return False

    # Method that counts how many clauses are NOT satisfied with the current assignment.
    def count_unsat_clauses(self):
        """Count how many clauses are unsatisfied"""
        count = 0
        for clause in self.clauses:
            if not self.evaluate_clause(clause):
                count += 1
        return count

    # Method that finds all clauses that are NOT satisfied with the current assignment.
    # Returns a list with the indices of those clauses
    def get_unsat_clauses(self):
        """Get all unsatisfied clauses"""
        unsat = []
        for i, clause in enumerate(self.clauses):
            if not self.evaluate_clause(clause):
                unsat.append(i)
        return unsat

    # Method that counts how many clauses would become unsatisfied if we flip a variable
    def get_break_count(self, var):
        count = 0
        for clause in self.clauses:
            # Check if this clause contains the variable
            contains_var = any(abs(lit) == var for lit in clause)
            if contains_var:
                currently_sat = self.evaluate_clause(clause)
                # Flip the variable and check
                self.assignment[var] = not self.assignment[var]
                if not self.evaluate_clause(clause) and currently_sat:
                    count += 1
                # Flip back
                self.assignment[var] = not self.assignment[var]
        return count

    # MAIN WALKSAT algorithm
    def solve(self):

        self.initialize_assignment()

        for _ in range(self.max_flips):
            unsat_clauses = self.get_unsat_clauses()
            if not unsat_clauses:
                return True  # Solution found

            # Randomly select an unsatisfied clause
            clause_idx = random.choice(unsat_clauses)
            clause = self.clauses[clause_idx]

            # With probability noise, flip a random variable in the clause
            if random.random() < self.noise:
                var = abs(random.choice(clause))
                self.assignment[var] = not self.assignment[var]
            else:
                # Otherwise, flip the variable that minimizes break count
                min_break = float('inf')
                best_vars = []

                for lit in clause:
                    var = abs(lit)
                    break_count = self.get_break_count(var)

                    if break_count < min_break:
                        min_break = break_count
                        best_vars = [var]
                    elif break_count == min_break:
                        best_vars.append(var)

                # Randomly select among variables with minimal break count
                var = random.choice(best_vars)
                self.assignment[var] = not self.assignment[var]

        return False  # No solution found within max_flips

# Reads a CNF file and extracts clauses and the number of variables
def parse_cnf_file(filename):
    """Parse CNF file into clauses and number of variables"""
    clauses = []
    num_vars = 0

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                num_vars = int(parts[2])
            else:
                clause = [int(x) for x in line.split()[:-1]]  # exclude trailing 0
                clauses.append(clause)

    return clauses, num_vars


def main():
    if len(sys.argv) != 2:
        print("Usage: ./walksat_solver <input_cnf_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    clauses, num_vars = parse_cnf_file(input_file)

    # Initialize WalkSAT with some parameters
    walksat = WalkSAT(clauses, num_vars, max_flips=100000, noise=0.5)

    start_time = time.time()
    solved = walksat.solve()
    elapsed_time = time.time() - start_time

    # Print results in required format
    print("c WalkSAT Solver")
    if solved:
        print("s SATISFIABLE")
        # Print variable assignments (1..num_vars)
        assignments = []
        for var in range(1, num_vars + 1):
            value = walksat.assignment[var]
            assignments.append(str(var) if value else str(-var))
        print("v " + " ".join(assignments) + " 0")
    else:
        print("s UNSATSATIFIABLE")


if __name__ == "__main__":
    main()