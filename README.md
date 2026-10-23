# Refatoração Arquitetural Automatizada com a skill `refactor-arch`

Solução do desafio descrito em [`ENUNCIADO.md`](ENUNCIADO.md): uma Skill do Claude Code que analisa, audita e refatora projetos legados para o padrão MVC, testada em três projetos com stacks diferentes (Python/Flask e Node.js/Express).

> **Status: versão preliminar.** A Etapa 0 do [`PLANO.md`](PLANO.md) (baseline dos 3 apps) está concluída. Os trechos marcados com _A preencher_ serão completados nas próximas etapas.

## Sumário

- [Estrutura do repositório](#estrutura-do-repositório)
- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

## Estrutura do repositório

```
.
├── README.md                       # este documento
├── ENUNCIADO.md                    # enunciado original do desafio
├── PLANO.md                        # plano de resolução por etapas
│
├── code-smells-project/            # Projeto 1 — Python/Flask (API de e-commerce)
│   └── .claude/skills/refactor-arch/   # a skill (a criar na Etapa 2)
├── ecommerce-api-legacy/           # Projeto 2 — Node.js/Express (LMS com checkout)
│   └── .claude/skills/refactor-arch/   # cópia da skill
├── task-manager-api/               # Projeto 3 — Python/Flask (Task Manager)
│   └── .claude/skills/refactor-arch/   # cópia da skill
│
├── reports/                        # saída da Fase 2 da skill (a gerar)
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
│
├── scripts/                        # validação independente da skill
│   ├── smoke.py                    # smoke test HTTP (sobe o app, chama as rotas, derruba)
│   └── specs/                      # requisições de cada projeto
└── evidencias/
    ├── baseline/                   # respostas do código original
    └── depois/                     # respostas do código refatorado (a gerar)
```

---

## A) Análise Manual

Os problemas foram classificados pela escala do enunciado:

| Severidade   | Critério resumido                                                                                                                |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **CRITICAL** | Falha grave de arquitetura ou segurança: expõe dados sensíveis, impede o funcionamento ou anula a separação de responsabilidades |
| **HIGH**     | Violação forte de MVC/SOLID que dificulta muito manutenção e testes                                                              |
| **MEDIUM**   | Padronização, duplicação ou performance moderada                                                                                 |
| **LOW**      | Legibilidade, nomenclatura, magic numbers                                                                                        |

Requisito mínimo por projeto: 5 problemas, com pelo menos 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW.

**Como a análise foi feita:** _A preencher na Etapa 1._

### Projeto 1 — code-smells-project

| Item         | Valor                                                                                                                 |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| Stack        | Python 3 + Flask 3.1.1, flask-cors 5.0.1                                                                              |
| Domínio      | API de e-commerce: produtos, usuários, pedidos e relatório de vendas                                                  |
| Banco        | SQLite via módulo `sqlite3`, arquivo `loja.db` criado no primeiro acesso com dados iniciais (10 produtos, 3 usuários) |
| Tabelas      | `produtos`, `usuarios`, `pedidos`, `itens_pedido`                                                                     |
| Código-fonte | 4 arquivos `.py`, 780 linhas                                                                                          |
| Rotas        | 19                                                                                                                    |
| Organização  | 4 arquivos na raiz (`app.py`, `controllers.py`, `models.py`, `database.py`), sem pastas por camada                    |

| #   | Severidade | Problema | Local | Por que é relevante |
| --- | ---------- | -------- | ----- | ------------------- |
| 1   |            |          |       |                     |

**Resumo:** CRITICAL _ · HIGH _ · MEDIUM _ · LOW _ — _A preencher na Etapa 1._

### Projeto 2 — ecommerce-api-legacy

| Item         | Valor                                                                   |
| ------------ | ----------------------------------------------------------------------- |
| Stack        | Node.js + Express ^4.18.2, sqlite3 ^5.1.6                               |
| Domínio      | LMS com checkout: cursos, matrículas, pagamentos e relatório financeiro |
| Banco        | SQLite em memória; schema e dados iniciais criados a cada boot          |
| Tabelas      | `users`, `courses`, `enrollments`, `payments`, `audit_logs`             |
| Código-fonte | 3 arquivos `.js`, 180 linhas                                            |
| Rotas        | 3                                                                       |
| Organização  | `src/app.js` (entry point), `src/AppManager.js`, `src/utils.js`         |

| #   | Severidade | Problema | Local | Por que é relevante |
| --- | ---------- | -------- | ----- | ------------------- |
| 1   |            |          |       |                     |

**Resumo:** CRITICAL _ · HIGH _ · MEDIUM _ · LOW _ — _A preencher na Etapa 1._

### Projeto 3 — task-manager-api

| Item         | Valor                                                                                                                   |
| ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Stack        | Python 3 + Flask 3.0.0, Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0), flask-cors 4.0.0, marshmallow, requests, python-dotenv |
| Domínio      | Task Manager: tarefas, usuários, categorias e relatórios                                                                |
| Banco        | SQLite em `instance/tasks.db`, populado pelo `seed.py` (3 usuários, 4 categorias, 10 tasks)                             |
| Tabelas      | `users`, `tasks`, `categories`                                                                                          |
| Código-fonte | 15 arquivos `.py` (4 são `__init__.py`), 1.158 linhas                                                                   |
| Rotas        | 22                                                                                                                      |
| Organização  | Camadas parciais: `models/`, `routes/` (Blueprints), `services/`, `utils/`                                              |

