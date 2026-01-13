# Plateforme Intelligente de Gestion Oracle avec IA

Ce projet est une plateforme intelligente pour l'assistance à l'administration de bases de données Oracle. Il combine l'extraction de données réelles, l'analyse par IA (LLM Gemini via l'API Google Generative AI) et une base de connaissances RAG pour fournir des audits de sécurité, des optimisations de requêtes et des recommandations de sauvegarde.

## Prérequis

- **Python 3.8+**
- **Clé API Gemini (Google Generative AI)** (dans un fichier `.env`)
- **Base de données Oracle** (nécessaire pour l'extraction)
  - Accès `SYSDBA` ou utilisateur avec privilèges d'audit.

## Installation

1. **Cloner le projet**
   Navigate to the project root.

2. **Configuration de l'environnement**
   Il est recommandé d'utiliser un environnement virtuel :

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Installer les dépendances**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration API**
   Créez un fichier `.env` à la racine (si absent) et ajoutez votre clé :

```
GEMINI_API_KEY=votre_clé_api
```

_Note : Le projet utilise le dossier `data/` pour stocker les données et résultats._

## Usage

### 1. Extraction de Données (Connexion Réelle)

Configurez `DB_CONFIG` dans `src/real_data_extractor.py` puis lancez :

```bash
python src/real_data_extractor.py
```

Cela générera les CSV dans `data/`.

### 2. Analyse et IA

Les modules d'analyse utilisent les données de `data/`.

- **Initialisation RAG** (Base de connaissances) :

  ```bash
  python src/rag_setup.py
  ```

- **Détection d'Anomalies** :

  ```bash
  python src/anomaly_detector.py
  ```

  Génère `data/detected_anomalies.json`.

- **Optimisation de Requêtes** :

  ```bash
  python src/query_optimizer.py
  ```

  Génère `data/query_analysis.json`.

- **Audit de Sécurité** :

  ```bash
  python src/security_audit.py
  ```

  Génère `data/last_audit.json`.

- **Recommandation de Sauvegarde** :
  ```bash
  python src/backup_recommender.py
  ```
  Génère `data/backup_plan.json` et `data/backup_script.rman`.

### 3. Interface Web (Dashboard)

Pour visualiser les résultats et interagir avec le Chatbot DBA :

```bash
python src/webapp/app.py
```

## Architecture des Dossiers

- `src/` : Code source des modules Python.
- `src/webapp/` : Application Flask et templates HTML.
- `data/` : Dossier principal pour les données (CSV extraits, JSON résultats, Base Vectorielle ChromaDB).
