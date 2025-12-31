"""
ETL Migration Script (Extract-Transform-Load)
Transfers restaurant data from PostgreSQL to MongoDB
"""

import psycopg2
import pymongo
from pymongo import UpdateOne
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CONFIGURATIONS

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"), 
    "password": os.getenv("POSTGRES_PASSWORD")
}

# MongoDB connection config + database/collection info
MONGODB_CONFIG = {
    "host": os.getenv("MONGO_HOST"),
    "port": int(os.getenv("MONGO_PORT", 27017)),  # Default MongoDB port
    "database": os.getenv("MONGO_DB"),
    "collection": "restaurants"  # Force collection name to 'restaurants'
}

# CONNECTION FUNCTIONS

def connect_postgres():
    """Connects to PostgreSQL and returns a connection object or None."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("PostgreSQL connection established.")
        return conn
    except Exception as e:
        print(f"[ERROR] Could not connect to PostgreSQL: {e}")
        return None

def connect_mongodb():
    """Connects to MongoDB and returns the collection object or None."""
    try:
        client = pymongo.MongoClient(
            MONGODB_CONFIG["host"],
            MONGODB_CONFIG["port"],
            serverSelectionTimeoutMS=3000  # fail fast if server not reachable
        )
        client.server_info()  # Force connection check
        print("MongoDB connection established.")
        db = client[MONGODB_CONFIG["database"]]
        return db[MONGODB_CONFIG["collection"]]
    except pymongo.errors.ServerSelectionTimeoutError:
        print("[ERROR] MongoDB not accessible (wrong host or port).")
        return None
    except Exception as e:
        print(f"[ERROR] MongoDB connection error: {e}")
        return None

# EXTRACTION (E in ETL)

def extract_restaurant_data(pg_conn):
    """Extract restaurant data from PostgreSQL and return as a list of dicts."""
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
        print(f"[ERROR] Extraction failed: {e}")
        return []

# TRANSFORMATION (T in ETL)

def transform_document(restaurant):
    """Convert grade dates from string to datetime if needed."""
    if restaurant.get("grades"):
        for grade in restaurant["grades"]:
            if isinstance(grade.get("date"), str):
                try:
                    grade["date"] = datetime.fromisoformat(grade["date"])
                except ValueError:
                    print(f"[WARN] Invalid date format: {grade.get('date')}")
    return restaurant

# LOADING (L in ETL)

def load_to_mongodb(collection, restaurants):
    """Load restaurant data into MongoDB with upsert to avoid duplicates."""
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
            print("[INFO] No operations to perform in MongoDB.")
            return False
        collection.bulk_write(operations)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load data into MongoDB: {e}")
        return False

# VERIFICATION

def verify_migration(pg_conn, mongo_collection):
    """Compare record counts between PostgreSQL and MongoDB."""
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sql_main")
    pg_count = cursor.fetchone()[0]
    mongo_count = mongo_collection.count_documents({})
    cursor.close()
    
    print(f"PostgreSQL count: {pg_count}, MongoDB count: {mongo_count}")
    if pg_count == mongo_count:
        return True
    return False

# MAIN FUNCTION

def main():
    """Orchestrates ETL: connect, extract, transform, load, verify."""
    pg_conn = connect_postgres()
    mongo_collection = connect_mongodb()

    if pg_conn is None:
        print("[ERROR] PostgreSQL connection failed. Exiting.")
        return
    if mongo_collection is None:
        print("[ERROR] MongoDB connection failed. Exiting.")
        pg_conn.close()
        return

    # Ensure unique index
    mongo_collection.create_index("restaurant_id", unique=True)

    try:
        restaurants = extract_restaurant_data(pg_conn)
        if not restaurants:
            print("[INFO] No data extracted from PostgreSQL.")
            return
        
        print(f"Extracted {len(restaurants)} restaurants from PostgreSQL.")
        
        success = load_to_mongodb(mongo_collection, restaurants)
        if success:
            print("[SUCCESS] Data loaded into MongoDB.")
            if verify_migration(pg_conn, mongo_collection):
                print("[SUCCESS] Migration verified: record counts match.")
            else:
                print("[WARN] Migration warning: record counts do not match.")
        else:
            print("[ERROR] Failed to load data into MongoDB.")
    finally:
        pg_conn.close()
        # Optional: close MongoDB client
        mongo_collection.database.client.close()

# Script entry point
if __name__ == "__main__":
    main()