| #   | Severidade | Problema | Local | Por que é relevante |
| --- | ---------- | -------- | ----- | ------------------- |
| 1   |            |          |       |                     |

**Resumo:** CRITICAL _ · HIGH _ · MEDIUM _ · LOW _ — _A preencher na Etapa 1._

---

## B) Construção da Skill

### Estrutura da skill

_A preencher na Etapa 2._ Estrutura planejada:

```
.claude/skills/refactor-arch/
├── SKILL.md                       # orquestra as 3 fases
└── references/
    ├── project-analysis.md        # heurísticas de detecção de stack e arquitetura
    ├── anti-patterns-catalog.md   # catálogo com sinais de detecção e severidade
    ├── audit-report-template.md   # formato do relatório da Fase 2
    ├── mvc-guidelines.md          # regras das camadas MVC
    └── refactoring-playbook.md    # transformações com código antes/depois
```

### Decisões de design

_A preencher nas Etapas 2 e 3:_ como o `SKILL.md` foi estruturado, como as fases usam as referências e como a pausa da Fase 2 foi garantida.

### Catálogo de anti-patterns

_A preencher na Etapa 3._

| ID  | Anti-pattern | Severidade | Por que foi incluído |
| --- | ------------ | ---------- | -------------------- |
|     |              |            |                      |

### Agnosticismo de tecnologia

_A preencher na Etapa 3:_ como a skill evita depender de nomes de arquivos, tabelas ou rotas dos projetos e como mapeia as camadas MVC para cada framework.

### Desafios encontrados e soluções

| Desafio                                                                                 | Impacto                                                                                               | Como foi resolvido                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| No macOS, o Receptor AirPlay ocupa a porta 5000                                         | P1 e P3 não sobem com `python app.py`, que fixa a porta 5000 (`Errno 48: Address already in use`)     | O baseline usou o mesmo app iniciado com `flask --app app run --port 5001` (P1) e `--port 5002` (P3), sem alterar o código. No código refatorado, a porta vem de config/variável de ambiente (`PORT`). |
| O npm 12 bloqueia scripts de instalação de dependências por padrão                      | O `sqlite3` não compila o módulo nativo e o P2 falha no boot com `Could not locate the bindings file` | `npm install-scripts approve sqlite3` e um novo `npm install`. Esse comando grava um bloco `allowScripts` no `package.json`, mesmo com `--dry-run`.                                                    |
| O Python disponível é o 3.9.6                                                           | O código refatorado não pode usar recursos do 3.10 em diante (`X \| None`, `match`, `datetime.UTC`)   | A Fase 1 deve detectar a versão do runtime, e a Fase 3 deve respeitá-la. _Confirmar na Etapa 2._                                                                                                       |
| Respostas com datas geradas na hora e listas cuja ordem pode mudar entre implementações | Um `diff` direto entre antes e depois daria falsos positivos                                          | O `smoke.py` troca datas por `<timestamp>` e, quando a spec pede, ordena listas antes de gravar (usado no relatório financeiro do P2).                                                                 |
| Servidores que criam processos filhos (`npm start` → `node`)                            | Encerrar só o processo principal pode deixar a porta ocupada                                          | O `smoke.py` sobe o app numa sessão própria e encerra o grupo de processos inteiro.                                                                                                                    |

