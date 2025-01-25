import osmnx as ox
import networkx as nx
import heapq
from math import sqrt

# Interface utilisateur pour obtenir l'adresse de départ
def get_starting_point() -> str:
    """
    Retourne les coordonnées GPS d'un point de départ. Ici, c'est un exemple fixe.
    """
    adress = "police auch 32000"  # centre de auch
    return ox.geocode(adress)  # Utilisation de la fonction geocode d'osmnx pour obtenir un point géographique

# Convertir la vitesse de km/h en m/s
def kmh_to_ms(a: float) -> float:
    return a / 3.6  # Conversion de la vitesse de km/h à m/s

# Convertir la vitesse de m/s en km/h
def ms_to_kmh(a: float) -> float:
    return a * 3.6  # Conversion de la vitesse de m/s à km/h

# Appliquer la vitesse aux arêtes du graphe en fonction du type de route
def apply_speed(road_type: str | list[str], speeds: dict[str, int]) -> float:
    """
    Applique la vitesse appropriée à une arête en fonction de son type de route.
    Si road_type est une liste, seule la première valeur est prise en compte.
    """
    if isinstance(road_type, list):
        road_type = road_type[0]  # Si road_type est une liste, on prend le premier type de route
    road_type = road_type.lower() if road_type else "default"  # On met en minuscules pour éviter les erreurs de casse
    return speeds.get(road_type, speeds["default"])  # Retourne la vitesse correspondante au type de route ou "default"

# Récupérer le point de départ dans le graphe de route en utilisant les coordonnées GPS
def get_point_in_graph(coords: tuple[float, float], graph: nx.MultiDiGraph) -> int:
    """
    Retourne le nœud du graphe le plus proche des coordonnées GPS données.
    """
    return ox.nearest_nodes(graph, coords[1], coords[0])  # Utilisation de la fonction nearest_nodes pour trouver le nœud le plus proche

# Vérifie si un point est dans l'isochrone (si le temps est inférieur à celui de l'isochrone)
def is_in_isochrone(time: float, isotime: float) -> int:
    """
    Retourne 1 si le temps est inférieur ou égal à l'isochrone, sinon 0.
    """
    return int(time <= isotime)

# Dijkstra avec une limite de temps sur les trajets
def dijkstra_with_limit(graph: nx.MultiDiGraph, source: int, weight: str, limit: float = float("inf")) -> dict[int, float]:
    """
    Implémentation de l'algorithme de Dijkstra avec une contrainte de temps sur le poids des arêtes.
    
    graph : Le graphe sur lequel effectuer la recherche.
    source : Le nœud de départ.
    weight : Le poids à utiliser pour le calcul des trajets (par exemple "travel_time").
    limit : Le temps limite pour l'isochrone.
    
    Retourne un dictionnaire des chemins les plus courts vers chaque nœud, avec leurs poids respectifs.
    """
    shortest_paths = {source: 0}  # Temps de parcours depuis la source pour chaque nœud
    visited = set()  # Ensemble des nœuds déjà explorés
    priority_queue = [(0, source)]  # Pile de priorité contenant les nœuds à explorer

    while priority_queue:
        current_weight, current_node = heapq.heappop(priority_queue)  # Extraire le nœud avec le plus petit poids

        # Si le temps dépasse la limite, on arrête l'exploration
        if current_weight > limit or current_node in visited:
            continue

        visited.add(current_node)

        # Exploration des voisins du nœud actuel
        test = graph[current_node].items()
        for neighbor, attr in test:
            travel_weight = attr[0][weight]  # Récupérer le poids (temps de parcours) de l'arête
            new_weight = current_weight + travel_weight  # Calculer le nouveau poids total du chemin

            # Si le nouveau poids est plus petit que l'existant, mettre à jour le chemin
            if neighbor not in shortest_paths or new_weight < shortest_paths[neighbor]:
                shortest_paths[neighbor] = new_weight
                heapq.heappush(priority_queue, (new_weight, neighbor))  # Ajouter à la pile de priorité

    return shortest_paths  # Retourne le dictionnaire des chemins les plus courts jusqu'à chaque nœud

