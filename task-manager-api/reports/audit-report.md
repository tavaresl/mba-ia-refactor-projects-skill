# Audit Report — task-manager-api

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.11 (.venv/bin/python 3.11.17)
Framework:     Flask 3.0.0
Dependencies:  Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.6 instalado), Flask-CORS 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domain:        API REST de gerenciamento de tarefas — CRUD de tasks, usuários e categorias, login, busca, estatísticas e relatórios de produtividade
Architecture:  Camadas parciais — existem models/, routes/, services/ e utils/, mas as rotas concentram validação, regra de negócio, serialização e persistência; services/ e utils/ não são usados pelas rotas
Source files:  12 files analyzed (~1155 linhas; + 3 __init__.py vazios em routes/, services/, utils/)
DB tables:     users, tasks, categories (SQLite via Flask-SQLAlchemy, sqlite:///tasks.db → instance/tasks.db)
Entry point:   app.py (boot: python app.py, porta 5000 fixa no código; host 0.0.0.0, debug=True; porta alternativa sem editar código: flask --app app run --port <porta>)
Setup:         pip install -r requirements.txt; python seed.py (apaga e recria 3 usuários, 4 categorias, 10 tasks; o banco é criado por db.create_all() ao importar app.py)
================================
```

Inventário de rotas (22):

```
GET    /
GET    /health
GET    /tasks
GET    /tasks/<int:task_id>
POST   /tasks
PUT    /tasks/<int:task_id>
DELETE /tasks/<int:task_id>
GET    /tasks/search          (query: q, status, priority, user_id)
GET    /tasks/stats
GET    /users
GET    /users/<int:user_id>
POST   /users
PUT    /users/<int:user_id>
DELETE /users/<int:user_id>
GET    /users/<int:user_id>/tasks
POST   /login
GET    /reports/summary
GET    /reports/user/<int:user_id>
GET    /categories
POST   /categories
PUT    /categories/<int:cat_id>
DELETE /categories/<int:cat_id>
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLite)
Files:   12 analyzed | ~1155 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Privilégio autoatribuível — campo role aceito do corpo sem credencial (AP-SEC-07)
File: routes/user_routes.py:52,71-72,78 (POST /users); routes/user_routes.py:119-122 (PUT /users/<id>)
Description: `role` vem do corpo (`data.get('role', 'user')` / `data['role']`) e só é checado contra a lista ['user', 'admin', 'manager']; nenhuma credencial é exigida. Comprovado em cópia isolada: `POST /users {"role":"admin"}` anônimo → 201 com `"role":"admin"`; `PUT /users/2 {"role":"admin"}` anônimo → 200, promovendo "Maria Santos" a admin.
Impact: qualquer cliente anônimo cria um administrador ou muda o papel de qualquer usuário; o papel "admin" não protege nada.
Recommendation: RF-16 nível 1 — valor de role diferente do padrão (criação) ou do atual (atualização) exige `X-Admin-Token` igual ao `ADMIN_TOKEN` do ambiente (comparação em tempo constante); sem token configurado ou com token errado → 403 `{"error": "Acesso negado"}`, antes de qualquer escrita.

### [CRITICAL] Hash de senha exposto nas respostas e nos logs (AP-SEC-04)
File: models/user.py:16-25 (linha 21: 'password': self.password); usado em routes/user_routes.py:33 (GET /users/<id>), 85-86 (POST /users), 129 (PUT /users/<id>), 209 (POST /login); logs em routes/user_routes.py:89 e routes/task_routes.py:153
Description: `User.to_dict()` serializa o hash da senha, e 4 endpoints o devolvem a clientes anônimos. Comprovado: `GET /users/1` → `"password":"81dc9bdb52d04dc20036dbd8313ed055"` (MD5 de "1234"). Além disso, `print(f"ERRO: {str(e)}")` grava a mensagem da exceção do SQLAlchemy, que inclui os parâmetros do INSERT (comprovado no log de task_routes: `[parameters: ('abcd', {'a': 1}, 'pending', ...)]`); numa falha de INSERT em users, o hash vai para o log.
Impact: qualquer cliente obtém o hash de todos os usuários iterando ids; com MD5 sem sal (finding seguinte) a senha original é recuperada em segundos.
Recommendation: RF-13 — remover `password` do `to_dict`; logar sem `str(e)` e configurar o engine com `hide_parameters=True`.

