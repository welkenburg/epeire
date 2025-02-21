// Initialisation de la carte avec Leaflet
var map = L.map('map').setView([48.8566, 2.3522], 12); // Centré sur Paris
        
// localisation des boutons de zoom
map.zoomControl.setPosition('bottomleft');

// Ajouter une couche de tuiles (map tiles)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Tableau pour stocker les marqueurs
var markers = [];

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
    var direction_fuite = $('#direction_fuite').val(); // Ou récupérer une valeur spécifique selon le contenu de ce bouton
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

    // Envoyer la requête au backend Flask pour géocoder l'adresse
    $.post('/chercher', {adresse: adresse}, function(data){
        if (data.lat && data.lon) {
            // Recentrer la carte et déplacer le marqueur
            map.setView([data.lat, data.lon], 12);
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
        console.log(response.graph);
        L.geoJSON(response.valid_zone, {
            style: { color: "blue", weight: 2, opacity: 0.7 },
        }).addTo(map);

        // Ajout des x premiers nœuds (cercles verts translucides)
        response.graph.nodes.forEach(node => {
            L.circleMarker([node.lat, node.lon], {
            radius: 4,
            color: "green",
            fillColor: "green",
            fillOpacity: 0.5
            }).addTo(map);
        });

        // Ajout des arêtes (lignes vertes)
        response.graph.edges.slice(0, 10000).forEach(edge => {
            let source = response.graph.nodes.find(n => n.id === edge.source);
            let target = response.graph.nodes.find(n => n.id === edge.target);

            if (source && target) {
                L.polyline([[source.lat, source.lon], [target.lat, target.lon]], {
                    color: "green",
                    weight: 2
                }).addTo(map);
            }
        });

        console.log(Object.keys(response));
        if (response.points) {
            points = response.points
            markerColor = $('#dot_color').val()
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


// Fonction pour réinitialiser la carte
$('#rst-btn').click(function(event) {
    event.preventDefault();
    // Supprimer tous les marqueurs de la carte
    markers.forEach(function(marker) {
        map.removeLayer(marker);
    });
    markers = []; // Réinitialise le tableau de marqueurs
});