_Desafios das próximas etapas: a preencher._

### Iterações da skill

_A preencher nas Etapas 4 a 6._

| Iteração | Projeto | O que falhou | Ajuste feito nas referências |
| -------- | ------- | ------------ | ---------------------------- |
|          |         |              |                              |

---

## C) Resultados

### Metodologia de validação

A skill valida o próprio trabalho na Fase 3. Para não depender só dessa autoavaliação, cada projeto também passa por um smoke test externo (`scripts/smoke.py`), rodado antes e depois da refatoração:

1. Recria o banco (apaga o SQLite e, no P3, roda o `seed.py`) e sobe o app.
2. Chama todas as rotas, com casos de sucesso e de erro (400, 401, 404, 409), na ordem definida em `scripts/specs/`. As rotas destrutivas ficam por último.
3. Grava três arquivos por projeto:
    - `pN.txt`: resposta completa de cada requisição, com datas mascaradas
    - `pN.contract.txt`: uma linha por requisição, com status e formato do JSON
    - `pN.server.log`: saída do servidor
4. Encerra o app.

A comparação é um `diff` entre `evidencias/baseline/` e `evidencias/depois/`. Toda diferença precisa ser uma mudança intencional e documentada.

**Baseline do código original (23/10/2026):**

| Projeto                 | Rotas | Requisições | Status como esperado | 2ª execução |
| ----------------------- | ----- | ----------- | -------------------- | ----------- |
| P1 code-smells-project  | 19    | 31          | 31/31                | idêntica    |
| P2 ecommerce-api-legacy | 3     | 8           | 8/8                  | idêntica    |
| P3 task-manager-api     | 22    | 35          | 35/35                | idêntica    |

### Resumo das auditorias

_A preencher nas Etapas 4 a 6._

| Projeto                 | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório                                        |
| ----------------------- | -------- | ---- | ------ | --- | ----- | ------------------------------------------------ |
| P1 code-smells-project  |          |      |        |     |       | [audit-project-1.md](reports/audit-project-1.md) |
| P2 ecommerce-api-legacy |          |      |        |     |       | [audit-project-2.md](reports/audit-project-2.md) |
| P3 task-manager-api     |          |      |        |     |       | [audit-project-3.md](reports/audit-project-3.md) |

### Estrutura antes e depois

Números entre parênteses: linhas de cada arquivo no código original.

#### Projeto 1 — code-smells-project

```
ANTES                                   DEPOIS
code-smells-project/                    (a preencher na Etapa 4)
├── app.py               (88)
├── controllers.py      (292)
├── database.py          (86)
├── models.py           (314)
└── requirements.txt
```

#### Projeto 2 — ecommerce-api-legacy

```
ANTES                                   DEPOIS
ecommerce-api-legacy/                   (a preencher na Etapa 5)
├── api.http
├── package.json
└── src/
    ├── app.js           (14)
    ├── AppManager.js   (141)
    └── utils.js         (25)
```

#### Projeto 3 — task-manager-api

```
ANTES                                   DEPOIS
task-manager-api/                       (a preencher na Etapa 6)
├── app.py               (34)
├── database.py           (3)
├── seed.py              (99)
├── requirements.txt
├── models/
│   ├── category.py      (21)
│   ├── task.py          (60)
│   └── user.py          (38)
├── routes/
│   ├── report_routes.py (223)
│   ├── task_routes.py  (299)
│   └── user_routes.py  (211)
├── services/
│   └── notification_service.py (48)
└── utils/
    └── helpers.py      (116)
```

### Checklist de validação