### [CRITICAL] Senha com hash fraco — MD5 sem sal (AP-SEC-03)
File: models/user.py:3,27-32; seed.py:19,26,33
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` sem sal, e `check_password` compara com `==` (tempo não constante). As senhas do seed ("1234", "abcd", "pass") viram hashes MD5 conhecidos; senhas iguais geram hashes iguais.
Impact: qualquer vazamento do banco (ou da API, finding anterior) revela as senhas.
Recommendation: RF-08 — `werkzeug.security.generate_password_hash`/`check_password_hash`; reconhecer o hash MD5 legado (32 hex), validá-lo com `hmac.compare_digest` e regravar no formato novo no primeiro login bem-sucedido; seed com as mesmas senhas documentadas.

### [CRITICAL] Segredos hardcoded no código (AP-SEC-01)
File: app.py:13; services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` literal; credenciais SMTP literais (`email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`, host e porta fixos). Nada é lido do ambiente, embora `python-dotenv` esteja nas dependências e exista `.env.example`.
Impact: segredos versionados vazam junto com o repositório e não podem ser trocados por ambiente; a chave conhecida permitiria forjar qualquer assinatura que venha a usar `SECRET_KEY`.
Recommendation: RF-01 — `config/settings.py` lendo `SECRET_KEY`, `SMTP_*` e demais parâmetros do ambiente (e do `.env` da raiz do projeto), sem default para segredos.

### [HIGH] API sem autenticação de base e token de login previsível (AP-SEC-07)
File: routes/user_routes.py:207-211; models/user.py:34-38; todas as rotas de routes/task_routes.py, routes/user_routes.py e routes/report_routes.py
Description: nenhuma rota verifica credencial (a busca por `before_request`, `login_required`, `Authorization` e `jwt` só encontra o token falso). `POST /login` devolve `'fake-jwt-token-' + str(user.id)` — previsível e nunca validado. `User.is_admin()` nunca é chamado. As 9 rotas de escrita/exclusão (POST/PUT/DELETE de /tasks, /users e /categories) estão abertas, e `GET /users` lista o e-mail de todos os usuários.
Impact: qualquer cliente lê, altera e apaga tasks, usuários e categorias de terceiros.
Recommendation: RF-16 nível 2 (token assinado com expiração, `login_required`/`role_required`, checagem de dono do recurso). Muda o contrato de todas as rotas e o token do /login, por isso fica para decisão do usuário; o nível 1 (finding CRITICAL acima) vale independentemente.

### [HIGH] Debug habilitado no boot e exposto em todas as interfaces (AP-SEC-06)
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug no comando de boot oficial (`python app.py`), escutando em todas as interfaces de rede.
Impact: toda exceção não tratada (há várias — ver AP-QUAL-02) devolve página com traceback e console interativo do Werkzeug; com o PIN, execução remota de código.
Recommendation: RF-01 — `DEBUG` vindo do ambiente com default `false`; `HOST`/`PORT` do ambiente mantendo `0.0.0.0`/`5000` como padrão.

### [HIGH] Regra de negócio, validação e persistência dentro das rotas (AP-ARCH-02)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132, 134-151, 185-211; routes/report_routes.py:12-155, 157-223
Description: as funções de rota validam o payload, aplicam regras de domínio (task atrasada, normalização de tags, unicidade de e-mail, exclusão em cascata das tasks ao apagar usuário, taxas de conclusão, agregações dos relatórios) e falam direto com o ORM (`db.session.add/commit`). Não há controllers, e `services/` e `utils/` não são chamados por nenhuma rota. O CRUD de categorias está no blueprint de relatórios.
Impact: regras não testáveis sem HTTP, duplicadas e já divergentes entre rotas; qualquer mudança exige editar várias rotas.
Recommendation: RF-04 — rotas finas → controllers → services/models; /categories em blueprint próprio.

### [HIGH] Acoplamento sem composition root nem injeção de dependência (AP-ARCH-04)
File: app.py:9-31; services/notification_service.py:5-20; seed.py:2
Description: a app é criada no import do módulo, com config literal e `db.create_all()` executado como efeito colateral do import; sem `create_app()`, não há como subir a app com outra config ou outro banco (ex.: testes). `NotificationService` instancia `smtplib.SMTP` diretamente e fixa host e credenciais no construtor. `seed.py` depende dos efeitos colaterais de `import app`.
Impact: impossível testar em isolamento ou trocar banco/SMTP por ambiente; importar `app` já cria o banco.
Recommendation: RF-03/RF-05 — `create_app()` como composition root, config injetada, inicialização do schema explícita, dependências do serviço recebidas no construtor.

