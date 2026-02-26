import subprocess
import sys
import networkx as nx
import matplotlib.pyplot as plt
import random


def run_solver(graph_file):
    """Executa prova.py amb el fitxer de graf generat i retorna la solució."""
    result = subprocess.run([sys.executable, "prova.py", graph_file], capture_output=True, text=True)
    output = result.stdout.split("\n")
    solution = {}

    for line in output:
        if line.startswith("v "):
            values = line.split()[1:-1]  # Eliminem la "v" inicial i el "0" final
            for val in values:
                var = int(val)
                node = (abs(var) - 1) // num_colors
                color = (abs(var) - 1) % num_colors
                if var > 0:
                    solution[node] = color

    return solution


def generate_graph(num_nodes, edge_prob, num_colors):
    """Genera un graf aleatori i l'escriu en un fitxer."""
    graph_file = "graph.cnf"
    subprocess.run([sys.executable, "graph_generator.py", str(num_nodes), str(edge_prob), str(num_colors)],
                   stdout=open(graph_file, "w"))
    return graph_file


def draw_graph(num_nodes, edge_prob, solution):
    """Dibuixa el graf amb els colors obtinguts de la solució."""
    G = nx.Graph()

    # Creació de nodes
    for i in range(num_nodes):
        G.add_node(i)

    # Creació d'arestes
    random.seed(42)  # Per reproduïbilitat
    for i in range(num_nodes - 1):
        for j in range(i + 1, num_nodes):
            if random.random() < edge_prob:
                G.add_edge(i, j)

    # Dibuix del graf
    pos = nx.spring_layout(G)
    colors = [solution.get(node, 0) for node in G.nodes()]
    cmap = plt.cm.get_cmap("tab10", num_colors)

    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, node_color=[cmap(c) for c in colors], with_labels=True, node_size=500, edge_color='gray')
    plt.show()


if __name__ == "__main__":
    # Paràmetres
    num_nodes = 10  # Nombre de nodes
    edge_prob = 0.3  # Probabilitat de connexió entre nodes
    num_colors = 3  # Nombre de colors

    # Generar graf i obtenir solució
    graph_file = generate_graph(num_nodes, edge_prob, num_colors)
    solution = run_solver(graph_file)

    # Dibuixar graf amb colors de la solució
    draw_graph(num_nodes, edge_prob, solution)
