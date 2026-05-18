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
  }
}
```

---

## Leads

### `GET /api/v1/leads`

Lista leads com filtros opcionais e paginação.

> Exige autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

**Query params**

| Parâmetro     | Tipo                                                    | Obrigatório | Descrição                        |
| ------------- | ------------------------------------------------------- | ----------- | -------------------------------- |
| `status`      | `novo` \| `em_atendimento` \| `fechado` \| `descartado` | Não         | Filtra por status                |
| `assigned_to` | `integer`                                               | Não         | Filtra por ID do responsável     |
| `page`        | `integer` (≥ 1)                                         | Não         | Página atual (default: `1`)      |
| `limit`       | `integer` (1–100)                                       | Não         | Itens por página (default: `20`) |

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
      "assigned_to": null,
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

| Status | Code           | Situação                        |
| ------ | -------------- | ------------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido       |
| 403    | `FORBIDDEN`    | Usuário autenticado não é ADMIN |

---

### `POST /api/v1/leads`

Cria um novo lead originado do formulário de contato. Público — não exige autenticação.

Leads com o mesmo e-mail enviados dentro da janela configurada (`LEAD_DEDUP_WINDOW_HOURS`, padrão: `1h`) são rejeitados com 409.

**Body**

```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "phone": "11999999999",
  "message": "Preciso de ajuda."
}
```

> `phone` e `message` são opcionais.

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
    "assigned_to": null,
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T12:00:00Z"
  }
}
```

**Erros**

| Status | Code               | Situação                                         |
| ------ | ------------------ | ------------------------------------------------ |
| 409    | `LEAD_DUPLICATE`   | Mesmo e-mail submetido dentro da janela de dedup |
| 422    | `VALIDATION_ERROR` | Body inválido                                    |

---

### `PATCH /api/v1/leads/{lead_id}`

Atualiza o status ou o responsável de um lead. Todos os campos são opcionais.

> Exige autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

**Body**

```json
{
  "status": "em_atendimento",
  "assigned_to": 2
}
```

> `status`: `"novo"` | `"em_atendimento"` | `"fechado"` | `"descartado"`
> `assigned_to`: ID de um usuário cadastrado, ou `null` para desatribuir.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "11999999999",
    "message": "Preciso de ajuda.",
    "status": "em_atendimento",
    "assigned_to": 2,
    "created_at": "2026-05-06T12:00:00Z",
    "updated_at": "2026-05-06T13:00:00Z"
  }
}
```

**Erros**

| Status | Code               | Situação                        |
| ------ | ------------------ | ------------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido       |
| 403    | `FORBIDDEN`        | Usuário autenticado não é ADMIN |
| 404    | `LEAD_NOT_FOUND`   | Lead não encontrado             |
| 422    | `VALIDATION_ERROR` | Body inválido                   |

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

| Status | Code                  | Situação                                           |
| ------ | --------------------- | -------------------------------------------------- |
| 401    | `INVALID_CREDENTIALS` | E-mail não encontrado ou senha incorreta           |
| 403    | `INACTIVE_USER`       | Usuário desativado                                 |
| 422    | `VALIDATION_ERROR`    | Body inválido (e-mail malformado, campos ausentes) |

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

### `POST /api/v1/auth/password-reset/request`

Solicita o envio de e-mail com link para redefinição de senha. Sempre retorna 200, mesmo que o e-mail não exista, para não expor se o usuário está cadastrado.

**Body**

```json
{
  "email": "usuario@email.com"
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": null
}
```

**Erros**

| Status | Code               | Situação      |
| ------ | ------------------ | ------------- |
| 422    | `VALIDATION_ERROR` | Body inválido |

---

### `POST /api/v1/auth/password-reset/confirm`

Confirma a redefinição de senha usando o token recebido por e-mail. O token é de uso único e expira após o prazo configurado.

**Body**

```json
{
  "token": "<token-recebido-por-email>",
  "new_password": "novaSenha123"
}
```

> `new_password` deve ter no mínimo 8 caracteres.

**Resposta 200**

```json
{
  "success": true,
  "data": null
}
```

**Erros**

| Status | Code                  | Situação                                |
| ------ | --------------------- | --------------------------------------- |
| 400    | `INVALID_RESET_TOKEN` | Token inválido, inexistente ou expirado |
| 422    | `VALIDATION_ERROR`    | Body inválido                           |

---

## Users

> Todos os endpoints abaixo exigem autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

---

### `GET /api/v1/users`

Lista usuários com filtros opcionais e paginação.

**Query params**

| Parâmetro   | Tipo              | Obrigatório | Descrição                        |
| ----------- | ----------------- | ----------- | -------------------------------- |
| `role`      | `ADMIN` \| `USER` | Não         | Filtra por papel                 |
| `is_active` | `boolean`         | Não         | Filtra por status de ativação    |
| `page`      | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`     | `integer` (1–100) | Não         | Itens por página (default: `20`) |

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

