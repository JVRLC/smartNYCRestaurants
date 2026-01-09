import time
import json
from math import radians, sin, cos, sqrt, atan2
from conversion import get_pg_connection, get_mongo_coll

# calcul de distance
def calcul_distance(lat1, lon1, lat2, lon2):
    R = 6371 # Rayon de la terre
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def demander_positions():
    # Bornes pour New York
    print("-- Veuillez entrer votre position actuelle --")
    while True:
        try:
            la = float(input("Latitude (ex: 40.7): "))
            if 40.50 <= la <= 41.20:
                break
            print("Erreur: Latitude hors zone NY.")
        except:
            print("Entrez un nombre valide.")
            
    while True:
        try:
            lo = float(input("Longitude (ex: -73.9): "))
            if -74.26 <= lo <= -73.20:
                break
            print("Erreur: Longitude hors zone NY.")
        except:
            print("Entrez un nombre valide.")
    return la, lo

def verifier_cache(conn, lat, lon, k, cuisine):
    cursor = conn.cursor()
    # récupère pour comparer manuellement
    cursor.execute("SELECT latitude, longitude, k, cuisine_filter, results FROM cache")
    lignes = cursor.fetchall()
    
    for l in lignes:
        # Si c'est les mêmes paramètres
        if l[2] == k and l[3] == cuisine:
            # On regarde si la position est très proche (diff de 0.001 max)
            if abs(l[0] - lat) < 0.001 and abs(l[1] - lon) < 0.001:
                return l[4]
    return None

def sauver_en_cache(conn, lat, lon, k, cuisine, data):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cache")
    # Limite de 20 entrées 
    if cur.fetchone()[0] >= 20:
        cur.execute("DELETE FROM cache") 
    
    sql = "INSERT INTO cache (latitude, longitude, k, cuisine_filter, results) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(sql, (lat, lon, k, cuisine, json.dumps(data)))
    conn.commit()

def recherche_restos():
    db_sql = get_pg_connection()
    coll_mongo = get_mongo_coll()
    
    if db_sql is None or coll_mongo is None:
        return

    # utilisateur
    ma_lat, ma_lon = demander_positions()
    pref = input("Type de cuisine (laisser vide pour tout) : ").strip()
    
    #  si la cuisine existe ? dans la base
    liste_cuisines = coll_mongo.distinct("cuisine")
    cuisine_ok = None
    for c in liste_cuisines:
        if pref.lower() == c.lower():
            cuisine_ok = c
            break
            
    if pref and not cuisine_ok:
        print("!!! Cuisine non trouvée, recherche globale lancée.")
    
    # Détermination du nombre de résultats (k)
    nb_k = 5
    if pref and not cuisine_ok:
        nb_k = 3 # Petite règle perso

    start_time = time.perf_counter()

    # 2. On regarde si on a déjà fait cette recherche
    en_cache = verifier_cache(db_sql, ma_lat, ma_lon, nb_k, cuisine_ok)
    
    if en_cache:
        resultats = json.loads(en_cache) if isinstance(en_cache, str) else en_cache
        print("\n[CACHE] Résultats trouvés en mémoire locale :")
    else:
        # 3. Sinon calcul complet avec Mongo
        print("\n base de mongo demandée, Calcul des distances en cours...")
        tous_restos = coll_mongo.find({}, {"name": 1, "address.coord": 1, "cuisine": 1})
        
        liste_distances = []
        for r in tous_restos:
            try:
                # Extraction des coordonnées Mongo
                coords = r['address']['coord']['coordinates']
                r_lat, r_lon = coords[1], coords[0]
                
                # Filtre cuisine
                if cuisine_ok and r.get('cuisine') != cuisine_ok:
                    continue
                
                dist = calcul_distance(ma_lat, ma_lon, r_lat, r_lon)
                liste_distances.append({
                    'name': r.get('name', 'Sans nom'),
                    'distance': dist,
                    'cuisine': r.get('cuisine', 'N/A')
                })
            except:
                continue # On ignore les restos sans coordonnées valides

        
        liste_distances.sort(key=lambda x: x['distance'])
        resultats = liste_distances[:nb_k]
        
        # On sauvegarde pour la prochaine fois
        sauver_en_cache(db_sql, ma_lat, ma_lon, nb_k, cuisine_ok, resultats)

    for i, res in enumerate(resultats, 1):
        print(f"{i}. {res['name']} - {round(res['distance'], 2)} km ({res['cuisine']})")

    diff = time.perf_counter() - start_time
    print(f"\nTerminé en {diff:.4f} secondes.")

if __name__ == "__main__":
    recherche_restos()