_A preencher nas Etapas 4 a 6._ Para conferir a Fase 1, use as tabelas de visão geral da [seção A](#a-análise-manual).

| Item                                                           | P1  | P2  | P3  |
| -------------------------------------------------------------- | :-: | :-: | :-: |
| **Fase 1 — Análise**                                           |     |     |     |
| Linguagem detectada corretamente                               | ⬜  | ⬜  | ⬜  |
| Framework detectado corretamente                               | ⬜  | ⬜  | ⬜  |
| Domínio da aplicação descrito corretamente                     | ⬜  | ⬜  | ⬜  |
| Número de arquivos analisados condiz com a realidade           | ⬜  | ⬜  | ⬜  |
| **Fase 2 — Auditoria**                                         |     |     |     |
| Relatório segue o template definido nos arquivos de referência | ⬜  | ⬜  | ⬜  |
| Cada finding tem arquivo e linhas exatos                       | ⬜  | ⬜  | ⬜  |
| Findings ordenados por severidade (CRITICAL → LOW)             | ⬜  | ⬜  | ⬜  |
| Mínimo de 5 findings identificados                             | ⬜  | ⬜  | ⬜  |
| Detecção de APIs deprecated incluída (se aplicável)            | ⬜  | ⬜  | ⬜  |
| Skill pausa e pede confirmação antes da Fase 3                 | ⬜  | ⬜  | ⬜  |
| **Fase 3 — Refatoração**                                       |     |     |     |
| Estrutura de diretórios segue padrão MVC                       | ⬜  | ⬜  | ⬜  |
| Configuração extraída para módulo de config (sem hardcoded)    | ⬜  | ⬜  | ⬜  |
| Models criados para abstrair dados                             | ⬜  | ⬜  | ⬜  |
| Views/Routes separadas para visualização ou roteamento         | ⬜  | ⬜  | ⬜  |
| Controllers concentram o fluxo da aplicação                    | ⬜  | ⬜  | ⬜  |
| Error handling centralizado                                    | ⬜  | ⬜  | ⬜  |
| Entry point claro                                              | ⬜  | ⬜  | ⬜  |
| Aplicação inicia sem erros                                     | ⬜  | ⬜  | ⬜  |
| Endpoints originais respondem corretamente                     | ⬜  | ⬜  | ⬜  |

### Critérios de aceite

| Critério                                    | P1  | P2  | P3  |
| ------------------------------------------- | :-: | :-: | :-: |
| Fase 1 detecta a stack corretamente         | ⬜  | ⬜  | ⬜  |
| Fase 2 encontra ≥ 5 findings                | ⬜  | ⬜  | ⬜  |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | ⬜  | ⬜  | ⬜  |
| Aplicação funciona após a refatoração       | ⬜  | ⬜  | ⬜  |

### Evidências de execução

**Baseline:** respostas completas e logs em [`evidencias/baseline/`](evidencias/baseline/). Exemplo de execução (P2):

```
$ python3 scripts/smoke.py scripts/specs/p2-ecommerce-legacy.json --out evidencias/baseline/p2
[ecommerce-api-legacy] http://127.0.0.1:3000  (8 requisições)
  01 POST   /api/checkout                                 200
  02 POST   /api/checkout                                 400
  03 POST   /api/checkout                                 200
  04 POST   /api/checkout                                 400
  05 POST   /api/checkout                                 404
  06 GET    /api/admin/financial-report                   200
  07 DELETE /api/users/1                                  200
  08 GET    /api/admin/financial-report                   200
[ecommerce-api-legacy] 8/8 com o status esperado -> evidencias/baseline/p2.txt
```

**Após a refatoração:** _A preencher nas Etapas 4 a 6_ com o log de boot de cada app, a saída do smoke test e o `diff` contra o baseline, explicando cada diferença.

### Comportamento da skill em stacks diferentes

_A preencher na Etapa 7:_ diferenças entre o monolito Flask (P1), o projeto Express (P2) e o projeto Flask já em camadas (P3).

---

## D) Como Executar

### Pré-requisitos

| Ferramenta                                                             | Versão usada    | Observação                                                                                |
| ---------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------- |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) | 2.1.309         | Instalado e autenticado. A skill fica em `.claude/skills/refactor-arch/` de cada projeto. |
| Python                                                                 | 3.9.6           | Mínimo 3.9. Um venv por projeto Python.                                                   |
| Node.js / npm                                                          | 26.5.0 / 12.2.0 | Veja a nota sobre o npm 12 abaixo.                                                        |
| Sistema                                                                | macOS           | Veja a nota sobre a porta 5000 abaixo.                                                    |

