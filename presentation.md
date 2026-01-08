# Présentation du projet smartNYCRestaurants

## Introduction

Ce projet vise à optimiser la recherche de restaurants à New York en exploitant les avantages des bases de données relationnelles et NoSQL, ainsi qu’un mécanisme de cache pour améliorer les performances.

## 1. La base relationnelle et les données initiales

Les données sources sont réparties dans trois tables PostgreSQL :
- **sql_main** : informations principales (restaurant_id, nom, cuisine, borough)
- **sql_geo** : adresses au format JSONB
- **sql_feedback** : notes (grades) au format JSONB

Un script SQL (`insert_queries.sql`) permet de créer et remplir ces tables.

## 2. Migration vers NoSQL et formatage des données

### MongoDB

Les données sont migrées vers MongoDB dans une collection unique `restaurants`.  
Chaque document regroupe toutes les informations d’un restaurant :
```json
{
  "restaurant_id": "50018995",
  "name": "Cold Press D",
  "cuisine": "Other",
  "borough": "Brooklyn",
  "address": {
    "building": "921",
    "coord": { "type": "Point", "coordinates": [-73.9691347, 40.6389857] },
    "street": "Cortelyou Rd",
    "zipcode": "11218"
  },
  "grades": []
}
```

### PostgreSQL (Cache)

Une table `cache` stocke les 20 dernières requêtes/réponses :
- latitude, longitude, k, cuisine_filter, results (JSONB), created_at

## 3. Application conversion.py

Ce script réalise la migration ETL :
- **Extraction** : jointure des 3 tables PostgreSQL
- **Transformation** : formatage des documents
- **Chargement** : insertion dans MongoDB avec protection contre les doublons

## 4. Application finale sae.py

Ce script permet à l’utilisateur de rechercher les restaurants les plus proches selon sa position et ses préférences :
- Interrogation du cache PostgreSQL en priorité (tolérance ±0.001 sur la position)
- Si absence dans le cache, interrogation de MongoDB et mise à jour du cache

## 5. Performances du cache

- Le cache réduit fortement le temps de réponse pour les requêtes répétées.
- Limitation à 20 entrées pour éviter la surcharge.
- Vidage automatique si la limite est atteinte.

## Conclusion

Ce projet illustre la complémentarité entre bases relationnelles et NoSQL pour la gestion de catalogues volumineux, et l’intérêt d’un cache pour optimiser les performances d’une application de recherche.  
La modularité des scripts permet une maintenance et une évolution aisées.

---
**Auteurs** : Serigne & Aurel  
GitHub : [JVRLC](https://github.com/JVRLC), [aurvl](https://github.com/aurvl)
