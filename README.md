# Refatoração Arquitetural Automatizada com a skill `refactor-arch`

Solução do desafio descrito em [`ENUNCIADO.md`](ENUNCIADO.md): uma Skill do Claude Code que analisa, audita e refatora projetos legados para o padrão MVC, testada em três projetos com stacks diferentes (Python/Flask e Node.js/Express).

> **Status:** skill `refactor-arch` concluída (4 iterações) e executada nos 3 projetos; relatórios em `reports/`, código refatorado nas pastas dos projetos e evidências em `evidencias/`. Planejamento em [`PLANO.md`](PLANO.md).

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
│   └── .claude/skills/refactor-arch/   # a skill (fonte única)
├── ecommerce-api-legacy/           # Projeto 2 — Node.js/Express (LMS com checkout)
│   └── .claude/skills/refactor-arch/   # cópia da skill
├── task-manager-api/               # Projeto 3 — Python/Flask (Task Manager)
│   └── .claude/skills/refactor-arch/   # cópia da skill
│
├── reports/                        # relatórios de auditoria (saída da Fase 2)
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
│
├── scripts/                        # validação independente da skill
│   ├── smoke.py                    # smoke test HTTP (sobe o app, chama as rotas, derruba)
│   └── specs/                      # requisições de cada projeto
└── evidencias/
    ├── baseline/                   # respostas do código original
    └── depois/                     # respostas do código refatorado
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

```
.claude/skills/refactor-arch/
├── SKILL.md                       # orquestra as 3 fases, limites de acesso e gates
└── references/
    ├── project-analysis.md        # heurísticas de detecção de stack, escopo e arquitetura
    ├── anti-patterns-catalog.md   # 20 anti-patterns com sinais de detecção e severidade
    ├── audit-report-template.md   # formato dos blocos das Fases 1 e 3, do relatório, do plano e das evidências
    ├── mvc-guidelines.md          # camadas MVC, mapeamento por framework e políticas (endpoints perigosos, erros)
    ├── refactoring-playbook.md    # 15 padrões de transformação com código antes/depois
    └── validation-protocol.md     # baseline, porta livre, boot, chamadas, comparação e limpeza
```

Invocação: `/refactor-arch [caminho-do-projeto]`. Sem argumento, o projeto é o diretório atual.

### Decisões de design

- **`SKILL.md` é o prompt; as referências são o conhecimento.** O `SKILL.md` só diz *o que fazer em cada fase e quais regras não podem ser quebradas*. Critérios de detecção, formatos e exemplos de código ficam nas 6 referências, lidas na fase em que são necessárias (via `${CLAUDE_SKILL_DIR}`, para funcionarem em qualquer projeto).
- **Três fases em ordem.** Fase 1 (análise, com resumo impresso), Fase 2 (auditoria + plano) e Fase 3 (refatoração + validação).
- **Perguntas ao usuário via clarificação.** As decisões do fluxo são perguntas com opções fixas (no Claude Code, `AskUserQuestion`). Cada pergunta tem um comportamento padrão para respostas não claras, e uma resposta livre com instrução clara vale mais que o padrão.
- **Plan mode opcional.** Antes do plano, se a sessão não estiver em plan mode, a skill pergunta: `A. Alterar para plan mode e gerar o plano` (entra em plan mode obrigatoriamente) ou `B. Seguir no modo atual e gerar o plano` (padrão). Aprovar o plano ao sair do plan mode **não** conta como confirmação da Fase 3.
- **Gate de confirmação.** Ao fim da Fase 2, nenhum arquivo-fonte foi alterado e a skill pergunta como prosseguir. Relatório, plano e evidências **podem e devem** ser gravados em `<projeto>/reports/` a qualquer momento e continuam salvos se a Fase 3 não for iniciada.
- **Dois checkpoints de modelo/effort.** Antes da Fase 1, com regra objetiva baseada em `${CLAUDE_EFFORT}`: effort `low` ou modelo muito simples (Haiku) param a skill e ela propõe subir. No gate da Fase 2, a pergunta varia:
  - modelo de tarefas rotineiras (Sonnet) com effort `low`/`medium`: `A. Prosseguir para a fase 3` ou `B. Não prosseguir, e direi ao agente o que fazer`;
  - qualquer outro caso (Haiku, Opus, Fable, effort `high`/`xhigh`/`max` ou configuração desconhecida): a pergunta traz uma sugestão de ajuste e as opções `A. Vou alterar o modelo/effort antes de prosseguirmos` (pausa até o usuário pedir para retomar), `B. Prossiga com modelo e effort atuais` (padrão) e `C. Não prosseguir, e direi ao agente o que fazer`.

  Quem troca o modelo/effort é sempre o usuário.