| Status | Code           | Situação                        |
| ------ | -------------- | ------------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido       |
| 403    | `FORBIDDEN`    | Usuário autenticado não é ADMIN |

---

### `POST /api/v1/users`

Cria um novo usuário. O sistema gera a senha temporária e a registra no log do servidor.

**Body**

```json
{
  "name": "Carlos Souza",
  "email": "carlos@escritorio.com"
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

| Status | Code                   | Situação                        |
| ------ | ---------------------- | ------------------------------- |
| 401    | `UNAUTHORIZED`         | Token ausente ou inválido       |
| 403    | `FORBIDDEN`            | Usuário autenticado não é ADMIN |
| 409    | `EMAIL_ALREADY_EXISTS` | E-mail já cadastrado            |
| 422    | `VALIDATION_ERROR`     | Body inválido                   |

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

| Status | Code             | Situação                        |
| ------ | ---------------- | ------------------------------- |
| 401    | `UNAUTHORIZED`   | Token ausente ou inválido       |
| 403    | `FORBIDDEN`      | Usuário autenticado não é ADMIN |
| 404    | `USER_NOT_FOUND` | ID não encontrado               |

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

---

## Media

> Upload exige autenticação (qualquer role).
> Header obrigatório: `Authorization: Bearer <token>`

### `POST /api/v1/media/upload`

Faz upload de uma imagem. Retorna a URL pública para acesso ao arquivo.

**Content-Type:** `multipart/form-data`

**Body**

| Campo  | Tipo   | Obrigatório | Descrição         |
| ------ | ------ | ----------- | ----------------- |
| `file` | `file` | Sim         | Arquivo de imagem |

**Tamanho máximo:** configurável via `MAX_FILE_SIZE_MB` (padrão: 5 MB)

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "url": "http://localhost:8000/api/v1/media/3f2a1b4c-uuid.jpg"
  }
}
```

**Erros**

| Status | Code                | Situação                                  |
| ------ | ------------------- | ----------------------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido                 |
| 413    | `FILE_TOO_LARGE`    | Arquivo excede o tamanho máximo permitido |
| 415    | `INVALID_MIME_TYPE` | Tipo de arquivo não permitido             |
| 422    | `VALIDATION_ERROR`  | Campo `file` ausente                      |

---

### `GET /api/v1/media/{filename}`

Serve o arquivo de imagem pelo nome retornado no upload. Público — não exige autenticação.

**Path param**

| Parâmetro  | Tipo     | Descrição                           |
| ---------- | -------- | ----------------------------------- |
| `filename` | `string` | Nome do arquivo retornado no upload |

**Resposta 200**

Retorna o binário do arquivo com o `Content-Type` correspondente.

**Erros**

| Status | Code              | Situação               |
| ------ | ----------------- | ---------------------- |
| 404    | `MEDIA_NOT_FOUND` | Arquivo não encontrado |

---

## Audit Logs

> Exige autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

### `GET /api/v1/audit-logs`

Lista logs de auditoria com filtros opcionais e paginação.

**Query params**

| Parâmetro   | Tipo                                 | Obrigatório | Descrição                            |
| ----------- | ------------------------------------ | ----------- | ------------------------------------ |
| `action`    | `USER_CREATED` \| `USER_DEACTIVATED` | Não         | Filtra por tipo de ação              |
| `date_from` | `datetime` (ISO 8601)                | Não         | Filtra registros a partir desta data |
| `date_to`   | `datetime` (ISO 8601)                | Não         | Filtra registros até esta data       |
| `page`      | `integer` (≥ 1)                      | Não         | Página atual (default: `1`)          |
| `limit`     | `integer` (1–100)                    | Não         | Itens por página (default: `20`)     |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "action": "USER_CREATED",
      "performed_by_id": 1,
      "performed_by_name": "Ana Lima",
      "target_user_id": 2,
      "target_user_name": "Carlos Souza",
      "target_user_email": "carlos@escritorio.com",
      "target_user_role": "USER",
      "created_at": "2026-05-16T14:00:00Z"
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

| Status | Code           | Situação                        |
| ------ | -------------- | ------------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido       |
| 403    | `FORBIDDEN`    | Usuário autenticado não é ADMIN |

---

## Office Config

### `GET /api/v1/office-config`

