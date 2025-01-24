import networkx as nx
import matplotlib.pyplot as plt
import threading
import osmnx

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

# other
def _list_attributs(graph: nx.MultiDiGraph, limit=20):
    # imports
    from pprint import pprint

    # Créer des dictionnaires pour les attributs uniques des sommets et des arêtes
    sommet_attributs = {}
    arete_attributs = {}
    
    # Fonction pour convertir une valeur en un type hashable si nécessaire
    def make_hashable(value):
        if isinstance(value, list):
            return tuple(value)  # Convertir les listes en tuples
        return value
    
    # Récupérer les attributs des sommets
    for sommet, data in graph.nodes(data=True):
        for key, value in data.items():
            value = make_hashable(value)  # Convertir la valeur si nécessaire
            if key not in sommet_attributs:
                sommet_attributs[key] = set()  # Initialiser un set pour cet attribut
            sommet_attributs[key].add(value)  # Ajouter la valeur (sans doublons)
    
    # Récupérer les attributs des arêtes
    for u, v, key, data in graph.edges(data=True, keys=True):
        for key, value in data.items():
            value = make_hashable(value)  # Convertir la valeur si nécessaire
            if key not in arete_attributs:
                arete_attributs[key] = set()  # Initialiser un set pour cet attribut
            arete_attributs[key].add(value)  # Ajouter la valeur (sans doublons)
    
    # Limiter les valeurs à 5 premières (si nécessaire)
    def limit_values(attribute_dict):
        for key, values in attribute_dict.items():
            attribute_dict[key] = list(values)[:limit]  # Prendre les 5 premières valeurs (si disponibles)
    
    # Limiter les valeurs dans les dictionnaires d'attributs
    limit_values(sommet_attributs)
    limit_values(arete_attributs)
    
    # Afficher les résultats
    print("Attributs des sommets :")
    pprint(sommet_attributs)
    print("Attributs des arêtes :")
    pprint(arete_attributs)
    
    # Afficher les résultats
    print("Attributs des sommets :")
    pprint(sommet_attributs)
    print("Attributs des arêtes :")
    pprint(arete_attributs)