- **Plano separado do relatório.** A Fase 2 gera `audit-report.md` e `refactoring-plan.md`. O plano traz estrutura alvo, passos ordenados por severidade ligados a cada finding e padrão do playbook, o que *não* será tratado, o contrato a preservar e as mudanças de comportamento intencionais.
- **Limite de acesso.** A skill não lê nem escreve fora do projeto analisado (a exceção é ler as próprias referências), e a validação usa só o que existe no projeto e as ferramentas do sistema.
- **Contrato externo preservado e verificado.** Mesmas rotas, campos (inclusive nas respostas de erro) e comando de boot. Antes de alterar o código, a Fase 3 grava as respostas do app original em `reports/baseline-responses.txt`; depois da refatoração, grava `after-responses.txt` e compara. Toda diferença precisa estar declarada no plano; o resto é regressão e é corrigido.
- **Validação com protocolo fixo** (`validation-protocol.md`): script em `bash` explícito, porta livre conferida antes do boot, PID guardado e servidor sempre encerrado, dados restaurados entre execuções e arquivos temporários só em `reports/.tmp/`.
- **Política para endpoints perigosos.** Rotas de execução arbitrária ou destrutivas continuam existindo, mas ficam desligadas por padrão: só funcionam com um token vindo do ambiente (`ADMIN_TOKEN`), e a consulta arbitrária vira somente-leitura.
- **Todas as severidades recebem atenção.** A severidade define a *ordem* do relatório e do plano, não o que é procurado. Calibragem por few-shots curtos (3 exemplos genéricos por severidade) no próprio `SKILL.md`.

### Catálogo de anti-patterns

20 anti-patterns (6 CRITICAL, 4 HIGH, 6 MEDIUM, 4 LOW), cada um com sinais de detecção acionáveis e o padrão do playbook que o resolve. Os critérios de inclusão foram: ser citado no enunciado ou aparecer na análise manual dos 3 projetos, e ter um sinal que um agente consiga procurar no código ("query SQL concatenada", não "código ruim").

| ID | Anti-pattern | Severidade | Por que foi incluído |
| --- | --- | --- | --- |
| AP-SEC-01 | Credenciais/segredos hardcoded | CRITICAL | Citado no enunciado; presente nos 3 projetos |
| AP-SEC-02 | SQL Injection por concatenação | CRITICAL | Citado no enunciado; P1 inteiro |
| AP-SEC-03 | Senha em texto puro ou hash fraco | CRITICAL | MD5 (P3), hash caseiro (P2), texto puro (P1) |
| AP-SEC-04 | Dado sensível exposto em resposta ou log | CRITICAL | Senha em `to_dict`, cartão em log |
| AP-SEC-05 | Execução arbitrária / admin sem autenticação | CRITICAL | Rotas `/admin/*` do P1 |
| AP-ARCH-01 | God Class / God Module | CRITICAL | Citado no enunciado; `AppManager` (P2) |
| AP-ARCH-02 | Lógica de negócio na camada errada | HIGH | Citado no enunciado; rotas gordas (P3) e models (P1) |
| AP-ARCH-03 | Estado global mutável / conexão global | HIGH | Citado no enunciado; P1 e P2 |
| AP-ARCH-04 | Acoplamento sem injeção de dependência | HIGH | Citado no enunciado |
| AP-SEC-06 | Debug habilitado por padrão | HIGH | `debug=True` em P1 e P3 |
| AP-SEC-07 | API sem autenticação de base / privilégio autoatribuível (distinto de AP-SEC-05; RF-16) | CRITICAL/HIGH | `role: "admin"` aceito de requisição anônima em `POST/PUT /users` (P3). Nível 1 (restringir `role` com `ADMIN_TOKEN`) aplicado; nível 2 (JWT + rotas protegidas) proposto, não aplicado |
| AP-PERF-01 | Queries N+1 | MEDIUM | Citado no enunciado; P1, P2 e P3 |
| AP-QUAL-01 | Tratamento de erro genérico, sem handler central | MEDIUM | `except Exception` e `except:` repetidos |
| AP-QUAL-02 | Validação de entrada ausente ou fraca | MEDIUM | Citado no enunciado ("validações ausentes nas rotas") |
| AP-QUAL-03 | Duplicação de código | MEDIUM | Citado no enunciado |
| AP-DEPR-01 | APIs deprecated (com tabela obsoleto → moderno) | MEDIUM | Exigido pelo enunciado; `utcnow()` e `Query.get()` (P3) |
| AP-ARCH-05 | Callback hell | MEDIUM | Checkout do P2 |
| AP-QUAL-04 | `print`/`console.log` como log | LOW | Presente nos 3 projetos |
| AP-QUAL-05 | Magic numbers e enumerações soltas | LOW | Citado no enunciado |
| AP-QUAL-06 | Nomes ruins | LOW | Citado no enunciado |
| AP-QUAL-07 | Imports e código morto | LOW | P3 |

