# Audit Report — task-manager-api

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.11 (.venv local)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1 (SQLAlchemy 2.1.6), flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domain:        API REST de gerenciamento de tarefas (tasks, usuários, categorias, login e relatórios de produtividade)
Architecture:  Camadas parciais: existem models/, routes/, services/ e utils/, mas as rotas concentram validação, regra de negócio, serialização e acesso a dados; não há controllers, e services/utils quase não são usados
Source files:  12 files analyzed (+3 __init__.py vazios em routes/, services/, utils/; ~1155 linhas)
DB tables:     users, tasks, categories (SQLite via Flask-SQLAlchemy, arquivo instance/tasks.db)
Entry point:   app.py (boot: python app.py, porta 5000 fixa; alternativa sem editar código: flask --app app run --port <porta>)
Setup:         python seed.py (apaga e recria 3 usuários, 4 categorias, 10 tasks)
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
GET    /tasks/search
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
Stack:   Python 3.11 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.6)
Files:   12 analyzed | ~1155 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] AP-SEC-04 — Exposição do hash de senha nas respostas
File: models/user.py:16-25 (usado em routes/user_routes.py:33, 85, 129, 209)
Description: User.to_dict() inclui 'password' (hash MD5). Esse dicionário é devolvido por GET /users/<id>, POST /users, PUT /users/<id> e POST /login (campo 'user'). Prova (probe no app original): POST /login {"email":"joao@email.com","password":"1234"} -> 200 com "password":"81dc9bdb52d04dc20036dbd8313ed055"; PUT /users/2 -> "password":"e2fc714c4727ee9395f324cd2e7f331f".
Impact: Qualquer cliente obtém o hash de qualquer usuário; com MD5 sem sal, a senha original é recuperada por tabela de hashes em segundos.
Recommendation: RF-13 — remover 'password' da serialização do model (um único to_dict reutilizado).

### [CRITICAL] AP-SEC-03 — Hash de senha fraco (MD5 sem sal)
File: models/user.py:27-32
Description: set_password grava hashlib.md5(pwd).hexdigest(), sem sal. check_password compara com ==, sem tempo constante.
Impact: Um vazamento do banco (ou da API, ver finding anterior) expõe as senhas. O seed usa senhas curtas ('1234', 'abcd', 'pass'), que são quebradas na hora.
Recommendation: RF-08 — werkzeug.security (generate_password_hash/check_password_hash), com migração dos hashes MD5 existentes no primeiro login bem-sucedido ("rehash on login").

### [CRITICAL] AP-SEC-01 — Segredos hardcoded no código
File: app.py:13; services/notification_service.py:7-10
Description: SECRET_KEY = 'super-secret-key-123' fixo no código. Credenciais SMTP (usuário 'taskmanager@gmail.com', senha 'senha123', host e porta) fixas no construtor de NotificationService.
Impact: Os segredos vão para o controle de versão e não podem ser trocados por ambiente; quem lê o repositório tem a senha do e-mail e pode forjar sessões assinadas.
Recommendation: RF-01 — config/settings.py lendo variáveis de ambiente (python-dotenv), sem default para segredos, mais um .env.example.

### [HIGH] AP-SEC-06 — Debug habilitado e servidor exposto em todas as interfaces
File: app.py:33-34
Description: app.run(debug=True, host='0.0.0.0', port=5000). O debugger interativo do Werkzeug fica ativo e acessível na rede.
Impact: Um erro não tratado (há vários, ver AP-QUAL-02) abre a página do debugger com traceback e console Python, o que permite execução remota de código se o PIN vazar ou for contornado. Também expõe detalhes internos.
Recommendation: RF-01 — DEBUG, HOST e PORT via ambiente, com DEBUG=false por padrão e HOST/PORT com os valores atuais como padrão.

