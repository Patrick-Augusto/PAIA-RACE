#!/usr/bin/python3

import sys
import json
import networkx as nx
import matplotlib.pyplot as plt
import subprocess

def read_cnf(file_path):
    """ Llegeix un fitxer CNF i retorna les clàusules i el nombre de variables """
    clauses = []
    num_vars = 0
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            elif line.startswith('p'):
                _, _, num_vars, _ = line.split()
                num_vars = int(num_vars)
            else:
                clause = list(map(int, line.split()[:-1]))  # Elimina el 0 final
                if clause:
                    clauses.append(clause)
    return int(num_vars), clauses

def call_solver(cnf_file):
    """ Executa solver.py i retorna la seva sortida processada """
    try:
        # Usamos sys.executable para asegurar que usamos el mismo python
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

def draw_colored_graph(num_nodes, num_colors, clauses, solution, output_file="graph.png"):
    """ Dibuixa el graf real amb els colors de la solució """
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))

    # Detectar arestes de les clàusules de graph coloring
    # Les clàusules d'arestes tenen la forma: [-v1, -v2] on v1 i v2 són el mateix color per a nodes diferents
    # v = n * K + c + 1
    for clause in clauses:
        if len(clause) == 2 and clause[0] < 0 and clause[1] < 0:
            v1 = abs(clause[0])
            v2 = abs(clause[1])
            n1 = (v1 - 1) // num_colors
            c1 = (v1 - 1) % num_colors
            n2 = (v2 - 1) // num_colors
            c2 = (v2 - 1) % num_colors
            
            if c1 == c2 and n1 != n2:
                G.add_edge(n1, n2)

    # Determinar el color de cada node segons la solució
    # Palette de colors
    color_palette = [
        "#4CAF50", "#2196F3", "#F44336", "#FFEB3B", "#9C27B0", 
        "#FF9800", "#00BCD4", "#E91E63", "#795548", "#607D8B"
    ]
    
    node_colors = ["#CCCCCC"] * num_nodes
    for n in range(num_nodes):
        for c in range(num_colors):
            v = n * num_colors + c + 1
            if solution.get(v, False):
                node_colors[n] = color_palette[c % len(color_palette)]
                break

    # Configuració de la figura
    plt.figure(figsize=(10, 8), facecolor="#F8F9FA")
    ax = plt.gca()
    ax.set_facecolor("#F8F9FA")

    # Posicionament
    pos = nx.spring_layout(G, seed=42)
    
    # Dibuixar arestes
    nx.draw_networkx_edges(G, pos, edge_color="#B0BEC5", width=1.5, alpha=0.7)
    
    # Dibuixar nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, 
                           edgecolors="white", linewidths=2)
    
    # Dibuixar etiquetes
    nx.draw_networkx_labels(G, pos, font_color="white", font_weight="bold")

    plt.title(f"Solució de Coloració de Graf ({num_nodes} nodes, {num_colors} colors)", 
              fontsize=16, fontweight="bold", pad=20)
    plt.axis("off")
    plt.tight_layout()

    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Graf de coloració generat: {output_file}")
    plt.show()

def main():
    if len(sys.argv) < 4:
        print(f"Ús: {sys.argv[0]} <input_cnf> <num_nodes> <num_colors>")
        sys.exit(1)

    cnf_file = sys.argv[1]
    num_nodes = int(sys.argv[2])
    num_colors = int(sys.argv[3])

    num_vars, clauses = read_cnf(cnf_file)
    solution = call_solver(cnf_file)

    if solution is None:
        print("No s'ha trobat cap solució. (UNSAT)")
    else:
        print("Solució trobada!")
        draw_colored_graph(num_nodes, num_colors, clauses, solution)

if __name__ == "__main__":
    main()
