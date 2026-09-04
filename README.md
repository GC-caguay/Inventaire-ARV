# Inventaire ARV

App de gestion d'inventaire de matériel photo/vidéo pour l'association ARV.
Conçue pour tourner sur **un seul ordinateur**, dans l'entrepôt de matériel, sans dépendre d'internet.

## Démarrage rapide

Double-cliquer sur `run.command` (macOS). Ça va :
1. Créer un environnement Python local (`.venv`) et installer les dépendances (première fois seulement).
2. Créer/mettre à jour la base de données locale (`data/arv.db`).
3. Démarrer le serveur et ouvrir automatiquement `http://127.0.0.1:8000` dans le navigateur.

Pour arrêter l'app, fermer la fenêtre de terminal qui s'est ouverte (ou Ctrl+C).

## Démarrage manuel (développement)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn app.main:app --reload
```

## Sauvegarde des données

Toutes les données sont dans un seul fichier : `data/arv.db`. Pour sauvegarder, copier ce fichier
ailleurs (clé USB, Drive, etc.) pendant que l'app est fermée.

## Tests

```bash
source .venv/bin/activate
pytest
```

## Structure

- `app/models/` — tables de la base de données (SQLAlchemy)
- `app/services/` — logique métier (sortie de matériel, retours, tableau de bord)
- `app/routers/` — pages web
- `app/templates/` — pages HTML
- `migrations/` — historique des changements de structure de base de données (Alembic)
