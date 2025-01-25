# import externes
import osmnx as ox  # Bibliothèque pour télécharger et manipuler des réseaux de transport depuis OpenStreetMap

# import internes
from utils import *  # Importation des fonctions personnalisées définies dans un module externe 'utils'
from debug import *

def get_points(starting_point, fleeing_direction, time_limit, strategie, n_points):
    # Taille de la carte (multipliée par un coefficient)
    map_coeficient = 2  # Coefficient pour ajuster la taille de la carte (par rapport à l'isochrone)
    # Limite de vitesse maximale sur les routes
    speed_limit = 180  # Limite de vitesse maximale en km/h
    # Calcul du rayon de la carte (en mètres), en fonction de la vitesse, du temps limite et du coefficient de carte
    map_radius = kmh_to_ms(speed_limit) * time_limit * map_coeficient  # Convertir la vitesse en m/s et multiplier par le temps et le coefficient
    # Demander les coordonnées de départ de l'infraction
    starting_coords = ox.geocode(starting_point)

    # Générer un graphe de réseau routier autour du point de départ
    # Le rayon est défini par map_radius et on récupère tous les types de routes ('all')
    graph = ox.graph_from_address(f"{starting_coords[0]},{starting_coords[1]}", dist=map_radius, network_type="all")

    # Ajouter les informations de vitesse et de temps de trajet pour chaque arête dans le graphe
    ox.add_edge_speeds(graph)  # Ajoute les vitesses maximales de chaque route
    ox.add_edge_travel_times(graph)  # Ajoute les temps de trajet sur chaque arête du graphe

    # Identifier le nœud du graphe le plus proche du point de départ
    starting_node = get_point_in_graph(starting_coords, graph)  # Fonction qui trouve le nœud correspondant aux coordonnées

    # Générer un sous-graphe qui représente l'isochrone, la zone accessible dans le temps limite
    # L'algorithme de Dijkstra est utilisé avec une contrainte de temps (weight="travel_time" et limit=time_limit)
    isochrone = dijkstra_with_limit(graph, starting_node, weight="travel_time", limit=time_limit)

    # Ajouter des informations supplémentaires sur les nœuds (nombre de voisins, vitesse, distance par rapport au départ)
    add_node_speed(graph)  # Fonction pour ajouter la vitesse maximale de chaque nœud
    add_node_distance(graph, starting_coords, "distance_depart")  # Fonction pour ajouter la distance de chaque nœud au point de départ

    # Extraire les nœuds du sous-graphe isochrone
    isonodes = isochrone.keys()
    # Créer une copie du sous-graphe contenant uniquement les nœuds de l'isochrone
    subgraph = graph.subgraph(isonodes).copy()

    # Créer un graphe représentant la zone extérieure, en dehors de l'isochrone
    exterieur = graph.copy()  # Crée une copie complète du graphe original
    # Retirer les arêtes du sous-graphe de l'isochrone du graphe extérieur
    exterieur.remove_edges_from(subgraph.edges())
    # Retirer les nœuds du sous-graphe de l'isochrone du graphe extérieur
    exterieur.remove_nodes_from(subgraph.nodes())

    # On normalise les attributs
    new_weights = {}
    for attr in strategie["weights"]:
        normalize_attribute(exterieur, attr)
        new_weights[f"normalized_{attr}"] = strategie["weights"][attr]

    # algorithme glouton (solution suboptimale)
    top_nodes = []
    calculate_node_score(exterieur, weights=new_weights)
    for point in range(n_points):
        top_node = get_top_node(exterieur, top_nodes)
        top_nodes.append(top_node)
        if point != n_points-1:
            add_node_distance(exterieur, (exterieur.nodes[top_node]["y"],exterieur.nodes[top_node]["x"]), f"distance_{point}")
            normalize_attribute(exterieur, f"distance_{point}")
            update_node_score(exterieur, {f"normalized_distance_{point}":strategie["points_repeltion"]})

    points = [(exterieur.nodes[node]["y"],exterieur.nodes[node]["x"]) for node in top_nodes]
    return points

if __name__ == "__main__":
    # Taille de la carte (multipliée par un coefficient)
    map_coeficient = 2  # Coefficient pour ajuster la taille de la carte (par rapport à l'isochrone)
    # Limite de vitesse maximale sur les routes
    speed_limit = 180  # Limite de vitesse maximale en km/h
    # Demander les coordonnées de départ de l'infraction (par défaut : centre de Auch)
    starting_coords = get_starting_point()  # Fonction personnalisée pour obtenir le point de départ
    # Temps limite pour l'isochrone, en secondes
    time_limit = 1 * 60  # 4 minutes par défaut (en secondes), calculé à partir du temps écoulé depuis le début de la fuite
    # Calcul du rayon de la carte (en mètres), en fonction de la vitesse, du temps limite et du coefficient de carte
    map_radius = kmh_to_ms(speed_limit) * time_limit * map_coeficient  # Convertir la vitesse en m/s et multiplier par le temps et le coefficient

    # Générer un graphe de réseau routier autour du point de départ
    # Le rayon est défini par map_radius et on récupère tous les types de routes ('all')
    graph = ox.graph_from_address(f"{starting_coords[0]},{starting_coords[1]}", dist=map_radius, network_type="all")

    # Ajouter les informations de vitesse et de temps de trajet pour chaque arête dans le graphe
    ox.add_edge_speeds(graph)  # Ajoute les vitesses maximales de chaque route
    ox.add_edge_travel_times(graph)  # Ajoute les temps de trajet sur chaque arête du graphe

    # Identifier le nœud du graphe le plus proche du point de départ
    starting_node = get_point_in_graph(starting_coords, graph)  # Fonction qui trouve le nœud correspondant aux coordonnées

    # Ajouter des informations supplémentaires sur les nœuds (nombre de voisins, vitesse, distance par rapport au départ)
    add_node_speed(graph)  # Fonction pour ajouter la vitesse maximale de chaque nœud
    add_node_distance(graph, starting_coords, "distance_depart")  # Fonction pour ajouter la distance de chaque nœud au point de départ


    show_attr_val_on_map(graph, "arete", "service", "driveway")