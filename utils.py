# import externes
import osmnx as ox  # Bibliothèque pour télécharger et manipuler des graphes de réseaux routiers depuis OpenStreetMap
from osmnx.plot import get_node_colors_by_attr, plot_graph  # Importation des fonctions pour la visualisation des graphes
import networkx as nx  # Bibliothèque pour la manipulation de graphes
import heapq  # Bibliothèque pour la gestion de files de priorité (utilisée pour Dijkstra)
import matplotlib.pyplot as plt  # Bibliothèque pour la visualisation des graphiques
import matplotlib as mpl  # Module pour la gestion des couleurs et des axes dans les graphiques
from math import sqrt  # Fonction mathématique pour calculer la racine carrée, utilisée pour les distances
import json

# import légal des limites de vitesse et du score des routes (si ce n'est pas fait par une IA)
def import_data(dataFile: str) -> tuple[dict[str, int], dict[str, int]]:
    """
    Cette fonction est supposée importer des données sur les limites de vitesse et les scores des routes
    à partir d'un fichier, mais elle est laissée non implémentée pour l'instant.
    """
    pass
    # Retourne des dictionnaires pour les vitesses et scores des différents types de routes.
    return {"motorway": 130,  # Limite de vitesse pour les autoroutes
            "trunk": 100,     # Limite pour les routes principales
            "primary": 80,    # Routes primaires
            "secondary": 60,  # Routes secondaires
            "teriary": 50,    # Routes tertiaires
            "residential": 50,  # Routes résidentielles
            "service": 30,    # Routes de service
            "track": 10,      # Routes de terre
            "default": 50     # Limite par défaut
    }, {
            "motorway": 8,    # Score pour autoroutes
            "trunk": 7,       # Score pour routes principales
            "primary": 6,     # Score pour routes primaires
            "secondary": 5,   # Score pour routes secondaires
            "teriary": 3,     # Score pour routes tertiaires
            "residential": 4, # Score pour routes résidentielles
            "service": 2,     # Score pour routes de service
            "track": 1,       # Score pour routes de terre
            "default": 0      # Score par défaut
    }

# Interface utilisateur pour obtenir l'adresse de départ
def get_starting_point() -> str:
    """
    Retourne les coordonnées GPS d'un point de départ. Ici, c'est un exemple fixe.
    """
    adress = "44.0090723, 1.2146635"
    adress = "police auch 32000"  # centre de auch
    return ox.geocode(adress)  # Utilisation de la fonction geocode d'osmnx pour obtenir un point géographique

# Interface utilisateur pour obtenir le temps limite pour l'isochrone en secondes
def get_time() -> float:
    """
    Cette fonction permet de récupérer le temps limite (en secondes) pour l'isochrone.
    Pour l'instant, elle retourne une valeur fixe de 240 secondes (4 minutes).
    """
    pass
    return 240  # Temps limite par défaut en secondes

# Récupère la vitesse maximale possible sur les routes
def get_max_speed(data: dict[str, int]) -> float:
    """
    Entrée : un dictionnaire de vitesses maximales pour différents types de routes (en km/h)
    Sortie : la vitesse maximale parmi toutes les routes.
    """
    return max(data.values())  # Retourne la vitesse maximale dans le dictionnaire des vitesses des routes

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

# Fonction pour obtenir la direction de fuite (non implémentée)
def get_fleeing_direction() -> None:
    """
    Fonction pour obtenir la direction de fuite. Actuellement non implémentée.
    """
    return

# Affichage du graphe pondéré en fonction d'un attribut
def show_weighted_graph(graph: nx.MultiDiGraph, ax: plt.Axes, weight: str, color_map: str = "terrain") -> None:
    """
    Affiche un graphe avec des couleurs de nœuds représentant un attribut pondéré donné.
    
    graph : Le graphe à afficher.
    ax : L'axe matplotlib sur lequel dessiner le graphe.
    weight : L'attribut à afficher (par exemple "speed_max").
    color_map : Le schéma de couleurs à utiliser pour la visualisation.
    """
    node_weights = [graph.nodes[node].get(weight, 0) for node in graph.nodes]  # Récupérer les poids des nœuds pour l'attribut spécifié

    # Créer une carte de couleurs pour les nœuds selon leur poids
    node_colors = get_node_colors_by_attr(graph, weight, cmap=color_map)

    # Créer une barre de couleurs (color bar)
    norm = mpl.colors.Normalize(vmin=min(node_weights), vmax=max(node_weights))  # Normalisation basée sur les poids des nœuds
    sm = plt.cm.ScalarMappable(cmap=color_map, norm=norm)
    sm.set_array([])  # Nécessaire pour la barre de couleur

    # Ajouter la barre de couleur à l'axe (ax)
    cbar = ax.figure.colorbar(sm, ax=ax, orientation='vertical')
    cbar.set_label(weight)  # L'étiquette de la barre de couleur

    # Tracer le graphe avec les couleurs de nœuds
    plot_graph(graph, ax=ax, node_color=node_colors, show=False, close=False)

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

# Affichage de la répartition des valeurs d'un attribut (par exemple la vitesse)
def show_attribute_repartition(graph: nx.MultiDiGraph, ax: plt.Axes, attribute: str) -> None:
    """
    Affiche la répartition de l'attribut spécifié sur l'axe donné (ax).
    
    graph : Le graphe contenant les nœuds avec leurs attributs.
    ax : L'axe matplotlib sur lequel afficher la répartition.
    attribute : L'attribut dont on veut afficher la répartition (par exemple "speed_max").
    """
    values = sorted([graph.nodes[node][attribute] for node in graph])  # Trie les valeurs de l'attribut pour chaque nœud
    xrange = [i * 100 / len(values) for i in range(len(values))]  # Pourcentage cumulatif des nœuds
    ax.plot(xrange, values, "+")  # Tracer la répartition
    ax.set_title(f"Répartition de l'attribut {attribute}")
    ax.set_xlabel("Pourcentage des nœuds")
    ax.set_ylabel(f"Valeur de {attribute}")

def highlight_nodes(graph: nx.MultiDiGraph, ax: plt.Axes, nodes: list) -> None:
    """
    Met en évidence les nœuds stratégiques sur la carte tout en atténuant les autres éléments.
    """
    # Créer une liste de couleurs pour les nœuds (rouge pour les stratégiques, bleu clair transparent pour les autres)
    node_colors = ["red" if node in nodes else "lightblue" for node in graph.nodes]
    node_size = [30 if node in nodes else 1 for node in graph.nodes] # Taille
    
    # Tracer le graphe avec des propriétés ajustées
    plot_graph(
        graph,
        ax=ax,
        node_color=node_colors,
        node_size=node_size,
        show=False,
        close=False,
    )


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

# DEPRECIATED
def get_top_nodes(graph: nx.MultiDiGraph, top_n) -> list:
    """
    Retourne le nœud avec le meilleur score.
    """
    node_scores = nx.get_node_attributes(graph, "node_score")
    return sorted(node_scores, key=node_scores.get, reverse=True)[:top_n]


def generate_geojson(points:list[tuple[float,float]], output_file: str="points.geojson" ) -> None:
    """
    Génère un fichier GeoJSON à partir d'une liste de points.
    
    :param points: Liste de tuples (x, y) représentant longitude et latitude.
    :param output_file: Nom du fichier GeoJSON à générer.
    """
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for point in points:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point[0], point[1]]  # Longitude, Latitude
            },
            "properties": {}  # Ajouter des propriétés si nécessaire
        }
        geojson["features"].append(feature)
    
    # Écriture dans un fichier GeoJSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)

