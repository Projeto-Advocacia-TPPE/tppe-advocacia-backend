# Arquitetura

Este projeto segue o padrão **Modular Monolith** com camadas internas por módulo. Cada domínio (users, leads, auth, health) é uma pasta autônoma com suas próprias camadas — model, schema, repository, service, controller e router. Código verdadeiramente compartilhado entre módulos fica em `shared/`.

---

## Estrutura de pastas

```
app/
├── main.py                        # ponto de entrada da aplicação
├── config/
│   └── settings.py                # configurações e variáveis de ambiente
├── db/
│   └── database.py                # conexão com o banco de dados
├── scheduler/                     # APScheduler — jobs agendados (cron)
│   ├── scheduler.py               # setup/start/shutdown do BackgroundScheduler
│   └── jobs.py                    # deadline alerts + DataJud sync jobs
├── shared/                        # código transversal entre módulos
│   ├── base_model.py              # DeclarativeBase do SQLAlchemy
│   ├── exceptions.py              # exceções customizadas (AppException e subclasses)
│   ├── responses.py               # envelope padrão de resposta da API
│   └── auth_deps.py               # dependências de autenticação (get_current_user, require_admin)
├── modules/
│   ├── users/                     # domínio de usuários
│   │   ├── model.py               # ORM: User, Role
│   │   ├── schema.py              # DTOs: UserCreate, UserRead, UserUpdate
│   │   ├── repository.py          # queries de usuário
│   │   ├── service.py             # regras de negócio de usuário
│   │   ├── controller.py          # orquestração
│   │   └── router.py              # rotas HTTP /users
│   ├── leads/                     # domínio de leads
│   │   ├── model.py
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   └── router.py
│   ├── auth/                      # autenticação
│   │   ├── schema.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   └── router.py
│   ├── office_config/             # configurações institucionais
│   │   ├── model.py
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   └── router.py
│   ├── audit_logs/                # log de auditoria
│   │   ├── model.py
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   └── router.py
│   ├── media/                     # upload e servimento de arquivos
│   │   ├── schema.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   ├── router.py
│   │   └── storage/
│   │       ├── protocol.py        # StorageProvider (Protocol)
│   │       └── local.py           # LocalStorageProvider
│   ├── email/                     # envio de e-mail
│   │   ├── protocol.py            # EmailService (Protocol)
│   │   ├── resend_service.py      # implementação Resend
│   │   └── fake_service.py        # implementação fake para testes
│   ├── datajud/                   # integração com API pública DataJud (US-20)
│   │   ├── protocol.py            # DataJudClient (Protocol)
│   │   ├── datajud_service.py     # implementação real via httpx
│   │   ├── fake_service.py        # implementação fake para testes
│   │   ├── service.py             # sync manual/lote, dedup e persistência
│   │   ├── controller.py
│   │   └── router.py              # /processes/{id}/sync, /datajud/sync-active-processes
│   ├── external_api_logs/         # logs de sucesso/falha de integrações externas
│   │   ├── model.py               # ORM: ExternalApiLog
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   ├── notifier.py            # notifica admins em falhas via notifications
│   │   └── router.py              # GET /external-api-logs (admin)
│   ├── notifications/             # preferências e disparo de notificações por e-mail
│   │   ├── model.py               # ORM: NotificationPreference
│   │   ├── schema.py              # EventType, PreferencesRead, PreferencesUpdate
│   │   ├── repository.py
│   │   ├── service.py             # notify(user_id, event_type, payload)
│   │   ├── controller.py
│   │   ├── router.py              # GET/PATCH /notifications/preferences
│   │   └── templates/             # subject + body por evento
│   ├── forensic_holidays/         # feriados forenses (nacional, court, comarca)
│   │   ├── model.py               # ORM: ForensicHoliday, HolidayScope
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   ├── router.py              # /forensic-holidays (GET autenticado, CUD admin)
│   │   ├── data/holidays.json     # nacionais + recesso + TJDFT
│   │   └── seed.py                # `python -m app.modules.forensic_holidays.seed`
│   ├── deadlines/                 # cálculo, persistência e alertas de prazos
│   │   ├── model.py               # ORM: Deadline, DeadlineAlert
│   │   ├── schema.py              # DeadlineCalculate*, DeadlineCreate/Update/Read, DeadlineAlertRead
│   │   ├── repository.py          # DeadlineRepository, DeadlineAlertRepository
│   │   ├── service.py             # calculate_due_date, business_days_until, dispatch_alerts
│   │   ├── controller.py
│   │   └── router.py              # /deadlines/calculate, /processes/{id}/deadlines, /deadlines/{id}, .../alerts
│   ├── appointments/              # agenda de compromissos (CRUD pessoal)
│   │   ├── model.py               # ORM: Appointment, AppointmentType
│   │   ├── schema.py              # AppointmentCreate/Update/Read
│   │   ├── repository.py
│   │   ├── service.py             # CRUD + validação de refs + autorização + sync Google
│   │   ├── controller.py
│   │   └── router.py              # /appointments, /appointments/{id}
│   ├── google_calendar/           # integração OAuth + sync com Google Calendar
│   │   ├── model.py               # ORM: GoogleCredential
│   │   ├── schema.py
│   │   ├── repository.py
│   │   ├── crypto.py              # TokenCipher (Fernet) p/ o refresh_token
│   │   ├── protocol.py            # GoogleCalendarClient (Protocol)
│   │   ├── google_service.py      # impl real (Google Calendar API)
│   │   ├── fake_service.py        # impl fake para testes
│   │   ├── oauth.py               # fluxo OAuth (auth URL, troca de code)
│   │   ├── service.py             # GoogleCalendarService + sync_appointment
│   │   ├── controller.py
│   │   └── router.py              # /integrations/google/*
│   ├── tasks/                     # tarefas em Kanban (CRUD + move atômico)
│   │   ├── model.py               # ORM: Task, TaskStatus, TaskPriority
│   │   ├── schema.py              # TaskCreate, TaskUpdate, TaskMove, TaskRead
│   │   ├── repository.py          # CRUD + reordenação atômica em transação
│   │   ├── service.py             # valida referências, dispara TASK_ASSIGNED
│   │   ├── controller.py
│   │   └── router.py              # /tasks, /tasks/{id}, /tasks/{id}/move
│   └── health/                    # health check
│       ├── schema.py
│       ├── controller.py
│       └── router.py
└── api/
    └── router.py                  # agrega todos os modules/*/router.py
```

