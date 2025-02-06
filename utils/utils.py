# utils/utils.py
import networkx as nx
from math import sqrt, atan2, degrees
from typing import Any

def kmh_to_ms(speed_kmh: float) -> float:
    """Convertit la vitesse de km/h en m/s."""
    return speed_kmh / 3.6

def ms_to_kmh(speed_ms: float) -> float:
    """Convertit la vitesse de m/s en km/h."""
    return speed_ms * 3.6

def normalize_attribute(graph: nx.MultiDiGraph, attribute: str) -> None:
    """
    Normalise un attribut dans le graphe en utilisant la normalisation Min-Max.
    """
    try:
        values = [float(graph.nodes[node].get(attribute, 0)) for node in graph.nodes]
        if not values:
            return
        min_value = min(values)
        max_value = max(values)
        for node in graph.nodes:
            value = float(graph.nodes[node].get(attribute, 0))
            normalized_value = (value - min_value) / (max_value - min_value) if (max_value - min_value) else 0.0
            graph.nodes[node][f"normalized_{attribute}"] = normalized_value
    except Exception as e:
        raise RuntimeError(f"Erreur dans normalize_attribute pour '{attribute}': {e}")

def calculate_node_score(graph: nx.MultiDiGraph, weights: dict) -> None:
    """
    Calcule un score pour chaque nœud basé sur des facteurs pondérés.
    """
    try:
        node_scores = {}
        for node in graph.nodes:
            score = 0.0
            for attribute, weight in weights.items():
                value = float(graph.nodes[node].get(attribute, 0))
                score += value * weight
            node_scores[node] = score
        nx.set_node_attributes(graph, node_scores, "node_score")
    except Exception as e:
        raise RuntimeError(f"Erreur dans calculate_node_score: {e}")

def update_node_score(graph: nx.MultiDiGraph, weights: dict) -> None:
    """
    Met à jour le score pour chaque nœud basé sur des pondérations supplémentaires.
    """
    try:
        node_scores = {}
        for node in graph.nodes:
            score = float(graph.nodes[node].get("node_score", 0))
            for attribute, weight in weights.items():
                value = float(graph.nodes[node].get(attribute, 0))
                score += value * weight
            node_scores[node] = score
        nx.set_node_attributes(graph, node_scores, "node_score")
    except Exception as e:
        raise RuntimeError(f"Erreur dans update_node_score: {e}")

def get_top_node(graph: nx.MultiDiGraph, blacklist: list) -> Any:
    """
    Retourne le nœud avec le meilleur score en excluant ceux de la blacklist.
    """
    try:
        node_scores = nx.get_node_attributes(graph, "node_score")
        for node in blacklist:
            if node in node_scores:
                del node_scores[node]
        if not node_scores:
            raise ValueError("Aucun nœud disponible pour la sélection.")
        return max(node_scores, key=node_scores.get)
    except Exception as e:
        raise RuntimeError(f"Erreur dans get_top_node: {e}")

def add_every_node_info(graph: nx.MultiDiGraph, starting_point: tuple, direction: float) -> None:
    """
    Ajoute diverses informations aux nœuds du graphe (distance, angle, etc.).
    """
    try:
        for node in graph.nodes:
            node_data = graph.nodes[node]
            # Distance euclidienne depuis le point de départ
            node_data["distance_from_origin"] = sqrt((starting_point[0] - node_data["y"])**2 + (starting_point[1] - node_data["x"])**2)
            # Angle (en degrés) par rapport au point de départ
            node_data["angle"] = angle(starting_point, (node_data["y"], node_data["x"]))
            # TODO: Ajouter d'autres informations (vitesse moyenne, vitesse max, etc.)
    except Exception as e:
        raise RuntimeError(f"Erreur dans add_every_node_info: {e}")

def angle(pointA: tuple, pointB: tuple) -> float:
    """
    Calcule l'angle (en degrés) entre deux points.
    """
    try:
        delta_y = pointB[0] - pointA[0]
        delta_x = pointB[1] - pointA[1]
        rad = atan2(delta_y, delta_x)
        return degrees(rad)
    except Exception as e:
        raise RuntimeError(f"Erreur dans angle: {e}")

def angle_diff(angleA: float, angleB: float) -> float:
    """
    Calcule la différence d'angle en tenant compte de la circularité.
    """
    try:
        first_diff = abs(angleA - angleB)
        return first_diff if first_diff < 180 else 360 - first_diff
    except Exception as e:
        raise RuntimeError(f"Erreur dans angle_diff: {e}")

def lire_liste_du_fichier(nom_fichier: str) -> list:
    """
    Lit et retourne la liste des lignes d'un fichier.
    """
    try:
        with open(nom_fichier, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        raise RuntimeError(f"Erreur dans lire_liste_du_fichier ('{nom_fichier}'): {e}")
