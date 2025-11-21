import psycopg2
import pymongo
from datetime import datetime
import os
from dotenv import load_dotenv
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration des connexions
POSTGRES_CONFIG = {
    
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

MONGODB_CONFIG = {
    'host': os.getenv('MONGO_HOST'),
    'port': 27017,
    'database': os.getenv('MONGO_DB'),
    'collection': os.getenv('COLLECTION_NAME')
}

def connect_postgres():
    """Connexion à PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("Connexion PostgreSQL établie")
        return conn
    except Exception as e:
        print(f"Erreur connexion PostgreSQL: {e}")
        return None

def connect_mongodb():
    """Connexion à MongoDB"""
    try:
        client = pymongo.MongoClient(MONGODB_CONFIG['host'], MONGODB_CONFIG['port'])
        db = client[MONGODB_CONFIG['database']]
        collection = db[MONGODB_CONFIG['collection']]
        print("Connexion MongoDB établie")
        return collection
    except Exception as e:
        print(f"Erreur connexion MongoDB: {e}")
        return None

def extract_restaurant_data(pg_conn):
    """Extraction et regroupement des données depuis PostgreSQL"""
    cursor = pg_conn.cursor()
    
    query = """
    SELECT 
        m.restaurant_id,
        m.name,
        m.cuisine,
        m.borough,
        g.address,
        f.grades
    FROM sql_main m
    LEFT JOIN sql_geo g ON m.restaurant_id = g.restaurant_id
    LEFT JOIN sql_feedback f ON m.restaurant_id = f.restaurant_id
    ORDER BY m.restaurant_id;
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"✓ {len(rows)} restaurants extraits de PostgreSQL")
        
        restaurants = []
        for row in rows:
            restaurant = {
                'restaurant_id': row[0],
                'name': row[1],
                'cuisine': row[2],
                'borough': row[3],
                'address': row[4] if row[4] else {},
                'grades': row[5] if row[5] else []
            }
            restaurants.append(restaurant)
        
        cursor.close()
        return restaurants
    
    except Exception as e:
        print(f"✗ Erreur extraction données: {e}")
        cursor.close()
        return []


def transform_document(restaurant):
    """Transformation optionnelle du document"""
    if 'grades' in restaurant and restaurant['grades']:
        for grade in restaurant['grades']:
            if 'date' in grade and isinstance(grade['date'], str):
                try:
                    grade['date'] = datetime.fromisoformat(grade['date'])
                except:
                    pass
    return restaurant

def load_to_mongodb(collection, restaurants):
    """Chargement des documents dans MongoDB"""
    try:
        transformed_restaurants = [transform_document(r) for r in restaurants]
        if transformed_restaurants:
            result = collection.insert_many(transformed_restaurants)
            print(f"✓ {len(result.inserted_ids)} documents insérés dans MongoDB")
            return True
        else:
            print("✗ Aucun document à insérer")
            return False
    except Exception as e:
        print(f"✗ Erreur insertion MongoDB: {e}")
        return False


def verify_migration(pg_conn, mongo_collection):
    """Vérification de la migration"""
    cursor = pg_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sql_main")
    pg_count = cursor.fetchone()[0]
    
    mongo_count = mongo_collection.count_documents({})
    
    cursor.close()
    
    print("\n=== Vérification de la migration ===")
    print(f"Restaurants dans PostgreSQL: {pg_count}")
    print(f"Documents dans MongoDB: {mongo_count}")
    
    if pg_count == mongo_count:
        print("✓ Migration réussie - Les nombres correspondent")
    else:
        print("⚠ Attention - Les nombres ne correspondent pas")
    

def main():
    """Fonction principale de migration"""
    print("=== Début de la migration PostgreSQL → MongoDB ===\n")
    
    pg_conn = connect_postgres()
    mongo_collection = connect_mongodb()
    
    # ⚡ Correction : on compare explicitement à None pour MongoDB
    if pg_conn is None or mongo_collection is None:
        print("✗ Impossible de continuer sans connexions")
        return
    
    try:
        print("\n--- Étape 1: Extraction ---")
        restaurants = extract_restaurant_data(pg_conn)
        
        if not restaurants:
            print("✗ Aucune donnée à migrer")
            return
        
       
        
        print("\n--- Étape 3: Chargement MongoDB ---")
        # mongo_collection.delete_many({})  # Décommenter si tu veux vider la collection
        
        success = load_to_mongodb(mongo_collection, restaurants)
        
        if success:
            print("\n--- Étape 4: Vérification ---")
            verify_migration(pg_conn, mongo_collection)
        
        print("\n=== Migration terminée ===")
    
    except Exception as e:
        print(f"\n✗ Erreur durant la migration: {e}")
    
    finally:
        if pg_conn:
            pg_conn.close()
            print("\n✓ Connexion PostgreSQL fermée")

if __name__ == "__main__":
    main()
