from pymongo import MongoClient
client = MongoClient()

# Connexion à MongoDB
try:
    while True:
        host = input("Veuillez entrer l'adresse du serveur MongoDB [localhost]: ").strip()
        port_str = input("Veuillez entrer le port du serveur MongoDB [27017]: ").strip()

        if host == "":
            host = "localhost"
        if port_str == "":
            port = 27017
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

def show_k_nearest_restaurants(user_long, user_lat, k=5, cuisine_filter=None):
    restaus = collection.find({}, {'name': 1, 'address.coord': 1, 'cuisine': 1, '_id': 0})

    distances = []
    for restaurant in restaus:
        distance = compute_distance(restaurant, user_long, user_lat, cuisine_filter)
        if distance is not None:
            distances.append((restaurant['name'], distance))

    distances.sort(key=lambda x: x[1])

    print(f"\nLes {k} restaurants les plus proches:")
    for i in range(min(k, len(distances))):
        # print(f"{i+1}. {distances[i][0]} - {distances[i][1]:.2f} km | {restaurant['cuisine']}")
        print(f"{i+1:>2}. {distances[i][0]:<30} - {distances[i][1]:>8.2f} km | {restaurant['cuisine']}")

show_k_nearest_restaurants(long_oe, lat_sn, k=5, cuisine_filter=cuisine_type)
