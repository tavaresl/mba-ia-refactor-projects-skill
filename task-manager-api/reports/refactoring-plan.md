# Plano de refatoração — task-manager-api (Flask → MVC)

## Context

A auditoria (`reports/audit-report.md`) achou 17 findings: 3 CRITICAL, 4 HIGH, 6 MEDIUM e 4 LOW. Os mais graves: o hash MD5 da senha volta nas respostas, as senhas usam MD5 sem sal, há segredos no código e o debug fica ligado em 0.0.0.0. As rotas concentram validação, regra de negócio, acesso a dados e serialização. O objetivo é levar o projeto ao MVC (config, models, controllers, services, routes, middlewares e um entry point que monta tudo) e resolver os findings sem mudar o contrato externo. Ficam só as mudanças de segurança e de rejeição de entrada inválida listadas abaixo.

## Refactoring Plan

Target structure:
```
task-manager-api/
├── app.py                       # composition root: create_app(); `app = create_app()` e `db` exportados (seed e `flask --app app` continuam funcionando); boot: python app.py
├── seed.py                      # mesmo comando e mesmos dados; prints mantidos (saída de CLI)
├── requirements.txt             # sem marshmallow e requests (não usados)
├── .env.example                 # SECRET_KEY, DATABASE_URL, DEBUG, HOST, PORT, SMTP_*
├── config/
│   ├── __init__.py
│   └── settings.py              # lê o ambiente (python-dotenv); defaults seguros
├── models/
│   ├── __init__.py
│   ├── database.py              # db = SQLAlchemy(); utc_now() (substitui utcnow)
│   ├── user.py                  # USER_ROLES; hashing werkzeug + verificação do MD5 legado; to_dict sem password; consultas
│   ├── task.py                  # TASK_STATUSES, PRIORITY_MIN/MAX, HIGH_PRIORITY_MAX; is_overdue(); to_dict(); consultas e agregações (select/GROUP BY)
│   └── category.py              # DEFAULT_COLOR; consultas e contagem de tasks por categoria
├── controllers/
│   ├── __init__.py
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py          # authenticate() + rehash do MD5 no login
│   ├── report_service.py        # summary, user report, task stats (regras de atraso, taxas, janela de 7 dias)
│   └── notification_service.py  # config SMTP injetada pelo construtor, logger (continua sem ser ligado a rotas)
├── routes/
│   ├── __init__.py
│   ├── main_routes.py           # GET /, GET /health
│   ├── task_routes.py           # /tasks...
│   ├── user_routes.py           # /users..., /login
│   ├── category_routes.py       # /categories... (sai de report_routes)
│   ├── report_routes.py         # /reports...
│   └── validators.py            # checagens de tipo/obrigatoriedade na ordem e com as mensagens originais
└── middlewares/
    ├── __init__.py
    └── errors.py                # ApiError + errorhandlers centrais
```
Removidos: `database.py` (raiz, vira `models/database.py`) e `utils/` (helpers.py e __init__.py: código morto; o que for útil vira constante/model).

