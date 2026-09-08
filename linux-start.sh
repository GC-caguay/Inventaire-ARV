#!/bin/bash
# Démarre l'app Inventaire ARV en arrière-plan (si elle ne tourne pas déjà)
# et ouvre directement le navigateur, sans terminal visible.
cd "$(dirname "$0")"

mkdir -p logs data

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ./.venv/bin/pip install --quiet --upgrade pip
    ./.venv/bin/pip install --quiet -r requirements.txt
fi

./.venv/bin/python -m scripts.init_db >> logs/launcher.log 2>&1

# Ne démarre un nouveau serveur que si aucun ne répond déjà sur le port 8000.
if ! (exec 3<>/dev/tcp/127.0.0.1/8000) 2>/dev/null; then
    nohup ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 >> logs/server.log 2>&1 &
    disown
    sleep 2
else
    exec 3<&- 3>&- 2>/dev/null
fi

xdg-open "http://127.0.0.1:8000" >/dev/null 2>&1 &