### Agnosticismo de tecnologia

- **Detecção por sinais, não por nomes.** O catálogo descreve padrões de código ("query SQL concatenada", "variável global mutável", "query dentro de laço"), com exemplos em Python e JavaScript, sem citar arquivos, tabelas ou rotas dos projetos.
- **Stack descoberta na Fase 1:** manifesto de dependências (`requirements.txt`, `package.json`, `go.mod`...) e imports indicam linguagem e framework; as rotas são inventariadas por padrões de cada framework (`@app.route`, `add_url_rule`, `app.get`...).
- **MVC mapeado por framework:** `mvc-guidelines.md` define as camadas de forma neutra e mostra como ficam em Flask (`create_app`, Blueprints, `errorhandler`) e Express (`Router`, middleware de erro).
- **Adaptação ao ponto de partida:** o mesmo conjunto de regras serviu para um monólito (P1), uma God Class em Node (P2) e um projeto já em camadas (P3), onde a skill preservou a organização existente.
- **Validação independente de stack:** o protocolo usa `bash`, `curl` e a comparação de respostas antes/depois, sem depender de um framework de testes.

### Desafios encontrados e soluções

| Desafio                                                                                 | Impacto                                                                                               | Como foi resolvido                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| No macOS, o Receptor AirPlay ocupa a porta 5000                                         | P1 e P3 não sobem com `python app.py`, que fixa a porta 5000 (`Errno 48: Address already in use`)     | O baseline usou o mesmo app iniciado com `flask --app app run --port 5001` (P1) e `--port 5002` (P3), sem alterar o código. No código refatorado, a porta vem de config/variável de ambiente (`PORT`). |
| Respostas com datas geradas na hora e listas cuja ordem pode mudar entre implementações | Um `diff` direto entre antes e depois daria falsos positivos                                          | O `smoke.py` troca datas por `<timestamp>` e, quando a spec pede, ordena listas antes de gravar (usado no relatório financeiro do P2).                                                                 |
| Servidores que criam processos filhos (`npm start` → `node`)                            | Encerrar só o processo principal pode deixar a porta ocupada                                          | O `smoke.py` sobe o app numa sessão própria e encerra o grupo de processos inteiro.                                                                                                                    |
| O agente já tinha lido o projeto antes de invocar a skill e pulou ou resumiu a Fase 1 | O resumo da análise não aparecia no chat, só no arquivo salvo | A Fase 1 passou a ser obrigatória em toda invocação, com o bloco impresso antes de abrir o catálogo e repetido no gate. **Ainda não resolvido após 3 iterações**: o agente agrupa as leituras das Fases 1 e 2 e só escreve no chat no fim. Próximo passo: encerrar a Fase 1 com uma pergunta via clarificação, que obriga a abrir um turno novo. |
| O agente lia e usava arquivos de fora do projeto (o smoke test e as evidências deste repositório) | Quebra a independência da validação e o agnosticismo | Seção "Limite de acesso" no `SKILL.md` e argumento com o caminho do projeto. Na 2ª execução restou uma escrita em `/tmp`; na 3ª, nada em `/tmp`, mas houve uma consulta ao `git` na raiz do repositório. |
| A regra "nenhuma escrita antes do sim" contradizia a ordem de salvar o relatório na Fase 2 | Ambiguidade sobre o que podia ser gravado | Separação explícita: arquivo-fonte só depois do "sim"; análises, relatórios, planos e evidências sempre que pedidos. |
| O agente validou contra a porta 5000 e tratou o 403 do AirPlay como resposta da aplicação | Validação inicial falsa; retrabalho | Resolvido na iteração 3 pelo protocolo de validação: porta livre conferida antes do boot e passada via `PORT`. |
| Validação deixou um servidor rodando ao terminar | Porta ocupada por processo órfão | Resolvido na iteração 3: PID guardado e `trap` no script; nenhum servidor órfão na 3ª execução. |
| O código original já tinha sido apagado quando o baseline precisou ser recapturado | O agente reescreveu o original de memória em `reports/.tmp/original` (conferido contra o baseline real) | Frágil. Próximo passo: copiar os arquivos-fonte originais para `reports/.tmp/` antes de qualquer alteração e capturar os IDs das respostas no script, em vez de fixá-los. |
| A correção de credenciais alcançou a senha do admin do seed | Login com a credencial documentada passou a dar 401; sem a variável, a senha gerada vai para o log | Declarado no plano, mas não detectado pela validação da skill. Próximo passo: manter os valores documentados dos seeds (parte do contrato) ou documentar como restaurá-los, nunca registrando segredos em log. |

