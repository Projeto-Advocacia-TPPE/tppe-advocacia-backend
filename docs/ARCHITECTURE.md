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
│   ├── users/      test_user_service.py
│   ├── auth/       test_auth_service.py, test_auth_deps.py
│   ├── health/     test_health_controller.py
│   └── shared/     test_responses.py
├── integration/
│   └── users/      test_user_repository.py
└── e2e/
    ├── users/      test_users.py
    ├── auth/       test_auth.py
    └── health/     test_health.py
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
