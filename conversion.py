import psycopg2
import pymongo
from pymongo import UpdateOne
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Config pour postgres et MongoDb

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

MONGODB_CONFIG = {
    "host": os.getenv("MONGO_HOST"),
    "port": 27017,
    "database": os.getenv("MONGO_DB"),
    "collection": os.getenv("COLLECTION_NAME")
}

# Connexion

def connect_postgres():
    try:
        return psycopg2.connect(**POSTGRES_CONFIG)
    except Exception as e:
        print(e)
        return None

def connect_mongodb():
    try:
        client = pymongo.MongoClient(
            MONGODB_CONFIG["host"],
            MONGODB_CONFIG["port"]
        )
        db = client[MONGODB_CONFIG["database"]]
        return db[MONGODB_CONFIG["collection"]]
    except Exception as e:
        print(e)
        return None

# Extraction from postgresSQL
def extract_restaurant_data(pg_conn):
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
        restaurants = []
        for row in rows:
            restaurants.append({
                "restaurant_id": row[0],
                "name": row[1],
                "cuisine": row[2],
                "borough": row[3],
                "address": row[4] if row[4] else {},
                "grades": row[5] if row[5] else []
            })
        cursor.close()
        return restaurants
    except Exception as e:
        cursor.close()
        print(e)
        return []
    
# Transformations
def transform_document(restaurant):
    if restaurant.get("grades"):
        for grade in restaurant["grades"]:
            if isinstance(grade.get("date"), str):
                try:
                    grade["date"] = datetime.fromisoformat(grade["date"])
                except ValueError:
                    pass
    return restaurant

# chargement
def load_to_mongodb(collection, restaurants):
    try:
        operations = []
        for restaurant in restaurants:
            restaurant = transform_document(restaurant)
            operations.append(
                UpdateOne(
                    {"restaurant_id": restaurant["restaurant_id"]},
                    {"$set": restaurant},
                    upsert=True
                )
            )
        if not operations:
            return False
        collection.bulk_write(operations)
        return True
    except Exception as e:
        print(e)
        return False

def verify_migration(pg_conn, mongo_collection):
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sql_main")
    pg_count = cursor.fetchone()[0]
    mongo_count = mongo_collection.count_documents({})
    cursor.close()
    print(pg_count, mongo_count)

def main():
    pg_conn = connect_postgres()
    mongo_collection = connect_mongodb()

    if pg_conn is None or mongo_collection is None:
        return

    mongo_collection.create_index("restaurant_id", unique=True)

    try:
        restaurants = extract_restaurant_data(pg_conn)
        if not restaurants:
            return
        success = load_to_mongodb(mongo_collection, restaurants)
        if success:
            print("ok")
            verify_migration(pg_conn, mongo_collection)
    finally:
        pg_conn.close()

if __name__ == "__main__":
    main()
"10.3.124.4"