# core/epervier.py
import osmnx as ox  # Pour manipuler des réseaux OSM
import networkx as nx
from typing import Tuple, List, Dict, Any
from shapely.geometry import Polygon
import psycopg2
import json

# Import depuis le dossier utils
from utils.utils import (
    get_isochrone,
    get_top_node,
)

DATA_FOLDER: str = "data/"

class Epervier:
    def __init__(self, starting_point: str, time : float) -> None:
        # Obtention des coordonnées de commission de l'infraction
        try:
            self.starting_coords: Tuple[float, float] = ox.geocode(starting_point)
        except Exception as e:
            raise ValueError(f"Erreur de géocodage pour l'adresse '{starting_point}': {e}")
        
        # obtention des parametres de connection a la base de donnee
        try:
            with open(f"{DATA_FOLDER}/db_params.json") as infile:
                self.db_params: Dict = json.load(infile)
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement des paramètres de la base de donnée: {e}")
        
        # obtention du graphe du réseau routier
        try:
            self.graph: nx.MultiDiGraph = self.get_graph(time)
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe: {e}")
        
        
    def get_graph(self, time, delta_time : float = 20*60, fichier_osm: str = f"{DATA_FOLDER}midi-pyrenees-latest.osm.pbf") -> nx.MultiDiGraph:
        """
        Charge le graphe depuis un fichier osm.pbf à partir de deux isochrones
        """
        try:
            isochrone_A : Polygon = get_isochrone(self.starting_coords, time + delta_time)
            isochrone_B : Polygon = get_isochrone(self.starting_coords, time)
            valid_zone = isochrone_A.difference(isochrone_B)

            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            query = """
                SELECT way, osm_id 
                FROM planet_osm_line
                WHERE ST_Intersects(way, ST_GeomFromText(%s, 4326));
            """

            cursor.execute(query, (valid_zone.wkt,))
            roads = cursor.fetchall()
            conn.close()

            return roads  # Retourne les routes dans A \ B
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe depuis {fichier_osm}: {e}")


    def __add_graph_infos(self, strategie : dict[str, float]):
        """
        Ajoute des informations supplémentaires aux nœuds du graphe.
        f_dir: chemin optionnel pour charger des configurations.
        """
        try:
            # TODO: Implémenter l'ajout d'informations (par exemple, vitesse, nombre d'arêtes, etc.) et de leur normalisation
            pass
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ajout des informations au graphe: {e}")

    def __calculate_node_score(self, graph: nx.MultiDiGraph, strategie: dict[str, float]) -> None:
        """
        Calcule un score pour chaque nœud basé sur des facteurs pondérés.
        """
        pass

    def __update_graph_score(self, strategie : dict[str, float], node_id: int):
        pass

    def select_points(self, strategie: Dict[str, float], n_points: int) -> List[Tuple[float, float]]:
        """
        Sélectionne et retourne une liste de points (lat, lon) en fonction de la stratégie et du nombre de points.
        """
        try:
            # On ajoute les informations au graphe
            self.__add_graph_infos(strategie)

            # Algorithme glouton pour la sélection des nœuds
            top_nodes: List[Any] = []
            self.__calculate_node_score(self.graph, strategie)
            for point in range(n_points - 1):
                top_node = get_top_node(self.graph, top_nodes)
                top_nodes.append(top_node)
                self.__update_graph_score(self.graph, top_node)
            
            top_node = get_top_node(self.graph, top_nodes)
            top_nodes.append(top_node)

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
