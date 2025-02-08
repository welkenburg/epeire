#!/bin/bash

set -e

OSM_FILE="midi-pyrenees-latest.osm.pbf"
DB_NAME="osm"
PG_USER="postgres"

echo "🔧 Installation de PostgreSQL, PostGIS et osm2pgsql..."
sudo apt update
sudo apt install -y postgis postgresql postgresql-contrib osm2pgsql

echo "🛠️ Création de la base de données $DB_NAME..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION postgis;"

echo "📦 Import des données OSM..."
osm2pgsql -d $DB_NAME --create --slim --hstore --drop --number-processes 4 $OSM_FILE

echo "✅ Import terminé avec succès !"