### [MEDIUM] Validação de entrada fraca e invariantes de negócio violados (AP-QUAL-02)
File: routes/task_routes.py:87-124, 140-144, 166-198, 209-213, 260-264; routes/user_routes.py:44-65, 102-125, 187-202; routes/report_routes.py:169-180, 196-202
Description: comprovado em cópia isolada do app original:
- Erro 500 por entrada inválida: corpo JSON que não é objeto (`[1]`, `"x"`) em POST/PUT; `title` não-texto em POST/PUT /tasks; `priority` texto ou nulo (`"5"`, `null`); `tags` com itens não-texto (`[1,2]`); `description`/`color` objeto (500 "Erro ao criar task"/"Erro ao criar categoria"); `email`/`password` não-texto em POST /users, PUT /users e /login; `active: "x"` (500 "Erro ao atualizar"); `PUT /categories` com corpo `null` (a rota não checa o corpo); `/tasks/search?priority=abc` ou `user_id=abc` (`int()` sem tratamento).
- Entrada inválida aceita: `priority: 2.5` é gravado como 2.5 e `priority: true` como 1 (prioridade é inteiro de 1 a 5); `user_id: 0` / `category_id: 0` pulam a checagem de existência (`if user_id:`) e gravam referência solta; `PUT /users` e `PUT /categories` aceitam `name: ""` (o POST exige nome) e `name: null` vira 500; `name: 123` e `tags: 123` são gravados como texto.
- JSON malformado devolve a página HTML 400 genérica do Flask, fora do formato `{"error": ...}` da rota.
- Busca: `q` entra no LIKE sem escapar `%`/`_` (`q=%` devolve tudo). Não é injeção (o valor é parâmetro ligado), mas o filtro fica incorreto.
Impact: erros 500 provocados pelo cliente, dados inconsistentes (prioridade fora do domínio, referências soltas, nomes vazios) e regras diferentes entre criar e atualizar.
Recommendation: RF-14 — camada `validators/` com tipo e invariantes por campo, respondendo 4xx no formato da rota e na mesma posição da checagem original; existência de `user_id`/`category_id` checada para qualquer valor não nulo.

### [MEDIUM] Tratamento de erro genérico e sem handler central (AP-QUAL-01)
File: routes/task_routes.py:13,62-63,137,151-154,204,221-223,236-238; routes/user_routes.py:87-90,130-132,149-151; routes/report_routes.py:186-188,207-209,221-223; utils/helpers.py:46,49,88; services/notification_service.py:23-25
Description: 16 blocos `except:`/`except Exception` espalhados; GET /tasks embrulha o handler inteiro num `except:` que esconde qualquer erro como "Erro interno". Não há `errorhandler`: toda exceção fora desses blocos vira página HTML 500 (9 casos comprovados) ou, com `debug=True`, o traceback do debugger.
Impact: causa real escondida, respostas inconsistentes (JSON × HTML), detalhes internos expostos em debug.
Recommendation: RF-07 — `middlewares/errors.py` com `ApiError` e handler central que preserva o formato `{"error": "<mensagem original>"}`; rotas deixam de capturar `Exception`.

### [MEDIUM] Queries N+1 e contagens repetidas (AP-PERF-01)
File: routes/task_routes.py:14-57 (GET /tasks), 275-287 (GET /tasks/stats); routes/user_routes.py:12-22 (GET /users); routes/report_routes.py:15-30, 53-68 (GET /reports/summary), 159-164 (GET /categories)
Description: GET /tasks faz `User.query.get` e `Category.query.get` para cada task; GET /users carrega `u.tasks` de cada usuário só para contar; GET /categories faz um COUNT por categoria; /reports/summary faz uma query de tasks por usuário, mais 12 COUNTs separados, e carrega todas as tasks; /tasks/stats faz 5 COUNTs e carrega todas as tasks.
Impact: o número de queries cresce linearmente com usuários, tasks e categorias.
Recommendation: RF-06 — `selectinload` para user/category e contagens com GROUP BY numa única query.

### [MEDIUM] Duplicação de lógica, serialização e validação (AP-QUAL-03)
File: routes/task_routes.py:17-39,71-80,96-114,140-144,166-184,209-213,283-287,296; routes/user_routes.py:61,71,106,120,162-180; routes/report_routes.py:19-22,33-37,67,132-135,151; models/task.py:23-60; utils/helpers.py:14-23,57-116
Description: a regra de "task atrasada" está copiada 6 vezes nas rotas, enquanto `Task.is_overdue()` existe e não é usado; GET /tasks replica `Task.to_dict()` campo a campo; a lista de status aparece 5 vezes, a de papéis 3 vezes e a regex de e-mail 3 vezes; validações de título/prioridade/tags estão duplicadas entre criar e atualizar (e há uma 3ª versão, não usada, em `helpers.process_task_data`); a taxa de conclusão é calculada 3 vezes (e `calculate_percentage` não é usado).
Impact: uma correção precisa ser feita em vários lugares; as cópias já divergem (mensagens diferentes entre POST e PUT).
Recommendation: RF-04/RF-13 — `Task.is_overdue`/`to_dict` únicos, validators e constantes compartilhados, mantendo a mensagem de cada rota palavra por palavra.

