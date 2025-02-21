# utils/utils.py
import networkx as nx
from math import atan2, degrees
from typing import Any
import requests
from shapely.geometry import shape, Polygon, Point
from functools import wraps
from time import time
from flask import jsonify
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def kmh_to_ms(speed_kmh: float) -> float:
    """Convertit la vitesse de km/h en m/s."""
    logging.debug(f"Converting {speed_kmh} km/h to m/s")
    return speed_kmh / 3.6

def ms_to_kmh(speed_ms: float) -> float:
    """Convertit la vitesse de m/s en km/h."""
    logging.debug(f"Converting {speed_ms} m/s to km/h")
    return speed_ms * 3.6

def angle(pointA: tuple, pointB: tuple) -> float:
    """
    Calcule l'angle (en degrés) entre deux points.
    """
    try:
        logging.debug(f"Calculating angle between points {pointA} and {pointB}")
        delta_y = pointB[0] - pointA[0]
        delta_x = pointB[1] - pointA[1]
        rad = atan2(delta_y, delta_x)
        return degrees(rad)
    except Exception as e:
        logging.error(f"Erreur dans angle: {e}")
        raise RuntimeError(f"Erreur dans angle: {e}")

def angle_diff(angleA: float, angleB: float) -> float:
    """
    Calcule la différence d'angle en tenant compte de la circularité.
    """
    try:
        logging.debug(f"Calculating angle difference between {angleA} and {angleB}")
        first_diff = abs(angleA - angleB)
        return first_diff if first_diff < 180 else 360 - first_diff
    except Exception as e:
        logging.error(f"Erreur dans angle_diff: {e}")
        raise RuntimeError(f"Erreur dans angle_diff: {e}")

def get_angle_fuite(direction : str | int) -> float | None:
    logging.debug(f"Getting angle fuite for direction {direction}")
    db = {"None" : None, "E" : 0, "NE" : 45, "N" : 90, "NO" : 135, "O" : 180, "SO" : 225, "S" : 270, "SE" : 315}
    if isinstance(direction, str):
        return db[direction]
    if isinstance(direction, int):
        return float(direction)
    raise RuntimeError(f"Il y a une erreur dans get_direction_fuite pour la direction suivante : {direction}")

