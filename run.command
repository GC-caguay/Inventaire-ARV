#!/bin/bash
# Double-clic pour démarrer l'app Inventaire ARV et l'ouvrir dans le navigateur.
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Premiere installation : creation de l'environnement..."
    python3 -m venv .venv
    ./.venv/bin/pip install --quiet --upgrade pip
    ./.venv/bin/pip install --quiet -r requirements.txt
fi

mkdir -p data

./.venv/bin/python -m scripts.init_db

( sleep 1.5 && open "http://127.0.0.1:8000" ) &

./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
