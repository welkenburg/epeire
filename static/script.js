// Initialisation de la carte avec Leaflet
var map = L.map('map').setView([48.8566, 2.3522], 12); // Centré sur Paris

var last_response = null;

// Localisation des boutons de zoom
map.zoomControl.setPosition('bottomleft');

// Ajouter une couche de tuiles (map tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Tableau pour stocker les marqueurs
var markers = [];

/**
 * Fonction pour changer le menu visible
 * @param {string} menuToShow - Le menu à afficher (basic-menu ou advanced-menu)
 */
function toggleMenu(menuToShow) {
    // Cacher tous les menus
    $('.strat-menu').removeClass('active-menu');
    // Afficher le menu sélectionné
    $('.' + menuToShow).addClass('active-menu');
}

/**
 * Fonction pour afficher une popup avec un message
 * @param {string} message - Le message à afficher
 * @param {string} backgroundColor - La couleur de fond de la popup
 */
function showResponsePopup(message, backgroundColor) {
    var popup = $('#response-popup');
    popup.css('background-color', backgroundColor);
    popup.text(message);
    popup.fadeIn();

    // Masquer la popup après 10 secondes
    setTimeout(function() {
        popup.fadeOut();
    }, 10000);
}

// Bouton "Basic" (par défaut sélectionné, donc désactivé)
$('#basic-btn').click(function() {
    toggleMenu('basic-menu');
    $('#basic-btn').prop('disabled', true);  // Désactiver le bouton Basic
    $('#advanced-btn').prop('disabled', false);  // Activer le bouton Advanced
});

// Bouton "Advanced"
$('#advanced-btn').click(function() {
    toggleMenu('advanced-menu');
    $('#basic-btn').prop('disabled', false);  // Activer le bouton Basic
    $('#advanced-btn').prop('disabled', true);  // Désactiver le bouton Advanced
});

// Initialiser avec le menu Basic affiché par défaut
toggleMenu('basic-menu');

// Soumission du formulaire de recherche d'adresse
$('#search-form').submit(function(event) {
    event.preventDefault();
    var adresse = $('#adresse-generale').val();

    // Envoyer la requête au backend Flask pour géocoder l'adresse
    $.post('/chercher', { adresse: adresse }, function(data) {
        if (data.lat && data.lon) {
            // Recentrer la carte et déplacer le marqueur
            map.setView([data.lat, data.lon], 12);
        } else {
            alert(data.error);
        }
    });
});

