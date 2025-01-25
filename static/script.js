// Initialisation de la carte avec Leaflet
var map = L.map('map').setView([48.8566, 2.3522], 12); // Centré sur Paris
        
// localisation des boutons de zoom
map.zoomControl.setPosition('bottomleft');

// Ajouter une couche de tuiles (map tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Marqueur initial sur Paris
var marker = L.marker([48.8566, 2.3522]).addTo(map);

// Fonction pour changer le menu visible
function toggleMenu(menuToShow) {
    // Cacher tous les menus
    $('.strat-menu').removeClass('active-menu');
    // Afficher le menu sélectionné
    $('#' + menuToShow).addClass('active-menu');
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

$('#search-form').submit(function(event){
    event.preventDefault();
    var adresse = $('#adresse-generale').val();

    // Envoyer la requête au backend Flask pour géocoder l'adresse
    $.post('/chercher', {adresse: adresse}, function(data){
        if (data.lat && data.lon) {
            // Recentrer la carte et déplacer le marqueur
            map.setView([data.lat, data.lon], 12);
            marker.setLatLng([data.lat, data.lon]);
        } else {
            alert(data.error);
        }
    });
});

$('#go-btn').click(function(event) {
    event.preventDefault(); // Empêche le comportement par défaut du bouton
    
    // Récupérer les valeurs des champs du formulaire
    var adresse = $('#adresse').val();
    var temps_fuite = $('#temps_fuite').val();
    var direction_fuite = $('#basic_btn').text(); // Ou récupérer une valeur spécifique selon le contenu de ce bouton
    var strategie = $('#strategie').val();
    var pts_num = $('#pts_num').val();
    
    // Créer un objet avec les données à envoyer
    var formData = {
        adresse: adresse,
        temps_fuite: temps_fuite,
        direction_fuite: direction_fuite,
        strategie: strategie,
        num : pts_num
    };

    // Changer l'apparence du bouton "GO" pour indiquer qu'il est en attente
    $('#go-btn').addClass('waiting'); // Ajouter la classe 'waiting' pour changer le style
    $('#go-btn').text('En attente...');

    // Envoyer la requête POST au serveur Flask
    $.post('/submit', formData, function(response) {
        // Traiter la réponse du serveur
        markerColor = $('#dot_color').val()
        for (let i = 0; i < response.length; i++) {
            L.circleMarker(response[i], {
                color: markerColor, // Couleur de la bordure
                fillColor: markerColor, // Couleur de remplissage
                fillOpacity: 0.6, // Opacité du remplissage
                radius: 5 // Taille du cercle
            }).addTo(map);
        }
        
        // Réinitialiser le bouton à son style initial une fois la réponse reçue
        $('#go-btn').removeClass('waiting'); // Retirer la classe 'waiting' pour restaurer l'apparence initiale
        $('#go-btn').text('GO');
    }).fail(function() {
        // En cas d'erreur, également réinitialiser le bouton
        $('#go-btn').removeClass('waiting');
        $('#go-btn').text('GO');
        alert("Erreur lors de l'envoi de la requête.");
    });
});
