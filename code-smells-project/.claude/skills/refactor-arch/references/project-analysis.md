# Referência — Análise de Projeto (Fase 1)

Heurísticas para detectar linguagem, framework, banco e arquitetura de forma
agnóstica de tecnologia, e para inventariar o projeto corretamente.

## 1. Escopo: o que contar e o que ignorar

Antes de qualquer detecção, monte a lista de **arquivos de código-fonte**.

**Conte** os fontes da aplicação (ex.: `.py`, `.js`, `.ts`, `.go`, `.rb`,
`.java`, `.php`), incluindo os dentro de pastas de camadas (`models/`, `routes/`
etc.).

**Ignore sempre**:

- Diretórios de ferramentas: `.claude/`, `.git/`
- Dependências: `node_modules/`, `.venv/`, `venv/`, `vendor/`, `site-packages/`
- Artefatos: `__pycache__/`, `dist/`, `build/`, `*.pyc`
- Locks e manifestos não-fonte: `package-lock.json`, `yarn.lock`, `*.lock`
- Bancos e dados: `*.db`, `*.sqlite`, `instance/`
- Os próprios arquivos da skill (`.claude/skills/...`)

> A contagem de "source files" do relatório **deve** refletir essa lista. Se o
> projeto tem 4 arquivos de código, o relatório diz 4 — não conte lock, db nem
> `__init__.py` vazios como se fossem módulos relevantes (mencione-os à parte se
> ajudar).

Comandos úteis (exemplos — adapte à stack):

```bash
# Python: fontes reais
find . -name '*.py' -not -path '*/.venv/*' -not -path '*/__pycache__/*'
# Node: fontes reais
find . -name '*.js' -not -path '*/node_modules/*'
# Contagem de linhas por arquivo
wc -l <arquivos>
```

## 2. Linguagem e framework

Detecte pela presença de manifesto + dependências, e confirme pelos imports.

| Sinal (arquivo) | Linguagem | Como achar o framework |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python | dependência `flask`, `django`, `fastapi`; confirme por `from flask import ...` |
| `package.json` | Node.js (JS/TS) | dependência `express`, `koa`, `fastify`, `nest`; confirme por `require('express')` / `import express` |
| `go.mod` | Go | `gin`, `echo`, `net/http` |
| `pom.xml`, `build.gradle` | Java | `spring-boot`, `javalin` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `composer.json` | PHP | `laravel`, `symfony`, `slim` |

Registre também a **versão** do framework (vinda do manifesto) e as demais
dependências relevantes (ex.: `flask-cors`, `flask-sqlalchemy`).

## 3. Banco de dados

Procure por:

- Drivers/ORMs nas dependências: `sqlite3`, `psycopg2`, `mysql`, `SQLAlchemy`,
  `sequelize`, `mongoose`, `prisma`.
- Conexão no código: `sqlite3.connect(...)`, `new sqlite3.Database(...)`,
  `create_engine(...)`, string de conexão.
- Banco em memória: `:memory:`.
- **Tabelas/modelos**: declarações `CREATE TABLE`, classes de modelo
  (`class X(db.Model)`), migrations. Liste os nomes.

## 4. Rotas / endpoints

Inventarie **todas** as rotas (método + path). Padrões comuns:

| Framework | Padrão de rota |
|---|---|
| Flask | `@app.route(...)`, `@bp.route(...)`, `app.add_url_rule(...)`, Blueprints |
| Express | `app.get/post/put/delete(...)`, `router.<verbo>(...)` |
| FastAPI | `@app.get/post(...)`, `APIRouter` |
| Django | `urlpatterns`, `path(...)` |

Esta lista é o **contrato** que a Fase 3 precisa preservar. Guarde-a.

## 5. Entry point, boot e porta

- **Entry point**: arquivo que inicia o servidor (`app.py`, `src/app.js`,
  `main.go`...).
- **Comando de boot**: como se sobe hoje (`python app.py`, `npm start`,
  `flask run`). A Fase 3 **não pode** mudar isso.
- **Porta**: fixa no código ou vinda de config/variável de ambiente.

## 6. Classificação da arquitetura

Com base na organização dos arquivos:

- **Monólito sem camadas**: tudo em poucos arquivos na raiz, sem separação.
- **Camadas parciais**: existem pastas (`models/`, `routes/`, `services/`) mas a
  lógica ainda vaza entre elas, ou camadas estão vazias/ignoradas.
- **MVC/estruturado**: separação clara de models, views/rotas e controllers.

Descreva em uma frase (ex.: "Monolítica — tudo em 4 arquivos, sem separação de
camadas").

## 7. Saída da Fase 1

Preencha o bloco `PHASE 1: PROJECT ANALYSIS` do template com: linguagem,
framework (+versão), dependências, domínio, arquitetura, nº de arquivos
analisados e tabelas do banco.