### Iterações da skill

Metodologia: cada iteração roda a skill numa **cópia nova** do projeto, fora do repositório, avalia o relatório, o plano e a refatoração, e compara a aplicação refatorada com o baseline pelo mesmo smoke test.

#### Iteração 1 — primeira versão (Projeto 1)

Skill com `SKILL.md`, 5 referências, 20 anti-patterns e 14 padrões de refatoração. Foco em CRITICAL e HIGH.

| Aspecto | Resultado |
| --- | --- |
| Relatório | 19 achados (7 CRITICAL, 4 HIGH, 4 MEDIUM, 4 LOW). Todos os 12 da análise manual foram encontrados, mais 7 novos, com `arquivo:linha`, ordem por severidade e padrão do playbook. Contagem correta: 4 arquivos, ~780 linhas. |
| Plano e gates | Plano completo no chat, com as mudanças de comportamento listadas **antes** de executar. Os dois checkpoints funcionaram: o modelo/effort foi aprovado para auditar e, no gate, a skill sugeriu baixar; a refatoração foi feita com Sonnet 5.5 e effort medium. |
| Refatoração | Smoke test: 29/31 com o status esperado. As únicas diferenças em todo o `diff` são mudanças de segurança documentadas (`/health` sem a chave e com `debug` falso, `/usuarios` sem a senha, `/admin/*` com 403 sem token). 12/12 testes de segurança passaram, incluindo bypass de login por injeção (agora 401). |
| Problemas | O bloco da Fase 1 não foi impresso. O plano ficou só no chat. O agente leu o smoke test e as evidências de fora do projeto. O `SKILL.md` se contradizia sobre escrita antes do "sim". O bloco de resumo da Fase 3 não existia no template e foi improvisado. |

#### Iteração 2 — ajustes de processo (Projeto 1)

Mudanças: Fase 1 obrigatória e impressa; remoção da instrução de entrar em plan mode; 3 few-shots genéricos por severidade; separação entre "arquivo-fonte" e "artefatos de análise"; limite de acesso à raiz do projeto; caminho do projeto como argumento (`$ARGUMENTS`), com saída em `<projeto>/reports/`; fim do foco em CRITICAL/HIGH; template do bloco da Fase 3.

| Aspecto | Resultado |
| --- | --- |
| Melhorou | O argumento foi aplicado, os 3 artefatos (`audit-report.md`, `refactoring-plan.md`, `validation-report.md`) foram gerados no projeto, o plano passou a ter "Not addressed", e o checkpoint inicial chegou a **parar** com Sonnet e effort baixo. 20 achados (8 CRITICAL, 4 HIGH, 4 MEDIUM, 4 LOW), sem APIs deprecated. Smoke test: 29/31, com o mesmo conjunto de diferenças de segurança. |
| Não melhorou | O bloco da Fase 1 **continuou sem aparecer no chat** (só foi gravado no arquivo): a regra em texto não bastou. Com Opus e effort baixo, o checkpoint só comentou e seguiu. |
| Regrediu | Dois `PUT`/`DELETE` de produto inexistente passaram a devolver `"sucesso": false`, e `ambiente` passou de `producao` para `desenvolvimento`: mudanças de contrato não declaradas. `/admin/query` com token **aceitou escrita** (a primeira execução era somente-leitura). Pedir o mesmo produto em dois itens burla a checagem de estoque, que a 1ª execução tinha corrigido e a 2ª nem detectou. |
| Higiene da validação | Gravou um arquivo temporário em `/tmp`, validou primeiro na porta errada, tropeçou na separação de palavras do `zsh` e deixou um servidor rodando. O relatório de validação contou 2 concatenações de SQL remanescentes quando eram 3. |

