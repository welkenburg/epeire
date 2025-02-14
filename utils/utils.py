# utils/utils.py
import networkx as nx
from math import atan2, degrees
from typing import Any
import requests
from shapely.geometry import shape, Polygon, LineString
from shapely.wkt import loads
from functools import wraps
from time import time
from flask import jsonify

def kmh_to_ms(speed_kmh: float) -> float:
    """Convertit la vitesse de km/h en m/s."""
    return speed_kmh / 3.6

def ms_to_kmh(speed_ms: float) -> float:
    """Convertit la vitesse de m/s en km/h."""
    return speed_ms * 3.6

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

def get_angle_fuite(direction : str | int) -> float:
    db = {"None" : None, "E" : 0, "NE" : 45, "N" : 90, "NO" : 135, "O" : 180, "SO" : 225, "S" : 270, "SE" : 315}
    if isinstance(direction, str):
        return float(db[direction])
    if isinstance(direction, int):
        return float(direction)
    raise RuntimeError(f"Il y a une erreur dans get_direction_fuite pour la direction suivante : {direction}")

def lire_liste_du_fichier(nom_fichier: str) -> list:
    """
    Lit et retourne la liste des lignes d'un fichier.
    """
    try:
        with open(nom_fichier, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        raise RuntimeError(f"Erreur dans lire_liste_du_fichier ('{nom_fichier}'): {e}")

def get_isochrone(center_coords : tuple[float, float], time_lim) -> Polygon:
        """
        Revoit un polygon, isochrone
        """
        lat, lon = center_coords
        url: str = f'http://localhost:8989/isochrone?point={lat},{lon}&time_limit={time_lim}&profile=car'
        try:
            response = requests.get(url)
            response.raise_for_status()
            isochrone : dict = response.json()
            polygon_feature = isochrone.get('polygons', [None])[0]
            if polygon_feature is None:
                raise ValueError("Polygon isochrone non trouvé dans la réponse.")
            
            polygon = polygon_feature.get("geometry")
            return shape(polygon)
        
        # exception handling
        except requests.RequestException as re:
            raise RuntimeError(f"Erreur lors de la requête isochrone: {re}")
        except Exception as e:
            raise RuntimeError(f"Erreur dans get_isochrone: {e}")

def create_graph_from_osm_data(roads):
    """
    Crée un MultiDiGraph à partir des données osm récupérées avec osm_id et la géométrie de chaque route.

    Args:
        roads (list of tuple): Liste de tuples contenant le WKT de la route et son osm_id.

    Returns:
        nx.MultiDiGraph: Le graphe construit avec les sommets et arêtes.
    """
    G = nx.MultiDiGraph()

    for way_wkt, osm_id in roads:
        way: LineString = loads(way_wkt)  # Convertir WKT en objet LineString

        coords = list(way.coords)  # Liste des points (lon, lat)
        raise RuntimeError(coords)
        if len(coords) < 2:
            continue  # Éviter les géométries trop courtes

        for i in range(len(coords) - 1):
            u = coords[i]
            v = coords[i + 1]
            length = way.length  # Longueur de la ligne

            # Ajouter les sommets
            G.add_node(u, pos=u)
            G.add_node(v, pos=v)

            # Ajouter l'arête avec des attributs (osm_id, longueur, etc.)
            G.add_edge(u, v, key=osm_id, length=length, geometry=way)

    return G

def measure_time(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time()
        response = f(*args, **kwargs)
        dt = time() - start_time

        # Si la réponse est un objet Flask (jsonify), ajoute dt
        if isinstance(response, tuple):  # Si la fonction retourne (json, status)
            response_dict, status_code = response
            response_dict['dt'] = dt
            return jsonify(response_dict), status_code

        elif isinstance(response, dict):  # Si la fonction retourne directement un dict
            response['dt'] = dt
            return jsonify(response)

        return response  # Cas où ce n'est pas un JSON
    return wrapper


# TODO
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


# TODO
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
    


