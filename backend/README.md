# Aura Bell Backend

FastAPI backend for the Aura Bell multi-store e-commerce platform
(Best Gadget & Aura Skin Care). Supabase PostgreSQL is the hosted database.

## Run with Docker

```bash
cp .env.example .env   # fill in real values
docker compose build
docker compose up -d
```

Health check: `http://localhost:8000/api/v1/health`

## Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `http://localhost:8000/api/v1/health`