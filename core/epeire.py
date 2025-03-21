# core/Epeire.py
import osmnx as ox
from typing import Tuple, List, Dict, Any
from shapely.geometry import Polygon, mapping


# Import depuis le dossier utils
from utils.utils import (
    get_isochrone,
    get_angle_fuite,
)

from utils.db_utils import (
    get_db_attributes,
    set_distance_to_start,
    create_table_from_isochrone,
    normalize_column,
    set_difference_angle,
    set_score,
    update_score_from_points_repeltion,
    set_distance_to_point,
    get_top_point,
    apply_sigmoid,
    set_sigmoid
)

class Epeire:
    def __init__(self, starting_point: str, direction_fuite: float | str = None) -> None:
        """
        Initialise la classe Epeire avec un point de départ et une direction de fuite.
        """
        # Obtention des coordonnées de commission de l'infraction
        try:
            self.starting_coords: Tuple[float, float] = ox.geocode(starting_point)
        except Exception as e:
            raise ValueError(f"Erreur de géocodage pour l'adresse '{starting_point}': {e}")
        
        # Obtention de l'angle de fuite
        try:
            self.angle_fuite = get_angle_fuite(direction_fuite)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'obtention de l'angle de fuite: {e}")
        
        self.table_name: str = "zone_valide"
        set_sigmoid()

    def get_graph_from_isochrones(self, time: float, delta_time: float = 30*60) -> Dict[str, Any]:
        """
        Charge le graphe depuis un fichier osm.pbf à partir de deux isochrones.
        Retourne ces deux isochrones et la zone valide.
        """
        try:
            isochrone_A: Polygon = get_isochrone(self.starting_coords, time + delta_time + 10*60) # fenetre de 10min
            isochrone_B: Polygon = get_isochrone(self.starting_coords, time + delta_time)
            isochrone_C: Polygon = get_isochrone(self.starting_coords, time)
            valid_zone = isochrone_A.difference(isochrone_B)
            zpp = isochrone_B.difference(isochrone_C)

            # Création d'une table temporaire qui contient les noeuds dans la zone valide
            create_table_from_isochrone(self.table_name, valid_zone)

            return {
                'isoA': mapping(isochrone_A),
                'isoB': mapping(isochrone_B),
                'isoC' : mapping(isochrone_C),
                'valid_zone': mapping(valid_zone),
                'zpp': mapping(zpp)
            }
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement du graphe depuis la base de données: {e}")

    def __add_graph_infos(self, strategie) -> None:
        """
        Ajoute et normalise les informations aux nœuds du graphe :
        - Nombre d'arêtes adjacentes -> statique
        - Vitesse maximale autorisée (min, max, mean) -> statique
        - Nombre de voies sur la route (min, max, mean) -> statique
        - Distance au point de commission des faits -> dynamique
        - Différence angulaire avec la direction de fuite -> dynamique
        """
        # Ajouter la distance au point de départ
        set_distance_to_start(self.table_name, self.starting_coords)

        # Ajouter la différence angulaire avec la direction de fuite
        set_difference_angle(self.table_name, self.starting_coords, self.angle_fuite)

        # Normaliser les colonnes
        attrs = get_db_attributes(blacklist=['id', 'osmid', 'geometry'], table_name=self.table_name)
        for attr in attrs:
            normalize_column(self.table_name, attr)

        # appliquer la sigmoid à distance_to_start et difference_angle:
        apply_sigmoid(self.table_name, 'distance_to_start', scale = 1)
        apply_sigmoid(self.table_name, 'difference_angle', offset=0.5, scale=strategie['direction_alpha'])

    def select_points(self, strategie: Dict[str, float], n_points: int) -> List[Tuple[float, float]]:
        """
        Sélectionne et retourne une liste de points (lat, lon) en fonction de la stratégie et du nombre de points.
        """
        try:
            # Ajouter les informations au graphe
            self.__add_graph_infos(strategie)

            points = []
            # Récupérer les n_points meilleurs points
            set_score(self.table_name, strategie)
            first_point = get_top_point(self.table_name)
            points.append(first_point)

            # Récupérer les n_points - 1 autres points
            for i in range(1, n_points):
                set_distance_to_point(self.table_name, points[-1], f"distance_to_point_{i}")
                normalize_column(self.table_name, f"distance_to_point_{i}")
                apply_sigmoid(self.table_name, f'distance_to_point_{i}', scale=strategie['points_repeltion_alpha'])
                update_score_from_points_repeltion(self.table_name, strategie, f"distance_to_point_{i}")
                point = get_top_point(self.table_name)
                points.append(point)
            
            return points
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la sélection des points: {e}")

if __name__ == "__main__":
    try:
        e = Epeire("auch", 30 * 60)
    except Exception as err:
        print(f"Erreur: {err}")