**Leitura geral:** a qualidade do relatório e da estrutura MVC gerada é estável entre execuções. O que varia é o que o `SKILL.md` deixa em aberto: política para endpoints perigosos, invariantes de negócio e formato exato da validação. Esses pontos dependem de sorte enquanto não estiverem escritos como regra.

#### Iteração 3 — perguntas via clarificação e validação com baseline (Projeto 1)

Mudanças:
1. **Perguntas via clarificação:** plan mode opcional antes do plano e gate da Fase 3 com 2 ou 3 opções, conforme o modelo e o effort.
2. **Checkpoint inicial objetivo,** com `${CLAUDE_EFFORT}`.
3. **Bloco da Fase 1** exigido no chat antes de abrir o catálogo e repetido no gate.
4. **Validação:** baseline antes de alterar o código e comparação depois; novo `validation-protocol.md` com script-modelo em `bash`.
5. **Política para endpoints perigosos** (RF-15).
6. **Autenticação de base e campos de privilégio** (RF-16): feedback pós-entrega apontou que o AP-SEC-05 do P3 ficou "Not addressed". O padrão foi separado em AP-SEC-07 e a skill agora aplica o nível 1 (só admin com `X-Admin-Token` altera `role`); reexecutada no P3 (`task-manager-api/reports/`).
6. **Invariantes de negócio no catálogo.**
7. **Ajustes no código gerado:** relatório de validação com saídas reais, nada de `str(err)`, SQL fixo em vez de concatenar constantes, `validators/` e exceções dentro da estrutura.

| Aspecto | Resultado |
| --- | --- |
| Perguntas e gates | Funcionaram como especificado. A pergunta do plan mode usou as opções exatas; com "A", entrou em plan mode. Ao aprovar o plano, a ferramenta liberou a implementação, mas a skill só salvou o plano e foi para o gate. Com Opus e effort `high`, o gate trouxe a sugestão e as 3 opções; com "A", pausou, e ao ouvir "retome" (já com Sonnet e effort `medium`) releu relatório e plano e seguiu para a Fase 3. |
| Checkpoint inicial | `${CLAUDE_EFFORT}` foi substituído por `high` e a skill seguiu, como esperado. |
| Relatório | 21 findings (7 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW), cobrindo os 12 da análise manual. Contagem correta (4 arquivos, 780 linhas) e invariantes de negócio detectados (quantidade negativa, itens repetidos, pedido de usuário inexistente, status de pedido inexistente). |
| Validação da skill | 64 chamadas antes e 64 depois, com o `diff` real no relatório e cada diferença ligada a um item do plano. Rotas protegidas testadas com e sem token. Nenhum servidor órfão, dados restaurados, `reports/.tmp` apagado, nada em `/tmp`. |
| Refatoração | Nenhum sinal do catálogo restante. Formato dos erros idêntico ao original. Na raiz ficou só o `app.py`. Smoke test: 29/31 (com `SEED_ADMIN_PASSWORD=admin123`), e testes de segurança 12/12, incluindo os dois que falharam na 2ª execução (item repetido no pedido e `/admin/query` somente-leitura). |
| Problemas | O bloco da Fase 1 **continuou fora do chat**: o catálogo foi aberto antes dele, e o gate não repetiu o bloco. Uma consulta ao `git` na raiz do repositório saiu da PROJECT_ROOT. O código original foi reconstruído de memória para recapturar o baseline. A senha do admin do seed deixou de ser a documentada e, sem a variável, é escrita no log. Algumas mudanças declaradas não são de segurança (pedido inexistente → 404, e-mail duplicado → 400), ao contrário do que diz o `SKILL.md`. |

**Comparação das três execuções (Projeto 1):**

| | Iteração 1 | Iteração 2 | Iteração 3 |
| --- | --- | --- | --- |
| Findings | 19 | 20 | 21 |
| Smoke test oficial | 29/31 | 29/31 | 29/31 (28/31 sem `SEED_ADMIN_PASSWORD`) |
| Testes de segurança | 12/12 | 10/12 | 12/12 |
| Sinais do catálogo restantes no código | 2 | 4 | 0 |
| Formato dos erros preservado | sim | não | sim |
| Servidor órfão / escrita em `/tmp` | — | sim / sim | não / não |
| Bloco da Fase 1 impresso no chat | não | não | não |