```
tests/
├── unit/
│   ├── users/         test_user_service.py
│   ├── auth/          test_auth_service.py
│   ├── health/        test_health_controller.py
│   ├── media/         test_media_service.py, test_local_storage.py
│   ├── office_config/ test_office_config_service.py
│   ├── audit_logs/    test_audit_log_service.py
│   └── shared/        test_responses.py, test_auth_deps.py
├── integration/
│   ├── users/         test_user_repository.py
│   ├── office_config/ test_office_config_repository.py
└── e2e/
    ├── users/         test_users.py
    ├── auth/          test_auth.py
    ├── health/        test_health.py
    ├── media/         test_media.py
    └── office_config/ test_office_config.py
```

---

## Camadas e responsabilidades

Cada módulo em `modules/` contém as mesmas camadas internas:

### `router.py` — Rotas (entrada HTTP)

Ponto de entrada de cada requisição. Define os endpoints, aplica os schemas de validação de entrada e delega ao controller. Não contém lógica de negócio.

### `controller.py` — Orquestração

Coordena o fluxo entre service e schemas. Recebe dados já validados da rota, chama o service e retorna a resposta serializada. Não acessa o banco diretamente.

### `service.py` — Regras de negócio

Concentra a lógica do domínio: validações de negócio, cálculos, decisões. Usa o repository para persistência. É a camada mais importante e deve ter maior cobertura de testes.

### `repository.py` — Acesso a dados

Responsável exclusivamente por interagir com o banco: queries, inserções, atualizações e deleções. Recebe e retorna models ORM. Não conhece regras de negócio.

### `model.py` — Modelo ORM

Define o esquema do banco de dados via SQLAlchemy. Representa a entidade persistida. Herda de `shared/base_model.py`.

### `schema.py` — Contratos de entrada e saída

Schemas Pydantic que definem o formato esperado nas requisições e nas respostas. Funcionam como DTOs e desacoplam a camada HTTP dos models internos.

---

## `shared/` — Código transversal

Código que pertence a nenhum módulo específico, mas é usado por vários:

- **`base_model.py`** — `DeclarativeBase` do SQLAlchemy; todos os models herdam daqui
- **`exceptions.py`** — `AppException` e subclasses; lançadas nos services, convertidas pelo handler global
- **`responses.py`** — `SuccessResponse[T]`, `PaginatedResponse[T]`, `ErrorResponse`; helpers `ok()`, `paginated()`, `error_responses()`
- **`auth_deps.py`** — `get_current_user()` e `require_admin()`; injetados via `Depends()` nas rotas

---

## Fluxo de uma requisição

```
HTTP Request
  └─► modules/*/router.py                      valida entrada com schema
        └─► modules/*/controller               orquestra a operação
              └─► modules/*/service            aplica regras de negócio
                    └─► modules/*/repository   executa query no banco
                          └─► modules/*/model  entidade ORM
  ◄── HTTP Response
        schema serializa a saída
```

---

## Padrão de resposta

Definido em `app/shared/responses.py`. Três tipos de envelope:

### Sucesso simples — `SuccessResponse[T]`

```json
{ "success": true, "data": { ... } }
```

Usar o helper `ok(data)` nas rotas.

