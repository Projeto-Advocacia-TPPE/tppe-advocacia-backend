# Backend

API base em FastAPI com organização MVC e Postgres.

## Estrutura

```text
.
├── app/
│   ├── controllers/
│   ├── core/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   └── views/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Rodando com Docker

```bash
cp .env.example .env
docker compose up --build
```

## Endpoints iniciais

- `GET /api/v1/health`
- `GET /api/v1/leads`
- `POST /api/v1/leads`
