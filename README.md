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

**Como a análise foi feita:** leitura integral dos três projetos (código original do commit inicial), cruzando cada arquivo com a lista de anti-patterns citados no enunciado. Foram priorizados os problemas apontados no enunciado. Problemas adicionais só entraram quando eram evidentes e de severidade MEDIUM ou superior.

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

| #   | Severidade   | Problema                                                          | Local                                                                                                                                                                                                         | Por que é relevante                                                                                                                                                                                                                                                     |
| --- | ------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **CRITICAL** | SQL Injection por concatenação de strings                         | `models.py` (praticamente todas as funções de query: `get_produto_por_id`, `criar_produto`, `atualizar_produto`, `deletar_produto`, `login_usuario`, `criar_usuario`, `criar_pedido`, `buscar_produtos` etc.) | Todas as queries montam SQL com `+` e dados do cliente. O `login_usuario` (`... WHERE email = '" + email + "' AND senha = '" + senha + "'`) permite bypass de autenticação com `' OR '1'='1`. Qualquer campo de texto (nome, busca) permite ler/alterar/apagar o banco. |
| 2   | **CRITICAL** | Endpoint que executa SQL arbitrário sem autenticação              | `app.py` — `POST /admin/query` (`executar_query`)                                                                                                                                                             | A rota roda qualquer SQL recebido no corpo (`cursor.execute(query)`), sem autenticação. É um backdoor total ao banco, exposto na API pública.                                                                                                                           |
| 3   | **CRITICAL** | Credenciais e flags sensíveis hardcoded no código                 | `app.py` (`SECRET_KEY` e `DEBUG` no módulo, `debug=True` no `app.run`)                                                                                                                                        | `SECRET_KEY` fixa no fonte e `DEBUG=True` tanto no config quanto no `app.run`. Segredo versionado no git e debugger do Werkzeug (com execução remota de código via console PIN) ligado em qualquer ambiente. Não há módulo de configuração nem variáveis de ambiente.   |
| 4   | **CRITICAL** | Senhas armazenadas e comparadas em texto puro                     | `models.py` — `criar_usuario` (grava), `login_usuario` (compara), `get_usuario_por_id` e `get_todos_usuarios` (retornam)                                                                                      | A senha é inserida e comparada sem qualquer hash. Vazamento do banco expõe todas as senhas diretamente, e o `get_usuario_por_id`/`get_todos_usuarios` ainda devolve a coluna `senha` na resposta.                                                                       |
| 5   | **HIGH**     | Regras de negócio acopladas à camada de dados (sem MVC)           | `models.py` — `criar_pedido` (estoque/total) e `relatorio_vendas` (desconto e ticket médio)                                                                                                                   | O arquivo de "models" mistura acesso a dados com lógica de domínio (precificação, desconto, baixa de estoque). Não há camada de serviço nem controller real — impossível testar a regra sem o banco e qualquer mudança no SQL arrisca a regra de negócio.               |
| 6   | **HIGH**     | Conexão de banco global e mutável, compartilhada entre threads    | `database.py` — `get_db` (global `db_connection`, aberta com `check_same_thread=False`)                                                                                                                       | Uma única conexão global para toda a aplicação, reaproveitada por todas as requisições e threads. Estado global mutável que impede testes isolados e gera condições de corrida sob concorrência.                                                                        |
| 7   | **MEDIUM**   | Queries N+1 na listagem de pedidos                                | `models.py` — `get_pedidos_usuario` e `get_todos_pedidos`                                                                                                                                                     | Para cada pedido roda uma query de itens e, para cada item, mais uma query do nome do produto. Uma listagem de N pedidos com M itens dispara 1 + N + N×M queries, resolvível com um JOIN.                                                                               |
| 8   | **MEDIUM**   | `except Exception` genérico vazando a mensagem crua ao cliente    | `controllers.py` (16 ocorrências, um por handler) e `app.py` (`executar_query`)                                                                                                                               | Todo handler captura `Exception` e retorna `str(e)` no corpo. Não há tratamento de erro centralizado, e a mensagem interna (inclusive trechos de SQL) vaza para o cliente.                                                                                              |
| 9   | **MEDIUM**   | Duplicação extensa de mapeamento e de blocos inteiros             | `models.py` — dict de produto em `get_todos_produtos`, `get_produto_por_id` e `buscar_produtos`; bloco de montagem de pedido duplicado entre `get_pedidos_usuario` e `get_todos_pedidos`                      | A mesma transformação linha→dict e o mesmo laço de montagem de pedido estão copiados em vários pontos. Qualquer novo campo precisa ser alterado em todos os lugares, com risco de divergência.                                                                          |
| 10  | **MEDIUM**   | Notificações simuladas como efeito colateral dentro do controller | `controllers.py` — `criar_pedido` e `atualizar_status_pedido`                                                                                                                                                 | Envio de e-mail/SMS/push é "simulado" com `print` no meio do controller de pedidos. Responsabilidade que pertence a um serviço, acoplada ao fluxo HTTP e impossível de testar ou trocar.                                                                                |
| 11  | **LOW**      | `print()` usado como log em toda a aplicação                      | `controllers.py` (9 ocorrências) e `app.py` (`reset_database` e bloco de boot)                                                                                                                                | Sem biblioteca de logging: nível, formato e destino fixos no `stdout`. Dificulta operação e observabilidade.                                                                                                                                                            |
| 12  | **LOW**      | Magic numbers e listas fixas no código                            | `models.py` — `relatorio_vendas` (faixas de faturamento 10000/5000/1000 e taxas 0.1/0.05/0.02); `controllers.py` — `criar_produto` (lista de categorias válidas)                                              | Valores de negócio e enumerações soltos no meio da lógica, sem constantes nomeadas nem configuração.                                                                                                                                                                    |

