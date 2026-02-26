#!/usr/bin/python3

import sys
import random


def read_cnf(file_path):
    """ Llegeix un fitxer CNF i retorna les clàusules i el nombre de variables """
    clauses = []
    num_vars = 0
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('c'):
                continue
            elif line.startswith('p'):
                _, _, num_vars, _ = line.split()
                num_vars = int(num_vars)
            else:
                clause = list(map(int, line.split()[:-1]))  # Elimina el 0 final
                clauses.append(clause)
    return int(num_vars), clauses


def is_satisfied(clause, assignment):
    """ Retorna True si la clàusula és satisfeta """
    return any(assignment[abs(lit)] == (lit > 0) for lit in clause)


def evaluate(clauses, assignment):
    """ Comprova quantes clàusules es satisfan donada una assignació """
    return sum(is_satisfied(clause, assignment) for clause in clauses)


def flip_variable(assignment, var):
    """ Inverteix el valor d'una variable en l'assignació """
    assignment[var] = not assignment[var]


def walksat(num_vars, clauses, max_flips=50000, p=0.5):
    """ Implementació millorada de WalkSAT """
    assignment = {var: random.choice([True, False]) for var in range(1, num_vars + 1)}

    for _ in range(max_flips):
        unsatisfied = [clause for clause in clauses if not is_satisfied(clause, assignment)]

        if not unsatisfied:
            return assignment


        clause = random.choice(unsatisfied)

        if random.random() < p:
            flip_var = abs(random.choice(clause))
        else:
            flip_var = abs(max(clause, key=lambda v: evaluate(clauses, {**assignment, abs(v): not assignment[abs(v)]})))

        flip_variable(assignment, flip_var)

    return None

def main():
    if len(sys.argv) != 2:
        print("Ús: ./solver.py <input_cnf>")
        sys.exit(1)

    num_vars, clauses = read_cnf(sys.argv[1])
    solution = walksat(num_vars, clauses)

    if solution:
        print("s SATISFIABLE")
        print("v", " ".join(str(var if val else -var) for var, val in sorted(solution.items())), "0")
    else:
        print("s UNSATISFIABLE")

if __name__ == "__main__":
    main()


