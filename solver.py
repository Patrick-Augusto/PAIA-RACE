#!/usr/bin/python3

import sys
import random

def read_cnf(file_path):
    """ Llegeix un fitxer CNF i retorna les clàusules i el nombre de variables """
    clauses = []
    num_vars = 0
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                if len(parts) >= 3:
                    num_vars = int(parts[2])
                continue
            
            # Gestionem clàusules que poden ocupar múltiples línies
            clause = [int(x) for x in line.split() if x != '0']
            if clause:
                clauses.append(clause)
    return num_vars, clauses

def walksat(num_vars, clauses, max_flips=100000, p=0.3):
    """ Implementació optimitzada de WalkSAT """
    # Representació de l'assignació com a llista (1-based index)
    # True = 1, False = 0 per a velocitat
    assignment = [random.randint(0, 1) for _ in range(num_vars + 1)]
    
    # Pre-calcular a quines clàusules apareix cada literal
    # pos_in_clauses[v] -> clàusules on apareix v
    # neg_in_clauses[v] -> clàusules on apareix -v
    pos_in_clauses = [[] for _ in range(num_vars + 1)]
    neg_in_clauses = [[] for _ in range(num_vars + 1)]
    
    for idx, clause in enumerate(clauses):
        for lit in clause:
            if lit > 0:
                pos_in_clauses[lit].append(idx)
            else:
                neg_in_clauses[-lit].append(idx)
                
    # sat_count[i] = quantes literals de la clàusula i són certs
    sat_count = [0] * len(clauses)
    unsat_clauses = []
    
    for idx, clause in enumerate(clauses):
        count = 0
        for lit in clause:
            val = assignment[abs(lit)]
            if (lit > 0 and val) or (lit < 0 and not val):
                count += 1
        sat_count[idx] = count
        if count == 0:
            unsat_clauses.append(idx)
            
    # Índexos per a accés ràpid i eliminació en O(1) d'unsat_clauses
    unsat_idx_in_list = [-1] * len(clauses)
    for i, c_idx in enumerate(unsat_clauses):
        unsat_idx_in_list[c_idx] = i

    for _ in range(max_flips):
        if not unsat_clauses:
            return assignment
            
        # Triar una clàusula no satisfeta a l'atzar
        c_idx = random.choice(unsat_clauses)
        clause = clauses[c_idx]
        
        # Estratègia WalkSAT: triar quina variable girar
        best_var = -1
        
        if random.random() < p:
            # Moviment aleatori
            best_var = abs(random.choice(clause))
        else:
            # Moviment cobdiciós: minimitzar "break" (quantes clàusules deixen d'estar satisfetes)
            min_break = float('inf')
            candidates = []
            
            for lit in clause:
                v = abs(lit)
                # Calculem el "break count" (quantes clàusules tenen sat_count == 1 i aquest literal és el que les satisfà)
                break_count = 0
                
                # Si girem v, mirem les clàusules on v actualment satisfà la clàusula
                relevant_clauses = pos_in_clauses[v] if assignment[v] else neg_in_clauses[v]
                for rc_idx in relevant_clauses:
                    if sat_count[rc_idx] == 1:
                        break_count += 1
                
                if break_count < min_break:
                    min_break = break_count
                    candidates = [v]
                elif break_count == min_break:
                    candidates.append(v)
            
            best_var = random.choice(candidates)
            
        # Girar la variable best_var i actualitzar estats incrementalment
        old_val = assignment[best_var]
        new_val = 1 - old_val
        assignment[best_var] = new_val
        
        # Clàusules on la variable apareixia com a TRUE (ara és FALSE) -> sat_count baixa
        to_false_clauses = pos_in_clauses[best_var] if old_val else neg_in_clauses[best_var]
        for rc_idx in to_false_clauses:
            sat_count[rc_idx] -= 1
            if sat_count[rc_idx] == 0:
                # S'ha tornat insatisfeta
                unsat_idx_in_list[rc_idx] = len(unsat_clauses)
                unsat_clauses.append(rc_idx)
                
        # Clàusules on la variable apareixia com a FALSE (ara és TRUE) -> sat_count puja
        to_true_clauses = neg_in_clauses[best_var] if old_val else pos_in_clauses[best_var]
        for rc_idx in to_true_clauses:
            if sat_count[rc_idx] == 0:
                # Ha deixat d'estar insatisfeta (O(1) remove)
                pos = unsat_idx_in_list[rc_idx]
                last_c_idx = unsat_clauses[-1]
                unsat_clauses[pos] = last_c_idx
                unsat_idx_in_list[last_c_idx] = pos
                unsat_clauses.pop()
                unsat_idx_in_list[rc_idx] = -1
            sat_count[rc_idx] += 1

    return None

def main():
    if len(sys.argv) != 2:
        print("Ús: ./solver.py <input_cnf>")
        sys.exit(1)

    num_vars, clauses = read_cnf(sys.argv[1])
    if not clauses:
        print("s SATISFIABLE")
        print("v 0")
        return

    # Intentar diverses vegades amb diferents llavors si no es troba solució
    for _ in range(10): 
        solution = walksat(num_vars, clauses)
        if solution:
            print("s SATISFIABLE")
            # Convertim 1/0 a True/False per mantenir compatibilitat si cal, 
            # però aquí imprimim directament el format SAT
            res = []
            for var in range(1, num_vars + 1):
                res.append(str(var if solution[var] else -var))
            print("v", " ".join(res), "0")
            return

    print("s UNSATISFIABLE")

if __name__ == "__main__":
    main()


