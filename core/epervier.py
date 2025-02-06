# core/epervier.py
import osmnx as ox  # Pour manipuler des réseaux OSM
import networkx as nx
import requests
from typing import Tuple, List, Dict, Any, Optional

# Import depuis le dossier utils
from utils.utils import (
    kmh_to_ms,
    normalize_attribute,
    calculate_node_score,
    get_top_node,
    update_node_score
)

DATA_FOLDER: str = "data/"

class Epervier:
    def __init__(self, starting_point: str, time_limit: float) -> None:
        self.map_coef: float = 2.0
        self.time_lim: float = time_limit  # en secondes
        self.speed_lim: float = 180.0  # km/h
        self.map_radius: float = kmh_to_ms(self.speed_lim) * time_limit * self.map_coef
        
        try:
            self.starting_coords: Tuple[float, float] = ox.geocode(starting_point)
        except Exception as e:
            raise ValueError(f"Erreur de géocodage pour l'adresse '{starting_point}': {e}")
        
        try:
            self.graph: nx.MultiDiGraph = self.get_graph(self.starting_coords, self.map_radius)
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe: {e}")
        
        # Définir le chemin de sauvegarde du graphe
        self.map_path: str = f"{DATA_FOLDER}graph_{starting_point.replace(' ', '_')}.graphml"

    def get_graph(self, coords: Tuple[float, float], radius: float) -> nx.MultiDiGraph:
        """
        Charge le graphe depuis le fichier OSM.pbf ou via une requête OSMnx.
        Pour l'instant, on utilise graph_from_point d'OSMnx (à remplacer par une lecture locale).
        """
        fichier_osm: str = f"{DATA_FOLDER}midi-pyrenees-latest.osm.pbf"
        try:
            # TODO : Remplacer par une méthode utilisant pyrosm ou pyosmium pour charger depuis le fichier .osm.pbf
            graph = ox.graph_from_point(coords, dist=radius, network_type='drive')
            return graph
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe depuis {fichier_osm}: {e}")

    def add_graph_infos(self, f_dir: Optional[str] = None) -> None:
        """
        Ajoute des informations supplémentaires aux nœuds du graphe.
        f_dir: chemin optionnel pour charger des configurations.
        """
        try:
            # TODO: Implémenter l'ajout d'informations (par exemple, vitesse, nombre d'arêtes, etc.)
            pass
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ajout des informations au graphe: {e}")

    def exclude_isochrone(self) -> None:
        """
        Exclut l'isochrone de la zone de recherche du graphe.
        """
        lat, lon = self.starting_coords
        url: str = f'http://localhost:8989/isochrone?point={lat},{lon}&time_limit={self.time_lim}&profile=car'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            isochrone = response.json()
            polygon = isochrone.get('polygons', [None])[0]
            if polygon is None:
                raise ValueError("Polygon isochrone non trouvé dans la réponse.")
            # TODO : Soustraire l'isochrone du graphe (par exemple avec Shapely)
        except requests.RequestException as re:
            raise RuntimeError(f"Erreur lors de la requête isochrone: {re}")
        except Exception as e:
            raise RuntimeError(f"Erreur dans exclude_isochrone: {e}")

    def select_points(self, strategie: Dict[str, Any], n_points: int) -> List[Tuple[float, float]]:
        """
        Sélectionne et retourne une liste de points (lat, lon) en fonction de la stratégie et du nombre de points.
        """
        new_weights: Dict[str, float] = {}
        try:
            for attr, weight in strategie.get("weights", {}).items():
                normalize_attribute(self.graph, attr)
                new_weights[f"normalized_{attr}"] = weight

            # Algorithme glouton pour la sélection des nœuds
            top_nodes: List[Any] = []
            calculate_node_score(self.graph, weights=new_weights)
            for point in range(n_points):
                top_node = get_top_node(self.graph, top_nodes)
                top_nodes.append(top_node)
                if point != n_points - 1:
                    # TODO: Ajouter la prise en compte de la distance pour espacer les points
                    normalize_attribute(self.graph, f"distance_{point}")
                    update_node_score(self.graph, {f"normalized_distance_{point}": strategie.get("points_repeltion", 0)})
            points: List[Tuple[float, float]] = [
                (self.graph.nodes[node]["y"], self.graph.nodes[node]["x"]) for node in top_nodes
            ]
            return points
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sélection des points: {e}")

    def save(self) -> None:
        """
        Sauvegarde le graphe dans un fichier GraphML.
        """
        try:
            ox.save_graphml(self.graph, filepath=self.map_path)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sauvegarde du graphe: {e}")

if __name__ == "__main__":
    try:
        e = Epervier("auch", 30 * 60)
        # e.add_graph_infos()
        # e.exclude_isochrone()
        # e.save()
        # strat = {"weights": {
        #             "distance_depart": -0.8,
        #             "speed_avg": 0.2,
        #             "street_count": 0.1,
        #             "speed_max": 0.4
        #         },
        #         "points_repeltion": 0.6}
        # points = e.select_points(strat, 6)
        # print(points)
    except Exception as err:
        print(f"Erreur: {err}")
