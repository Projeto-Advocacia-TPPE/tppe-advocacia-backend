# Endpoints

Todas as respostas seguem o envelope `APIResponse[T]`. Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para detalhes do padrão.

---

## Health

### `GET /api/v1/health`

Verifica a saúde da API e a conectividade com o banco de dados.

**Resposta 200**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "app_name": "Advocacia API",
    "version": "0.1.0",
    "database": "ok"
  },
  "error": null
}
```

---

## Leads

### `GET /api/v1/leads`

Lista todos os leads cadastrados.

**Resposta 200**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "João Silva",
      "email": "joao@email.com",
      "phone": "11999999999",
      "message": "Preciso de ajuda.",
      "status": "novo",
      "created_at": "2026-05-06T12:00:00Z",
      "updated_at": "2026-05-06T12:00:00Z"
    }
  ]
}
```

---

### `POST /api/v1/leads`

Cria um novo lead.

**Body**
```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "phone": "11999999999",
  "message": "Preciso de ajuda."
}
```

**Resposta 201**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "11999999999",
    "message": "Preciso de ajuda.",
    "status": "novo",
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T12:00:00Z"
  }
}
```

---

## Auth

### `POST /api/v1/auth/login`

Autentica um usuário com e-mail e senha e retorna um JWT de acesso.

**Body**
```json
{
  "email": "usuario@email.com",
  "password": "senha123"
}
```

**Resposta 200**
```json
{
  "success": true,
  "data": {
    "access_token": "<jwt>",
    "token_type": "bearer"
  }
}
```

**Erros**

| Status | Code | Situação |
|--------|------|----------|
| 401 | `INVALID_CREDENTIALS` | E-mail não encontrado ou senha incorreta |
| 403 | `INACTIVE_USER` | Usuário desativado |
| 422 | `VALIDATION_ERROR` | Body inválido (e-mail malformado, campos ausentes) |

**Resposta de erro (exemplo)**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid credentials"
  }
}
```

---

## Users

> Todos os endpoints abaixo exigem autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

---

### `GET /api/v1/users`

Lista usuários com filtros opcionais e paginação.

**Query params**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `role` | `ADMIN` \| `USER` | Não | Filtra por papel |
| `is_active` | `boolean` | Não | Filtra por status de ativação |
| `page` | `integer` (≥ 1) | Não | Página atual (default: `1`) |
| `limit` | `integer` (1–100) | Não | Itens por página (default: `20`) |

**Resposta 200**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Ana Lima",
      "email": "ana@escritorio.com",
      "role": "ADMIN",
      "is_active": true,
      "created_at": "2026-05-06T12:00:00Z",
      "updated_at": "2026-05-06T12:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Erros**

| Status | Code | Situação |
|--------|------|----------|
| 401 | `UNAUTHORIZED` | Token ausente ou inválido |
| 403 | `FORBIDDEN` | Usuário autenticado não é ADMIN |

---

### `POST /api/v1/users`

Cria um novo usuário. O sistema gera a senha temporária e a registra no log do servidor.

**Body**
```json
{
  "name": "Carlos Souza",
  "email": "carlos@escritorio.com",
  "role": "USER"
}
```

**Resposta 201**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Carlos Souza",
    "email": "carlos@escritorio.com",
    "role": "USER",
    "is_active": true,
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T12:00:00Z"
  }
}
```

**Erros**

| Status | Code | Situação |
|--------|------|----------|
| 401 | `UNAUTHORIZED` | Token ausente ou inválido |
| 403 | `FORBIDDEN` | Usuário autenticado não é ADMIN |
| 409 | `EMAIL_ALREADY_EXISTS` | E-mail já cadastrado |
| 422 | `VALIDATION_ERROR` | Body inválido |

---

### `GET /api/v1/users/{id}`

Retorna os dados de um usuário específico.

**Resposta 200**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Carlos Souza",
    "email": "carlos@escritorio.com",
    "role": "USER",
    "is_active": true,
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T12:00:00Z"
  }
}
```

**Erros**

| Status | Code | Situação |
|--------|------|----------|
| 401 | `UNAUTHORIZED` | Token ausente ou inválido |
| 403 | `FORBIDDEN` | Usuário autenticado não é ADMIN |
| 404 | `USER_NOT_FOUND` | ID não encontrado |

---

### `PATCH /api/v1/users/{id}`

Atualiza parcialmente os dados de um usuário. Todos os campos são opcionais.
Usado também para **desativar** (`is_active: false`) e **alterar o papel** (`role`).

**Body**
```json
{
  "name": "Carlos Souza Atualizado",
  "email": "novo@escritorio.com",
  "role": "ADMIN",
  "is_active": false
}
```

**Resposta 200**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Carlos Souza Atualizado",
    "email": "novo@escritorio.com",
    "role": "ADMIN",
    "is_active": false,
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T13:00:00Z"
  }
}
```

**Erros**

| Status | Code | Situação |
|--------|------|----------|
| 401 | `UNAUTHORIZED` | Token ausente ou inválido |
| 403 | `FORBIDDEN` | Usuário autenticado não é ADMIN |
| 404 | `USER_NOT_FOUND` | ID não encontrado |
| 409 | `EMAIL_ALREADY_EXISTS` | Novo e-mail já está em uso por outro usuário |
| 422 | `VALIDATION_ERROR` | Body inválido |