Retorna a configuração atual do escritório. Público — não exige autenticação.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "office_name": "Escritório Silva Advocacia",
    "cnpj": "00.000.000/0001-00",
    "address": "Rua das Flores, 123, São Paulo - SP",
    "phone": "11999999999",
    "email": "contato@escritorio.com",
    "instagram_url": "https://instagram.com/escritorio",
    "linkedin_url": "https://linkedin.com/company/escritorio",
    "whatsapp_url": "https://wa.me/5511999999999",
    "hero_title": "Defendendo seus direitos",
    "hero_subtitle": "Com experiência e dedicação",
    "hero_image_url": "https://cdn.exemplo.com/hero.jpg",
    "about_title": "Sobre nós",
    "about_description": "Somos um escritório especializado...",
    "about_image_url": "https://cdn.exemplo.com/about.jpg",
    "lawyer_name": "Dr. João Silva",
    "lawyer_oab": "OAB/SP 123456",
    "lawyer_description": "Especialista em direito civil...",
    "lawyer_image_url": "https://cdn.exemplo.com/lawyer.jpg",
    "differentials": [{ "title": "Atendimento humanizado", "description": "..." }],
    "areas_of_practice": [{ "title": "Direito Civil", "description": "..." }]
  }
}
```

---

### `PATCH /api/v1/office-config`

Atualiza parcialmente a configuração do escritório. Todos os campos são opcionais.

> Exige autenticação com role `ADMIN`.
> Header obrigatório: `Authorization: Bearer <token>`

**Body**

```json
{
  "office_name": "Novo Nome",
  "cnpj": "00.000.000/0001-00",
  "address": "Rua Nova, 456, São Paulo - SP",
  "phone": "11988888888",
  "email": "novo@escritorio.com",
  "instagram_url": "https://instagram.com/novo",
  "linkedin_url": "https://linkedin.com/company/novo",
  "whatsapp_url": "https://wa.me/5511988888888",
  "hero_title": "Novo título",
  "hero_subtitle": "Novo subtítulo",
  "hero_image_url": "https://cdn.exemplo.com/hero-novo.jpg",
  "about_title": "Sobre nós atualizado",
  "about_description": "Descrição atualizada...",
  "about_image_url": "https://cdn.exemplo.com/about-novo.jpg",
  "lawyer_name": "Dra. Maria Santos",
  "lawyer_oab": "OAB/SP 654321",
  "lawyer_description": "Especialista em direito de família...",
  "lawyer_image_url": "https://cdn.exemplo.com/lawyer-novo.jpg",
  "differentials": [{ "title": "Agilidade", "description": "Respostas rápidas" }],
  "areas_of_practice": [{ "title": "Direito de Família", "description": "..." }]
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "office_name": "Novo Nome",
    "..."
  }
}
```

**Erros**

| Status | Code           | Situação                        |
| ------ | -------------- | ------------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido       |
| 403    | `FORBIDDEN`    | Usuário autenticado não é ADMIN |

---

## Articles

### `POST /api/v1/articles`

Cria um novo artigo. O autor é o usuário autenticado.

> Exige autenticação. Header: `Authorization: Bearer <token>`

**Body**

```json
{
  "title": "Direitos do Consumidor",
  "content": "Conteúdo completo do artigo...",
  "category": "Direito Civil",
  "summary": "Resumo opcional do artigo",
  "cover_image_url": "https://cdn.exemplo.com/capa.jpg",
  "status": "draft"
}
```

> `status`: `"draft"` (padrão) ou `"published"`. Campo `cover_image_url` é opcional.

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Direitos do Consumidor",
    "content": "Conteúdo completo do artigo...",
    "category": "Direito Civil",
    "summary": "Resumo opcional do artigo",
    "cover_image_url": "https://cdn.exemplo.com/capa.jpg",
    "status": "draft",
    "author_id": 3,
    "author_name": "Dr. João Silva",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T14:00:00Z"
  }
}
```

**Erros**

| Status | Code               | Situação                  |
| ------ | ------------------ | ------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido |
| 422    | `VALIDATION_ERROR` | Body inválido             |

---

### `PATCH /api/v1/articles/{article_id}`

Atualiza parcialmente um artigo. Todos os campos são opcionais. Usado também para publicar (`status: "published"`) ou reverter para rascunho (`status: "draft"`).

> Exige autenticação. Header: `Authorization: Bearer <token>`

**Body**

```json
{
  "title": "Título Atualizado",
  "content": "Novo conteúdo...",
  "category": "Direito Trabalhista",
  "summary": "Novo resumo",
  "cover_image_url": "https://cdn.exemplo.com/nova-capa.jpg",
  "status": "published"
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Título Atualizado",
    "content": "Novo conteúdo...",
    "category": "Direito Trabalhista",
    "summary": "Novo resumo",
    "cover_image_url": "https://cdn.exemplo.com/nova-capa.jpg",
    "status": "published",
    "author_id": 3,
    "author_name": "Dr. João Silva",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T15:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                  |
| ------ | ------------------- | ------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido |
| 404    | `ARTICLE_NOT_FOUND` | Artigo não encontrado     |
| 422    | `VALIDATION_ERROR`  | Body inválido             |

---

### `GET /api/v1/articles`

Lista artigos publicados com paginação. Público — não exige autenticação.

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                        |
| --------- | ----------------- | ----------- | -------------------------------- |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`) |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Direitos do Consumidor",
      "summary": "Resumo do artigo",
      "status": "published",
      "created_at": "2026-05-16T14:00:00Z",
      "url": "http://api.exemplo.com/api/v1/articles/1"
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

---

### `GET /api/v1/articles/{article_id}`

