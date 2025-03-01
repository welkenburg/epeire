# utils/db_utils.py

from functools import wraps
import psycopg2
import logging
from typing import Dict, Tuple
import json
from shapely import wkt

DATA_FOLDER: str = "data/"

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def connect_database(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logging.debug(f"Connexion à PostgreSQL pour la fonction {f.__name__}")
        
        try:
            with open(f"{DATA_FOLDER}/db_params.json") as infile:
                db_params: Dict = json.load(infile)
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement des paramètres de la base de donnée: {e}")
        
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                response = f(cur, *args, **kwargs)

        return response
    return wrapper

@connect_database
def get_db_attributes(cur: psycopg2.extensions.cursor, blacklist : list, table_name : str = 'filtered_nodes') -> list:
    try:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
        return [row[0] for row in cur.fetchall() if row[0] not in blacklist]
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la récupération des attributs: {e}")

@connect_database
def create_table_from_isochrone(cur: psycopg2.extensions.cursor, table_name: str, isochrone: str) -> None:
    """
    Crée une table temporaire à partir d'une isochrone.
    """
    try:
        cur.execute(
            f"""
            DROP TABLE IF EXISTS {table_name};
            CREATE TABLE {table_name} AS
            SELECT * FROM filtered_nodes
            WHERE ST_Intersects(
                geometry,
                ST_Transform(ST_GeomFromText('{isochrone}', 4326), 3857)
            );
            """
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la création de la table à partir de l'isochrone: {e}")

@connect_database
def set_distance_to_start(cur: psycopg2.extensions.cursor, table_name : str, starting_point: Tuple[float, float]) -> None:
    """
    fonction qui ajoute une colonne distance_to_start à la table filtered_nodes et qui remplit cette colonne avec la distance entre chaque point et le point de départ
    """
    try:
        cur.execute(
            f"""
            -- Ajout de la colonne si elle n'existe pas
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='distance_to_start') THEN
                    ALTER TABLE {table_name} ADD COLUMN distance_to_start FLOAT;
                END IF;
            END $$;

            -- Mise à jour de la colonne avec les distances calculées
            UPDATE {table_name}
            SET distance_to_start = ST_Distance(geometry, ST_Transform(ST_SetSRID(ST_MakePoint({starting_point[1]}, {starting_point[0]}), 4326), 3857));
            """
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'ajout de la colonne distance au point de départ: {e}")

@connect_database
def normalize_columns(cur: psycopg2.extensions.cursor, table_name: str, attrs: list) -> None:
    """
    Normalise les colonnes d'une table donnée.
    """
    try:
        for attr in attrs:
            cur.execute(
                f"""
                -- Calculer les valeurs min et max
                WITH stats AS (
                    SELECT
                        MIN({attr}) AS min_val,
                        MAX({attr}) AS max_val
                    FROM {table_name}
                )
                -- Mettre à jour la colonne avec les {attr}s normalisées
                UPDATE {table_name}
                SET {attr} = CASE
                    WHEN (SELECT max_val FROM stats) = (SELECT min_val FROM stats) THEN 0
                    ELSE ({attr} - (SELECT min_val FROM stats)) / ((SELECT max_val FROM stats) - (SELECT min_val FROM stats))
                END;
                """
            )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la normalisation des colonnes: {e}")
    
@connect_database
def set_difference_angle(cur: psycopg2.extensions.cursor, table_name: str, starting_point: Tuple[float, float], angle_fuite: float) -> None:
    """
    Ajoute une colonne difference_angle à la table filtered_nodes et remplit cette colonne avec la différence angulaire entre chaque point et la direction de fuite.
    """
    try:
        if angle_fuite:
            cur.execute(
                f"""
                -- Ajout de la colonne si elle n'existe pas
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='difference_angle') THEN
                        ALTER TABLE {table_name} ADD COLUMN difference_angle FLOAT;
                    END IF;
                END $$;

                -- Mise à jour de la colonne avec les différences angulaires calculées
                UPDATE {table_name}
                SET difference_angle = LEAST(
                    ABS(DEGREES(ST_Azimuth(
                        ST_Transform(ST_SetSRID(ST_MakePoint({starting_point[1]}, {starting_point[0]}), 4326), 3857),
                        geometry
                    )) - {angle_fuite}),
                    360 - ABS(DEGREES(ST_Azimuth(
                        ST_Transform(ST_SetSRID(ST_MakePoint({starting_point[1]}, {starting_point[0]}), 4326), 3857),
                        geometry
                    )) - {angle_fuite})
                );"""
            )
        else:
            cur.execute(
                f"""
                -- Ajout de la colonne si elle n'existe pas
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='difference_angle') THEN
                        ALTER TABLE {table_name} ADD COLUMN difference_angle FLOAT;
                    END IF;
                END $$;

                -- Mise à jour de la colonne avec les différences angulaires calculées
                UPDATE {table_name}
                SET difference_angle = 0;
                """
            )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'ajout de la colonne difference_angle: {e}")
    
@connect_database
def set_score(cur: psycopg2.extensions.cursor, table_name: str, strategie: dict[str, float]) -> list:
    """
    Calcule le score de chaque point en fonction de la stratégie donnée.
    """
    try:
        logging.debug(strategie)
        cur.execute(f"""
            -- Ajout de la colonne si elle n'existe pas
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='score') THEN
                    ALTER TABLE {table_name} ADD COLUMN score FLOAT;
                END IF;
            END $$;
            """
        )

        for attr, weight in strategie["weights"].items():
            cur.execute(
                f"""
                -- Mise à jour de la colonne avec les scores calculés
                UPDATE {table_name}
                SET score = COALESCE(score, 0) + ({attr} * {weight});
                """
            )
        
        cur.execute(
            f"""
            SELECT ST_AsText(ST_Transform(geometry, 4326)) FROM {table_name} ORDER BY score DESC LIMIT 100;
            """
        )

        points = []
        for row in cur.fetchall():
            point = wkt.loads(row[0])
            points.append((point.y, point.x))
        return points
    except Exception as e:
        raise RuntimeError(f"Erreur lors du calcul des scores: {e}")