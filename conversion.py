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
    "collection": os.getenv("COLLECTION_NAME")
}

# CONNECTION FUNCTIONS

def connect_postgres():
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("PostgreSQL connection established.")
        return conn
    except Exception as e:
        print(e)
        return None

def connect_mongodb():
    try:
        # Connect to MongoDB server
        client = pymongo.MongoClient(
            MONGODB_CONFIG["host"],
            MONGODB_CONFIG["port"]
        )
        print("MongoDB connection established.")
        # Select the database
        db = client[MONGODB_CONFIG["database"]]
        # Return the collection (equivalent to a "table" in SQL)
        return db[MONGODB_CONFIG["collection"]]
    except Exception as e:
        print(e)
        return None

# EXTRACTION (E in ETL)

def extract_restaurant_data(pg_conn):
    cursor = pg_conn.cursor()
    # SQL query with joins to retrieve all info
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
        
        # Transform each SQL row into a dictionary
        for row in rows:
            restaurants.append({
                "restaurant_id": row[0],
                "name": row[1],
                "cuisine": row[2],
                "borough": row[3],
                "address": row[4] if row[4] else {},    # Empty dict if no address
                "grades": row[5] if row[5] else []      # Empty list if no grades
            })
        cursor.close()
        return restaurants
    except Exception as e:
        cursor.close()
        print(e)
        return []

# TRANSFORMATION (T in ETL)
    
def transform_document(restaurant):
    if restaurant.get("grades"):
        for grade in restaurant["grades"]:
            # If the date is a string, convert it to datetime
            if isinstance(grade.get("date"), str):
                try:
                    grade["date"] = datetime.fromisoformat(grade["date"])
                except ValueError:
                    pass  # If conversion fails, keep the string
    return restaurant

# LOADING (L in ETL)

def load_to_mongodb(collection, restaurants):
    try:
        operations = []
        for restaurant in restaurants:
            # Apply transformations
            restaurant = transform_document(restaurant)
            
            # Prepare UpdateOne operation with upsert
            operations.append(
                UpdateOne(
                    # Filter: search by restaurant_id (prevents duplicates)
                    {"restaurant_id": restaurant["restaurant_id"]},
                    {"$set": restaurant},
                    upsert=True
                )
            )
        
        if not operations:
            return False
        
        # Execute all operations in a single request (more efficient)
        collection.bulk_write(operations)
        return True
    except Exception as e:
        print(e)
        return False

# VERIFICATION

def verify_migration(pg_conn, mongo_collection):
    cursor = pg_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sql_main")
    pg_count = cursor.fetchone()[0]              # Count in PostgreSQL
    mongo_count = mongo_collection.count_documents({})  # Count in MongoDB
    cursor.close()
    
    print(f"PostgreSQL count: {pg_count}, MongoDB count: {mongo_count}")
    
    if pg_count == mongo_count:
        return True
    return False

# MAIN FUNCTION

def main():
    """
    Orchestrates the complete ETL process:
    1. Connect to databases
    2. Create unique index (duplicate protection)
    3. Extract data from PostgreSQL
    4. Load into MongoDB
    5. Verify the migration
    """
    # Step 1: Connections
    pg_conn = connect_postgres()
    mongo_collection = connect_mongodb()

    # Check that connections are established
    if pg_conn is None or mongo_collection is None:
        return

    # Step 2: Create unique index on restaurant_id
    # Prevents MongoDB from accepting duplicates (extra safety)
    mongo_collection.create_index("restaurant_id", unique=True)

    try:
        # Step 3: Extract data
        restaurants = extract_restaurant_data(pg_conn)
        if not restaurants:
            print("No data extracted from PostgreSQL.")
            return
        
        print(f"Extracted {len(restaurants)} restaurants from PostgreSQL.")
        
        # Step 4: Load into MongoDB (with transformation)
        success = load_to_mongodb(mongo_collection, restaurants)
        
        # Step 5: Verification
        if success:
            print("Data loaded successfully.")
            if verify_migration(pg_conn, mongo_collection):
                print("Migration verified: record counts match.")
            else:
                print("Migration warning: record counts do not match.")
        else:
            print("Failed to load data into MongoDB.")

    finally:
        # Always close the PostgreSQL connection
        pg_conn.close()

# Script entry point
if __name__ == "__main__":
    main()
