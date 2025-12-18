# Deploy guide

This repository contains a static frontend (`/web`) and a backend FastAPI service (`/backend`).

Quick overview:
- Frontend: static files in `/web` — ideal for Vercel.
- Backend: FastAPI app in `/backend/app/main.py` — ideal for Railway or any container host.

Deploy frontend to Vercel
1. Log in to Vercel and import this GitHub repo.
2. Set the root to the repository (no build step needed). `vercel.json` routes `/` to `/web/index.html`.

Deploy backend to Railway (or any container host)
1. Create a new service on Railway and connect the GitHub repo, or deploy using Docker.
2. Railway sets a `PORT` env var; the `Dockerfile` uses it. If using Railway's GitHub deploy, set the start command to:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Local run (backend):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Local run (frontend):

```bash
# Serve static files; simplest: use Python http.server
cd web
python -m http.server 3000
# then open http://localhost:3000
```

Notes
- The ML model weights are not included here. The backend exposes `/compile-gui` which accepts `.gui` files (token lists) and uses the repository `Compiler` to convert them to HTML. To add image->HTML inference, integrate a model server and update the API.