**Situação frente ao enunciado (Projeto 1):** todos os itens do checklist de validação e os 4 critérios de aceite são atendidos, exceto **"a Fase 1 imprime o resumo"**: o bloco é gerado e gravado no topo do `audit-report.md`, mas não aparece no chat. Os Projetos 2 e 3 ainda não foram executados.

#### Iteração 4 — contrato, dados e higiene (Projetos 1, 2 e 3)

Motivada pela execução da iteração 3 nos Projetos 2 e 3 (cópias fora do repositório), que mostrou: comandos `git` (`git rm --cached`, `git reset`) executados pelo agente, escrita fora do projeto no momento da auditoria, mudanças que não eram de segurança (mensagem alterada e histórico financeiro apagado no P2; hashes MD5 sem migração no P3; senha do admin do seed alterada e escrita em log no P1) e cobertura de validação fraca no P2.

| Problema observado | Regra adicionada |
| --- | --- |
| Comandos `git` pelo agente | Proibido qualquer comando de controle de versão; apagar e mover com `rm`/`mv` |
| Script no scratchpad da ferramenta, `zsh` quebrando buscas | `bash` explícito e arquivos temporários em `reports/.tmp/` em **todas** as fases |
| Código original reconstruído de memória | Cópia dos fontes em `reports/.tmp/original-src/` antes de alterar; reconstruir de memória é proibido |
| IDs fixos e pouca cobertura na validação | IDs capturados da resposta; cobertura mínima por rota (sucesso, ID inexistente, corpo incompleto, JSON malformado, rotas protegidas com e sem token, login com credencial do seed) |
| Seed alterado, segredo em log | Seeds mantêm os valores documentados; nenhum segredo vai para log ou resposta |
| Troca de hash invalidando credenciais | Migração dos hashes existentes ("rehash on login", RF-08) |
| Correção apagando dados | Nenhuma correção apaga ou altera registros persistidos; vai para "Not addressed" |
| Mensagens e regras alteradas | Mensagens preservadas; só duas categorias de mudança aceitas: **segurança** e **rejeição de entrada claramente inválida** |

**Resultado:** a skill foi executada nos 3 projetos, nas pastas reais. Os relatórios foram validados contra o código original (20, 19 e 17 findings, Summary e Total coerentes, ordem correta, 320 referências de linha e 56 amostras de conteúdo conferidas, cobertura de 33 dos 34 achados da análise manual) e copiados para `reports/`. O smoke test independente nas pastas refatoradas (seção C) mostrou apenas as diferenças declaradas nos planos: P1 29/31, P2 5/8 e P3 35/35, onde os 403 vêm da ausência do token na spec do baseline. O login com a credencial de exemplo do seed continua funcionando no P1, e o `validation-report.md` do P3 traz a seção de migração de hash MD5.

**Pendência conhecida:** o bloco `PHASE 1: PROJECT ANALYSIS` é gerado e gravado no topo de cada `audit-report.md`, mas não é impresso no chat. A decisão foi não tratar mais esse ponto.

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

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
| --- | :-: | :-: | :-: | :-: | :-: | --- |
| P1 code-smells-project | 6 | 5 | 5 | 4 | 20 | [audit-project-1.md](reports/audit-project-1.md) |
| P2 ecommerce-api-legacy | 5 | 5 | 5 | 4 | 19 | [audit-project-2.md](reports/audit-project-2.md) |
| P3 task-manager-api | 3 | 4 | 6 | 4 | 17 | [audit-project-3.md](reports/audit-project-3.md) |

Os relatórios foram validados contra o código original: Summary e Total batem com os findings, a ordem é CRITICAL → LOW, todos os findings têm `arquivo:linha` (320 referências dentro do tamanho dos arquivos originais e 56 amostras de conteúdo conferidas) e cobrem 33 dos 34 achados da análise manual. O P3 reporta `datetime.utcnow()` (~19×) e `Query.get()` (16×) como APIs deprecated; P1 e P2 declaram que não há nenhuma. Artefatos completos de cada execução (plano, respostas antes/depois e relatório de validação) ficam em `<projeto>/reports/`.

### Estrutura antes e depois

Código-fonte apenas (`.py` e `.js`; sem dependências, bancos e `reports/`). A raiz do projeto aparece como `./`. O "antes" vem do commit inicial do repositório.

| Projeto | Diretórios (antes → depois) | Arquivos de código (antes → depois) | Linhas (antes → depois) |
| --- | :-: | :-: | :-: |
| Projeto 1 — code-smells-project | 1 → 9 | 4 → 36 | 780 → 1087 |
| Projeto 2 — ecommerce-api-legacy | 1 → 10 | 3 → 29 | 180 → 654 |
| Projeto 3 — task-manager-api | 5 → 8 | 15 → 29 | 1158 → 1317 |

