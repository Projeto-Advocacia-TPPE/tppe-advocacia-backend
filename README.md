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

## DataJud

A integração com a API pública do DataJud usa `DATAJUD_API_KEY` e `DATAJUD_BASE_URL` do `.env`. Para sincronização automática, o APScheduler registra um job recorrente configurado por `DATAJUD_SYNC_INTERVAL_HOURS` (default `6`) e `DATAJUD_SYNC_LIMIT` (default `50`).

Cada processo pode salvar `tribunal_alias` (ex.: `tjsp`). A sincronização manual fica em `POST /api/v1/processes/{process_id}/sync`; a sincronização em lote fica em `POST /api/v1/datajud/sync-active-processes` para admins. Movimentações importadas entram como `source = SYSTEM` e usam `external_id` para deduplicação.

Também existe o script agendável externo:

```bash
python scripts/sync_datajud_active_processes.py --limit 50
```

## Rodando com Docker

```bash
cp .env.example .env
docker compose up --build
```

Se as portas `8000` ou `5432` já estiverem em uso, ajuste `API_HOST_PORT` e `POSTGRES_PORT` no `.env` antes de subir os containers.