### [MEDIUM] APIs deprecated (AP-DEPR-01)
File: datetime.utcnow() em 22 linhas — models/category.py:11; models/task.py:15,16,52; models/user.py:14; routes/task_routes.py:31,72,215,285; routes/user_routes.py:172; routes/report_routes.py:35,42,45,71,133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66,67,69,70,74. Model.query.get() em 16 linhas — routes/task_routes.py:42,51,67,117,122,158,188,195,227; routes/user_routes.py:29,94,136,155; routes/report_routes.py:105,192,213
Description: `datetime.utcnow()` é deprecated desde o Python 3.12; `Query.get()` emite `LegacyAPIWarning` no SQLAlchemy 2.1.6 instalado (comprovado no log: "The Query.get() method is considered legacy ... The method is now available as Session.get()").
Impact: quebra em versões futuras; warnings no log a cada requisição.
Recommendation: RF-10 — `utc_now()` baseado em `datetime.now(timezone.utc)` (mantendo datetime sem fuso em UTC, para não mudar o formato gravado e devolvido) e `db.session.get(Model, id)` / `select()`.

### [LOW] print como log (AP-QUAL-04)
File: routes/task_routes.py:149,153,219,234; routes/user_routes.py:83,89,147; services/notification_service.py:21,24; utils/helpers.py:39,41
Description: 11 `print` registram eventos e erros (incluindo `str(e)` com parâmetros SQL). Os `print` de seed.py:93-96 são a saída de um script de linha de comando, não log.
Impact: sem nível nem destino configurável; mistura com stdout.
Recommendation: RF-12 — `logging.getLogger(__name__)`.

### [LOW] Magic numbers e enumerações soltas (AP-QUAL-05)
File: routes/task_routes.py:96-114,136,166-184,203,276-279; routes/user_routes.py:52,64,71,115,120; routes/report_routes.py:19-28,45,84-88,120-129; models/task.py:11-12,39,46; models/category.py:10; utils/helpers.py:110-116
Description: status ('pending', 'done'…), papéis, faixa de prioridade 1–5, prioridade padrão 3, limite de "alta prioridade" `<= 2`, mapa 1–5 → critical…minimal, janela de 7 dias, título de 3 a 200 caracteres, senha mínima de 4, cor padrão '#000000' e formato '%Y-%m-%d' aparecem como literais; `helpers.py` define constantes que ninguém usa.
Impact: regra espalhada; mudar um limite exige caçar literais.
Recommendation: RF-11 — `config/constants.py`.

### [LOW] Código morto, imports e dependências não usados (AP-QUAL-07)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3,38-48; models/user.py:34-38; utils/helpers.py:2-116; services/notification_service.py:1-48; requirements.txt:4-6
Description: imports não usados (`os`, `sys`, `json`, `time`, `hashlib`, `format_date`, `calculate_percentage`…); `utils/helpers.py` inteiro sem uso (9 funções e as constantes); `Task.validate_status`/`validate_priority` e `User.is_admin` nunca chamados; `NotificationService` nunca importado; `marshmallow`, `requests` e `python-dotenv` declarados e não usados.
Impact: ruído, falsa impressão de que existe validação e notificação, dependências a manter.
Recommendation: remover o que não tem uso; reaproveitar o que tem valor (constantes, taxa de conclusão) nos módulos novos; passar a usar `python-dotenv` no config (RF-01).

### [LOW] Nomes pouco descritivos (AP-QUAL-06)
File: routes/task_routes.py:16,51,268,283; routes/user_routes.py:14,37,141,161; routes/report_routes.py:24-28,33,55,59,119,161,192,213; models/category.py:14; models/task.py:45; models/user.py:27,31
Description: variáveis de uma letra ou abreviadas (`t`, `u`, `c`, `d`, `p`, `p1`…`p5`, `cat`, `pwd`).
Impact: leitura mais lenta, principalmente nas agregações dos relatórios.
Recommendation: renomear internamente, sem mudar campos de request/response.

================================
Total: 17 findings
================================
```

APIs deprecated: encontradas — ver AP-DEPR-01 (`datetime.utcnow()` → `datetime.now(timezone.utc)`; `Model.query.get()` → `db.session.get(Model, id)`).

Verificados sem ocorrência: AP-SEC-02 (todo acesso ao banco passa pelo ORM com parâmetros; `like(f'%{q}%')` monta só o valor do parâmetro), AP-SEC-05 (não há rota administrativa nem execução de SQL/comando recebido), AP-ARCH-01 (não há God module: o maior arquivo tem 299 linhas e o problema é lógica na rota, AP-ARCH-02), AP-ARCH-03 (não há estado global mutável compartilhado: `db = SQLAlchemy()` usa sessão por requisição e `NotificationService.notifications` é estado de instância), AP-ARCH-05 (não se aplica: Python síncrono).

Evidências: buscas por sinais do catálogo sobre os 12 arquivos e chamadas ao app original numa cópia isolada (`reports/.tmp/sandbox`, Flask test client, banco próprio). Nenhum arquivo do projeto foi alterado.
