# smartNYCRestaurants

Application Python de migration et consolidation des données de restaurants à New York, intégrant PostgreSQL et MongoDB pour une gestion optimisée des informations géographiques, culinaires et d'évaluations.

## Description

**smartNYCRestaurants** est une solution ETL (Extract, Transform, Load) conçue pour migrer les données de restaurants depuis une base de données PostgreSQL relationnelle vers MongoDB, offrant une meilleure flexibilité et scalabilité. Le système unifie trois sources de données distinctes pour créer un modèle de document cohérent et optimisé.

### Sources de données

- **sql_main** : Informations générales et métadonnées des restaurants (nom, type de cuisine, arrondissement, identifiant unique)
- **sql_geo** : Données géographiques et de localisation (adresse complète, coordonnées GPS, code postal)
- **sql_feedback** : Historique des évaluations sanitaires et grades d'inspection

## Fonctionnalités principales

- Extraction automatisée des données PostgreSQL avec gestion des jointures relationnelles
- Transformation et fusion des documents dans un format NoSQL optimisé
- Chargement en masse vers MongoDB avec gestion des erreurs
- Vérification et validation automatique de l'intégrité de la migration
- Gestion robuste des erreurs et logging détaillé
- Support complet des variables d'environnement pour la configuration

## Structure du Projet

```
smartNYCRestaurants/
├── main.py                  # Point d'entrée principal
├── conversion.py            # Logique ETL (extraction, transformation, chargement)
├── sae.py                   # Fonctions utilitaires SAE
├── util.py                  # Fonctions utilitaires générales
├── insert_queries.sql       # Requêtes SQL d'insertion
├── requirements.txt         # Dépendances Python
├── .env                     # Variables d'environnement (à configurer)
└── README.md               # Documentation
```

## Installation

### Prérequis système

- Python 3.8 ou supérieur
- PostgreSQL 12.0 ou supérieur
- MongoDB 4.4 ou supérieur
- pip (gestionnaire de paquets Python)
- Accès en lecture aux tables PostgreSQL
- Accès en écriture à MongoDB

### Procédure d'installation

#### 1. Cloner le dépôt
```bash
git clone https://github.com/JVRLC/smartNYCRestaurants.git
cd smartNYCRestaurants
```

#### 2. Créer et activer un environnement virtuel Python
```bash
python -m venv venv
source venv/bin/activate
```
Sur Windows (PowerShell) :
```powershell
venv\Scripts\Activate.ps1
```

#### 3. Installer les dépendances du projet
```bash
pip install -r requirements.txt
```

#### 4. Configuration des variables d'environnement
Créer un fichier `.env` à la racine du projet avec les paramètres de connexion :

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=nyc_restaurants
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# MongoDB Configuration
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=nyc_restaurants
COLLECTION_NAME=restaurants
MONGO_USERNAME=optional_user
MONGO_PASSWORD=optional_password
```



## Utilisation

### Lancement de la migration complète

```bash
python .py

python main.py
```

### Processus d'exécution détaillé

L'application exécute une pipeline ETL structurée en quatre étapes distinctes :

#### Étape 1 : Extraction des données
- Établissement de la connexion à PostgreSQL
- Exécution de requêtes SQL avec jointures LEFT JOIN sur les trois tables
- Récupération complète des restaurants avec toutes leurs données associées
- Vérification du nombre de lignes extraites

#### Étape 2 : Transformation des documents
- Fusion des données provenant de trois tables relationnelles
- Restructuration au format de document NoSQL
- Parsing et normalisation des dates d'inspection
- Validation de l'intégrité des données transformées

#### Étape 3 : Chargement dans MongoDB
- Insertion en masse des documents transformés
- Création automatique des collections si nécessaire
- Gestion des doublons et des conflits potentiels
- Logging détaillé du nombre de documents insérés

#### Étape 4 : Vérification post-migration
- Comparaison du nombre d'enregistrements PostgreSQL vs MongoDB
- Validation de la complétude de la migration
- Génération d'un rapport de vérification détaillé
- Alertes en cas d'écarts détectés



## Architecture des données

### Format du document unifié

Chaque restaurant est représenté sous la forme d'un document JSON structuré, combinant les données de trois tables PostgreSQL distinctes :

```json
{
  "restaurant_id": "30075445",
  "name": "Morris Park Bake Shop",
  "cuisine": "Bakery",
  "borough": "Bronx",
  "address": {
    "building": "1007",
    "street": "Morris Park Ave",
    "zipcode": "10462",
    "coord": {
      "type": "Point",
      "coordinates": [-73.856077, 40.848447]
    }
  },
  "grades": [
    {
      "date": "2014-03-03T00:00:00",
      "grade": "A",
      "score": 2
    },
    {
      "date": "2013-09-11T00:00:00",
      "grade": "A",
      "score": 6
    }
  ]
}
```

### Schéma de données

- **restaurant_id** : Identifiant unique du restaurant (clé primaire)
- **name** : Nom commercial de l'établissement
- **cuisine** : Type de cuisine proposée
- **borough** : Arrondissement administratif (Manhattan, Bronx, Queens, Brooklyn, Staten Island)
- **address** : Objet imbriqué contenant les données géographiques complètes
  - building : Numéro du bâtiment
  - street : Nom de la rue
  - zipcode : Code postal
  - coord : Coordonnées géographiques au format GeoJSON (Point)
- **grades** : Tableau d'objets d'évaluation chronologiques
  - date : Date de l'inspection (format ISO 8601)
  - grade : Grade sanitaire attribué (A, B, C, Z)
  - score : Score numérique d'inspection




### Audit et traçabilité

- Tous les accès à PostgreSQL et MongoDB sont loggés
- Les timestamps d'insertion MongoDB permettent de retracer les migrations
- Maintenir des sauvegardes avant chaque migration importante

## Dépendances du projet

### Packages Python requis

Voir `requirements.txt` pour la liste détaillée avec versions :

- **psycopg2-binary** (>= 2.9.0) : Adaptateur PostgreSQL pour Python, permettant la communication native avec PostgreSQL
- **pymongo** (>= 3.12.0) : Driver MongoDB officiel pour Python, gérant les connexions et opérations
- **python-dotenv** (>= 0.19.0) : Gestion des variables d'environnement depuis fichier `.env`

### Versions supportées

- Python 3.8, 3.9, 3.10, 3.11
- PostgreSQL 12+
- MongoDB 4.4+

