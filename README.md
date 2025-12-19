# Smart NYC Restaurants

**Smart NYC Restaurants** est un projet conçu pour gérer, migrer et interroger des données sur les restaurants de New York. Il permet de transférer des données d'une base relationnelle (PostgreSQL) vers une base NoSQL (MongoDB) et d'effectuer des recherches géospatiales optimisées pour trouver les restaurants les plus proches.

## Fonctionnalités

*   **Migration de Données** : Script automatisé pour extraire les données de PostgreSQL (tables relationnelles) et les structurer dans MongoDB (documents).
*   **Recherche de Proximité (KNN)** : Algorithme pour trouver les `k` restaurants les plus proches d'une position géographique donnée (latitude/longitude).
*   **Système de Cache Intelligent** :
    *   **Fuzzy Matching** : Utilise une tolérance de +/- 0.001 sur les coordonnées pour réutiliser les résultats en cache, évitant des requêtes inutiles.
    *   **Politique d'Éviction** : Gestion automatique de la taille du cache (limité à 20 entrées) pour maintenir les performances.
*   **Filtres** : Possibilité de filtrer les recherches par type de cuisine.

## Prérequis

*   Python 3.11+:
    *   `pymongo`
    *   `psycopg2-binary`
*   Serveur PostgreSQL
*   Serveur MongoDB

## Installation

1.  **Cloner le dépôt**
    ```bash
    git clone https://github.com/JVRLC/smartNYCRestaurants.git
    cd smartNYCRestaurants
    ```

2.  **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration de l'environnement**
    Créez un fichier `.env` à la racine du projet avec vos identifiants de base de données :
    ```env
    POSTGRES_HOST=localhost
    POSTGRES_DB=votre_db_postgres
    POSTGRES_USER=votre_user
    POSTGRES_PASSWORD=votre_password

    MONGO_HOST=localhost
    MONGO_DB=tp5
    COLLECTION_NAME=restau
    ```

## Mise en place des Données

1.  **Initialiser PostgreSQL**
    Exécutez le script SQL fourni pour créer les tables et insérer les données brutes :
    ```bash
    psql -U votre_user -d votre_db_postgres -f insert_queries.sql
    ```

2.  **Migrer vers MongoDB**
    Lancez le script de conversion pour transférer les données vers MongoDB :
    ```bash
    python conversion.py
    ```

## Utilisation

### Recherche de Restaurants (`sae.py`)

Le script principal `sae.py` permet de lancer des recherches. Il vous demandera les informations de connexion à MongoDB au démarrage.

```bash
python sae.py
```

Le script effectue les actions suivantes :
1.  Connexion à MongoDB.
2.  Vérification du cache local (`cache.json`) pour une requête similaire.
3.  Si non trouvé en cache, interrogation de MongoDB et calcul des distances.
4.  Affichage des résultats et mise à jour du cache.

## Structure du Projet

```
smartNYCRestaurants/
├── sae.py                  # Script principal pour la recherche de restaurants et la gestion du cache.
├── conversion.py           # Script de migration des données de PostgreSQL vers MongoDB.
├── insert_queries.sql      # Données initiales pour PostgreSQL.
├── cache.json              # Fichier de stockage local pour le cache des requêtes.
├── util.py                 # Fonctions utilitaires.
└── requirements.txt        # Liste des dépendances Python.
```

## Auteurs

*   JVRLC
*   AV