Retorna um artigo publicado pelo ID. Público — não exige autenticação. Retorna 404 se o artigo for rascunho.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Direitos do Consumidor",
    "content": "Conteúdo completo do artigo...",
    "category": "Direito Civil",
    "summary": "Resumo do artigo",
    "cover_image_url": "https://cdn.exemplo.com/capa.jpg",
    "status": "published",
    "author_id": 3,
    "author_name": "Dr. João Silva",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                                |
| ------ | ------------------- | --------------------------------------- |
| 404    | `ARTICLE_NOT_FOUND` | Artigo não encontrado ou ainda rascunho |

---

### `GET /api/v1/articles/{article_id}/preview`

Retorna um artigo independente do status (rascunho ou publicado). Usado para preview antes de publicar.

> Exige autenticação. Header: `Authorization: Bearer <token>`

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Direitos do Consumidor",
    "content": "Conteúdo completo do artigo...",
    "category": "Direito Civil",
    "summary": null,
    "cover_image_url": null,
    "status": "draft",
    "author_id": 3,
    "author_name": "Dr. João Silva",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                  |
| ------ | ------------------- | ------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido |
| 404    | `ARTICLE_NOT_FOUND` | Artigo não encontrado     |

---

### `GET /api/v1/articles/admin`

Lista todos os artigos incluindo rascunhos, com paginação. URLs dos itens apontam para o endpoint de preview.

> Exige autenticação. Header: `Authorization: Bearer <token>`

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                        |
| --------- | ----------------- | ----------- | -------------------------------- |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`) |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "title": "Artigo em Rascunho",
      "summary": null,
      "status": "draft",
      "created_at": "2026-05-16T13:00:00Z",
      "url": "http://api.exemplo.com/api/v1/articles/2/preview"
    }
  ],
  "meta": {
    "total": 5,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Erros**

| Status | Code           | Situação                  |
| ------ | -------------- | ------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido |

---

## Clients

> Todos os endpoints exigem autenticação (qualquer role).
> Header obrigatório: `Authorization: Bearer <token>`

---

### `POST /api/v1/clients`

Cria um novo cliente. CPF e CNPJ são mutuamente exclusivos — exatamente um deve ser informado. Ambos devem ser enviados sem formatação (só dígitos).

**Body**

```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "phone": "11999999999",
  "cpf": "12345678901",
  "address": "Rua das Flores, 123, São Paulo - SP"
}
```

> `email`, `phone` e `address` são opcionais.
> Usar `cnpj` (14 dígitos) no lugar de `cpf` (11 dígitos) para pessoa jurídica.

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "11999999999",
    "cpf": "12345678901",
    "cnpj": null,
    "address": "Rua das Flores, 123, São Paulo - SP",
    "created_by": 3,
    "updated_by": 3,
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                         | Situação                          |
| ------ | ---------------------------- | --------------------------------- |
| 401    | `UNAUTHORIZED`               | Token ausente ou inválido         |
| 409    | `CLIENT_CPF_ALREADY_EXISTS`  | CPF já cadastrado                 |
| 409    | `CLIENT_CNPJ_ALREADY_EXISTS` | CNPJ já cadastrado                |
| 422    | `VALIDATION_ERROR`           | Body inválido ou CPF/CNPJ ausente |

---

### `GET /api/v1/clients`

Lista clientes com paginação e busca opcional por nome (parcial, case-insensitive) ou CPF/CNPJ (exato).

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                                     |
| --------- | ----------------- | ----------- | --------------------------------------------- |
| `search`  | `string`          | Não         | Filtra por nome (parcial) ou CPF/CNPJ (exato) |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)                   |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`)              |

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
      "cpf": "12345678901",
      "cnpj": null
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

| Status | Code           | Situação                  |
| ------ | -------------- | ------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido |

---

### `GET /api/v1/clients/{id}`

Retorna dados completos de um cliente.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com",
    "phone": "11999999999",
    "cpf": "12345678901",
    "cnpj": null,
    "address": "Rua das Flores, 123, São Paulo - SP",
    "created_by": 3,
    "updated_by": 5,
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T15:00:00Z"
  }
}
```

**Erros**

| Status | Code               | Situação                  |
| ------ | ------------------ | ------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido |
| 404    | `CLIENT_NOT_FOUND` | Cliente não encontrado    |

---

### `PATCH /api/v1/clients/{id}`

Atualiza parcialmente um cliente. Todos os campos são opcionais. Não é permitido enviar `cpf` e `cnpj` simultaneamente.

**Body**

```json
{
  "name": "João Silva Atualizado",
  "email": "novo@email.com",
  "phone": "11988888888",
  "address": "Av. Paulista, 1000, São Paulo - SP"
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "João Silva Atualizado",
    "email": "novo@email.com",
    "phone": "11988888888",
    "cpf": "12345678901",
    "cnpj": null,
    "address": "Av. Paulista, 1000, São Paulo - SP",
    "created_by": 3,
    "updated_by": 5,
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T15:00:00Z"
  }
}
```

**Erros**

| Status | Code                         | Situação                           |
| ------ | ---------------------------- | ---------------------------------- |
| 401    | `UNAUTHORIZED`               | Token ausente ou inválido          |
| 404    | `CLIENT_NOT_FOUND`           | Cliente não encontrado             |
| 409    | `CLIENT_CPF_ALREADY_EXISTS`  | CPF já pertence a outro cliente    |
| 409    | `CLIENT_CNPJ_ALREADY_EXISTS` | CNPJ já pertence a outro cliente   |
| 422    | `VALIDATION_ERROR`           | Body inválido ou CPF e CNPJ juntos |

---

### `POST /api/v1/clients/{client_id}/notes`

Cria uma observação interna vinculada ao cliente. O autor é o usuário autenticado.

**Body**

```json
{
  "content": "Cliente prefere contato por WhatsApp."
}
```

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "client_id": 7,
    "created_by": 3,
    "updated_by": null,
    "created_by_name": "Ana Lima",
    "updated_by_name": null,
    "content": "Cliente prefere contato por WhatsApp.",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T14:00:00Z"
  }
}
```

