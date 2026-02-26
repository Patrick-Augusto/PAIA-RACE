#!/usr/bin/python3

import sys
import random
import subprocess
import networkx as nx
import matplotlib.pyplot as plt


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


def call_solver(cnf_file):
    """ Executa solver.py i retorna la seva sortida processada """
    try:
        result = subprocess.run(["python3", "solver.py", cnf_file], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()

        if "s UNSATISFIABLE" in lines:
            return None

        for line in lines:
            if line.startswith("v"):
                values = list(map(int, line.split()[1:-1]))  # Elimina el "v" i el "0" final
                return {abs(v): (v > 0) for v in values}

    except subprocess.CalledProcessError as e:
        print("Error executant solver.py:", e)
        return None

    return None


def draw_graph(num_vars, solution, output_file="graph.png"):
    """ Dibuixa el graf amb els valors de la solució utilitzant networkx i matplotlib """
    G = nx.Graph()

    # Afegir nodes amb color segons la solució
    node_colors = []
    for var in range(1, num_vars + 1):
        G.add_node(var)
        node_colors.append("green" if solution[var] else "red")

    # Connectar els nodes en seqüència com a exemple
    for var in range(1, num_vars):
        G.add_edge(var, var + 1)

    # Dibuixar el graf
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G)  # Posició dels nodes
    nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color="black", node_size=800, font_size=10)

    # Guardar i mostrar el graf
    plt.savefig(output_file)
    print(f"Graf generat: {output_file}")
    plt.show()


def main():
    if len(sys.argv) != 2:
        print("Ús: ./generator.py <input_cnf>")
        sys.exit(1)

    cnf_file = sys.argv[1]
    num_vars, _ = read_cnf(cnf_file)

    solution = call_solver(cnf_file)

    if solution is None:
        print("No s'ha trobat cap solució.")
    else:
        print("Solució trobada:", solution)
        draw_graph(num_vars, solution)


if __name__ == "__main__":
    main()
