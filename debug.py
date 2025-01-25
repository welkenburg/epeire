import networkx as nx
import matplotlib.pyplot as plt
from utils import *
import osmnx
from osmnx.plot import get_node_colors_by_attr, plot_graph
import matplotlib as mpl
import json

# list attributes
def list_attributs(graph: nx.MultiDiGraph, type : str =None):
    # attributs des sommets
    if type == None or type == "sommet":
        sommet_attributs = set()
        for sommet, data in graph.nodes(data=True):
            for key, value in data.items():
                sommet_attributs.add(key)
        
        print(f'attributs des sommets : {sommet_attributs}')
    
    # attributs des aretes
    if type == None or type == "arete":
        arete_attributs = set()
        for u, v, key, data in graph.edges(data=True, keys=True):
            for key, value in data.items():
                arete_attributs.add(key)
        
        print(f'attributs des aretes : {arete_attributs}')

# list things in this attribute
def list_attr_values(graph: nx.MultiDiGraph, obj: str, attr: str, nb_limit: int = float("inf")):
    """
    Liste les valeurs d'un attribut spécifique d'un objet (sommet ou arête) dans un graphe MultiDiGraph.

    Args:
        graph (nx.MultiDiGraph): Le graphe sur lequel on travaille.
        obj (str): Le type d'objet à examiner ('sommet' ou 'arete').
        attr (str): L'attribut dont on veut lister les valeurs.
        nb_limit (int, optional): Le nombre maximal de valeurs à afficher. Par défaut, il est infini.
    """

    def _hash_values(conteneur, new_entry):
        if type(new_entry) == list:
            for entry in new_entry:
                conteneur.add(entry)
            return conteneur
        conteneur.add(new_entry)
        return conteneur

    values = set()
    if obj == "sommet":
        # Parcourir tous les sommets du graphe
        for sommet, data in graph.nodes(data=True):
            # Si l'attribut est présent dans les données du sommet, ajouter sa valeur
            if attr in data:
                _hash_values(values,data[attr])
            # Arrêter si le nombre de valeurs atteint la limite
            if len(values) >= nb_limit:
                break

    elif obj == "arete":
        # Parcourir toutes les arêtes du graphe
        for u, v, key, data in graph.edges(data=True, keys=True):
            # Si l'attribut est présent dans les données de l'arête, ajouter sa valeur
            if attr in data:
                _hash_values(values,data[attr])
            # Arrêter si le nombre de valeurs atteint la limite
            if len(values) >= nb_limit:
                break

    # Affichage ou renvoi des valeurs
    print(f"Valeurs de l'attribut '{attr}' pour les {obj}s : {values}")

def show_attr_val_on_map(graph: nx.MultiDiGraph, obj: str, attr: str, value):
    """
    Affiche un graphe avec matplotlib, où les objets ayant un attribut spécifique avec une valeur donnée 
    sont colorés en bleu, et le reste du graphe est affiché en gris.

    Args:
        graph (nx.MultiDiGraph): Le graphe à afficher.
        obj (str): Le type d'objet à afficher ('sommet' ou 'arete').
        attr (str): L'attribut à vérifier.
        value: La valeur de l'attribut à rechercher.
    """

    
    # Dictionnaire pour stocker les couleurs des noeuds et des arêtes
    node_color = {}
    edge_color = {}

    # création du visuel
    fig, ax = plt.subplots()

    # Colorer les sommets
    if obj == "sommet":
        for sommet, data in graph.nodes(data=True):
            if attr in data and data[attr] == value:
                node_color[sommet] = 'blue'  # Couleur bleu si la condition est remplie
            else:
                node_color[sommet] = 'gray'  # Sinon gris
        osmnx.plot_graph(graph, ax=ax, node_color=node_color)
    # ou les aretes
    elif obj == "arete":
        for u, v, key, data in graph.edges(data=True, keys=True):
            if attr in data and data[attr] == value:
                edge_color[(u, v, key)] = 'blue'  # Couleur bleu si la condition est remplie
            else:
                edge_color[(u, v, key)] = 'gray'  # Sinon gris
        osmnx.plot_graph(graph, ax=ax, edge_color=edge_color)

    plt.show()

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