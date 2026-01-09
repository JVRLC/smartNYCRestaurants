import psycopg2
import pymongo
from pymongo import UpdateOne
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Récupération des variables d'environnement
PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PWD = os.getenv("POSTGRES_PASSWORD")

M_HOST = os.getenv("MONGO_HOST")
M_PORT = int(os.getenv("MONGO_PORT", 27017))
M_DB = os.getenv("MONGO_DB")

def get_pg_connection():
    try:
        # On tente la connexion à Postgres
        c = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PWD)
        print(f"Connecté à Postgres sur {PG_HOST}")
        return c
    except Exception as err:
        print(f"Erreur PG: {err}")
        return None

def get_mongo_coll():
    try:
        cl = pymongo.MongoClient(M_HOST, M_PORT, serverSelectionTimeoutMS=2000)
        # Petit test pour voir si le serveur répond
        cl.server_info()
        db = cl[M_DB]
        return db["restaurants"]
    except Exception as err:
        print(f"Erreur Mongo: {err}")
        return None

def fetch_data(conn):
    cur = conn.cursor()
    # Ma requête de jointure pour récupérer les infos restos + feedback
    sql = """
    SELECT m.restaurant_id, m.name, m.cuisine, m.borough, g.address, f.grades
    FROM sql_main m
    LEFT JOIN sql_geo g ON m.restaurant_id = g.restaurant_id
    LEFT JOIN sql_feedback f ON m.restaurant_id = f.restaurant_id
    ORDER BY m.restaurant_id;
    """
    try:
        cur.execute(sql)
        data = cur.fetchall()
        
        # On transforme les tuples en dict pour Mongo
        resultat = []
        for r in data:
            resultat.append({
                "restaurant_id": r[0],
                "name": r[1],
                "cuisine": r[2],
                "borough": r[3],
                "address": r[4] or {},
                "grades": r[5] or []
            })
        cur.close()
        return resultat
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}")
        return []

def run_migration():
    # 1. Connexions
    p_conn = get_pg_connection()
    m_coll = get_mongo_coll()

    if p_conn is None or m_coll is None:
        print("Problème de connexion, arrêt du script.")
        return

    # Index pour éviter les doublons sur l'ID resto
    m_coll.create_index("restaurant_id", unique=True)

    # 2. Extraction
    raw_data = fetch_data(p_conn)
    if not raw_data:
        print("Rien à migrer.")
        return

    print(f"Nombre de lignes récupérées : {len(raw_data)}")

    # 3. Transformation & Load
    batch_updates = []
    for item in raw_data:
        # Nettoyage des dates dans le dictionnaire
        if item.get("grades"):
            for g in item["grades"]:
                if isinstance(g.get("date"), str):
                    try:
                        g["date"] = datetime.fromisoformat(g["date"])
                    except:
                        pass # On laisse tel quel si ça foire
        
        # Préparation de l'upsert
        batch_updates.append(
            UpdateOne(
                {"restaurant_id": item["restaurant_id"]},
                {"$set": item},
                upsert=True
            )
        )

    if batch_updates:
        try:
            res = m_coll.bulk_write(batch_updates)
            print(f"Migration terminée. Modifiés/Upsertés: {res.upserted_count + res.modified_count}")
        except Exception as e:
            print(f"Erreur insertion bulk: {e}")

    # 4. Petite verif rapide
    cur = p_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sql_main")
    count_pg = cur.fetchone()[0]
    count_mongo = m_coll.count_documents({})
    
    print(f"Vérification finale -> PG: {count_pg} / Mongo: {count_mongo}")
    
    p_conn.close()
    m_coll.database.client.close()

if __name__ == "__main__":
    run_migration()