**Erros**

| Status | Code               | Situação                   |
| ------ | ------------------ | -------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido  |
| 404    | `CLIENT_NOT_FOUND` | Cliente não encontrado     |
| 422    | `VALIDATION_ERROR` | `content` ausente ou vazio |

---

### `GET /api/v1/clients/{client_id}/notes`

Lista todas as observações do cliente em ordem cronológica decrescente (mais recente primeiro), com paginação.

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                        |
| --------- | ----------------- | ----------- | -------------------------------- |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`) |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "client_id": 7,
      "created_by": 5,
      "updated_by": 3,
      "created_by_name": "Carlos Souza",
      "updated_by_name": "Ana Lima",
      "content": "Reunião agendada para segunda-feira.",
      "created_at": "2026-05-16T15:00:00Z",
      "updated_at": "2026-05-16T16:00:00Z"
    },
    {
      "id": 1,
      "client_id": 7,
      "created_by": 3,
      "updated_by": null,
      "created_by_name": "Ana Lima",
      "updated_by_name": null,
      "content": "Cliente prefere contato por WhatsApp.",
      "created_at": "2026-05-16T14:00:00Z",
      "updated_at": "2026-05-16T14:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Erros**

| Status | Code               | Situação                  |
| ------ | ------------------ | ------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido |
| 404    | `CLIENT_NOT_FOUND` | Cliente não encontrado    |

---

### `PATCH /api/v1/clients/{client_id}/notes/{note_id}`

Edita o conteúdo de uma observação. Apenas o autor original pode editar; usuários com role `ADMIN` podem editar qualquer observação.

**Body**

```json
{
  "content": "Cliente prefere contato por e-mail, não WhatsApp."
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "client_id": 7,
    "created_by": 3,
    "updated_by": 3,
    "created_by_name": "Ana Lima",
    "updated_by_name": "Ana Lima",
    "content": "Cliente prefere contato por e-mail, não WhatsApp.",
    "created_at": "2026-05-16T14:00:00Z",
    "updated_at": "2026-05-16T17:00:00Z"
  }
}
```

**Erros**

| Status | Code                    | Situação                                             |
| ------ | ----------------------- | ---------------------------------------------------- |
| 401    | `UNAUTHORIZED`          | Token ausente ou inválido                            |
| 403    | `FORBIDDEN`             | Usuário não é o autor nem ADMIN                      |
| 404    | `CLIENT_NOT_FOUND`      | Cliente não encontrado                               |
| 404    | `CLIENT_NOTE_NOT_FOUND` | Observação não encontrada ou não pertence ao cliente |
| 422    | `VALIDATION_ERROR`      | `content` ausente ou vazio                           |

---

### `GET /api/v1/clients/{client_id}/timeline`

Retorna visão 360º do cliente: dados do cliente, notas recentes, processos vinculados (com última movimentação) e feed de atividades recentes (movimentações + notas mescladas e ordenadas por data).

**Query params**

| Parâmetro         | Tipo             | Obrigatório | Descrição                                                 |
| ----------------- | ---------------- | ----------- | --------------------------------------------------------- |
| `notes_limit`     | `integer` (1–50) | Não         | Máx. notas recentes do cliente (default: `10`)            |
| `processes_limit` | `integer` (1–50) | Não         | Máx. processos retornados (default: `20`)                 |
| `activity_limit`  | `integer` (1–50) | Não         | Máx. itens no feed de atividades recentes (default: `20`) |

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "client": {
      "id": 7,
      "name": "João Silva",
      "email": "joao@email.com",
      "phone": "11999999999",
      "cpf": "12345678901",
      "cnpj": null,
      "address": "Rua das Flores, 123, São Paulo - SP",
      "created_by": 3,
      "updated_by": 3,
      "created_at": "2026-05-16T14:00:00Z",
      "updated_at": "2026-05-16T14:00:00Z"
    },
    "notes": [
      {
        "id": 1,
        "client_id": 7,
        "created_by": 3,
        "updated_by": null,
        "created_by_name": "Ana Lima",
        "updated_by_name": null,
        "content": "Cliente prefere contato por WhatsApp.",
        "created_at": "2026-05-16T14:00:00Z",
        "updated_at": "2026-05-16T14:00:00Z"
      }
    ],
    "processes": [
      {
        "id": 1,
        "number": "1234567-89.2024.8.26.0100",
        "action_type": "Ação Cível",
        "court": "TJSP",
        "status": "ATIVO",
        "created_at": "2026-05-17T14:00:00Z",
        "last_movement": {
          "id": 2,
          "title": "Petição inicial protocolada",
          "occurred_at": "2026-05-15T09:00:00Z",
          "source": "MANUAL"
        }
      }
    ],
    "recent_activity": [
      {
        "kind": "movement",
        "process_id": 1,
        "note_id": null,
        "title": "Petição inicial protocolada",
        "content": null,
        "occurred_at": "2026-05-15T09:00:00Z",
        "actor_id": 3,
        "actor_name": "Ana Lima"
      },
      {
        "kind": "client_note",
        "process_id": null,
        "note_id": 1,
        "title": null,
        "content": "Cliente prefere contato por WhatsApp.",
        "occurred_at": "2026-05-16T14:00:00Z",
        "actor_id": 3,
        "actor_name": "Ana Lima"
      }
    ]
  }
}
```

