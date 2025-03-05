# web/web_utils.py
import json
from typing import Any

def load_data(data_file: str) -> Any:
    """
    Charge et retourne les données JSON depuis un fichier.
    """
    try:
        with open(data_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement du fichier JSON '{data_file}': {e}")

def save_data(data: Any, data_file: str) -> None:
    """
    Sauvegarde les données dans un fichier JSON.
    """
    try:
        with open(data_file, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la sauvegarde dans le fichier JSON '{data_file}': {e}")

def load_menu(modes: list) -> str:
    """
    Génère et retourne un menu HTML à partir d'une liste de modes.
    """
    try:
        options = [f'<option value="{mode}">{mode}</option>' for mode in modes]
        prompt = (
            '<label for="strategie" class="form-label">mode* :</label>'
            '<select name="strategie" id="strategie" class="form-input" required>'
            '<option value="" disabled selected>Sélectionnez une stratégie</option>'
        )
        prompt += "".join(options)
        prompt += "</select>"
        return prompt
    except Exception as e:
        raise RuntimeError(f"Erreur dans load_menu: {e}")

def load_advanced_menu(attrs: list) -> str:
    """
    Génère et retourne un menu HTML avancé à partir d'une liste d'attributs.
    """
    try:
        options = [
            f'<div class="slider-container"><label class="slider-label">{attr}</label><input type="range" class="slider-input slider" min="-100" max="100" value="0"><input type="number" class="slider-value" value="0" min="-100" max="100"></div>'
            for attr in attrs
        ]
        prompt = '<div style="display: flex; flex-direction: column">'
        prompt += "".join(options)
        prompt += "</div>"
        return prompt
    except Exception as e:
        raise RuntimeError(f"Erreur dans load_advanced_menu: {e}")
