from pymongo import MongoClient
client = MongoClient() 

# Connexion à MongoDB
try:
    client = MongoClient('localhost', 27017)
    print("Connexion MongoDB établie.")
except Exception as e:
    print(f"Erreur de connexion à MongoDB: {e}")

# Connexion à la collection 
# collection = client['restau']['db']
collection = client['tp5']['restau']
print(collection)
document = collection.find_one({})

if document:
    print("--- Attributs trouvés dans le premier document ---")
    for key in document.keys():
        print(f"- {key}")
else:
    print("La collection est vide ou la connexion a échoué.")

premier_document = collection.find({}).limit(20)
print(f"\n{premier_document}")

# nb de doc:
print(f"Il y a {collection.count_documents({})} documents dans la collection.")