#### Projeto 1 — code-smells-project

**Antes**
```
./                  4 arquivo(s),  780 linhas
```
**Depois**
```
./                  1 arquivo(s),   34 linhas
config/             3 arquivo(s),   58 linhas
controllers/        7 arquivo(s),  205 linhas
db/                 3 arquivo(s),  157 linhas
middlewares/        3 arquivo(s),   50 linhas
models/             5 arquivo(s),  256 linhas
routes/             7 arquivo(s),   62 linhas
services/           5 arquivo(s),  134 linhas
validators/         2 arquivo(s),  131 linhas
```

#### Projeto 2 — ecommerce-api-legacy

**Antes**
```
src/                3 arquivo(s),  180 linhas
```
**Depois**
```
src/                1 arquivo(s),   72 linhas
src/config/         2 arquivo(s),   36 linhas
src/controllers/    3 arquivo(s),   35 linhas
src/db/             2 arquivo(s),   70 linhas
src/middlewares/    4 arquivo(s),   51 linhas
src/models/         5 arquivo(s),  104 linhas
src/routes/         4 arquivo(s),   37 linhas
src/services/       5 arquivo(s),  182 linhas
src/utils/          1 arquivo(s),   21 linhas
src/validators/     2 arquivo(s),   46 linhas
```

#### Projeto 3 — task-manager-api

**Antes**
```
./                  3 arquivo(s),  136 linhas
models/             4 arquivo(s),  122 linhas
routes/             4 arquivo(s),  734 linhas
services/           2 arquivo(s),   49 linhas
utils/              2 arquivo(s),  117 linhas
```
**Depois**
```
./                  2 arquivo(s),  119 linhas
config/             2 arquivo(s),   44 linhas
controllers/        6 arquivo(s),  233 linhas
middlewares/        2 arquivo(s),   30 linhas
models/             5 arquivo(s),  263 linhas
routes/             6 arquivo(s),  142 linhas
services/           4 arquivo(s),  196 linhas
validators/         2 arquivo(s),  290 linhas
```

### Checklist de validação

| Item | P1 | P2 | P3 |
| --- | :-: | :-: | :-: |
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | ✓ | ✓ | ✓ |
| Framework detectado corretamente | ✓ | ✓ | ✓ |
| Domínio da aplicação descrito corretamente | ✓ | ✓ | ✓ |
| Número de arquivos analisados condiz com a realidade¹ | ✓ | ✓ | ✓ |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template definido nos arquivos de referência | ✓ | ✓ | ✓ |
| Cada finding tem arquivo e linhas exatos | ✓ | ✓ | ✓ |
| Findings ordenados por severidade (CRITICAL → LOW) | ✓ | ✓ | ✓ |
| Mínimo de 5 findings identificados | ✓ | ✓ | ✓ |
| Detecção de APIs deprecated incluída (se aplicável) | ✓ | ✓ | ✓ |
| Skill pausa e pede confirmação antes da Fase 3 | ✓ | ✓ | ✓ |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue padrão MVC | ✓ | ✓ | ✓ |
| Configuração extraída para módulo de config (sem hardcoded) | ✓ | ✓ | ✓ |
| Models criados para abstrair dados | ✓ | ✓ | ✓ |
| Views/Routes separadas para visualização ou roteamento | ✓ | ✓ | ✓ |
| Controllers concentram o fluxo da aplicação | ✓ | ✓ | ✓ |
| Error handling centralizado | ✓ | ✓ | ✓ |
| Entry point claro | ✓ | ✓ | ✓ |
| Aplicação inicia sem erros | ✓ | ✓ | ✓ |
| Endpoints originais respondem corretamente² | ✓ | ✓ | ✓ |

¹ P3: o relatório informa 12 arquivos analisados mais 3 `__init__.py` vazios (15 no total).
² Respondem com o mesmo status e formato do original, exceto as mudanças declaradas no plano (ver "Evidências de execução"). As rotas `/admin/*` (P1) e `/api/admin/*` e `DELETE /api/users/:id` (P2) passam a exigir `ADMIN_TOKEN`; sem ele respondem 403.

### Critérios de aceite

