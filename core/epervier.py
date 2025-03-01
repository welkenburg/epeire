# core/epervier.py
import osmnx as ox  # Pour manipuler des réseaux OSM
import networkx as nx
from typing import Tuple, List, Dict, Any
from shapely.geometry import Polygon, mapping
import json
import math
from geopy.distance import geodesic
from concurrent.futures import ThreadPoolExecutor


# Import depuis le dossier utils
from utils.utils import (
    get_isochrone,
    get_angle_fuite,
)

from utils.db_utils import (
    get_db_attributes,
    set_distance_to_start,
    create_table_from_isochrone,
    normalize_columns,
    set_difference_angle,
    set_score,
)

class Epervier:
    def __init__(self, starting_point: str, direction_fuite: float | str = None) -> None:
        # Obtention des coordonnées de commission de l'infraction
        try:
            self.starting_coords: Tuple[float, float] = ox.geocode(starting_point)
        except Exception as e:
            raise ValueError(f"Erreur de géocodage pour l'adresse '{starting_point}': {e}")
        
        # obtention de l'angle de fuite
        try:
            self.angle_fuite = get_angle_fuite(direction_fuite)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'obtention de l'angle de fuite: {e}")
        
        self.table_name: str = "zone_valide"

    def get_graph_from_isochrones(self, time, delta_time : float = 5*60) -> nx.MultiDiGraph:
        """
        Charge le graphe depuis un fichier osm.pbf à partir de deux isochrones
        Retourne ces deux isochrones
        """
        try:
            isochrone_A : Polygon = get_isochrone(self.starting_coords, time + delta_time)
            isochrone_B : Polygon = get_isochrone(self.starting_coords, time)
            valid_zone = isochrone_A.difference(isochrone_B)

            # création d'une table temporaire qui contient les noeuds dans la zone valide
            create_table_from_isochrone(self.table_name, valid_zone)

            return {
                'isoA': mapping(isochrone_A),
                'isoB': mapping(isochrone_B),
                'valid_zone': mapping(valid_zone),
                # 'graph': {"nodes": nodes, "edges": edges}
            }
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe depuis la base de donnees: {e}")

    def __add_graph_infos(self):
        """
        Ajoute et normalise les informations aux nœuds du graphe :
        - Nombre d'arêtes adjacentes -> statique
        - Vitesse maximale autorisée (min, max, mean) -> statique
        - Nombre de voies sur la route (min, max, mean) -> statique
        - Distance au point de commission des faits -> dynamique
        - Différence angulaire avec la direction de fuite -> dynamique
        """
        # ajouter la distance au point de départ
        set_distance_to_start(self.table_name,self.starting_coords)

        # ajouter la différence angulaire avec la direction de fuite
        set_difference_angle(self.table_name,self.starting_coords, self.angle_fuite)

        # normaliser les colonnes
        attrs = get_db_attributes(blacklist=['id', 'osmid', 'geometry'], table_name=self.table_name)
        normalize_columns(self.table_name, attrs)

    def __update_graph_score(self, strategie : dict[str, float], node_id: int):
        pass

    def select_points(self, strategie: Dict[str, float], n_points: int) -> List[Tuple[float, float]]:
        """
        Sélectionne et retourne une liste de points (lat, lon) en fonction de la stratégie et du nombre de points.
        """
        try:
            # On ajoute les informations au graphe
            self.__add_graph_infos()

            geoms = set_score(self.table_name, strategie)
            
            # on récupère les n_points meilleurs points qu'on traduit en lat, lon
            return geoms[:n_points]
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sélection des points: {e}")
            
            # Algorithme glouton pour la sélection des nœuds
            top_nodes: List[Any] = []
            self.__calculate_node_score(strategie)
            raise RuntimeError(self.graph.nodes)
            top_nodes = sorted(self.graph.nodes(data=True), key=lambda x: x[1]["score"], reverse=True)[:n_points]
            raise RuntimeError(top_nodes)
            # for point in range(n_points - 1):
            #     top_node = get_top_node(self.graph, top_nodes)
            #     top_nodes.append(top_node)
            #     self.__update_graph_score(self.graph, top_node)
            
            # top_node = get_top_node(self.graph, top_nodes)
            # top_nodes.append(top_node)

            # on formate comme il faut
            return [(self.graph.nodes[node]["y"], self.graph.nodes[node]["x"]) for node in top_nodes]
        
        # error handling
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sélection des points: {e}")

if __name__ == "__main__":
    try:
        e = Epervier("auch", 30 * 60)
    except Exception as err:
        print(f"Erreur: {err}")