Steps (CRITICAL → LOW):
1. [CRITICAL] Tirar `password` de `User.to_dict()`, que passa a ser o único serializador de usuário — resolve AP-SEC-04 — padrão RF-13
2. [CRITICAL] `set_password` com `werkzeug.security.generate_password_hash`; `check_password` reconhece hash MD5 legado (`^[0-9a-f]{32}$`), compara com `hmac.compare_digest` e o `auth_service` regrava no formato novo depois do login bem-sucedido — resolve AP-SEC-03 — padrão RF-08
3. [CRITICAL] `config/settings.py` lendo `SECRET_KEY` (sem literal; se ausente, valor aleatório por processo via `secrets`, nunca logado), `SMTP_HOST/PORT/USER/PASSWORD` (sem default para usuário/senha); `NotificationService(settings)` recebe a config; `.env.example` — resolve AP-SEC-01 — padrão RF-01
4. [HIGH] `DEBUG` (padrão false), `HOST` (padrão 0.0.0.0) e `PORT` (padrão 5000) vindos do ambiente — resolve AP-SEC-06 — padrão RF-01
5. [HIGH] `create_app()` em app.py como composition root: carrega settings, `db.init_app`, CORS, registra blueprints e error handlers, `db.create_all()` dentro do contexto; `DATABASE_URL` padrão `sqlite:///tasks.db` (mesmo arquivo `instance/tasks.db`) — resolve AP-ARCH-04 — padrão RF-03/RF-05
6. [HIGH] Rotas finas (só leem request, chamam o validator e o controller, devolvem jsonify); controllers orquestram; regras de relatório/estatística em `report_service`; consultas nos models; CRUD de categorias em `category_routes.py` — resolve AP-ARCH-02 — padrão RF-04/RF-03
7. [MEDIUM] `middlewares/errors.py`: `ApiError(message, status)` → `{'error': message}`; `HTTPException` devolvida como está (mantém as páginas padrão do Flask para JSON malformado 400, sem content-type 415, 404/405); qualquer outra exceção → log + `{'error': 'Erro interno'}` 500. Falhas de commit continuam com rollback e as mesmas mensagens ('Erro ao criar task', 'Erro ao atualizar', 'Erro ao deletar', 'Erro ao criar usuário', 'Erro ao criar categoria'); `except` restritos (ValueError/TypeError no parse de data, SQLAlchemyError no commit) — resolve AP-QUAL-01 — padrão RF-07
8. [MEDIUM] `routes/validators.py` reproduz exatamente a sequência e as mensagens atuais de cada rota e acrescenta só a checagem de tipo (ver "Intentional behavior changes") — resolve AP-QUAL-02 (validação) — padrão RF-14
9. [MEDIUM] `selectinload(Task.user, Task.category)` em GET /tasks; `selectinload(User.tasks)` em GET /users; `GROUP BY` para contagens por status, prioridade, usuário (total/concluídas) e categoria; a consulta principal e a ordem dos resultados (por id) não mudam — resolve AP-PERF-01 — padrão RF-06
10. [MEDIUM] Atraso só via `Task.is_overdue()`; serialização de task no model (`to_dict()` e a variante resumida de `/users/<id>/tasks`); validação de criar e atualizar compartilhada; uma regex de e-mail — resolve AP-QUAL-03 — padrão RF-04/RF-13
11. [MEDIUM] `utc_now()` = `datetime.now(timezone.utc).replace(tzinfo=None)` (mantém o formato naive gravado e exibido); `db.session.get(Model, id)`; `select()`/`db.session.execute` nas consultas — resolve AP-DEPR-01 — padrão RF-10
12. [LOW] `logging.getLogger(__name__)` no lugar dos print (exceto a saída de CLI do seed) — resolve AP-QUAL-04 — padrão RF-12
13. [LOW] Constantes nomeadas (status, papéis, limites de título 3/200, senha mínima 4, prioridade 1..5, alta prioridade <= 2, janela de 7 dias, mapa prioridade → rótulo, cor padrão, porta) — resolve AP-QUAL-05 — padrão RF-11
14. [LOW] Renomear variáveis internas (t/u/c/p/d/p1..p5/td/pwd → nomes descritivos), sem mudar campos de request/response — resolve AP-QUAL-06
15. [LOW] Remover imports mortos, `utils/helpers.py`, `Task.validate_status/validate_priority`, `User.is_admin` (sem uso); tirar marshmallow e requests do requirements.txt; python-dotenv passa a ser usado pela config — resolve AP-QUAL-07

Not addressed:
- AP-SEC-05 (sem autenticação; token 'fake-jwt-token-<id>'; role admin autoatribuível): exigir token em todas as rotas, ou trocar o token, muda o contrato de todos os clientes. Recomendação: JWT assinado com SECRET_KEY do ambiente, um decorator `login_required`/`role_required` e restringir `role` a admins. A política de endpoints perigosos (token do ambiente) não é aplicada aos DELETE de CRUD porque eles são funcionalidade normal da API, não operações administrativas. Se você quiser aplicá-la, peça e eu incluo.
- AP-QUAL-02 (integridade): DELETE /users/<id> continua apagando as tasks do usuário e DELETE /categories/<id> continua deixando tasks órfãs. Mudar isso alteraria o comportamento ou os registros. Recomendação: exclusão lógica de usuário e 409 para categoria em uso.
- Validação de formato além do tipo (cor `#RRGGBB`, regex de e-mail mais rígida): seria regra nova. Recomendação registrada.
- Respostas HTML padrão do Flask para JSON malformado (400), content-type ausente (415) e rota/método inexistente (404/405): mantidas como contrato. Recomendação: padronizar em JSON.
- NotificationService continua sem ser chamado por rotas (ligá-lo criaria o envio de e-mail, um efeito colateral novo).

