import os
import json
import time
from pymongo import MongoClient
from dotenv import load_dotenv
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

MONGODB_CONFIG = {
    'host': os.getenv('MONGO_HOST'),
    'port': 27017,
    'database': os.getenv('MONGO_DB'),
    'collection': os.getenv('COLLECTION_NAME')
}
# Connexion à MongoDB
client = MongoClient()
try:
    while True:
        host = input("Veuillez entrer l'adresse du serveur MongoDB [localhost]: ").strip()
        port_str = input("Veuillez entrer le port du serveur MongoDB [27017]: ").strip()

        if host == "":
            host = MONGODB_CONFIG['host']
        if port_str == "":
            port = MONGODB_CONFIG['port']
        else:
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    print("[ERROR] Le port doit être compris entre 1 et 65535. Réessayez.")
                    continue
            except ValueError:
                print("[ERROR] Le port doit être un entier. Réessayez.")
                continue

        # Infos sur la connexion choisie
        print(f"Tentative de connexion à MongoDB sur {host}:{port}...")
        break
    client = MongoClient(host, port)
    print("Connexion MongoDB établie.")
except Exception as e:
    print(f"[ERROR] Erreur de connexion à MongoDB: {e}")

# Connexion à la collection 
# collection = client['restau']['db']
collection = client['tp5']['restau']

# Nb de doc:
print(f"\nIl y a {collection.count_documents({})} documents dans la collection.")

document = collection.find_one({})

if document:
    print("--- Attributs du document ---")
    for key in document.keys():
        print(f"- {key}")

# Affichage des 20 premiers documents
# premier_documents = collection.find({}).limit(20)
# print(f"\n{list(premier_documents)}")

# User inputs
# Validation des intervalles pour les latitudes et longitudes
lat_min, lat_max = 40.50, 41.20
long_min, long_max = -74.26, -73.20

# lat Sud-Nord
while True:
    lat_sudnord = input("\n- Veuillez entrer votre latitude Sud-Nord (ex: 41.1): ").strip()
    try:
        lat_sn = float(lat_sudnord)
    except ValueError:
        print("[ERROR] La latitude doit être un nombre. Réessayez.")
        continue

    if not (lat_min <= lat_sn <= lat_max):
        print(f"[ERROR] La latitude doit être dans l'intervalle [{lat_min}, {lat_max}]. Réessayez.")
        continue
    break

# long Ouest-Est
while True:
    long_ouestest = input("\n- Veuillez entrer votre longitude Ouest-Est (ex: -74.0): ").strip()
    try:
        long_oe = float(long_ouestest)
    except ValueError:
        print("[ERROR] La longitude doit être un nombre. Réessayez.")
        continue
    if not (long_min <= long_oe <= long_max):
        print(f"[ERROR] La longitude doit être dans l'intervalle [{long_min}, {long_max}]. Réessayez.")
        continue
    break

# cuisine (optionnel)
cuisine_input = input("\n- Veuillez entrer le type de cuisine recherché (laisser vide pour ne pas filtrer): ").strip()
cuisine_type = cuisine_input if cuisine_input != "" else None

# Distance computer
def haversine(lon1, lat1, lon2, lat2):
    """Permet de calculer l'angle entre deux points sur une sphère, puis de le convertir en distance."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371      # rayon de la terre en km

    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

# extract restau long lats
# 'address': {'building': '206', 'coord': {'type': 'Point', 'coordinates': [-73.9993545, 40.7286288]}, 'street': 'Thompson Street', 'zipcode': '10012'}
restaus = collection.find({}, {'name': 1, 'address.coord': 1, 'cuisine': 1, '_id': 0})
# print(list(restaus))

def compute_distance(restaurant, user_long, user_lat, cuisine_filter=None):
    restau_long = restaurant['address']['coord']['coordinates'][0]
    restau_lat = restaurant['address']['coord']['coordinates'][1]
    distance = haversine(user_long, user_lat, restau_long, restau_lat)

    if cuisine_filter:
        if 'cuisine' in restaurant and restaurant['cuisine'].lower() == cuisine_filter.lower():
            return distance
        else:
            return None
    return distance

def manage_cache(user_lat, user_long, k, cuisine_filter, new_results=None):
    """
    Gère le cache pour les recherches de restaurants.
    Lecture : Vérifie si une requête similaire (+/- 0.001 lat/long) existe.
    Tache : Ajoute les résultats. Si le cache a 20 entrées, on vide tout avant d'ajouter.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(BASE_DIR, 'cache.json')
    
    # Chargement du cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                if not isinstance(cache_data, list):
                    cache_data = []
        except Exception:
            cache_data = []
    else:
        cache_data = []

    # Mode Lecture (Recherche)
    if new_results is None:
        for entry in cache_data:
            q = entry.get('query', {})
            # Vérification des critères exacts
            if q.get('k') != k or q.get('cuisine_filter') != cuisine_filter:
                continue
            
            # Vérification de la tolérance géographique (+/- 0.001)
            lat_diff = abs(q.get('latitude', 0) - user_lat)
            long_diff = abs(q.get('longitude', 0) - user_long)
            
            if lat_diff <= 0.001 and long_diff <= 0.001:
                return entry.get('results')
        return None

    # Mode Écriture (Mise à jour)
    else:
        # Politique d'éviction : si 20 lignes ou plus, on vid tout
        if len(cache_data) >= 20:
            cache_data = []
        
        new_entry = {
            'query': {
                'latitude': user_lat,
                'longitude': user_long,
                'k': k,
                'cuisine_filter': cuisine_filter
            },
            'results': new_results
        }
        cache_data.append(new_entry)
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        return new_results

def show_k_nearest_restos(user_long, user_lat, k=5, cuisine_filter=None):
    t0 = time.perf_counter()
    
    # 1. Interrogation du cache via manage_cache
    cached_results = manage_cache(user_lat, user_long, k, cuisine_filter)
    
    if cached_results:
        source = "cache"
        print("[INFO] Résultats récupérés depuis le cache.")
        user_results = cached_results
    else:
        source = "mongo"
        print("[INFO] Calcul des résultats depuis MongoDB...")
        
        # Récupération des restaurants depuis MongoDB
        restaus = collection.find({}, {'name': 1, 'address.coord': 1, 'cuisine': 1, '_id': 0})
        
        distances = []
        for restaurant in restaus:
            distance = compute_distance(restaurant, user_long, user_lat, cuisine_filter)
            if distance is not None:
                distances.append({
                    'name': restaurant.get('name', 'Unknown'), 
                    'distance': distance, 
                    'cuisine': restaurant.get('cuisine', 'Unknown')
                })
        
        # Tri et limitation à k
        distances.sort(key=lambda x: x['distance'])
        user_results = distances[:k]
        
        # 2. Mise à jour du cache via manage_cache
        manage_cache(user_lat, user_long, k, cuisine_filter, new_results=user_results)

    t1 = time.perf_counter()
    elapsed = t1 - t0

    print(f"\nLes {k} restaurants les plus proches ({source}, {elapsed:.4f} s) :")
    for i, res in enumerate(user_results):
        print(f"{i+1:>2}. {res['name']:<30} - {res['distance']:>8} km | {res['cuisine']}")

    return elapsed, source

show_k_nearest_restos(long_oe, lat_sn, k=5, cuisine_filter=cuisine_type)
