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
    get_top_node,
    create_graph_from_postgreSQL,
    get_angle_fuite
)

DATA_FOLDER: str = "data/"

class Epervier:
    def __init__(self, starting_point: str, direction_fuite: float | str = None) -> None:
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

        # obtention de l'angle de fuite
        try:
            self.angle_fuite = get_angle_fuite(direction_fuite)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'obtention de l'angle de fuite: {e}")
        
    def get_graph_from_isochrones(self, time, delta_time : float = 2*60) -> nx.MultiDiGraph:
        """
        Charge le graphe depuis un fichier osm.pbf à partir de deux isochrones
        Retourne ces deux isochrones
        """
        try:
            isochrone_A : Polygon = get_isochrone(self.starting_coords, time + delta_time)
            isochrone_B : Polygon = get_isochrone(self.starting_coords, time)
            valid_zone = isochrone_A.difference(isochrone_B)

            self.graph = create_graph_from_postgreSQL(self.db_params, valid_zone)

            return mapping(isochrone_A), mapping(isochrone_B)
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe depuis la base de donnees: {e}")

    def __add_graph_infos(self):
        """
        Ajoute et normalise les informations aux nœuds du graphe en parallèle :
        - Nombre d'arêtes adjacentes
        - Vitesse maximale autorisée
        - Distance au point de commission des faits
        - Différence angulaire avec la direction de fuite
        """
        try:
            if not hasattr(self, "graph") or self.graph is None:
                raise ValueError("Le graphe n'a pas encore été généré. Appelez `get_graph_from_isochrones` d'abord.")

            try:
                with open(f"{DATA_FOLDER}/road_speeds.json", "r", encoding="utf-8") as f:
                    ROAD_SPEEDS = json.load(f)
            except Exception as e:
                raise RuntimeError(f"Erreur lors du chargement du JSON: {e}")

            # Création du vecteur de fuite
            angle_rad = math.radians(self.angle_fuite)
            escape_vector = (math.cos(angle_rad), math.sin(angle_rad))

            # Structure pour stocker les résultats et min/max simultanément
            node_data = {}
            min_max_values = {}

            def process_node(node):
                """ Calcule les informations pour un seul nœud et met à jour min/max. """
                edges = list(self.graph.edges(node, data=True))

                # Nombre d’arêtes adjacentes
                num_edges = len(edges)

                # Vitesse maximale autorisée
                maxspeeds = [
                    float(data["maxspeed"]) if "maxspeed" in data and data["maxspeed"].isdigit()
                    else ROAD_SPEEDS.get(data.get("highway", "unclassified"), 30)
                    for _, _, data in edges
                ]
                vitesse_max = max(maxspeeds) if maxspeeds else 30

                # for node in self.graph.nodes():
                #     raise RuntimeError(node, self.graph.nodes[node])  # Vérifie les attributs stockés
                #     break  # Affiche un seul nœud pour éviter un flood

                # Distance au point de commission des faits
                node_location = (self.graph.nodes[node]["pos"][0], self.graph.nodes[node]["pos"][1])
                distance = geodesic(self.starting_coords, node_location).meters

                # Différence angulaire avec la direction de fuite
                node_vector = (self.graph.nodes[node]["pos"][0] - self.starting_coords[0], self.graph.nodes[node]["pos"][1] - self.starting_coords[1])
                node_magnitude = math.sqrt(node_vector[0]**2 + node_vector[1]**2)
                escape_magnitude = math.sqrt(escape_vector[0]**2 + escape_vector[1]**2)

                if node_magnitude > 0 and escape_magnitude > 0:
                    dot_product = (node_vector[0] * escape_vector[0] + node_vector[1] * escape_vector[1])
                    angle_diff = math.acos(dot_product / (node_magnitude * escape_magnitude)) * 180 / math.pi
                else:
                    angle_diff = 0

                # Stockage direct des min/max en parallèle
                values = {
                    "nombre_routes_adjacentes": num_edges,
                    "vitesse_max": vitesse_max,
                    "distance_point_depart": distance,
                    "ecart_direction_fuite": angle_diff
                }

                for key, val in values.items():
                    if key not in min_max_values:
                        min_max_values[key] = [val, val]  # min, max
                    else:
                        min_max_values[key][0] = min(min_max_values[key][0], val)
                        min_max_values[key][1] = max(min_max_values[key][1], val)

                return node, values

            # Exécution parallèle sur tous les nœuds
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(process_node, self.graph.nodes()))

            # Mise à jour des nœuds avec normalisation
            for node, values in results:
                for key, val in values.items():
                    min_val, max_val = min_max_values[key]
                    norm_val = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
                    self.graph.nodes[node][key] = norm_val  # On change par la valeur normalisée

                # Ajout des valeurs brutes
                self.graph.nodes[node].update(values)

        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ajout et de la normalisation des informations au graphe: {e}")

    from concurrent.futures import ThreadPoolExecutor

    def __calculate_node_score(self, strategie: dict[str, float]) -> None:
        """
        Calcule un score pour chaque nœud en parallèle en utilisant des facteurs pondérés.

        :param strategie: Dictionnaire contenant les poids pour chaque facteur.
                        Exemple :
                        {
                            "nombre_routes_adjacentes_norm": 0.3,
                            "vitesse_max_norm": 0.2,
                            "distance_point_depart_norm": -0.4,
                            "ecart_direction_fuite_norm": 0.1
                        }
        """
        try:
            if not hasattr(self, "graph") or self.graph is None:
                raise ValueError("Le graphe n'a pas encore été généré. Appelez `get_graph_from_isochrones` d'abord.")

            def process_node(node):
                """Calcule le score d'un nœud selon la stratégie."""
                score = 0.0
                for key, weight in strategie["weights"].items():
                    if key in self.graph.nodes[node]:
                        score += weight * self.graph.nodes[node][key]
                    else:
                        raise KeyError(f"Clé '{key}' absente du nœud {node}. Vérifiez votre stratégie.")
                return node, score

            # Calcul des scores en parallèle
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(process_node, self.graph.nodes()))

            # Mise à jour des scores dans le graphe
            for node, score in results:
                self.graph.nodes[node]["score"] = score

        except Exception as e:
            raise RuntimeError(f"Erreur lors du calcul des scores des nœuds: {e}")


    def __update_graph_score(self, strategie : dict[str, float], node_id: int):
        pass

    def select_points(self, strategie: Dict[str, float], n_points: int) -> List[Tuple[float, float]]:
        """
        Sélectionne et retourne une liste de points (lat, lon) en fonction de la stratégie et du nombre de points.
        """
        try:
            # On ajoute les informations au graphe
            self.__add_graph_infos()
            
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
