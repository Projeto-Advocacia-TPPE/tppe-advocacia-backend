# Arquitetura

Este projeto segue uma arquitetura em camadas inspirada no padrão MVC, adaptada para APIs REST com FastAPI. O objetivo é separar responsabilidades de forma clara, facilitando manutenção, testes e evolução do sistema.

---

## Estrutura de pastas

```
app/
├── main.py                  # ponto de entrada da aplicação
├── config/
│   └── settings.py          # configurações e variáveis de ambiente
├── db/
│   └── database.py          # conexão com o banco de dados
├── models/                  # modelos ORM (mapeamento banco ↔ objeto)
├── schemas/                 # schemas Pydantic (contratos de entrada/saída)
├── repositories/            # acesso a dados e queries
├── services/                # regras de negócio
├── controllers/             # orquestração entre camadas
├── utils/                   # utilitários transversais
│   ├── exceptions.py        # exceções customizadas da aplicação
│   └── responses.py         # envelope padrão de resposta da API
└── api/
    └── v1/                  # rotas HTTP versionadas
```

---

## Camadas e responsabilidades

### `api/` — Rotas (entrada HTTP)
Ponto de entrada de cada requisição. Define os endpoints, aplica os schemas de validação de entrada e delega ao controller correspondente. Não contém lógica de negócio.

### `controllers/` — Orquestração
Coordena o fluxo entre services e schemas. Recebe dados já validados da rota, chama os services necessários e retorna a resposta serializada. Não acessa o banco diretamente.

### `services/` — Regras de negócio
Concentra a lógica do domínio: validações de negócio, cálculos, decisões. Usa repositories para persistência. É a camada mais importante e a que deve ter maior cobertura de testes.

### `repositories/` — Acesso a dados
Responsável exclusivamente por interagir com o banco de dados: queries, inserções, atualizações e deleções. Recebe e retorna models ORM. Não conhece regras de negócio.

### `models/` — Modelos ORM
Definem o esquema do banco de dados via ORM. Representam as entidades persistidas.

### `schemas/` — Contratos de entrada e saída
Schemas Pydantic que definem o formato esperado nas requisições e nas respostas da API. Funcionam como DTOs (Data Transfer Objects) e desacoplam a camada HTTP dos models internos.

### `utils/` — Utilitários transversais
Código compartilhado entre camadas que não pertence ao domínio. Inclui as exceções customizadas da aplicação (`AppException` e subclasses) e o envelope padrão de resposta (`APIResponse[T]`). Todas as rotas devem retornar `APIResponse[T]`; todos os erros de negócio devem ser lançados como subclasses de `AppException`.

### `config/` — Configurações
Centraliza variáveis de ambiente e configurações da aplicação (usando `pydantic-settings`).

### `db/` — Banco de dados
Gerencia a conexão com o banco e a criação de sessões.

---

## Fluxo de uma requisição

```
HTTP Request
  └─► api/v1/                        valida entrada com schema
        └─► controller/              orquestra a operação
              └─► service/           aplica regras de negócio
                    └─► repository/  executa query no banco
                          └─► model/ entidade ORM
  ◄── HTTP Response
        schema/          serializa a saída
```

---

## Padrão de resposta

Todas as respostas da API seguem o envelope `APIResponse[T]` definido em `app/utils/responses.py`:

```json
// sucesso
{ "success": true, "data": { ... }, "error": null }

// erro de negócio ou autenticação
{ "success": false, "data": null, "error": { "code": "ERROR_CODE", "message": "mensagem legível" } }
```

Erros de validação de entrada (422) seguem o mesmo envelope com `code: "VALIDATION_ERROR"`.

---

## Princípios que guiam as decisões

- **Uma responsabilidade por camada:** cada camada conhece apenas a camada imediatamente abaixo.
- **Regras de negócio no service:** nenhuma lógica de domínio nos controllers, rotas ou repositories.
- **Schemas desacoplados dos models:** nunca expor diretamente um model ORM na resposta da API.
- **Repository como única porta para o banco:** nenhuma query fora do repository.
- **Versionamento de rotas:** toda rota pública fica sob `/api/v1/` para permitir evolução sem quebrar contratos.
- **Erros via exceções customizadas:** toda falha de negócio deve ser lançada como subclasse de `AppException`; nunca usar `HTTPException` diretamente nos services.
- **Resposta padronizada:** toda rota retorna `APIResponse[T]` usando o helper `ok(data)`.
