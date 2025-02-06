# web/webapp.py
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from web.web_utils import load_data, load_menu, load_advanced_menu
from utils.utils import lire_liste_du_fichier
from core.epervier import Epervier
from typing import Dict, Union

app = Flask(__name__)

# Chargement de la clé secrète
try:
    with open("data/secret", "r") as f:
        app.secret_key = f.read().strip()
except Exception as e:
    raise RuntimeError(f"Erreur lors du chargement de la clé secrète: {e}")

modes_file: str = 'data/modes.json'

@app.route('/')
def index() -> str:
    """
    Affiche la page d'accueil avec les menus de stratégies de base et avancées.
    """
    try:
        modes = load_data(modes_file)
        basic = load_menu(modes)
        attrs = lire_liste_du_fichier("data/attributes")
        advanced = load_advanced_menu(attrs)
        return render_template('index.html', strategie_basic=basic, strategie_advanced=advanced)
    except Exception as e:
        return f"Erreur lors du chargement de la page d'accueil: {e}"

@app.route('/chercher', methods=['POST'])
def chercher() -> Dict[str, Union[float, str]]:
    """
    Recherche une adresse et retourne ses coordonnées géographiques.
    """
    try:
        adresse = request.form['adresse']
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.geocode(adresse, timeout=10)
        if location:
            lat, lon = location.latitude, location.longitude
            return jsonify({'lat': lat, 'lon': lon})
        else:
            return jsonify({'error': 'Adresse non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': f"Erreur lors de la recherche d'adresse: {e}"}), 500

@app.route('/submit', methods=['POST'])
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
        modes = load_data(modes_file)
        
        # Conversion du temps de fuite
        heures, minutes = map(int, temps_fuite.split(':'))
        total_secondes = heures * 3600 + minutes * 60
        strat = modes.get(strategie)
        if strat is None:
            return jsonify({'error': 'Stratégie invalide'}), 400

        e = Epervier(adresse, total_secondes)
        points = e.select_points(strat, num)
        return jsonify({'points': points})
    except Exception as e:
        return jsonify({'error': f"Erreur lors du traitement du formulaire: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
