#!/usr/bin/python3

import sys
import random
import subprocess
import networkx as nx
import matplotlib.pyplot as plt


def infer_graph_coloring_structure(num_vars, clauses):
    """Infereix (num_nodes, num_colors) a partir de les clàusules ALO del generador rnd-graph-gen.py."""
    positive_clauses = [
        c for c in clauses
        if c and all(lit > 0 for lit in c) and c == list(range(c[0], c[0] + len(c)))
    ]

    if not positive_clauses:
        return None, None

    num_colors = max(set(len(c) for c in positive_clauses), key=lambda k: sum(1 for c in positive_clauses if len(c) == k))
    if num_colors <= 0 or num_vars % num_colors != 0:
        return None, None

    num_nodes = num_vars // num_colors
    return num_nodes, num_colors


def var_to_node_color(var, num_colors):
    """Converteix un identificador de variable en (node, color) amb índex començant a 1."""
    zero_based = var - 1
    node = zero_based // num_colors + 1
    color = zero_based % num_colors
    return node, color


def extract_coloring_solution(solution, num_nodes, num_colors):
    """Extreu la coloració final de cada node a partir d'una assignació SAT."""
    node_color = {}
    for var, is_true in solution.items():
        if not is_true:
            continue
        node, color = var_to_node_color(var, num_colors)
        if 1 <= node <= num_nodes and node not in node_color:
            node_color[node] = color

    # Fallback defensiu en cas d'assignacions parcials
    for node in range(1, num_nodes + 1):
        node_color.setdefault(node, 0)

    return node_color


def extract_graph_edges(clauses, num_colors):
    """Reconstrueix arestes del graf des de clàusules de tipus [-x_u_c, -x_v_c]."""
    edges = set()
    for clause in clauses:
        if len(clause) != 2 or not all(lit < 0 for lit in clause):
            continue

        node1, _ = var_to_node_color(abs(clause[0]), num_colors)
        node2, _ = var_to_node_color(abs(clause[1]), num_colors)
        if node1 != node2:
            edges.add(tuple(sorted((node1, node2))))

    return edges


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
    """Dibuixa el graf utilitzant colors reals del problema de graph coloring."""
    num_nodes, num_colors = infer_graph_coloring_structure(num_vars, clauses)
    if num_nodes is None or num_colors is None:
        print("No s'ha pogut inferir l'estructura de graph coloring del CNF.")
        return

    node_color_assignment = extract_coloring_solution(solution, num_nodes, num_colors)
    edges = extract_graph_edges(clauses, num_colors)

    G = nx.Graph()
    G.add_nodes_from(range(1, num_nodes + 1))
    G.add_edges_from(edges)

    palette = list(plt.cm.get_cmap("tab20", max(3, num_colors)).colors)
    node_colors = [palette[node_color_assignment[node] % len(palette)] for node in G.nodes()]

    # Fallback: connectar seqüencialment si el fitxer no ens ha generat cap aresta
    if G.number_of_edges() == 0:
        for node in range(1, num_nodes):
            G.add_edge(node, node + 1)

    # Configuració de la figura
    plt.figure(figsize=(12, 9), facecolor="#F8F9FA")
    ax = plt.gca()
    ax.set_facecolor("#F8F9FA")

    # Posició dels nodes (utilitzant spring de forma predeterminada, k s'ajusta perquè no estiguin massa junts)
    try:
        # Kamada-Kawai té molt bona estètica per grafs petits però falla si hi ha components desconnectats
        pos = nx.kamada_kawai_layout(G)
    except Exception:
        pos = nx.spring_layout(G, seed=42, k=1.2 / ((num_nodes) ** 0.5 if num_nodes > 0 else 1))

    # Dibuixar les arestes del graf amb transparència
    nx.draw_networkx_edges(
        G, pos,
        edge_color="#B0BEC5",
        width=1.5,
        alpha=0.6
    )

    # Ajust de mides per a millor visualització independent del tamany
    node_size = max(500, min(2000, 30000 // max(1, num_nodes)))
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
    plt.title(
        f"Graph Coloring SAT: {num_nodes} nodes, {num_colors} colors",
        fontsize=18,
        fontweight="bold",
        color="#333333",
        pad=20,
    )
    plt.axis("off")
    plt.tight_layout()

    # Guardar i mostrar el graf (alta resolució)
    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="#F8F9FA")
    print(f"Graf generat amb coloració: {output_file}")
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
