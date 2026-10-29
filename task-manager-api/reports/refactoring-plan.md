# Plano de refatoração — task-manager-api → MVC

> Gerado em plan mode e aprovado pelo usuário. Base: `reports/audit-report.md`.

## Context

A auditoria (`reports/audit-report.md`) achou 17 problemas: **CRITICAL 4 | HIGH 4 | MEDIUM 5 | LOW 4**. Os mais graves:
qualquer cliente anônimo se promove a admin via `role`; o hash MD5 da senha volta em 4 endpoints;
os segredos estão no código; o boot sobe com `debug=True` em `0.0.0.0`. Na arquitetura, as rotas
concentram validação, regra e persistência, e `services/` e `utils/` não são usados.
Objetivo: chegar ao MVC e resolver todos os findings de todas as severidades, **sem mudar o contrato externo**
(paths, campos, mensagens, boot), a não ser pelas mudanças de segurança e de entrada inválida listadas abaixo.

Findings (ids usados nos passos): F1 role autoatribuível · F2 hash exposto · F3 MD5 · F4 segredos ·
F5 sem auth de base · F6 debug · F7 lógica nas rotas · F8 acoplamento · F9 validação/invariantes ·
F10 erro genérico · F11 N+1 · F12 duplicação · F13 deprecated · F14 print · F15 magic numbers ·
F16 código morto · F17 nomes.

## Refactoring Plan

Target structure:
```
task-manager-api/
├── app.py                      # composition root: create_app(); app = create_app(); boot "python app.py"
├── seed.py                     # setup "python seed.py" — mesmos dados e mensagens
├── requirements.txt            # sem marshmallow/requests (python-dotenv passa a ser usado)
├── .env.example                # já existe: SECRET_KEY, DATABASE_URL, DEBUG, HOST, PORT, SMTP_*, ADMIN_TOKEN
├── README.md                   # + seção curta de configuração (variáveis de ambiente, X-Admin-Token)
├── config/
│   ├── settings.py             # Settings via os.environ + load_dotenv(<raiz>/.env) — caminho explícito
│   └── constants.py            # status, papéis, prioridade 1–5/padrão 3/alta ≤2, rótulos, limites, 7 dias, formato de data
├── models/
│   ├── __init__.py             # exporta db, init_db, Task, User, Category
│   ├── db.py                   # db = SQLAlchemy(); init_db(app) → create_all (substitui database.py)
│   ├── task.py                 # Task: to_dict, is_overdue(now), to_user_task_dict (subset de /users/<id>/tasks)
│   ├── user.py                 # User: to_dict SEM password; set/check_password (scrypt + migração MD5)
│   └── category.py
├── validators/
│   ├── common.py               # checagens de tipo (objeto, str, int não-bool, lista de str)
│   ├── task_validator.py
│   ├── user_validator.py       # + check_role_change(role, current_role, is_admin)
│   └── category_validator.py
├── services/
│   ├── report_service.py       # stats, summary, user_report — agregações com GROUP BY
│   └── notification_service.py # SMTP com config e smtp_factory injetados (continua não conectado às rotas)
├── controllers/
│   ├── common.py               # commit_or_fail(mensagem_da_rota): rollback + log + ApiError(msg, 500)
│   ├── task_controller.py
│   ├── user_controller.py      # CRUD + login (+ commit do rehash)
│   ├── category_controller.py
│   └── report_controller.py
├── routes/
│   ├── __init__.py             # register_routes(app)
│   ├── common.py               # read_json(): JSON malformado → ApiError('Dados inválidos', 400); 415 mantido
│   ├── system_routes.py        # GET /, GET /health
│   ├── task_routes.py
│   ├── user_routes.py          # /users..., /login
│   ├── category_routes.py      # /categories... (sai do blueprint de relatórios)
│   └── report_routes.py        # /reports/...
├── middlewares/
│   ├── errors.py               # ApiError + register_error_handlers(app)
│   └── admin_auth.py           # has_admin_token(): X-Admin-Token × ADMIN_TOKEN, hmac.compare_digest
└── utils/
    └── dates.py                # utc_now() = datetime.now(timezone.utc).replace(tzinfo=None); parse_date()
```
Removidos: `database.py` (→ `models/db.py`), `utils/helpers.py` (o que tem valor vai para constants/validators/services).
Direção: routes → controllers → services/models; validators puros (recebem `is_admin` booleano, sem Flask).