// Soumission du formulaire principal
$('#go-btn').click(function(event) {
    event.preventDefault(); // Empêche le comportement par défaut du bouton

    // Récupérer les valeurs des champs du formulaire
    var adresse = $('#adresse').val();
    var temps_fuite = $('#temps_fuite').val();
    var direction_fuite = $('#direction_fuite').val();
    var strategie = $('#strategie').val();
    var pts_num = $('#pts_num').val();
    var print_iso = $('#isochrone').is(':checked');
    var dt = $('#dt').val();
    var iso_color = $('#iso_color').val();

    // Créer un objet avec les données à envoyer
    var formData = {
        adresse: adresse,
        temps_fuite: temps_fuite,
        direction_fuite: direction_fuite,
        strategie: strategie,
        num: pts_num,
        iso_color: iso_color
    };

    if ($('#dt').is(':visible')) {
        formData.dt = dt;
    }

    // Changer l'apparence du bouton "GO" pour indiquer qu'il est en attente
    $('#go-btn').addClass('waiting');
    $('#go-btn').text('En attente...');

    // Envoyer la requête au backend Flask pour géocoder l'adresse
    $.post('/chercher', { adresse: adresse }, function(data) {
        if (data.lat && data.lon) {
            // Recentrer la carte et déplacer le marqueur
            map.setView([data.lat, data.lon], 10);
            marker = L.marker([data.lat, data.lon]).addTo(map);
            markers.push(marker);
        } else {
            alert(data.error);
        }
    });

    // Envoyer la requête POST au serveur Flask
    $.post('/submit', formData, function(response) {
        // Traiter la réponse du serveur
        console.log(`temps de chargement : ${response.dt}s`);
        // console.log(`Liste des clés de la réponse : ${Object.keys(response)}`);
        // console.log(response);

        last_response = response;
        
        // L.geoJSON(response.isoA, {
        //     style: { color: "#FF0000", weight: 2, fill: false },
        // }).addTo(map);

        // L.geoJSON(response.isoB, {
        //     style: { color: "#0000FF", weight: 2, fill: false },
        // }).addTo(map);

        // L.geoJSON(response.isoC, {
        //     style: { color: "#00FF00", weight: 2, fill: false },
        // }).addTo(map);

        if (response.zpp){
            L.geoJSON(response.zpp, {
                style: { color: iso_color, weight: 2, opacity: 0.1 },
            }).addTo(map);
        }

        if (response.points) {
            points = response.points;
            markerColor = $('#dot_color').val();
            for (let i = 0; i < points.length; i++) {
                marker = L.circleMarker(points[i], {
                    color: markerColor, // Couleur de la bordure
                    fillColor: markerColor, // Couleur de remplissage
                    fillOpacity: 0.6, // Opacité du remplissage
                    radius: 5 // Taille du cercle
                }).addTo(map);
                markers.push(marker);
            }
        }
        if (response.error) {
            console.log(response.error);
            showResponsePopup(`[${response.dt.toFixed(2)}s] Une erreur est survenue, voir les logs`, '#ff0000aa');
        } else {
            showResponsePopup(`[${response.dt.toFixed(2)}s] Requête traitée avec succès`, '#ffffffaa');
        }

        // Réinitialiser le bouton à son style initial une fois la réponse reçue
        $('#go-btn').removeClass('waiting');
        $('#go-btn').text('GO');
    }).fail(function() {
        // En cas d'erreur, également réinitialiser le bouton
        $('#go-btn').removeClass('waiting');
        $('#go-btn').text('GO');
        alert("Erreur lors de l'envoi de la requête.");
    });
});

// Fonction pour réinitialiser la carte
$('#rst-btn').click(function(event) {
    event.preventDefault();
    // Supprimer tous les marqueurs de la carte
    markers.forEach(function(marker) {
        map.removeLayer(marker);
    });
    markers = []; // Réinitialise le tableau de marqueurs

    // Supprimer toutes les couches GeoJSON de la carte
    map.eachLayer(function(layer) {
        if (layer instanceof L.GeoJSON) {
            map.removeLayer(layer);
        }
    });
});

$('#save-btn').click(function(event) {
    event.preventDefault(); // Empêche le comportement par défaut du bouton
    
    if (last_response) {
        var kml = generateKML(last_response.points, last_response.zpp);
        var blob = new Blob([kml], { type: 'application/vnd.google-earth.kml+xml' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'export.kml';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
});

// Fonction pour générer le contenu KML
function generateKML(points, polygon) {
    let kml = `<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Epeire</name>`;
  
    // Ajouter les points
    points.forEach((point, index) => {
        kml += `
        <Placemark>
            <name>Point ${index + 1}</name>
            <Point>
                <coordinates>${point[1]},${point[0]},0</coordinates>
            </Point>
        </Placemark>`;
    });
  
    // Ajouter le polygone
    kml += `
        <Placemark>
            <name>ZPP</name>
            <Polygon>
                <outerBoundaryIs>
                    <LinearRing>
                        <coordinates>`;
  
    polygon.coordinates[0].forEach(point => {
    kml += `${point[0]},${point[1]},0 `;
    });
  
    kml += `
                        </coordinates>
                    </LinearRing>
                </outerBoundaryIs>
                <innerBoundaryIs>
                    <LinearRing>
                        <coordinates>`;
    
    polygon.coordinates[1].forEach(point => {
        kml += `${point[0]},${point[1]},0 `;
    });

    kml += `
                        </coordinates>
                    </LinearRing>
                </innerBoundaryIs>
            </Polygon>
        </Placemark>`;
  
    kml += `
    </Document>
    </kml>`;
  
    return kml;
  }