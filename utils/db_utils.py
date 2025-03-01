# utils/db_utils.py

from functools import wraps
import psycopg2
import logging
from typing import Dict
import json

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
def get_db_attributes(cur: psycopg2.extensions.cursor) -> list:
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'filtered_nodes';")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la récupération des attributs: {e}")