Steps (CRITICAL → LOW):
0. Pré-passo (validation-protocol): copiar os fontes originais para `reports/.tmp/original-src/` e gravar `reports/baseline-responses.txt` com o app original, antes de tocar em qualquer arquivo.
1. [CRITICAL] `middlewares/admin_auth.has_admin_token()` + `user_validator.check_role_change()`: no POST, role ausente ou `"user"` passa; outro valor exige token. No PUT, role igual ao atual passa; diferente exige token. Sem `ADMIN_TOKEN` configurado ou com token errado → 403 `{"error": "Acesso negado"}`. A checagem roda depois das validações existentes (inclusive `Role inválido`) e antes de qualquer escrita — resolve F1 (e o nível 1 de F5) — padrão RF-16 nível 1.
2. [CRITICAL] `User.to_dict()` sem `password` (afeta GET /users/<id>, POST/PUT /users, POST /login); logs sem `str(e)`; `SQLALCHEMY_ENGINE_OPTIONS={'hide_parameters': True}` — resolve F2 — RF-13.
3. [CRITICAL] `set_password` com `generate_password_hash` (scrypt); `check_password`: hash de 32 hex = MD5 legado → `hmac.compare_digest` e, se bater, regrava em scrypt (o controller de login faz o commit); senão `check_password_hash`. O seed grava as mesmas senhas no formato novo — resolve F3 — RF-08.
4. [CRITICAL] `config/settings.py`: `SECRET_KEY` do ambiente, sem default (ausente → `None` + aviso no log, sem valor; nada no app usa a chave); `SMTP_HOST/PORT` com os defaults não sensíveis antigos; `SMTP_USER/PASSWORD` só do ambiente; `ADMIN_TOKEN` do ambiente — resolve F4 — RF-01.
5. [HIGH] `DEBUG` do ambiente (default `false`); `HOST`/`PORT` do ambiente (defaults `0.0.0.0`/`5000`); `app.run(host, port, debug)` — resolve F6 — RF-01.
6. [HIGH] `create_app()` como composition root: carrega Settings, `db.init_app`, `init_db` (create_all), CORS, error handlers, blueprints e logging; `app = create_app()` em nível de módulo (para `python app.py`, `flask --app app` e `from app import app` no seed). `NotificationService(host, port, user, password, smtp_factory=smtplib.SMTP)` + `from_config()` — resolve F8 — RF-03/RF-05.
7. [HIGH] Rotas finas (ler JSON, `has_admin_token`, chamar o controller, `jsonify`); controllers orquestram na **ordem original das checagens** (ex.: POST /users: corpo → nome → email → senha → regex → tamanho → 409 email → `Role inválido` → privilégio; POST /tasks: … → usuário/categoria 404 → `due_date`); regra de relatório em `report_service`; `/categories` em `category_routes.py`; cascata do DELETE /users (apaga as tasks do usuário) mantida igual — resolve F7 — RF-04.
8. [HIGH] F5 nível 2 (autenticação completa) → "Not addressed" (abaixo); o nível 1 já entra no passo 1.
9. [MEDIUM] `validators/`: regra única "tipo errado → 400 `{"error": "Dados inválidos"}`", aplicada na posição em que o original quebrava ou aceitava. Corpo precisa ser objeto JSON; `user_id`/`category_id` com qualquer valor não nulo passam pela checagem de existência (0 → 404); `name: ""` em PUT /users e PUT /categories → `Nome é obrigatório`. `{}` em PUT /categories continua 200 (atualização vazia, como hoje) — resolve F9 — RF-14 + RF-04.
10. [MEDIUM] `middlewares/errors.py`: `ApiError` → `{"error": msg}`, status; `HTTPException` devolvida como está (404/405/415 iguais ao Flask); `Exception` → log + 500 `{"error": "Erro interno"}`. Falhas de commit usam a mensagem original de cada rota (`Erro ao criar task`, `Erro ao atualizar`, `Erro ao deletar`, `Erro ao criar usuário`, `Erro ao criar categoria`) via `commit_or_fail`; rotas sem `except:`/`except Exception` — resolve F10 — RF-07.
11. [MEDIUM] GET /tasks com `selectinload(Task.user, Task.category)`; contagens por usuário/categoria/status/prioridade com GROUP BY numa query; `order_by(id)` explícito, igual à ordem atual por rowid — resolve F11 — RF-06.
12. [MEDIUM] Uma só regra de atraso (`is_overdue(due_date, status, now)` no model) e um só `to_dict`; constantes e validators compartilhados; mensagens de cada rota mantidas palavra por palavra (ex.: `Formato de data inválido. Use YYYY-MM-DD` no POST × `Formato de data inválido` no PUT) — resolve F12 — RF-04/RF-13.
13. [MEDIUM] `utc_now()` (UTC sem fuso: mesmo formato gravado e devolvido, comparação sem TypeError) no lugar de `datetime.utcnow`; `db.session.get()` / `select()` no lugar de `Model.query.get()` — resolve F13 — RF-10.
14. [LOW] `logging.getLogger(__name__)` no lugar de `print` (mesmos textos de evento: "Task criada: …"); seed mantém os `print` de saída de CLI — resolve F14 — RF-12.
15. [LOW] Literais → `config/constants.py` — resolve F15 — RF-11.
16. [LOW] Remover imports sem uso, `utils/helpers.py`, `Task.validate_status/validate_priority`, `User.is_admin`, `marshmallow`/`requests` do requirements; `NotificationService` fica (serviço de domínio, refatorado no passo 6) — resolve F16 — limpeza.
17. [LOW] Nomes descritivos internos (`task`, `user`, `category`, `priority_counts`…) — resolve F17 — renomear.