**Resumo:** CRITICAL 4 · HIGH 2 · MEDIUM 4 · LOW 2 — **12 achados**.

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

| #   | Severidade   | Problema                                                       | Local                                                                                                                                       | Por que é relevante                                                                                                                                                                                                                                         |
| --- | ------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **CRITICAL** | God Class concentrando banco, schema, rotas e regra de negócio | `src/AppManager.js` — classe `AppManager` (`initDb` + `setupRoutes`)                                                                        | Uma só classe abre a conexão, cria o schema e os seeds (`initDb`), registra todas as rotas e executa a lógica de checkout e pagamento (`setupRoutes`). Violação completa da separação de responsabilidades: nada pode ser testado ou alterado isoladamente. |
| 2   | **CRITICAL** | Credenciais de produção hardcoded no código                    | `src/utils.js` — objeto `config`                                                                                                            | `config` com senha de banco (`senha_super_secreta_prod_123`), chave de pagamento `pk_live_...` e usuário SMTP versionados no fonte. Qualquer um com acesso ao repositório tem as chaves de produção.                                                        |
| 3   | **CRITICAL** | Hashing de senha caseiro e inseguro                            | `src/utils.js` — `badCrypto`                                                                                                                | Função própria que repete um `base64` 10.000 vezes e trunca em 10 caracteres — não é hash criptográfico, não tem sal e é facilmente reversível/colidível. Senhas ficam efetivamente desprotegidas.                                                          |
| 4   | **CRITICAL** | Número de cartão e chave de pagamento gravados em log          | `src/AppManager.js` — `POST /api/checkout`                                                                                                  | Um `console.log` registra o PAN completo (`cc`) e a chave `pk_live` em texto puro a cada checkout — violação direta de PCI-DSS e vazamento de dado sensível.                                                                                                |
| 5   | **HIGH**     | Estado global mutável compartilhado                            | `src/utils.js` — `globalCache`, `totalRevenue`, `logAndCache`                                                                               | Variáveis globais mutáveis exportadas e alteradas em runtime (`globalCache[key] = data`). Estado compartilhado entre requisições, não testável e fonte de acoplamento e condições de corrida.                                                               |
| 6   | **HIGH**     | Callback hell com fluxo de negócio aninhado                    | `src/AppManager.js` — `POST /api/checkout` (~5 níveis) e `GET /api/admin/financial-report`                                                  | Lógica de checkout e relatório escrita em callbacks aninhados do `sqlite3`, com tratamento de erro espalhado e sem transação. Praticamente impossível de ler, testar ou evoluir; um erro no meio deixa dados parciais.                                      |
| 7   | **MEDIUM**   | Queries N+1 no relatório financeiro                            | `src/AppManager.js` — `GET /api/admin/financial-report`                                                                                     | Para cada curso busca as matrículas e, para cada matrícula, uma query de usuário e outra de pagamento. O relatório dispara 1 + N + N×2 queries onde um JOIN resolveria em uma.                                                                              |
| 8   | **MEDIUM**   | Ausência de integridade referencial e registros órfãos         | `src/AppManager.js` — `initDb` (schema sem FK/constraints) e `DELETE /api/users/:id`                                                        | O schema não tem chaves estrangeiras, `NOT NULL` nem `UNIQUE` (e-mail duplicável). O `DELETE /api/users/:id` apaga o usuário e deixa matrículas e pagamentos órfãos — a própria resposta admite "ficaram sujos no banco".                                   |
| 9   | **MEDIUM**   | Validação de entrada fraca com default silencioso de senha     | `src/AppManager.js` — `POST /api/checkout`                                                                                                  | A validação cobre só presença de campos; `pwd` não é exigido e, quando ausente, a senha vira silenciosamente `"123456"` (`badCrypto(p                                                                                                                       |     | "123456")`). Formato de cartão/e-mail não é checado. Cria contas com senha previsível sem o cliente saber. |
| 10  | **MEDIUM**   | Erros de banco ignorados e sem tratamento central              | `src/AppManager.js` — `GET /api/admin/financial-report` e `DELETE /api/users/:id` (param `err` ignorado); respostas `500` ad-hoc espalhadas | Vários callbacks ignoram o `err` do SQLite e seguem o fluxo com dado possivelmente nulo; não há middleware de erro. Falhas passam despercebidas ou derrubam a resposta de forma inconsistente.                                                              |
| 11  | **LOW**      | Nomes crípticos de variáveis e campos                          | `src/AppManager.js` — `POST /api/checkout` (`u`, `e`, `p`, `cid`, `cc`) e o contrato `usr`/`eml`/`pwd`/`c_id`/`card`                        | Abreviações de uma letra e campos abreviados sem padrão prejudicam a legibilidade e escondem a intenção do código.                                                                                                                                          |
| 12  | **LOW**      | Formato de resposta inconsistente                              | `src/AppManager.js` — sucesso em JSON vs erros e delete em texto puro                                                                       | A API ora responde JSON, ora uma frase em texto puro. Clientes não têm um contrato previsível para tratar sucesso e erro.                                                                                                                                   |