### Sucesso paginado — `PaginatedResponse[T]`

```json
{
  "success": true,
  "data": [ ... ],
  "meta": { "total": 100, "page": 1, "limit": 10, "pages": 10 }
}
```

Usar o helper `paginated(items, total, page, limit)` nas rotas.

### Erro — `ErrorResponse`

```json
{ "success": false, "error": { "code": "ERROR_CODE", "message": "mensagem legível" } }
```

Erros de negócio devem ser lançados como subclasses de `AppException` (definidas em `app/shared/exceptions.py`). O handler global converte para `ErrorResponse` automaticamente. Nunca usar `HTTPException` diretamente nos services.

Erros disponíveis:

| Classe                    | HTTP | `code`                 |
| ------------------------- | ---- | ---------------------- |
| `InvalidCredentialsError` | 401  | `INVALID_CREDENTIALS`  |
| `InactiveUserError`       | 403  | `INACTIVE_USER`        |
| `UnauthorizedError`       | 401  | `UNAUTHORIZED`         |
| `ForbiddenError`          | 403  | `FORBIDDEN`            |
| `UserNotFoundError`       | 404  | `USER_NOT_FOUND`       |
| `EmailAlreadyExistsError` | 409  | `EMAIL_ALREADY_EXISTS` |

Para documentar respostas de erro no Swagger, usar o helper `error_responses(*codes)`:

```python
@router.get("/exemplo", responses=error_responses(401, 403, 404))
```

---

## Injeção de dependência

O projeto usa injeção manual (sem framework de DI). O padrão é:

```
router.py  →  resolve dependências via Depends()  →  instancia Controller inline
controller.py  →  constrói o grafo (Repository → Service)  →  expõe métodos
service.py  →  recebe dependências já construídas no __init__
```

### Regras

**Router** — resolve dependências externas via `Depends` (db, email, auth) e instancia o controller diretamente no corpo da rota:

```python
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse[UserRead]:
    return ok(UserController(db, email).create_user(payload, created_by=current_user))
```

**Controller** — recebe dependências resolvidas, monta o grafo internamente, não acessa `Session` diretamente após o `__init__`:

```python
class UserController:
    def __init__(self, db: Session, email: EmailService) -> None:
        self.service = UserService(
            UserRepository(db),
            email,
            AuditLogService(AuditLogRepository(db)),
        )
```

**Service** — recebe repositórios e serviços já construídos, nunca recebe `Session`:

```python
class UserService:
    def __init__(self, repository: UserRepository, email: EmailService, audit: AuditLogService) -> None:
        self.repository = repository
        self.email = email
        self.audit = audit
```

**Repository** — único ponto que recebe `Session`:

```python
class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
```

### Módulos sem banco de dados

Módulos sem persistência (ex: `media`) não recebem `db`. O controller aceita a dependência de infraestrutura como parâmetro opcional, com o provider padrão como fallback:

```python
class MediaController:
    def __init__(self, storage: StorageProvider | None = None) -> None:
        self.service = MediaService(storage or LocalStorageProvider())
```

Isso mantém o controller testável (passa mock de `storage`) sem exigir injeção via FastAPI.

### O que não fazer

- **Service receber `Session` diretamente** — quem constrói repositories é o controller, não o service
- **Controller hardcodar providers internamente sem parâmetro** — impede mock em testes
- **Router instanciar repositories ou services** — responsabilidade do controller

---

## Adicionando um novo módulo

Para cada nova história de usuário que introduz um novo domínio (ex: `email`):

1. Criar pasta `app/modules/email/`
2. Criar os arquivos: `model.py`, `schema.py`, `repository.py`, `service.py`, `controller.py`, `router.py`
3. Registrar o router em `app/api/router.py`
4. Criar testes em `tests/unit/email/`, `tests/integration/email/`, `tests/e2e/email/`

Zero toque em código de outros módulos.

---

## Princípios que guiam as decisões

- **Módulo autônomo:** cada módulo contém todas as suas camadas; mudança em um módulo não toca outros.
- **Regras de negócio no service:** nenhuma lógica de domínio nos controllers, rotas ou repositories.
- **Schemas desacoplados dos models:** nunca expor diretamente um model ORM na resposta da API.
- **Repository como única porta para o banco:** nenhuma query fora do repository.
- **Dependências entre módulos apenas quando semânticas e unidirecionais:** evitar acoplamento arbitrário entre módulos. Dependências circulares são proibidas. Dependências com relação de domínio clara são permitidas (ex: `auth` depende de `users` porque autentica usuários, já o inverso não existe).
- **Erros via exceções customizadas:** toda falha de negócio deve ser lançada como subclasse de `AppException`; nunca usar `HTTPException` diretamente nos services.
- **Versionamento de rotas:** toda rota pública fica sob `/api/v1/` para permitir evolução sem quebrar contratos.
