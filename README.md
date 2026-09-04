# Inventaire ARV

App de gestion d'inventaire de matériel photo/vidéo pour l'association ARV.
Conçue pour tourner sur **un seul ordinateur**, dans l'entrepôt de matériel, sans dépendre d'internet.

## Démarrage rapide

Double-cliquer sur **`Inventaire ARV.app`** (macOS). Ça va, sans ouvrir de fenêtre de terminal :
1. Créer un environnement Python local (`.venv`) et installer les dépendances (première fois seulement — une notification macOS l'indique).
2. Créer/mettre à jour la base de données locale (`data/arv.db`) et faire une sauvegarde automatique.
3. Démarrer le serveur en arrière-plan (s'il ne tourne pas déjà) et ouvrir `http://127.0.0.1:8000` dans le navigateur.

Au tout premier lancement, macOS va probablement avertir que l'app vient d'un développeur non identifié :
clic droit sur `Inventaire ARV.app` → **Ouvrir** → confirmer. À faire une seule fois.

Le serveur continue de tourner en arrière-plan après la fermeture du navigateur — redouble-cliquer sur
l'app rouvre juste une nouvelle fenêtre/onglet sans relancer un second serveur. Pour l'arrêter
complètement : `pkill -f "uvicorn app.main:app"` dans un terminal, ou redémarrer l'ordinateur.

`run.command` existe toujours en secours (utile pour voir les logs en direct dans un terminal si
quelque chose ne fonctionne pas comme prévu).

## Démarrage manuel (développement)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn app.main:app --reload
```

## Sauvegarde des données

Toutes les données sont dans un seul fichier : `data/arv.db`.

**Sauvegarde automatique** : à chaque démarrage du serveur, une copie
horodatée de `data/arv.db` est faite dans `data/backups/` avant toute autre opération. Les 60
dernières copies sont conservées, les plus vieilles sont effacées automatiquement.

Pour restaurer une sauvegarde : fermer l'app, remplacer `data/arv.db` par la copie voulue depuis
`data/backups/` (renommée `arv.db`), puis relancer.

Pour une sauvegarde hors du poste (clé USB, Drive, etc.), copier `data/arv.db` ou tout le dossier
`data/backups/` ailleurs de temps en temps.

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