| Critério | P1 | P2 | P3 |
| --- | :-: | :-: | :-: |
| Fase 1 detecta a stack corretamente | ✓ | ✓ | ✓ |
| Fase 2 encontra ≥ 5 findings | ✓ (20) | ✓ (19) | ✓ (17) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | ✓ (11) | ✓ (10) | ✓ (7) |
| Aplicação funciona após a refatoração | ✓ | ✓ | ✓ |

### Evidências de execução

Validação independente da skill, com o mesmo smoke test do baseline (`scripts/smoke.py`), rodado nas pastas refatoradas com o comando de boot original (`python app.py` e `npm start`). Saídas completas em [`evidencias/depois/`](evidencias/depois/); comparação com [`evidencias/py311-node22/`](evidencias/py311-node22/) (código original).

| Projeto | Requisições | Status como esperado | Linhas do contrato que mudaram |
| --- | :-: | :-: | :-: |
| P1 | 31 | 29/31 | 5 |
| P2 | 8 | 5/8 | 3 |
| P3 | 35 | 35/35 | 4 |

**Todas as diferenças são mudanças declaradas nos planos:**
- **P1:** `GET /health` deixa de devolver `secret_key` (e `debug` passa a `false`); `GET /usuarios` e `/usuarios/<id>` deixam de devolver `senha`; `POST /admin/query` e `/admin/reset-db` respondem 403 sem token. O login com a credencial de exemplo do seed continua funcionando.
- **P2:** `GET /api/admin/financial-report` e `DELETE /api/users/:id` respondem 403 sem `X-Admin-Token`. As 5 chamadas de checkout ficam idênticas ao original.
- **P3:** o campo `password` (hash) sai das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. As 35 chamadas continuam com o mesmo status do original.

Os 403 contam como "status inesperado" apenas porque a spec do baseline não envia o token. Com o token configurado, as rotas protegidas voltam ao comportamento original, verificado pela própria skill em `<projeto>/reports/validation-report.md` (seção "Rotas protegidas").

Evidências geradas pela skill em cada projeto (`reports/`): `baseline-responses.txt` e `after-responses.txt` (P1: 78 chamadas, P2: 26, P3: 100, mesmas chamadas antes e depois), `validation-report.md` (diff real, reverificação do catálogo, limpeza) e `refactoring-plan.md`. Log de boot do P2 refatorado: [`evidencias/depois/p2.server.log`](evidencias/depois/p2.server.log).

As aplicações são APIs sem interface; no lugar de screenshots, as evidências são os logs de boot e as respostas HTTP registradas acima.

### Comportamento da skill em stacks diferentes

- **P1 (Flask, monólito em 4 arquivos):** reestruturação completa para `config/`, `db/`, `models/`, `services/`, `controllers/`, `routes/`, `validators/` e `middlewares/`. Trocou SQL concatenado por consultas parametrizadas e a conexão global por conexão por requisição.
- **P2 (Express, uma God Class):** mesmas três fases numa stack diferente. Substituiu callbacks aninhados por `async/await`, escolheu `crypto.scrypt` no lugar do hash caseiro e criou um logger que não registra cartão nem chaves.
- **P3 (Flask com camadas parciais):** aproveitou a organização existente (manteve `models/`, `routes/`, `services/`, `utils/`, `seed.py`) e acrescentou `controllers/`, `config/`, `middlewares/`. Removeu todas as ocorrências de `Query.get()` e `utcnow()` e migrou hashes MD5 antigos no primeiro login.
- **Em comum:** nos três, os endpoints originais continuaram respondendo, as rotas perigosas ficaram desligadas por padrão e nenhum servidor ficou rodando ao final da validação.

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

A skill está em `code-smells-project/.claude/skills/refactor-arch/` e copiada para os outros dois projetos. Execução:

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

### Rodar os apps refatorados

O comando de boot é o mesmo do original (`python app.py` nos projetos Python, `npm start` no Node). Diferenças:

- A porta, o modo debug e os segredos vêm de variáveis de ambiente (veja o `.env.example` de cada projeto). Padrões: porta original e `DEBUG=false`.
- As rotas administrativas (P1: `/admin/*`; P2: `/api/admin/financial-report` e `DELETE /api/users/:id`) ficam desligadas até definir `ADMIN_TOKEN`; depois, envie o header `X-Admin-Token`.
- P3: para bancos criados antes da refatoração, os hashes MD5 são migrados no primeiro login; para um banco novo, rode `python seed.py`.

Exemplo: `ADMIN_TOKEN=meu-token PORT=5050 .venv/bin/python app.py`.
