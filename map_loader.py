import osmnx as ox
from utils import *

# Télécharger le graphe routier pour le Gers
region_name = "Gers, France"
graph = ox.graph_from_place(region_name, network_type="all", simplify=True)
# Ajouter les informations de vitesse et de temps de trajet pour chaque arête dans le graphe
ox.add_edge_speeds(graph)  # Ajoute les vitesses maximales de chaque route
ox.add_edge_travel_times(graph)  # Ajoute les temps de trajet sur chaque arête du graphe

# Ajouter des informations supplémentaires sur les nœuds (nombre de voisins, vitesse, distance par rapport au départ)
add_node_speed(graph)  # Fonction pour ajouter la vitesse maximale de chaque nœud

# Sauvegarder le graphe dans un fichier
ox.save_graphml(graph, filepath="gers.graphml")
print("Carte sauvegardée dans 'gers.graphml'")