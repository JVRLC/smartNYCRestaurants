import time
import json
from conversion import connect_postgres, connect_mongodb

def haversine(lon1, lat1, lon2, lat2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_user_coord():
    lat_min, lat_max = 40.50, 41.20
    long_min, long_max = -74.26, -73.20
    while True:
        try:
            lat = float(input("Latitude Sud-Nord (ex: 41.1): ").strip())
            if not (lat_min <= lat <= lat_max):
                print(f"[ERROR] Latitude hors intervalle [{lat_min}, {lat_max}]"); continue
            break
        except ValueError:
            print("[ERROR] La latitude doit être un nombre.")
    while True:
        try:
            lon = float(input("Longitude Ouest-Est (ex: -74.0): ").strip())
            if not (long_min <= lon <= long_max):
                print(f"[ERROR] Longitude hors intervalle [{long_min}, {long_max}]"); continue
            break
        except ValueError:
            print("[ERROR] La longitude doit être un nombre.")
    return lat, lon

def get_from_cache(pg_conn, lat, lon, k, cuisine_type):
    cur = pg_conn.cursor()
    cur.execute("SELECT latitude, longitude, k, cuisine_filter, results FROM cache")
    for row in cur.fetchall():
        if row[2] == k and row[3] == cuisine_type:
            if abs(row[0] - lat) <= 0.001 and abs(row[1] - lon) <= 0.001:
                return row[4]  # JSONB
    return None

def update_cache(pg_conn, lat, lon, k, cuisine_type, results):
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cache")
    count = cur.fetchone()[0]
    # Si la table contient déjà 20 lignes, on la vide avant d'insérer la nouvelle entrée
    if count >= 20:
        cur.execute("TRUNCATE cache")
    # Insertion de la nouvelle entrée dans le cache
    cur.execute(
        "INSERT INTO cache (latitude, longitude, k, cuisine_filter, results) VALUES (%s, %s, %s, %s, %s)",
        (lat, lon, k, cuisine_type, json.dumps(results))
    )
    pg_conn.commit()

def main():
    pg_conn = connect_postgres()
    if pg_conn is None:
        print("[ERROR] PostgreSQL connection failed. Exiting.")
        return
    collection = connect_mongodb()
    cuisines = collection.distinct("cuisine")
    lat, lon = get_user_coord()
    cuisine_input = input("Type de cuisine recherché (laisser vide pour tout): ").strip()
    cuisine_type = cuisine_input if cuisine_input else None
    found = False
    for cuisine in cuisines:
        if cuisine_type and cuisine.lower() == cuisine_type.lower():
            cuisine_type = cuisine
            found = True
            break
    if cuisine_type and not found:
        print("[WARNING] Type de cuisine inconnu, affichage sans préférence.")
        cuisine_type = None
    t0 = time.perf_counter()
    k = 3 if cuisine_input and not found else 5
    cached = get_from_cache(pg_conn, lat, lon, k, cuisine_type)
    if cached:
        user_results = json.loads(cached) if isinstance(cached, str) else cached
        print("[INFO] Résultats depuis le cache PostgreSQL.")
        for i, res in enumerate(user_results):
            print(f"{i+1:>2}. {res['name']:<30} - {res['distance']:.2f} km | {res['cuisine']}")
        elapsed = time.perf_counter() - t0
        print(f"Temps d'exécution : {elapsed:.6f} secondes")
        return
    # Sinon, on interroge MongoDB, calcule, puis update_cache et affiche
    restaus = collection.find({}, {'name': 1, 'address.coord': 1, 'cuisine': 1, '_id': 0})
    distances = []
    for r in restaus:
        try:
            coords = r['address']['coord']['coordinates']
            r_lat, r_lon = coords[1], coords[0]
        except Exception:
            continue
        if cuisine_type and r.get('cuisine', '').lower() != cuisine_type.lower():
            continue
        d = haversine(lon, lat, r_lon, r_lat)
        distances.append({'name': r.get('name', 'Unknown'), 'distance': d, 'cuisine': r.get('cuisine', 'Unknown')})
    distances.sort(key=lambda x: x['distance'])
    print(f"\nLes {k} restaurants les plus proches :")
    user_results = distances[:k]
    for i, res in enumerate(user_results):
        print(f"{i+1:>2}. {res['name']:<30} - {res['distance']:.2f} km | {res['cuisine']}")
    update_cache(pg_conn, lat, lon, k, cuisine_type, user_results)
    elapsed = time.perf_counter() - t0
    print(f"\nTemps d'exécution : {elapsed:.6f} secondes")

if __name__ == "__main__":
    main()
