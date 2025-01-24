# import externes
import osmnx as ox  # Bibliothèque pour télécharger et manipuler des réseaux de transport depuis OpenStreetMap
import matplotlib.pyplot as plt  # Bibliothèque pour la création de graphiques

# import internes
from utils import *  # Importation des fonctions personnalisées définies dans un module externe 'utils'
from debug import *

# Taille de la carte (multipliée par un coefficient)
map_coeficient = 2  # Coefficient pour ajuster la taille de la carte (par rapport à l'isochrone)
# Limite de vitesse maximale sur les routes
speed_limit = 180  # Limite de vitesse maximale en km/h
# Demander les coordonnées de départ de l'infraction (par défaut : centre de Auch)
starting_coords = get_starting_point()  # Fonction personnalisée pour obtenir le point de départ
# Direction de fuite, non encore implémentée
direction_fuite = get_fleeing_direction()  # Fonction personnalisée pour obtenir la direction de fuite
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
normalize_attribute(exterieur, "distance_depart")
# normalize_attribute(exterieur, "speed_avg")
normalize_attribute(exterieur, "street_count")
normalize_attribute(exterieur, "speed_max")

print("hit")
show_attr_val_on_map(exterieur, "arete", "service", "driveway")

exit()

# # Calcul des points
# n_points = 6
# weights = {
#     "normalized_distance_depart": -0.5,  # Plus près du point de départ = mieux
#     "normalized_speed_avg": 0.3,         # Routes plus rapides = mieux
#     "normalized_street_count": 0.2       # Plus d'intersections = mieux
# }
# calculate_node_score(exterieur, weights)
# top_nodes = get_top_nodes(exterieur, top_n=1)


# Calcul des points
n_points = 6    # nombre de points d'intéret générés
weights = {     # Poids pour attribuer un score a chaque sommet 
    "normalized_distance_depart": -0.5,  # Plus près du point de départ = mieux
    "normalized_speed_avg": 0.2,         # Routes plus rapides = mieux
    "normalized_street_count": 0.1,      # Plus d'intersections = mieux
    "normalized_speed_max" : 0.4         # Routes plus rapides = mieux
}
points_repeltion = 0.2 # plus éloigné des autres = mieux

# algorithme glouton (solution suboptimale)
top_nodes = []
calculate_node_score(exterieur, weights)
for point in range(n_points):
    top_node = get_top_node(exterieur, top_nodes)
    top_nodes.append(top_node)
    if point != n_points-1:
        add_node_distance(exterieur, (exterieur.nodes[top_node]["y"],exterieur.nodes[top_node]["x"]), f"distance_{point}")
        normalize_attribute(exterieur, f"distance_{point}")
        update_node_score(exterieur, {f"distance_{point}":points_repeltion})

print(top_nodes)
points = [(exterieur.nodes[node]["x"],exterieur.nodes[node]["y"]) for node in top_nodes]
# generate_geojson(points)
fig, ax = plt.subplots()
highlight_nodes(graph, ax, top_nodes)
plt.show()
exit()

# # Debuggage
# points = [(exterieur.nodes[node]["x"],exterieur.nodes[node]["y"]) for node in top_nodes]
# # generate_geojson(points)
# # exit()
# fig, ax = plt.subplots(2,2)
# show_weighted_graph(graph, ax[0][0], "distance_depart")
# show_weighted_graph(graph, ax[0][1], "street_count")
# show_weighted_graph(graph, ax[1][0], "speed_avg")
# highlight_nodes(graph, ax[1][1], top_nodes)

# # Afficher la figure avec tous les graphes et répartitions
# plt.show()

# # TODO : Implémenter une fonction d'optimisation pour le calcul des itinéraires ou autres