# Git Convention

## Branches

### US (funcionalidade ligada ao backlog)
```
feat/us-<id>-<descricao-curta>
fix/us-<id>-<descricao-curta>
```

### Feature de infraestrutura (sem US, mas dependência de US futura)
```
feat/<descricao-curta>
```

> Use `feat/` para código transversal que uma ou mais US vão precisar, mas que não representa uma US por si só (ex: serviço de e-mail, integração com storage, cliente HTTP externo).

### Outros
```
chore/<descricao-curta>     # configuração, dependências, infraestrutura
docs/<descricao-curta>      # documentação
refactor/<descricao-curta>  # refatoração sem mudança de comportamento
```

**Exemplos**
```
feat/us-01-login
feat/us-02-password-reset
fix/us-01-inactive-user-status
feat/email-service
feat/s3-storage
chore/add-alembic
docs/update-endpoints
```

---

## Commits

```
<tipo>(<escopo>): <mensagem no imperativo>
```

- **tipo**: feat, fix, chore, docs, refactor
- **escopo**: opcional, pode ser o nome da US, módulo ou área afetada
- **mensagem**: descrição curta do que foi feito, no imperativo **em inglês**

**Exemplos**
```
feat(auth): add JWT login endpoint
fix(auth): return 403 for inactive users
chore(deps): add PyJWT and bcrypt
docs(endpoints): document auth routes
refactor(leads): migrate repository to SQLAlchemy 2.0 style
feat(email): add email sending service
```

---

## Fluxo

```
main
 └── dev
       ├── feat/us-01-login         ← funcionalidade de US
       ├── feat/email-service       ← infraestrutura sem US
       └── fix/us-01-inactive-user
```

- Branches de US e features saem sempre de `dev`
- PR de feature/US sempre para `dev`
- PR de `dev` para `main` marca uma release estável
- Nunca commitar direto em `dev` ou `main`
