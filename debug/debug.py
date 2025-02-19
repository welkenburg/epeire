import networkx as nx

def pretty_print_graph_infos(graph : nx.MultiDiGraph) -> str:
    """
        Fonction qui revoie un appercu compréhensif du graphe comme le nombre de noeux, d'aretes, le nom de leurs parametres...
    """
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    node_params = set()
    for _, data in graph.nodes(data=True):
        node_params.update(data.keys())
    
    edge_params = set()
    for _, _, data in graph.edges(data=True):
        edge_params.update(data.keys())
    
    info = (
        f"Nombre de noeuds: {num_nodes}\n"
        f"Nombre d'arêtes: {num_edges}\n"
        f"Paramètres des noeuds: {node_params}\n"
        f"Paramètres des arêtes: {edge_params}\n"
    )
    
    return info