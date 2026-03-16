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
        result = subprocess.run([sys.executable, "solver.py", cnf_file], capture_output=True, text=True, check=True)
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


def draw_graph(num_vars, clauses, solution, output_file="graph.png"):
    """ Dibuixa el graf amb els valors de la solució utilitzant networkx i matplotlib """
    G = nx.Graph()

    # Afegir nodes amb color segons la solució
    node_colors = []
    for var in range(1, num_vars + 1):
        G.add_node(var)
        # Colors més agradables i moderns (Material Design) per marcar la veracitat
        color = "#4CAF50" if solution.get(var, False) else "#F44336"
        node_colors.append(color)

    # Connectar nodes que comparteixen clàusules (mostra l'estructura real del problema)
    for clause in clauses:
        vars_in_clause = [abs(lit) for lit in clause if lit != 0]
        for i in range(len(vars_in_clause)):
            for j in range(i + 1, len(vars_in_clause)):
                if vars_in_clause[i] != vars_in_clause[j]:
                    G.add_edge(vars_in_clause[i], vars_in_clause[j])

    # Fallback: connectar seqüencialment si el fitxer no ens ha generat cap aresta
    if G.number_of_edges() == 0:
        for var in range(1, num_vars):
            G.add_edge(var, var + 1)

    # Configuració de la figura
    plt.figure(figsize=(12, 9), facecolor="#F8F9FA")
    ax = plt.gca()
    ax.set_facecolor("#F8F9FA")

    # Posició dels nodes (utilitzant spring de forma predeterminada, k s'ajusta perquè no estiguin massa junts)
    try:
        # Kamada-Kawai té molt bona estètica per grafs petits però falla si hi ha components desconnectats
        pos = nx.kamada_kawai_layout(G)
    except:
        pos = nx.spring_layout(G, seed=42, k=1.2/((num_vars)**0.5 if num_vars > 0 else 1))

    # Dibuixar les arestes del graf amb transparència
    nx.draw_networkx_edges(
        G, pos,
        edge_color="#B0BEC5",
        width=1.5,
        alpha=0.6
    )

    # Ajust de mides per a millor visualització independent del tamany
    node_size = max(500, min(2000, 30000 // max(1, num_vars)))
    font_size = max(9, min(14, int(node_size ** 0.5 * 0.35)))

    # Dibuixar els nodes amb vora blanca
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_size,
        edgecolors="white",
        linewidths=2.5
    )

    # Dibuixar les etiquetes (números de les variables)
    nx.draw_networkx_labels(
        G, pos,
        font_size=font_size,
        font_color="white",
        font_weight="bold",
        font_family="sans-serif"
    )

    # Ocultar eixos i afegir títol
    plt.title("Estructura i Solució de les Variables (SAT)", fontsize=18, fontweight="bold", color="#333333", pad=20)
    plt.axis("off")
    plt.tight_layout()

    # Guardar i mostrar el graf (alta resolució)
    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="#F8F9FA")
    print(f"Graf generat amb estats: {output_file}")
    plt.show()


def main():
    if len(sys.argv) != 2:
        print(f"Ús: {sys.argv[0]} <input_cnf>")
        sys.exit(1)

    cnf_file = sys.argv[1]
    num_vars, clauses = read_cnf(cnf_file)

    solution = call_solver(cnf_file)

    if solution is None:
        print("No s'ha trobat cap solució. (UNSAT)")
    else:
        print("Solució trobada:", solution)
        draw_graph(num_vars, clauses, solution)


if __name__ == "__main__":
    main()
