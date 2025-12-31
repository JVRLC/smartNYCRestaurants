# smartNYCRestaurants

Ce projet permet de rechercher les restaurants les plus proches à New York selon la position de l'utilisateur et le type de cuisine souhaité, en utilisant MongoDB pour les données et PostgreSQL pour le cache.

## Prérequis

- Python 3.x
- MongoDB et PostgreSQL installés et accessibles
- Les modules Python listés dans `requirements.txt`

## Installation

1. **Installer les dépendances Python**  
   ```bash
   pip install -r requirements.txt
   ```

2. **Créer la base de données PostgreSQL**  
   Connectez-vous à PostgreSQL et créez la base :
   ```sql
   CREATE DATABASE sae;
   ```

3. **Configurer le fichier `.env`**  
   Modifiez la ligne suivante avec votre mot de passe PostgreSQL :
   ```
   POSTGRES_PASSWORD=xxxxxx
   ```
   (Remplacez `xxxxxx` par votre mot de passe réel.)

4. **Insérer les données restaurants**  
   Utilisez le script `insert_queries` pour insérer les données dans MongoDB.

5. **Utiliser le module `conversion.py`**  
   Ce module contient les fonctions de connexion à PostgreSQL et MongoDB.  
   - `connect_postgres()` : se connecte à la base PostgreSQL en utilisant les paramètres du `.env`.
   - `connect_mongodb()` : se connecte à la base MongoDB en utilisant les paramètres du `.env`.

## Utilisation

### Crée aussi la table cahe
```
CREATE TABLE cache (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    k INTEGER,
    cuisine_filter TEXT,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

```. Lancez le script principal :
   ```bash
   python sae.py
   ```
2. Saisissez la latitude, la longitude et éventuellement le type de cuisine.

## Fonctionnement du cache

- Le cache est géré dans la table PostgreSQL `cache` (max 20 entrées).
- Si une requête similaire existe (même position ±0.001, même filtre, même k), le résultat est affiché instantanément.
- Sinon, la recherche est effectuée sur MongoDB, puis le résultat est ajouté au cache.

## Table `cache` (PostgreSQL)

| Colonne        | Type      | Description                                 |
|----------------|-----------|---------------------------------------------|
| latitude       | FLOAT     | Latitude de la requête                      |
| longitude      | FLOAT     | Longitude de la requête                     |
| k              | INTEGER   | Nombre de résultats demandés                |
| cuisine_filter | TEXT      | Type de cuisine (ou NULL)                   |
| results        | JSONB     | Résultats de la requête (liste de dicts)    |

## Auteur

- Serigne & Aurel

## GitHub

- [https://github.com/JVRLC](https://github.com/JVRLC)
- [https://github.com/aurvl](https://github.com/aurvl)