# Ajouter les vitesses moyennes, maximales et minimales des nœuds
def add_node_speed(graph: nx.MultiDiGraph) -> None:
    """
    Calcule et ajoute les vitesses moyennes, maximales et minimales pour chaque nœud du graphe
    en fonction des arêtes connectées à ce nœud.
    """
    moyennes_vitesse = {}  # Dictionnaire pour stocker les vitesses moyennes
    max_vitesse = {}       # Dictionnaire pour stocker la vitesse maximale
    min_vitesse = {}       # Dictionnaire pour stocker la vitesse minimale

    # Parcours des nœuds du graphe
    for sommet in graph.nodes():
        vitesses = []  # Liste pour stocker les vitesses des arêtes connectées au sommet

        # Pour chaque voisin du sommet, on parcourt les arêtes
        for voisin in graph[sommet]:
            for arete in graph[sommet][voisin]:
                vitesses.append(graph[sommet][voisin][arete]["speed_kph"])  # On ajoute la vitesse de l'arête

        # Calcul des vitesses moyennes, minimales et maximales
        if vitesses:
            moyennes_vitesse[sommet] = sum(vitesses) / len(vitesses)  # Vitesse moyenne
            max_vitesse[sommet] = max(vitesses)  # Vitesse maximale
            min_vitesse[sommet] = min(vitesses)  # Vitesse minimale
        else:
            moyennes_vitesse[sommet] = 0
            max_vitesse[sommet] = 0
            min_vitesse[sommet] = 0

    # Ajout des vitesses comme attributs des nœuds
    nx.set_node_attributes(graph, moyennes_vitesse, "speed_avg")
    nx.set_node_attributes(graph, max_vitesse, "speed_max")
    nx.set_node_attributes(graph, min_vitesse, "speed_min")


# Ajouter la distance de chaque nœud par rapport à un point de référence
def add_node_distance(graph: nx.MultiDiGraph, point : tuple, label : str) -> None:
    """
    Calcule la distance Euclidienne entre chaque nœud du graphe et un point de référence,
    et ajoute cette distance comme attribut des nœuds.
    """
    processed_nodes = {}  # Dictionnaire pour stocker les distances
    for node in graph:
        # Calcul de la distance Euclidienne (en mètres) entre le point de référence et chaque nœud
        distance = sqrt((point[0] - graph.nodes[node]["y"])**2 + (point[1] - graph.nodes[node]["x"])**2)
        processed_nodes[node] = distance  # Stocke la distance calculée

    # Ajoute les distances comme attributs des nœuds
    nx.set_node_attributes(graph, processed_nodes, label)

def normalize_attribute(graph: nx.MultiDiGraph, attribute: str) -> None:
    """
    Normalise un attribut dans le graphe en utilisant la normalisation Min-Max.
    
    graph : Le graphe contenant les nœuds avec leurs attributs.
    attribute : L'attribut à normaliser (par exemple "speed_avg").
    """
    values = [graph.nodes[node].get(attribute, 0) for node in graph.nodes]
    min_value = min(values)
    max_value = max(values)
    
    for node in graph.nodes:
        value = graph.nodes[node].get(attribute, 0)
        # Normalisation Min-Max
        if max_value - min_value != 0:
            normalized_value = (value - min_value) / (max_value - min_value)
        else:
            normalized_value = 0  # Eviter la division par zéro si toutes les valeurs sont identiques
        graph.nodes[node][f"normalized_{attribute}"] = normalized_value

def calculate_node_score(graph: nx.MultiDiGraph, weights: dict) -> None:
    """
    Calcule un score pour chaque nœud basé sur des facteurs pondérés :
    - weights : dictionnaire des pondérations {attribut: poids}.
    """
    node_scores = {}
    for node in graph.nodes:
        score = 0
        for attribute, weight in weights.items():
            value = graph.nodes[node].get(attribute, 0)
            score += value * weight
        node_scores[node] = score
    nx.set_node_attributes(graph, node_scores, "node_score")

def update_node_score(graph: nx.MultiDiGraph, weights: dict) -> None:
    """
    Modifie le score pour chaque nœud basé sur des facteurs pondérés supplémentaires :
    - weights : dictionnaire des pondérations {attribut: poids}.
    """
    node_scores = {}
    for node in graph.nodes:
        score = graph.nodes[node].get("node_score", 0)
        for attribute, weight in weights.items():
            value = graph.nodes[node].get(attribute, 0)
            score += value * weight
        node_scores[node] = score
    nx.set_node_attributes(graph, node_scores, "node_score")

def get_top_node(graph: nx.MultiDiGraph, blacklist : list) -> list:
    """
    Retourne le nœud avec le meilleur score.
    """
    node_scores = nx.get_node_attributes(graph, "node_score")
    for node in blacklist:
        del node_scores[node]
    return max(node_scores, key=node_scores.get)