### Instalar as dependências

```bash
# Projeto 1
cd code-smells-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Projeto 2
cd ../ecommerce-api-legacy
npm install

# Projeto 3
cd ../task-manager-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
```

> **npm 12 e o `sqlite3`:** se o `npm install` avisar `install scripts blocked ... sqlite3` e o app falhar com `Could not locate the bindings file`, rode `npm install-scripts approve sqlite3` e depois `npm install` de novo. O primeiro comando grava um bloco `allowScripts` no `package.json`.

> **macOS e a porta 5000:** o Receptor AirPlay usa a porta 5000, a mesma do P1 e do P3 originais. Desligue-o em Ajustes do Sistema › Geral › AirDrop e Handoff › Receptor AirPlay, ou suba o app em outra porta com `flask --app app run --port <porta>`.

### Rodar os apps originais

| Projeto | Comando (na pasta do projeto)                                            | URL                               | Banco                                        |
| ------- | ------------------------------------------------------------------------ | --------------------------------- | -------------------------------------------- |
| P1      | `.venv/bin/python app.py` ou `.venv/bin/flask --app app run --port 5001` | `http://localhost:5000` (ou 5001) | `loja.db`, criado no primeiro acesso         |
| P2      | `npm start`                                                              | `http://localhost:3000`           | em memória, recriado a cada boot             |
| P3      | `.venv/bin/python app.py` ou `.venv/bin/flask --app app run --port 5002` | `http://localhost:5000` (ou 5002) | `instance/tasks.db`, populado pelo `seed.py` |

### Executar a skill

_A skill será criada na Etapa 2._ Uso previsto:

```bash
# Projeto 1 (onde a skill é desenvolvida)
cd code-smells-project
claude "/refactor-arch"

# Projetos 2 e 3: copiar a skill e executar
cd ..
rsync -a --delete code-smells-project/.claude/skills/refactor-arch/ ecommerce-api-legacy/.claude/skills/refactor-arch/
rsync -a --delete code-smells-project/.claude/skills/refactor-arch/ task-manager-api/.claude/skills/refactor-arch/
cd ecommerce-api-legacy && claude "/refactor-arch"
cd ../task-manager-api && claude "/refactor-arch"
```

Use o modo interativo (sem `-p`): a Fase 2 para e espera a sua confirmação antes de alterar qualquer arquivo.

### Validar a refatoração

O smoke test roda a partir da raiz do repositório. Ele recria o banco, sobe o app, chama todas as rotas e derruba o app no final.

| Projeto | Spec                                     | Porta | Preparação feita pelo script   |
| ------- | ---------------------------------------- | ----- | ------------------------------ |
| P1      | `scripts/specs/p1-code-smells.json`      | 5001  | apaga `loja.db`                |
| P2      | `scripts/specs/p2-ecommerce-legacy.json` | 3000  | nenhuma (banco em memória)     |
| P3      | `scripts/specs/p3-task-manager.json`     | 5002  | apaga o banco e roda `seed.py` |

```bash
# 1. Baseline do código original (já gerado em evidencias/baseline/)
python3 scripts/smoke.py scripts/specs/p1-code-smells.json --out evidencias/baseline/p1

# 2. Mesmas requisições no código refatorado
#    --start troca o comando de boot; o script passa a porta na variável PORT
python3 scripts/smoke.py scripts/specs/p1-code-smells.json --out evidencias/depois/p1 \
  --start ".venv/bin/python app.py"

# 3. Comparar
diff -u evidencias/baseline/p1.contract.txt evidencias/depois/p1.contract.txt   # status e formato
diff -u evidencias/baseline/p1.txt evidencias/depois/p1.txt                     # respostas completas
```

Outras opções: `--port` troca a porta e `--setup` troca os comandos de preparação (pode ser repetido).

Código de saída: `0` quando todas as rotas devolvem o status esperado, `2` quando alguma devolve outro status e `1` quando o app não sobe ou não responde.

_O comando de boot do código refatorado de cada projeto será definido nas Etapas 4 a 6._
