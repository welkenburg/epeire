# web/webapp.py
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from web.web_utils import load_data, load_menu, load_advanced_menu
from utils.utils import measure_time, time_to_seconds
from utils.db_utils import get_db_attributes
from core.epeire import Epeire
from typing import Dict, Union

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Chargement de la clé secrète
try:
    with open("data/secret", "r") as f:
        app.secret_key = f.read().strip()
except Exception as e:
    raise RuntimeError(f"Erreur lors du chargement de la clé secrète: {e}")

modes_file: str = 'data/modes.json'

# Configuration du géocodeur
geolocator = Nominatim(user_agent="e-pervier")

@app.route('/')
def index() -> str:
    """
    Affiche la page d'accueil avec les menus de stratégies de base et avancées.
    """
    try:
        modes = load_data(modes_file)
        basic = load_menu(modes)
        attrs = get_db_attributes(blacklist=['id', 'osmid', 'geometry'])
        attrs += ["distance de l'origine", "angle"]  # TODO Comment faire ça dynamiquement ?
        advanced = load_advanced_menu(attrs)
        return render_template('index.html', strategie_basic=basic, strategie_advanced=advanced)
    except Exception as e:
        return f"Erreur lors du chargement de la page d'accueil: {e}"

@app.route('/chercher', methods=['POST'])
@measure_time
def chercher() -> Dict[str, Union[float, str]]:
    """
    Recherche une adresse et retourne ses coordonnées géographiques.
    """
    try:
        adresse = request.form.get('adresse')
        location = geolocator.geocode(adresse, timeout=10)
        if location:
            return jsonify({'lat': location.latitude, 'lon': location.longitude})
        else:
            return jsonify({'error': 'Adresse non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': f"Erreur lors de la recherche d'adresse: {e}"}), 500

@app.route('/submit', methods=['POST'])
@measure_time
def submit_form() -> Union[str, Dict]:
    """
    Traite le formulaire soumis, calcule des points et retourne le résultat en JSON.
    """
    try:
        adresse = request.form.get('adresse')
        temps_fuite = request.form.get('temps_fuite')
        direction_fuite = request.form.get('direction_fuite')
        strategie = request.form.get('strategie')
        num = int(request.form.get("num", "0"))
        delta_time = request.form.get("dt", "00:10")
        modes = load_data(modes_file)

        time = time_to_seconds(temps_fuite)
        dt = time_to_seconds(delta_time)
        strat = modes.get(strategie)
        if strat is None:
            return {'error': 'Stratégie invalide'}, 400

        epeire = Epeire(adresse, direction_fuite)
        result = epeire.get_graph_from_isochrones(time, dt)
        
        points = epeire.select_points(strat, num)
        
        return {**result, "points": points}
    except Exception as e:
        return {'error': f"Erreur lors du traitement du formulaire: {e}"}

if __name__ == '__main__':
    app.run(debug=True)
