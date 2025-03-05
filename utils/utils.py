# utils/utils.py
import networkx as nx
from math import atan2, degrees
from typing import Any
import requests
from shapely.geometry import shape, Polygon
from functools import wraps
from time import time
from flask import jsonify
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
    db = {"None" : None, "E" : 90, "NE" : 45, "N" : 0, "NO" : 315, "O" : 270, "SO" : 225, "S" : 180, "SE" : 135}
    if isinstance(direction, str):
        return db[direction]
    if isinstance(direction, int):
        return float(direction)
    raise RuntimeError(f"Il y a une erreur dans get_direction_fuite pour la direction suivante : {direction}")

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

def time_to_seconds(time_str: str) -> int:
    """
    Convertit une chaîne de caractères de temps en secondes.
    """
    logging.debug(f"Converting time string {time_str} to seconds")
    try:
        heures, minutes = map(int, time_str.split(':'))
        return heures * 3600 + minutes * 60
    except Exception as e:
        logging.error(f"Erreur dans time_to_seconds: {e}")
        raise RuntimeError(f"Erreur dans time_to_seconds: {e}")