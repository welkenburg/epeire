from flask import Flask, render_template, request, jsonify, session
from geopy.geocoders import Nominatim
from web_utils import *
from epervier import *
from typing import Dict, Union

app = Flask(__name__)  # Création de l'application Flask
app.secret_key = open("data/secret", "r").read()
modes_file = 'data/modes.json'  # Chemin vers le fichier JSON contenant les modes de stratégies

# Route principale pour afficher la page d'accueil
@app.route('/')
def index() -> str:  # La fonction renvoie une chaîne de caractères (HTML)
    """
    Route qui sert la page d'accueil avec un menu de stratégies de base et avancées.
    """
    modes = load_data(modes_file)
    basic = load_menu(modes)
    advanced = "menu avancé"
    return render_template('index.html', strategie_basic=basic, strategie_advanced=advanced)

# Route pour la recherche d'une adresse et conversion en coordonnées géographiques
@app.route('/chercher', methods=['POST'])
def chercher() -> Dict[str, Union[float, str]]:  # Retourne un dictionnaire avec des coordonnées ou un message d'erreur
    """
    Route pour rechercher une adresse et renvoyer ses coordonnées géographiques (latitude et longitude).
    Si l'adresse est trouvée, retourne les coordonnées sous forme de JSON.
    Sinon, retourne un message d'erreur.
    """
    adresse = request.form['adresse']
    geolocator = Nominatim(user_agent="myGeocoder")
    location = geolocator.geocode(adresse)
    
    if location:
        lat, lon = location.latitude, location.longitude
        return jsonify({'lat': lat, 'lon': lon})
    else:
        return jsonify({'error': 'Adresse non trouvée'})

# Route pour soumettre un formulaire avec l'adresse, le temps de fuite, la direction, la stratégie, etc.
@app.route('/submit', methods=['POST'])
def submit_form() -> str:  # La fonction retourne une chaîne de caractères (JSON ou HTML)
    """
    Route pour traiter les données du formulaire de soumission, calculer des points basés sur la fuite et renvoyer les résultats.
    """
    adresse = request.form.get('adresse')
    temps_fuite = request.form.get('temps_fuite')
    direction_fuite = request.form.get('direction_fuite')
    strategie = request.form.get('strategie')
    num = int(request.form.get("num"))
    modes = load_data(modes_file)

    heures, minutes = map(int, temps_fuite.split(':'))
    total_secondes = heures * 3600 + minutes * 60
    strat = modes[strategie]
    
    # Vérifier si c'est la première requête
    if 'premiere_requete' not in session:
        session['premiere_requete'] = True
        e = Epervier(adresse,total_secondes)
        e.add_graph_infos()
        e.exclude_isochrone()
        e.save()
        
    # Traitement pour les requêtes suivantes
    e = Epervier(adresse,total_secondes)
    points = e.select_points(strat, num)
    return points

# Point d'entrée principal de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
