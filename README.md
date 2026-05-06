# Backend

API base em FastAPI com organização MVC + Camadas e Postgres.

## Rodando localmente

```bash
cp .env.example .env
docker compose up -d db
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

O modo local precisa do Postgres disponível. O caminho mais simples é subir apenas o serviço `db` com `docker compose up -d db` antes de iniciar o `uvicorn`.

## Rodando com Docker

```bash
cp .env.example .env
docker compose up --build
```

Se as portas `8000` ou `5432` já estiverem em uso, ajuste `API_HOST_PORT` e `POSTGRES_PORT` no `.env` antes de subir os containers.