> `notes` ordenadas por `created_at DESC`. `processes` ordenados por `created_at DESC`; `last_movement` é `null` quando o processo não tem movimentações. `recent_activity` mescla movimentações de todos os processos do cliente e notas do cliente, ordenado por `occurred_at DESC`. `kind` indica a origem: `"movement"` (movimentação de processo) ou `"client_note"` (observação do cliente).

**Erros**

| Status | Code               | Situação                  |
| ------ | ------------------ | ------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido |
| 404    | `CLIENT_NOT_FOUND` | Cliente não encontrado    |

---

## Processes

> Todos os endpoints exigem autenticação (qualquer role).
> Header obrigatório: `Authorization: Bearer <token>`

O campo `number` segue o padrão CNJ. Aceita tanto a forma mascarada (`NNNNNNN-DD.AAAA.J.TR.OOOO`) quanto apenas 20 dígitos no envio. Persistido como dígitos puros, retornado sempre mascarado.

---

### `POST /api/v1/processes`

Cria um novo processo judicial. Vincular a um cliente é opcional.

**Body**

```json
{
  "number": "1234567-89.2024.8.26.0100",
  "client_id": 7,
  "court": "TJSP",
  "action_type": "Ação Cível",
  "opposing_party": "Empresa X"
}
```

> `client_id` e `opposing_party` são opcionais. `number` aceita formato mascarado ou 20 dígitos.

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "number": "1234567-89.2024.8.26.0100",
    "client_id": 7,
    "client_name": "João Silva",
    "court": "TJSP",
    "action_type": "Ação Cível",
    "opposing_party": "Empresa X",
    "status": "ATIVO",
    "created_by": 3,
    "updated_by": 3,
    "created_at": "2026-05-17T14:00:00Z",
    "updated_at": "2026-05-17T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                            | Situação                               |
| ------ | ------------------------------- | -------------------------------------- |
| 401    | `UNAUTHORIZED`                  | Token ausente ou inválido              |
| 409    | `PROCESS_NUMBER_ALREADY_EXISTS` | Número CNJ já cadastrado               |
| 422    | `CLIENT_NOT_FOUND_FOR_PROCESS`  | `client_id` informado não existe       |
| 422    | `VALIDATION_ERROR`              | Body inválido ou número CNJ malformado |

---

### `GET /api/v1/processes`

Lista processos com filtros e paginação. Ordenado por `created_at DESC, id DESC`.

**Query params**

| Parâmetro   | Tipo                                                | Obrigatório | Descrição                                  |
| ----------- | --------------------------------------------------- | ----------- | ------------------------------------------ |
| `client_id` | `integer`                                           | Não         | Filtra por cliente                         |
| `status`    | `ATIVO` \| `SUSPENSO` \| `ARQUIVADO` \| `ENCERRADO` | Não         | Filtra por status                          |
| `search`    | `string`                                            | Não         | Busca parcial em `number` ou `action_type` |
| `page`      | `integer` (≥ 1)                                     | Não         | Página atual (default: `1`)                |
| `limit`     | `integer` (1–100)                                   | Não         | Itens por página (default: `20`)           |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "number": "1234567-89.2024.8.26.0100",
      "client_id": 7,
      "client_name": "João Silva",
      "court": "TJSP",
      "action_type": "Ação Cível",
      "status": "ATIVO",
      "created_at": "2026-05-17T14:00:00Z"
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

| Status | Code           | Situação                  |
| ------ | -------------- | ------------------------- |
| 401    | `UNAUTHORIZED` | Token ausente ou inválido |