**Resumo:** CRITICAL 4 · HIGH 2 · MEDIUM 4 · LOW 2 — **12 achados**.

### Projeto 3 — task-manager-api

| Item         | Valor                                                                                                                   |
| ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Stack        | Python 3 + Flask 3.0.0, Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x), flask-cors 4.0.0, marshmallow, requests, python-dotenv |
| Domínio      | Task Manager: tarefas, usuários, categorias e relatórios                                                                |
| Banco        | SQLite em `instance/tasks.db`, populado pelo `seed.py` (3 usuários, 4 categorias, 10 tasks)                             |
| Tabelas      | `users`, `tasks`, `categories`                                                                                          |
| Código-fonte | 15 arquivos `.py` (4 são `__init__.py`), 1.158 linhas                                                                   |
| Rotas        | 22                                                                                                                      |
| Organização  | Camadas parciais: `models/`, `routes/` (Blueprints), `services/`, `utils/`                                              |

| #   | Severidade   | Problema                                                                             | Local                                                                                                                                                                                                                                                                                   | Por que é relevante                                                                                                                                                                                                                                     |
| --- | ------------ | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **CRITICAL** | Hashing de senha com MD5 sem sal                                                     | `models/user.py` — `set_password` / `check_password`                                                                                                                                                                                                                                    | Senhas são guardadas como MD5, algoritmo quebrado para esse fim e sem sal — vulnerável a rainbow tables e colisão. Mesmo com a estrutura em camadas, a segurança de autenticação está comprometida.                                                     |
| 2   | **CRITICAL** | Hash de senha exposto nas respostas da API                                           | `models/user.py` — `to_dict` (inclui `password`), consumido em `routes/user_routes.py` (`get_user`, `create_user`, `update_user`, `login`)                                                                                                                                              | O `to_dict` do usuário devolve o campo `password`, então GET de usuário, criação, atualização e o próprio login retornam o hash no corpo. Expõe material sensível a qualquer cliente da API.                                                            |
| 3   | **CRITICAL** | Segredos hardcoded (app, banco e SMTP)                                               | `app.py` (`SECRET_KEY`, URI do banco) e `services/notification_service.py` (host, usuário e senha `senha123` do SMTP)                                                                                                                                                                   | Chave de aplicação e credenciais de e-mail fixas no fonte. O projeto já depende de `python-dotenv`, mas não o usa — nenhuma configuração vem de variável de ambiente.                                                                                   |
| 4   | **HIGH**     | Rotas "gordas" com regra de negócio inline; camada de serviço inexistente na prática | `routes/report_routes.py` (`summary_report`, `user_report`) e `routes/task_routes.py` (`get_tasks`)                                                                                                                                                                                     | Os handlers concentram agregação, cálculo de atraso, montagem de DTO e acesso a dados. A pasta `services/` existe mas só tem `NotificationService`, que nunca é chamado — ou seja, a separação de camadas é aparente, e a lógica mora toda nas rotas.   |
| 5   | **MEDIUM**   | APIs deprecated: `Model.query.get()` e `datetime.utcnow()`                           | `.query.get()` em 16 ocorrências (`routes/user_routes.py`, `routes/task_routes.py`, `routes/report_routes.py`) e `datetime.utcnow()` em 22 ocorrências (models, rotas, `services/`, `seed.py`)                                                                                          | `Query.get()` é legado no SQLAlchemy 2.x (instalado aqui, 2.1.6) — o certo é `db.session.get(Model, id)`. `datetime.utcnow()` está deprecado desde o Python 3.12 — o certo é `datetime.now(timezone.utc)`. Uso extenso de APIs com substituto moderno. |
| 6   | **MEDIUM**   | Queries N+1 em listagens e relatórios                                                | `routes/task_routes.py` (`get_tasks` — por task, busca user e category), `routes/report_routes.py` (`summary_report` — por usuário, busca as tasks), `routes/user_routes.py` (`get_users` — `len(u.tasks)` por usuário)                                                                 | As listagens carregam relacionamentos um a um dentro de laços, em vez de usar JOIN/eager loading. O volume de queries cresce com a quantidade de registros.                                                                                             |
| 7   | **MEDIUM**   | `except:` nu engolindo qualquer erro                                                 | 12 ocorrências em `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` e `utils/helpers.py`                                                                                                                                                                      | `except:` sem tipo captura até `KeyboardInterrupt`/`SystemExit`, esconde a causa real e devolve um 500 genérico. Em `get_tasks` qualquer falha some atrás de "Erro interno".                                                                            |
| 8   | **MEDIUM**   | Lógica de "overdue" e serialização duplicadas; métodos do model ignorados            | bloco `overdue` repetido em 7 pontos (`models/task.py`, `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`); `Task.is_overdue()` e `Task.to_dict()` reescritos inline em `get_tasks`/`get_user_tasks`                                                          | A mesma regra de atraso aparece em 7 lugares, e `get_tasks`/`get_user_tasks` remontam o dicionário manualmente em vez de usar `to_dict()`. O model tem os métodos certos, mas as rotas os ignoram — duplicação pura.                                    |
| 9   | **LOW**      | Imports, módulos e dependências sem uso                                              | imports não usados em `app.py`, `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` e `utils/helpers.py`; `NotificationService`, `helpers.process_task_data`, `format_date` e `calculate_percentage` nunca chamados; deps `marshmallow` e `requests` não usadas | Ruído que esconde o que o módulo realmente faz e sugere camadas/dependências que não existem de fato.                                                                                                                                                   |
| 10  | **LOW**      | Constantes compartilhadas ignoradas e aninhamento profundo                           | listas de status e faixa de prioridade `1..5` repetidas em `routes/task_routes.py` e `models/task.py`, embora `utils/helpers.py` já defina `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` etc.; `if/else` encadeado para `overdue`                                                 | Os valores de domínio estão duplicados como literais apesar de existirem constantes nomeadas, e o cálculo de atraso usa 3-4 níveis de `if/else` onde um retorno direto bastaria.                                                                        |