Contract to preserve:
- Rotas (22): GET /, GET /health, GET/POST /tasks, GET/PUT/DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats, GET/POST /users, GET/PUT/DELETE /users/<id>, GET /users/<id>/tasks, POST /login, GET /reports/summary, GET /reports/user/<id>, GET/POST /categories, PUT/DELETE /categories/<id>.
- Respostas: mesmos campos e valores (GET /tasks com overdue/user_name/category_name; GET /tasks/<id> = to_dict + overdue; /users/<id>/tasks com o subconjunto atual; GET /users com task_count; relatórios com as mesmas chaves e cálculos), mesma ordem das listas, mesmos status HTTP, mesmas mensagens de sucesso e erro palavra por palavra, na mesma ordem de checagem (ex.: PUT /tasks/<id> checa existência → corpo → title → status → priority → user → category → due_date). Token de login 'fake-jwt-token-<id>' mantido.
- Boot: `python app.py` (porta padrão 5000; `PORT` opcional). `python seed.py` continua sendo a preparação.

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] Campo `password` removido do objeto de usuário em GET /users/<id>, POST /users, PUT /users/<id> e POST /login (`user`) — expunha o hash — prova: `POST /login {"email":"joao@email.com","password":"1234"}` e `GET /users/1` sem `password`
- [segurança] Senhas novas gravadas com werkzeug (pbkdf2/scrypt + sal); hashes MD5 existentes aceitos e regravados no primeiro login — MD5 sem sal — prova: login de usuário com hash MD5 inserido no banco → 200, e o hash armazenado muda para o formato werkzeug
- [segurança] Debug desligado por padrão: um erro inesperado responde 500 `{'error': 'Erro interno'}` em vez do debugger/HTML do Werkzeug — debugger exposto em 0.0.0.0 — prova: log de boot sem "Debugger is active"
- [segurança] SECRET_KEY e credenciais SMTP vêm do ambiente (nenhuma resposta muda) — segredos no código — prova: grep sem literais
- [entrada inválida] Corpo JSON que não é objeto (ex.: `[1,2]`) em POST/PUT /tasks, POST/PUT /users, POST /login, POST/PUT /categories → 400 `{'error': 'Dados inválidos'}` (antes 500) — prova: `POST /tasks [1,2]`
- [entrada inválida] POST/PUT /tasks com tipo errado → 400 `{'error': 'Dados inválidos'}`: title não-string ou null no PUT, description não-string, priority não-inteiro (string, float, bool, null), tags que não sejam string ou lista de strings (ex.: `5`, `[1,2]`), user_id/category_id que não sejam inteiro/string/null (antes 500, ou gravado no caso de tags `5`) — prova: `POST /tasks {"title":"abcd","priority":"3"}`, `{"title":123}`, `{"title":"abcd","tags":[1,2]}`, `{"title":"abcd","tags":5}`, `PUT /tasks/1 {"priority":null}`
- [entrada inválida] GET /tasks/search com priority ou user_id não inteiros → 400 `{'error': 'Dados inválidos'}` (antes 500) — prova: `GET /tasks/search?priority=abc`
- [entrada inválida] POST /users com name/email/password não-string → 400 `{'error': 'Dados inválidos'}` (antes 500, ou gravado) — prova: `POST /users {"name":"X","email":"x@x.com","password":12345}`
- [entrada inválida] PUT /users/<id>: name null ou "" → 400 `{'error': 'Nome é obrigatório'}` (mensagem do POST; antes 500 / 200 com nome vazio); name/email/password não-string ou active não-booleano → 400 `{'error': 'Dados inválidos'}` (antes 500) — prova: `PUT /users/2 {"name":null}`, `{"name":""}`, `{"active":"abc"}`
- [entrada inválida] POST /login com email/password não-string → 400 `{'error': 'Dados inválidos'}` (antes 500) — prova: `POST /login {"email":"joao@email.com","password":1234}`
- [entrada inválida] POST/PUT /categories: corpo null/não-objeto no PUT → 400 `{'error': 'Dados inválidos'}`; name null ou "" no PUT → 400 `{'error': 'Nome é obrigatório'}`; name/description/color com tipo errado → 400 `{'error': 'Dados inválidos'}` (antes 500, ou aceito). `{}` no PUT continua 200 — prova: `PUT /categories/1` com corpo `null`, `{"name":null}`

Data preservation:
- Seeds: mesmos 3 usuários (joao@email.com/1234 admin, maria@email.com/abcd user, pedro@email.com/pass manager), 4 categorias e 10 tasks; só o formato do hash muda.
- Credenciais existentes: hashes MD5 já gravados (ex.: instance/tasks.db atual) continuam válidos e são migrados no primeiro login; nada de recriar o banco ou rodar o seed de novo.
- Registros persistidos: nenhuma correção apaga ou altera registros. A cascata atual de DELETE /users é mantida (contrato) e está em "Not addressed".
- Segredos: nenhum em log ou resposta; a SECRET_KEY aleatória de fallback nunca é logada; credenciais SMTP só pelo ambiente.

Validation:
- Antes de alterar: copiar os fontes para `reports/.tmp/original-src/`, fazer backup de `instance/tasks.db` em `reports/.tmp/data-backup/`, escolher uma porta livre (5000 pode estar com o AirPlay) e capturar `reports/baseline-responses.txt` com o app original (`flask --app app run --port $PORT`, já que a porta está fixa no código), depois de `python seed.py`.
- Cobertura: todas as 22 rotas no caso de sucesso; ID inexistente em cada rota com parâmetro; corpo válido, sem campo obrigatório e JSON malformado (`{`) em cada POST/PUT; cada chamada de prova acima; login com as credenciais do seed; IDs capturados das respostas; rotas destrutivas por último.
- Depois: `python app.py` com `PORT` livre, o mesmo seed e as mesmas chamadas → `reports/after-responses.txt`; diff com timestamps mascarados. Toda diferença tem que estar na lista acima; o resto é regressão e será corrigido.
- Prova do MD5 legado: inserir um usuário com hash MD5 direto no SQLite, fazer login (200) e conferir que o hash foi regravado.
- O app sobe sem erro com o comando de boot original; reverificação por grep dos sinais do catálogo (todas as severidades) com a saída real; nenhum sinal remanescente sem justificativa.
- Limpeza: servidores encerrados e porta livre, `instance/tasks.db` restaurado, `reports/.tmp/` apagado; evidências em `reports/validation-report.md`.