---

### `GET /api/v1/processes/{process_id}`

Retorna dados completos de um processo.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "number": "1234567-89.2024.8.26.0100",
    "client_id": 7,
    "client_name": "João Silva",
    "court": "TJSP",
    "action_type": "Ação Cível",
    "opposing_party": "Empresa X",
    "status": "ATIVO",
    "created_by": 3,
    "updated_by": 3,
    "created_at": "2026-05-17T14:00:00Z",
    "updated_at": "2026-05-17T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                  |
| ------ | ------------------- | ------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido |
| 404    | `PROCESS_NOT_FOUND` | Processo não encontrado   |

---

### `GET /api/v1/clients/{client_id}/processes`

Lista processos vinculados a um cliente específico, com paginação.

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                        |
| --------- | ----------------- | ----------- | -------------------------------- |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`) |

**Resposta 200**

Mesmo formato de `GET /api/v1/processes`.

**Erros**

| Status | Code               | Situação                  |
| ------ | ------------------ | ------------------------- |
| 401    | `UNAUTHORIZED`     | Token ausente ou inválido |
| 404    | `CLIENT_NOT_FOUND` | Cliente não encontrado    |

---

### `POST /api/v1/processes/{process_id}/movements`

Registra uma movimentação manual no processo. Movimentações são imutáveis — tentativas de `PATCH`/`DELETE` retornam 405.

**Body**

```json
{
  "title": "Audiência de conciliação marcada",
  "description": "Audiência designada para 30/06/2026 às 14h.",
  "occurred_at": "2026-05-17T10:30:00Z"
}
```

> `description` é opcional (até 5000 caracteres). `occurred_at` é opcional — default = `now()` em UTC. Não pode estar no futuro.

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "process_id": 1,
    "title": "Audiência de conciliação marcada",
    "description": "Audiência designada para 30/06/2026 às 14h.",
    "occurred_at": "2026-05-17T10:30:00Z",
    "source": "MANUAL",
    "created_by": 3,
    "created_by_name": "Ana Lima",
    "created_at": "2026-05-17T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                                                      |
| ------ | ------------------- | ------------------------------------------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido                                     |
| 404    | `PROCESS_NOT_FOUND` | Processo não encontrado                                       |
| 422    | `VALIDATION_ERROR`  | `title` vazio/>150, `description` >5000, `occurred_at` futuro |

---

### `GET /api/v1/processes/{process_id}/movements`

Lista movimentações do processo em ordem cronológica decrescente (`occurred_at DESC, id DESC`), com paginação e filtros.

**Query params**

| Parâmetro   | Tipo                  | Obrigatório | Descrição                         |
| ----------- | --------------------- | ----------- | --------------------------------- |
| `source`    | `MANUAL` \| `SYSTEM`  | Não         | Filtra por origem da movimentação |
| `date_from` | `datetime` (ISO 8601) | Não         | Filtra `occurred_at >= date_from` |
| `date_to`   | `datetime` (ISO 8601) | Não         | Filtra `occurred_at <= date_to`   |
| `page`      | `integer` (≥ 1)       | Não         | Página atual (default: `1`)       |
| `limit`     | `integer` (1–100)     | Não         | Itens por página (default: `20`)  |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "process_id": 1,
      "title": "Petição inicial protocolada",
      "description": null,
      "occurred_at": "2026-05-15T09:00:00Z",
      "source": "MANUAL",
      "created_by": 3,
      "created_by_name": "Ana Lima",
      "created_at": "2026-05-17T14:05:00Z"
    },
    {
      "id": 1,
      "process_id": 1,
      "title": "Processo cadastrado",
      "description": null,
      "occurred_at": "2026-05-10T08:00:00Z",
      "source": "MANUAL",
      "created_by": 3,
      "created_by_name": "Ana Lima",
      "created_at": "2026-05-17T14:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Erros**

| Status | Code                | Situação                  |
| ------ | ------------------- | ------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido |
| 404    | `PROCESS_NOT_FOUND` | Processo não encontrado   |

---

### `PATCH /api/v1/processes/{process_id}/status`

Altera o status do processo e registra automaticamente uma movimentação `SYSTEM` na timeline. Toda transição entre os 4 valores é permitida (sem máquina de estados rígida). A atualização do processo e a criação da movimentação ocorrem na mesma transação — se uma falhar, nenhuma persiste.

**Body**

```json
{
  "status": "SUSPENSO",
  "reason": "Aguardando acordo extrajudicial."
}
```

> `status`: `"ATIVO"` | `"SUSPENSO"` | `"ARQUIVADO"` | `"ENCERRADO"`.
> `reason` é opcional (até 500 caracteres) e fica gravado como `description` na movimentação automática.

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "number": "1234567-89.2024.8.26.0100",
    "client_id": 7,
    "client_name": "João Silva",
    "court": "TJSP",
    "action_type": "Ação Cível",
    "opposing_party": "Empresa X",
    "status": "SUSPENSO",
    "created_by": 3,
    "updated_by": 5,
    "created_at": "2026-05-17T14:00:00Z",
    "updated_at": "2026-05-17T16:00:00Z",
    "last_status_change_movement_id": 42
  }
}
```