Not addressed:
- F5 nível 2 (token assinado com expiração, `login_required`/`role_required`, dono do recurso): muda o contrato de todas as rotas e o valor do token de `/login`. Recomendado como próximo passo, só com pedido explícito.
- Busca LIKE sem escapar `%`/`_` (parte de F9): escapar mudaria resultados de buscas existentes. Recomendação: `like(..., escape='\\')`.
- Registros já gravados com valores inválidos (prioridade 2.5, `user_id` 0, nomes vazios) não são alterados (princípio 8). Recomendação: script de saneamento revisado manualmente.
- DELETE /users apaga as tasks do usuário e DELETE /categories zera o `category_id` das tasks (comportamento original, mantido). Recomendação: exclusão lógica ou reatribuição.
- Regex de e-mail permissiva (aceita `a@b`) e `color` sem validação de formato: endurecer rejeitaria valores hoje aceitos que não são claramente inválidos.
- `NotificationService` continua sem chamada nas rotas: ligar o envio de e-mail seria efeito colateral novo.

Contract to preserve:
- Rotas (22): GET / · GET /health · GET/POST /tasks · GET/PUT/DELETE /tasks/<id> · GET /tasks/search · GET /tasks/stats · GET/POST /users · GET/PUT/DELETE /users/<id> · GET /users/<id>/tasks · POST /login · GET /reports/summary · GET /reports/user/<id> · GET/POST /categories · PUT/DELETE /categories/<id>
- Respostas: mesmos campos e status; JSON do Flask (chaves ordenadas); erros `{"error": "<mensagem original>"}`; token do login `fake-jwt-token-<id>`; `/` e `/health` iguais; 404/405/415 do Flask inalterados.
- Boot: `python app.py` (porta padrão 5000, host 0.0.0.0); setup `python seed.py`; banco padrão `sqlite:///tasks.db` → `instance/tasks.db`.

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] `password` sai das respostas de GET /users/<id>, POST /users, PUT /users/<id> e POST /login — expunha o hash — prova: `GET /users/1`, `POST /login` com joao@email.com/1234.
- [segurança] `role` diferente do padrão (POST) ou do atual (PUT) sem `X-Admin-Token` válido → 403 `{"error":"Acesso negado"}`; com token → 201/200 como antes; `role:"user"` anônimo e role igual ao atual seguem como antes — escalada de privilégio — prova: `POST /users` com role admin (sem token / token errado / token certo); `PUT /users/2` com role admin (sem/com token); `POST /users` com role user sem token.
- [segurança] debug desligado por padrão: sem traceback nem console do Werkzeug; exceção inesperada → 500 `{"error":"Erro interno"}` em JSON — prova: log do boot ("Debug mode: off").
- [segurança] hash de senha scrypt no lugar de MD5, com migração no login — prova: login com credencial do seed; login num banco criado pelo seed **original** (MD5) e leitura do prefixo do hash no banco antes (32 hex) e depois (`scrypt:`).
- [segurança] `SECRET_KEY` e credenciais SMTP saem do código e passam a vir do ambiente — prova: grep sem literais.
- [entrada inválida] JSON malformado em POST/PUT → 400 `{"error":"Dados inválidos"}` (antes: página HTML 400) — prova: `POST /tasks -d '{'` (e o malformado de cada POST/PUT).
- [entrada inválida] corpo JSON que não é objeto (`[1]`, `"x"`, `null` no PUT /categories) → 400 `Dados inválidos` (antes 500) — prova: `POST /tasks '[1]'`, `PUT /categories/1 'null'`.
- [entrada inválida] tipo errado → 400 `Dados inválidos` (antes 500, ou valor gravado fora do domínio/convertido): tasks `title`, `description`, `priority` (inclui `"5"`, `null`, `2.5`, `true`), `user_id`/`category_id` não inteiros, `tags` que não é texto nem lista de textos; users `name`, `email`, `password`, `active` (só booleano); categories `name`, `description`, `color`; login `email`/`password`; `/tasks/search` com `priority`/`user_id` não numéricos — prova: `POST /tasks priority "5"` e `2.5`, `POST /users email 123`, `PUT /users/3 active "x"`, `POST /login password 123`, `GET /tasks/search?priority=abc`.
- [entrada inválida] `user_id`/`category_id` = 0 → 404 `Usuário não encontrado` / `Categoria não encontrada` (antes gravava referência solta) — prova: `POST /tasks user_id 0`.
- [entrada inválida] `name: ""` em PUT /users/<id> e PUT /categories/<id> → 400 `Nome é obrigatório` (antes gravava nome vazio) — prova: as duas chamadas.