**Resumo:** CRITICAL 3 · HIGH 1 · MEDIUM 4 · LOW 2 — **10 achados**.

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

Os três projetos foram revalidados nos runtimes alvo (**Python 3.11** e **Node 22**), com saída byte a byte idêntica ao baseline — evidências em [`evidencias/py311-node22/`](evidencias/py311-node22/).

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
| Python                                                                 | 3.11            | Mínimo suportado 3.9; os projetos foram validados no 3.11. Um venv por projeto Python.    |
| Node.js / npm                                                          | 22 / 10         | Node 22 LTS (ex.: via `nvm install 22`), que já traz o npm 10.                            |
| Sistema                                                                | macOS           | Veja a nota sobre a porta 5000 abaixo.                                                    |

### Instalar as dependências

```bash
# Projeto 1  (Python 3.11)
cd code-smells-project
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Projeto 2  (Node 22)
cd ../ecommerce-api-legacy
npm install

# Projeto 3  (Python 3.11)
cd ../task-manager-api
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
```

> **Node 22 e o `sqlite3`:** com o Node 22 (npm 10) o `npm install` compila o módulo nativo do `sqlite3` direto, sem passos extras. Em versões de npm mais novas (como a que acompanha o Node 26), que bloqueiam scripts de instalação por padrão, rode `npm install-scripts approve sqlite3` e um novo `npm install`.

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