def lire_liste_du_fichier(nom_fichier: str) -> list:
    """
    Lit et retourne la liste des lignes d'un fichier.
    """
    try:
        logging.debug(f"Reading file {nom_fichier}")
        with open(nom_fichier, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        logging.error(f"Erreur dans lire_liste_du_fichier ('{nom_fichier}'): {e}")
        raise RuntimeError(f"Erreur dans lire_liste_du_fichier ('{nom_fichier}'): {e}")

def get_isochrone(center_coords : tuple[float, float], time_lim) -> Polygon:
        """
        Revoit un polygon, isochrone
        """
        lat, lon = center_coords
        url: str = f'http://localhost:8989/isochrone?point={lat},{lon}&time_limit={time_lim}&profile=car'
        try:
            logging.debug(f"Requesting isochrone for center {center_coords} with time limit {time_lim}")
            response = requests.get(url)
            response.raise_for_status()
            isochrone : dict = response.json()
            polygon_feature = isochrone.get('polygons', [None])[0]
            if (polygon_feature is None):
                raise ValueError("Polygon isochrone non trouvé dans la réponse.")
            
            polygon = polygon_feature.get("geometry")
            return shape(polygon)
        
        # exception handling
        except requests.RequestException as re:
            logging.error(f"Erreur lors de la requête isochrone: {re}")
            raise RuntimeError(f"Erreur lors de la requête isochrone: {re}")
        except Exception as e:
            logging.error(f"Erreur dans get_isochrone: {e}")
            raise RuntimeError(f"Erreur dans get_isochrone: {e}")

def create_graph_from_postgreSQL(db_params: dict, valid_zone: Polygon) -> nx.MultiDiGraph:
    """
    Crée un MultiDiGraph à partir des données OSM récupérées depuis PostgreSQL, en optimisant les performances.

    Args:
        db_params (dict): Paramètres de connexion PostgreSQL.
        valid_zone (Polygon): Zone de délimitation du graphe.

    Returns:
        nx.MultiDiGraph: Le graphe construit.
    """
    G = nx.MultiDiGraph()
    
    try:
        logging.debug("Connexion à PostgreSQL...")
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                # Récupération des nœuds valides dans la zone
                logging.debug("Récupération des nœuds valides...")
                cur.execute("""
                    SELECT id, lat * 1e-7 AS lat, lon * 1e-7 AS lon, tags
                    FROM road_ends
                    WHERE ST_Intersects(
                        ST_SetSRID(ST_MakePoint(lon * 1e-7, lat * 1e-7), 4326),
                        ST_GeomFromText(%s, 4326)
                    );
                """, (valid_zone.wkt,))

                nodes = {row[0]: (row[1], row[2], row[3] or {}) for row in cur.fetchall()}
                G.add_nodes_from((nid, {"x": lon, "y": lat, **tags}) for nid, (lat, lon, tags) in nodes.items())

                logging.debug(f"Nombre de nœuds récupérés : {len(nodes)}")

                # Récupération des arêtes en lien avec les nœuds valides
                # logging.debug("Récupération des arêtes...")
                # cur.execute("""
                #     WITH valid_nodes AS (
                #         SELECT id
                #         FROM filtered_nodes
                #         WHERE ST_Intersects(
                #             ST_SetSRID(ST_MakePoint(lon * 1e-7, lat * 1e-7), 4326),
                #             ST_GeomFromText(%s, 4326)
                #         ) LIMIT 10000
                #     )
                #     SELECT w.id, w.nodes, w.tags
                #     FROM filtered_ways w
                #     WHERE w.nodes && ARRAY(SELECT id FROM valid_nodes);
                # """, (valid_zone.wkt,))

                # edges = []
                # for way_id, node_list, way_tags in cur.fetchall():
                #     if not way_tags:
                #         way_tags = {}
                    
                #     filtered_nodes = [nid for nid in node_list if nid in nodes]
                #     edges.extend((filtered_nodes[i], filtered_nodes[i+1], way_id, way_tags) for i in range(len(filtered_nodes) - 1))

                # G.add_edges_from((u, v, {"key": way_id, **tags}) for u, v, way_id, tags in edges)

                # logging.debug(f"Nombre d'arêtes récupérées : {len(edges)}")

    except psycopg2.Error as e:
        logging.error(f"Erreur PostgreSQL : {e}")
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")

    logging.debug(f"Graphe créé avec {G.number_of_nodes()} nœuds et {G.number_of_edges()} arêtes")
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

def normalize_attribute(graph: nx.MultiDiGraph, attribute: str) -> None:
    """
    Normalise un attribut dans le graphe en utilisant la normalisation Min-Max.
    """
    try:
        logging.debug(f"Normalizing attribute {attribute}")
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
        logging.error(f"Erreur dans normalize_attribute pour '{attribute}': {e}")
        raise RuntimeError(f"Erreur dans normalize_attribute pour '{attribute}': {e}")

def get_top_node(graph: nx.MultiDiGraph, blacklist: list) -> Any:
    """
    Retourne le nœud avec le meilleur score en excluant ceux de la blacklist.
    """
    try:
        logging.debug(f"Getting top node excluding blacklist {blacklist}")
        node_scores = nx.get_node_attributes(graph, "node_score")
        for node in blacklist:
            if node in node_scores:
                del node_scores[node]
        if not node_scores:
            raise ValueError("Aucun nœud disponible pour la sélection.")
        return max(node_scores, key=node_scores.get)
    except Exception as e:
        logging.error(f"Erreur dans get_top_node: {e}")
        raise RuntimeError(f"Erreur dans get_top_node: {e}")



