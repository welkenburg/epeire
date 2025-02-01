import json

# Fonction pour charger les données depuis le fichier JSON
def load_data(data_file):
    with open(data_file, 'r') as file:
        return json.load(file)

# Fonction pour enregistrer les données dans le fichier JSON
def save_data(data, data_file):
    with open(data_file, 'w') as file:
        json.dump(data, file, indent=4)


def load_menu(modes):
    lis = [f'<option value="{mode}">{mode}</option>' for mode in modes]
    prompt = """
        <label class="form-label">mode* :</label>
        <select name="strategie" id="strategie" class="form-input" required>
            <option value="" disabled selected>Sélectionnez une stratégie</option>"
        """
    for l in lis:
        prompt += l
    prompt += "</select>"
    return prompt

def load_advanced_menu(attrs):
    lis = [f'<div class="attr-slide"><input type="checkbox"><label>{attr}</label><input type="range"><label>0</label></div>' for attr in attrs]
    prompt = """
        <div style="display : flex; flex-direction : column">
    """
    for l in lis:
        prompt += l
    prompt += "</div>"
    return prompt