### [HIGH] AP-SEC-05 — Sem autenticação/autorização: token falso previsível e papel admin autoatribuível
File: routes/user_routes.py:207-211, 52, 71-78, 119-122; todas as rotas de escrita em routes/*.py
Description: POST /login devolve 'fake-jwt-token-' + id (previsível e nunca verificado). Nenhuma rota exige autenticação: qualquer cliente cria, altera e apaga tasks, categorias e usuários. POST /users e PUT /users/<id> aceitam role='admin' de qualquer requisição. User.is_admin() (models/user.py:34-38) nunca é usado.
Impact: Qualquer pessoa com acesso à rede apaga usuários (e, em cascata, as tasks deles) ou se promove a admin. O "token" dá falsa sensação de segurança.
Recommendation: implementar autenticação real (ex.: JWT assinado com SECRET_KEY vindo do ambiente) e autorização por papel. Isso muda o contrato de todas as rotas (clientes passam a enviar token), por isso o plano o deixa em "Not addressed" (ver plano). Severidade HIGH e não CRITICAL: não há execução arbitrária nem endpoint administrativo; a ausência de auth é uma lacuna conhecida do produto (a task do seed "Implementar autenticação JWT" está pendente).

### [HIGH] AP-ARCH-02 — Regra de negócio, validação, serialização e acesso a dados nas rotas
File: routes/task_routes.py:11-299; routes/user_routes.py:10-211; routes/report_routes.py:12-223
Description: As rotas fazem tudo: validam o payload campo a campo, consultam o banco, aplicam regras (atraso, contagens, taxa de conclusão, cascata de exclusão), montam o JSON e controlam a transação. Os relatórios (/reports/summary, /reports/user/<id>, /tasks/stats) são calculados dentro do handler HTTP. O CRUD de categorias está em report_routes.py:157-223, misturado com relatórios. Não existe camada de controllers, e services/ só tem um serviço que nunca é usado.
Impact: Nenhuma regra é testável sem HTTP; mudar uma regra (ex.: o que conta como atrasada) exige editar vários handlers; os arquivos de rota passam de 200 a 300 linhas.
Recommendation: RF-04 — rotas finas, que só fazem (de)serialização e chamam os controllers; controllers orquestram; regras de relatório em services/report_service.py; consultas nos models; categorias em routes/category_routes.py. RF-03 para a organização das camadas.

### [HIGH] AP-ARCH-04 — Acoplamento sem injeção: app criado no import, config fixa, dependências concretas
File: app.py:9-31; seed.py:2; services/notification_service.py:5-10, 15
Description: A app Flask é criada no nível do módulo, com config literal e db.create_all() executado no import. O seed.py depende desse efeito colateral (from app import app). Não há create_app() nem composition root. NotificationService monta a própria config SMTP e instancia smtplib.SMTP direto, sem como receber outra config ou outro transporte.
Impact: Não dá para criar a app com outra config (teste, outro banco) sem editar o código; importar app.py já mexe no banco; o serviço de notificação não é testável.
Recommendation: RF-03/RF-05 — create_app(settings) no app.py (composition root), com `app = create_app()` exposto para manter `python app.py`, `flask --app app` e o import do seed; NotificationService recebendo a config SMTP pelo construtor.

### [MEDIUM] AP-PERF-01 — Queries N+1 e contagens repetidas
File: routes/task_routes.py:41-57 (GET /tasks: 2 queries por task); routes/user_routes.py:14-22 (GET /users: len(u.tasks) carrega as tasks de cada usuário); routes/report_routes.py:53-68 (summary: 1 query por usuário); routes/report_routes.py:161-163 (GET /categories: 1 COUNT por categoria); routes/report_routes.py:19-30 (9 COUNTs separados + SELECT de todas as tasks); routes/task_routes.py:275-281 (5 COUNTs + SELECT de todas as tasks)
Description: Consultas dentro de laços e uma consulta por status/prioridade em vez de uma agregação.
Impact: O número de queries cresce com o número de tasks/usuários/categorias (GET /tasks com 10 tasks = 21 queries).
Recommendation: RF-06 — selectinload para user/category/tasks; GROUP BY para contagens por status, prioridade, usuário e categoria.

### [MEDIUM] AP-QUAL-02 — Validação de entrada fraca: tipos errados viram erro 500 e regras divergem entre criar e atualizar
File: routes/task_routes.py:87-114, 140-144, 162-213, 260-264; routes/user_routes.py:44-72, 98-125, 187-202; routes/report_routes.py:196-202
Description: Os tipos do payload não são checados. Casos confirmados no app original (probe):
  - POST /tasks {"title":"abcd","priority":"3"} -> 500 HTML ('<' entre str e int, task_routes.py:113)
  - POST /tasks {"title":123} -> 500 HTML (len de int, task_routes.py:96)
  - POST /tasks [1,2] -> 500 HTML (data.get em lista, task_routes.py:92)
  - POST /tasks {"title":"abcd","tags":[1,2]} -> 500 HTML (join de não-string, task_routes.py:142)
  - POST /tasks {"title":"abcd","tags":5} -> 201 (tipo errado aceito)
  - PUT /tasks/1 {"priority":null} -> 500 HTML (task_routes.py:182); PUT /tasks/1 {"title":null} -> 500 HTML (task_routes.py:167)
  - GET /tasks/search?priority=abc -> 500 HTML (int() sem tratamento, task_routes.py:261; idem user_id, :264)
  - POST /users {...,"password":12345} -> 500 HTML (len de int, user_routes.py:64)
  - POST /login {"email":"joao@email.com","password":1234} -> 500 HTML (encode de int, models/user.py:32)
  - PUT /users/2 {"name":null} -> 500 'Erro ao atualizar' (NOT NULL); PUT /users/2 {"name":""} -> 200 (POST /users rejeita nome vazio com 'Nome é obrigatório'; o PUT aceita)
  - PUT /users/2 {"active":"abc"} -> 500 'Erro ao atualizar'
  - PUT /categories/1 com corpo null -> 500 HTML (sem checagem de corpo, report_routes.py:196-197); PUT /categories/1 {"name":null} -> 500 'Erro ao atualizar' (POST rejeita nome vazio; o PUT aceita '')
  - A cor da categoria não tem o formato validado (utils/helpers.py:52-55 tem is_valid_color, mas ninguém chama).
Impact: Entrada inválida vira erro 500 (com debugger exposto, ver AP-SEC-06) ou é gravada; o mesmo campo segue regras diferentes no POST e no PUT.
Recommendation: RF-14 — routes/validators.py com checagem de tipo e obrigatoriedade na mesma ordem e com as mesmas mensagens das rotas atuais; tipo errado -> 400 {'error': 'Dados inválidos'}; nome vazio/nulo no PUT -> 400 'Nome é obrigatório' (a mensagem que o POST já usa).

### [MEDIUM] AP-QUAL-02 — Invariantes de integridade referencial (exclusões)
File: routes/user_routes.py:140-142; routes/report_routes.py:211-223; models/task.py:13-14
Description: DELETE /users/<id> apaga todas as tasks do usuário junto com ele (perda de histórico). DELETE /categories/<id> apaga a categoria e deixa as tasks com category_id apontando para um registro que não existe (órfãs; o SQLite não aplica FK sem PRAGMA foreign_keys=ON).
Impact: Histórico de tasks perdido sem aviso; tasks órfãs passam a mostrar category_name null em GET /tasks.
Recommendation: exclusão lógica de usuário (active=false) e bloqueio da exclusão de categoria em uso (409) ou desvínculo explícito. Isso exige mudar o comportamento atual das rotas ou alterar registros persistidos, por isso fica em "Not addressed" no plano.

### [MEDIUM] AP-QUAL-01 — Tratamento de erro genérico, sem handler central
File: routes/task_routes.py:13/62-63, 137, 151-154, 204, 221-223, 236-238; routes/user_routes.py:87-90, 130-132, 149-151; routes/report_routes.py:186-188, 207-209, 221-223; utils/helpers.py:46, 49, 88; services/notification_service.py:23-25
Description: 12 `except:` sem tipo e 4 `except Exception`. GET /tasks envolve o handler inteiro num try que devolve 'Erro interno' e engole a causa. Erros não previstos caem na página HTML 500 do Flask (ou no debugger). A mensagem da exceção é impressa com print(str(e)) em vez de ir para um logger.
Impact: A causa real fica escondida, o formato de erro é inconsistente (JSON em alguns casos, HTML em outros) e os parses (strptime) capturam qualquer exceção, inclusive bugs.
Recommendation: RF-07 — middlewares/errors.py com ApiError e @app.errorhandler central (JSON {'error': ...} com as mensagens originais, detalhe só no log); except restritos (ValueError/TypeError, SQLAlchemyError).

### [MEDIUM] AP-QUAL-03 — Duplicação de lógica, serialização e validação
File: routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:33-37, 132-135 (regra de atraso 6x, embora exista Task.is_overdue em models/task.py:50-60); routes/task_routes.py:17-28 e routes/user_routes.py:162-169 (Task.to_dict reimplementado); routes/task_routes.py:275-279 e routes/report_routes.py:19-22 (contagem por status); routes/task_routes.py:92-114 vs 166-184 e routes/user_routes.py:61-72 vs 105-122 (validação de criar e atualizar copiada); routes/user_routes.py:61, 106 e utils/helpers.py:21 (regex de e-mail 3x); models/task.py:38-48 (validate_status/validate_priority existem mas as rotas reimplementam)
Description: O mesmo bloco foi copiado em vários pontos, com pequenas variações.
Impact: Uma mudança de regra precisa ser feita em até 6 lugares, e as cópias já divergem (ex.: mensagens de data diferentes entre POST e PUT).
Recommendation: RF-04/RF-13 — Task.is_overdue() e serializadores no model; validators compartilhados entre criar e atualizar; agregações no report_service.

### [MEDIUM] AP-DEPR-01 — APIs deprecated (datetime.utcnow e Query.get)
File: datetime.utcnow() em models/task.py:15-16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74 (5x). Model.query.get() em routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 (16x)
Description: datetime.utcnow() está deprecated desde o Python 3.12. Query.get() é legado no SQLAlchemy 2.x; o probe registrou 27 avisos "LegacyAPIWarning: The Query.get() method is considered legacy ... now available as Session.get()". O restante usa a API Query legada (Model.query.filter_by...).
Impact: Avisos em runtime e quebra em versões futuras do Python e do SQLAlchemy.
Recommendation: RF-10 — datetime.now(timezone.utc) (convertido para naive UTC, para manter o formato gravado), db.session.get(Model, id) e select()/session.execute nas consultas dos models.

### [LOW] AP-QUAL-04 — print usado como log
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: Eventos e erros registrados com print (inclusive a mensagem da exceção).
Impact: Sem nível, sem destino configurável e sem contexto; mistura log com stdout.
Recommendation: RF-12 — logging.getLogger(__name__). As saídas de seed.py:93-96 são saída de CLI do script de setup e ficam como print.

### [LOW] AP-QUAL-05 — Magic numbers e enumerações soltas
File: lista de status em routes/task_routes.py:110, 177, models/task.py:39 e utils/helpers.py:75, 110; papéis em routes/user_routes.py:71, 120; limites de título 3/200 em routes/task_routes.py:96-100, 167-170; senha mínima 4 em routes/user_routes.py:64, 115; prioridade 1..5 em routes/task_routes.py:113, 182 e models/task.py:46; "alta prioridade" <= 2 em routes/report_routes.py:129; janela de 7 dias em routes/report_routes.py:45; mapa prioridade -> rótulo em routes/report_routes.py:24-28, 83-89; '#000000' em routes/report_routes.py:180 e models/category.py:10; porta 5000 em app.py:34
Description: Regras de negócio espalhadas como literais. Constantes existem em utils/helpers.py:110-116, mas ninguém as usa.
Impact: Mudar um limite exige caçar literais, com risco de divergência.
Recommendation: RF-11 — constantes nomeadas no model (TASK_STATUSES, USER_ROLES, PRIORITY_MIN/MAX...) e na config.

### [LOW] AP-QUAL-06 — Nomes pouco descritivos
File: routes/task_routes.py:16, 268, 283 (t); routes/user_routes.py:14, 37, 141, 161 (u, t); routes/report_routes.py:24-28 (p1..p5), 33, 55, 59, 119 (t, u), 161 (c), 192 (cat); models/category.py:14 (d); models/user.py:27, 31 (pwd); models/task.py:45 (p); seed.py:16-61, 78 (u1, c1, td, t)
Description: Variáveis de uma letra ou abreviadas, sem contexto.
Impact: Leitura e manutenção mais difíceis.
Recommendation: renomear internamente (task, user, category, priority_counts...) sem mudar campos de request/response.

### [LOW] AP-QUAL-07 — Imports, código e dependências mortos
File: app.py:7 (os, sys, json); routes/task_routes.py:7 (json, os, sys, time); routes/user_routes.py:6 (hashlib, json); routes/report_routes.py:7-8 (format_date, calculate_percentage, json); models/task.py:3 (json); utils/helpers.py:3-7 (os, json, sys, math, hashlib) e utils/helpers.py:9-116 (nenhuma função ou constante é usada); models/task.py:38-48 e models/user.py:34-38 (métodos nunca chamados); services/notification_service.py (classe nunca instanciada); requirements.txt:4-5 (marshmallow, requests não usados; python-dotenv também não)
Description: Muito código e dependência declarados sem uso.
Impact: Ruído, falsa impressão de que existe validação/notificação, superfície de dependências maior.
Recommendation: remover imports, helpers e métodos mortos; usar python-dotenv na config; tirar marshmallow e requests do requirements.txt; manter NotificationService (com config injetada) como serviço disponível, sem ligá-lo a rotas (ligá-lo criaria um efeito colateral novo, o envio de e-mail).

================================
Total: 17 findings
================================
```

APIs deprecated: encontradas e registradas em AP-DEPR-01 (datetime.utcnow, Query.get e a API Query legada do SQLAlchemy).

Evidência dos casos de AP-QUAL-02 e AP-SEC-04: app original executado numa cópia isolada (reports/.tmp/probe, banco próprio) com o Flask test client; o banco do projeto não foi tocado.