Data preservation:
- Seeds: os mesmos 3 usuários (joao@email.com/1234 admin, maria@email.com/abcd user, pedro@email.com/pass manager), 4 categorias e 10 tasks, com as mesmas mensagens; muda só o formato do hash.
- Credenciais existentes: hashes MD5 já gravados continuam válidos (aceitos com compare_digest e regravados em scrypt no 1º login); nunca é preciso recriar o banco ou rodar o seed de novo.
- Registros persistidos: nenhuma migração de dados; as cascatas originais (DELETE /users, DELETE /categories) não mudam e nenhuma nova é criada; as rejeições novas não tocam registros gravados.
- Segredos: `SECRET_KEY`, `SMTP_*` e `ADMIN_TOKEN` só por ambiente; nenhum gerado na hora; nenhum em log ou resposta (`hide_parameters` também tira o hash dos logs de erro SQL).

Validation (validation-protocol.md, tudo com scripts `bash` em `reports/.tmp/`):
- Estado de dados: hoje não existe `instance/`; garantir que não exista antes de cada execução, rodar `python seed.py` antes de cada uma e, no fim, deixar sem banco como antes.
- Baseline (app original, antes de qualquer alteração): `python app.py` se a 5000 estiver livre; senão `flask --app app run --port <livre>`. Depois: `PORT=<livre> ADMIN_TOKEN=<teste> python app.py`. Portas confirmadas livres antes do boot; PID + `trap` para encerrar.
- Mesmas chamadas, na mesma ordem: sucesso de cada uma das 22 rotas; id inexistente em cada rota com parâmetro; para cada POST/PUT, corpo válido, corpo sem campo obrigatório e JSON malformado; uma prova de cada mudança intencional; login com o seed; destrutivas por último; ids criados capturados da resposta.
- Prova extra da migração: banco criado pelo seed de `reports/.tmp/original-src/` (MD5) → login no app novo → 200 e hash regravado com `scrypt:`. Prova do 403 sem `ADMIN_TOKEN` configurado (boot curto sem a variável).
- `diff` mascarado (timestamps) entre baseline e depois: cada diferença conferida contra a lista acima; o resto é regressão e é corrigido antes de concluir.
- Reverificação do catálogo (grep: segredos, md5, `'password'` em to_dict, `debug=True`, `except:`/`except Exception`, `print(`, `utcnow`, `.query.get(`, imports sem uso), com a saída real e a justificativa de cada linha que ficar.
- Limpeza: servidores encerrados e porta livre, dados restaurados, `reports/.tmp/` apagado; evidências em `reports/validation-report.md` + bloco PHASE 3.