> `last_status_change_movement_id` aponta para a movimentação `SYSTEM` criada automaticamente, com `title = "Status alterado: <ANTERIOR> -> <NOVO>"` e `description = reason` (quando informado).

**Erros**

| Status | Code                        | Situação                                              |
| ------ | --------------------------- | ----------------------------------------------------- |
| 401    | `UNAUTHORIZED`              | Token ausente ou inválido                             |
| 404    | `PROCESS_NOT_FOUND`         | Processo não encontrado                               |
| 409    | `PROCESS_STATUS_UNCHANGED`  | Status enviado é igual ao status atual (idempotência) |
| 422    | `VALIDATION_ERROR`          | `status` fora do enum ou `reason` > 500 caracteres    |

---

### `POST /api/v1/processes/{process_id}/notes`

Cria uma anotação interna vinculada ao processo. O autor é o usuário autenticado. Notas são separadas das movimentações — não aparecem em `GET /processes/{id}/movements`.

**Body**

```json
{
  "content": "Estratégia: aguardar prazo recursal antes de protocolar contestação."
}
```

> `content` obrigatório, 1–5000 caracteres.

**Resposta 201**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "process_id": 1,
    "created_by": 3,
    "updated_by": null,
    "created_by_name": "Ana Lima",
    "updated_by_name": null,
    "content": "Estratégia: aguardar prazo recursal antes de protocolar contestação.",
    "created_at": "2026-05-17T14:00:00Z",
    "updated_at": "2026-05-17T14:00:00Z"
  }
}
```

**Erros**

| Status | Code                | Situação                                       |
| ------ | ------------------- | ---------------------------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido                      |
| 404    | `PROCESS_NOT_FOUND` | Processo não encontrado                        |
| 422    | `VALIDATION_ERROR`  | `content` ausente, vazio ou > 5000 caracteres  |

---

### `GET /api/v1/processes/{process_id}/notes`

Lista anotações internas do processo em ordem cronológica decrescente (`created_at DESC, id DESC`), com paginação.

**Query params**

| Parâmetro | Tipo              | Obrigatório | Descrição                        |
| --------- | ----------------- | ----------- | -------------------------------- |
| `page`    | `integer` (≥ 1)   | Não         | Página atual (default: `1`)      |
| `limit`   | `integer` (1–100) | Não         | Itens por página (default: `20`) |

**Resposta 200**

```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "process_id": 1,
      "created_by": 5,
      "updated_by": 3,
      "created_by_name": "Carlos Souza",
      "updated_by_name": "Ana Lima",
      "content": "Cliente confirmou disponibilidade para audiência.",
      "created_at": "2026-05-17T15:00:00Z",
      "updated_at": "2026-05-17T16:00:00Z"
    },
    {
      "id": 1,
      "process_id": 1,
      "created_by": 3,
      "updated_by": null,
      "created_by_name": "Ana Lima",
      "updated_by_name": null,
      "content": "Estratégia: aguardar prazo recursal antes de protocolar contestação.",
      "created_at": "2026-05-17T14:00:00Z",
      "updated_at": "2026-05-17T14:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

**Erros**

| Status | Code                | Situação                  |
| ------ | ------------------- | ------------------------- |
| 401    | `UNAUTHORIZED`      | Token ausente ou inválido |
| 404    | `PROCESS_NOT_FOUND` | Processo não encontrado   |

---

### `PATCH /api/v1/processes/{process_id}/notes/{note_id}`

Edita o conteúdo de uma anotação. Apenas o autor original pode editar; usuários com role `ADMIN` podem editar qualquer anotação.

**Body**

```json
{
  "content": "Estratégia revista: solicitar perícia técnica antes da audiência."
}
```

**Resposta 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "process_id": 1,
    "created_by": 3,
    "updated_by": 3,
    "created_by_name": "Ana Lima",
    "updated_by_name": "Ana Lima",
    "content": "Estratégia revista: solicitar perícia técnica antes da audiência.",
    "created_at": "2026-05-17T14:00:00Z",
    "updated_at": "2026-05-17T17:00:00Z"
  }
}
```

**Erros**

| Status | Code                     | Situação                                              |
| ------ | ------------------------ | ----------------------------------------------------- |
| 401    | `UNAUTHORIZED`           | Token ausente ou inválido                             |
| 403    | `FORBIDDEN`              | Usuário não é o autor nem ADMIN                       |
| 404    | `PROCESS_NOT_FOUND`      | Processo não encontrado                               |
| 404    | `PROCESS_NOTE_NOT_FOUND` | Anotação não encontrada ou não pertence ao processo   |
| 422    | `VALIDATION_ERROR`       | `content` ausente, vazio ou > 5000 caracteres         |
