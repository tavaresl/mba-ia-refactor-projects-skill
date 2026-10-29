# Validation Report

## Ambiente
- Porta usada: 5050 (livre antes do boot: sim; baseline e depois)
- Boot original: `flask --app app run --port 5050` (cópia em reports/.tmp/original-src); boot refatorado: `python app.py` com `PORT=5050` — log: `Debug mode: off`, sem erros.
- Estado de dados: `instance/` não existia antes; removido antes de cada execução, seed rodado antes de cada uma, removido no fim.
- 114 chamadas idênticas gravadas em `reports/baseline-responses.txt` e `reports/after-responses.txt`.

## Baseline × depois
Diferenças (diff mascarado de timestamps, conferido campo a campo), todas esperadas:

| Diferença | Esperada? | Mudança intencional do plano |
|---|---|---|
| `password` some de GET /users/<id>, POST/PUT /users, POST /login | sim | [segurança] hash fora das respostas |
| POST /users role admin sem token ou token errado: 201 → 403 `Acesso negado`; com token: 201 igual | sim | [segurança] role privilegiado |
| PUT /users/<id> role admin sem token: 200 → 403 | sim | [segurança] role privilegiado |
| JSON malformado em POST/PUT: HTML 400 → 400 `{"error":"Dados inválidos"}` | sim | [entrada inválida] |
| Corpo `[1]` / `null`: 500 (ou 200 sem efeito em PUT /tasks) → 400 `Dados inválidos` | sim | [entrada inválida] |
| Tipo errado (priority "5"/2.5, title 123, email 123, password 123, active "x", color {}, search priority/user_id=abc): 500 ou aceito → 400 | sim | [entrada inválida] |
| POST /tasks user_id 0: 201 → 404 `Usuário não encontrado` | sim | [entrada inválida] |
| PUT /users e PUT /categories `name:""`: 200 → 400 `Nome é obrigatório` | sim | [entrada inválida] |
| Totais de /tasks/stats, /reports/summary, ids seguintes, nome da categoria | sim | efeito em cascata das rejeições acima (o original criou 2 tasks e 2 usuários extras; categoria ficou com nome vazio) |

Nenhuma regressão encontrada.

## Rotas protegidas (role privilegiado)
| Rota | Sem token | Com token |
|---|---|---|
| POST /users role admin | 403 | 201 (role manager, ADMIN_TOKEN=test-admin-token) |
| PUT /users/<id> role admin | 403 | 200 (role manager) |
| Sem ADMIN_TOKEN configurado, qualquer header | 403 | — |

## Migração de hash e política sem ADMIN_TOKEN (saída real)
```
== banco criado pelo seed ORIGINAL (MD5) ==
joao antes: ('81dc9bdb52d0', 32)
POST /login {"email":"joao@email.com","password":"errada"} 
  -> {"error":"Credenciais inv\u00e1lidas"}
 [401]
joao após senha errada: ('81dc9bdb52d0', 32)
POST /login {"email":"joao@email.com","password":"1234"} 
  -> {"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,"created_at":"2026-10-28 22:23:25.496990","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role":"admin"}}
 [200]
joao após 1o login: ('scrypt:32768', 162)
POST /login {"email":"joao@email.com","password":"1234"} 
  -> {"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,"created_at":"2026-10-28 22:23:25.496990","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role":"admin"}}
 [200]
joao após 2o login: ('scrypt:32768', 162)
POST /login {"email":"maria@email.com","password":"abcd"} 
  -> {"message":"Login realizado com sucesso","token":"fake-jwt-token-2","user":{"active":true,"created_at":"2026-10-28 22:23:25.496993","email":"maria@email.com","id":2,"name":"Maria Santos","role":"user"}}
 [200]
maria após login: ('scrypt:32768', 162) | pedro (não logou): ('1a1dc91c9073', 32)
== ADMIN_TOKEN NÃO configurado ==
POST /users {"name":"A","email":"a1@x.com","password":"abcd1","role":"admin"} X-Admin-Token: qualquer
  -> {"error":"Acesso negado"}
 [403]
POST /users {"name":"A","email":"a2@x.com","password":"abcd1","role":"admin"} X-Admin-Token: 
  -> {"error":"Acesso negado"}
 [403]
POST /users {"name":"A","email":"a3@x.com","password":"abcd1","role":"manager"} 
  -> {"error":"Acesso negado"}
 [403]
POST /users {"name":"A","email":"a4@x.com","password":"abcd1"} 
  -> {"active":true,"created_at":"2026-10-28 22:23:26.596867","email":"a4@x.com","id":4,"name":"A","role":"user"}
 [201]
PUT /users/2 {"role":"admin"} X-Admin-Token: qualquer
  -> {"error":"Acesso negado"}
 [403]
PUT /users/2 {"role":"user"} 
  -> {"active":true,"created_at":"2026-10-28 22:23:25.496993","email":"maria@email.com","id":2,"name":"Maria Santos","role":"user"}
 [200]
== boot log (trecho) ==
2026-10-28 19:23:25,765 WARNING app: SECRET_KEY não configurada no ambiente
 * Serving Flask app 'app'
 * Debug mode: off
```

## Reverificação do catálogo
```
arquivos: 36
linhas: 1447

$ grep -nE 'SECRET_KEY *= *['"]|password *= *['"]|senha123|super-secret' <fontes>
(nenhuma ocorrência)

$ grep -nE 'execute\((f|")|" *\+ *[a-z_]+ *\+|%s.*%' <fontes>
./controllers/task_controller.py:68:    logger.info('Task criada: %s - %s', task.id, task.title)
./controllers/user_controller.py:69:    logger.info('Usuário criado: %s - %s', user.id, user.name)

$ grep -nE 'md5|sha1' <fontes>
./models/user.py:45:            legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()

$ grep -nE ''password'' <fontes>
./controllers/user_controller.py:86:    if 'password' in data:
./controllers/user_controller.py:87:        validator.check_password_on_update(data['password'])
./controllers/user_controller.py:97:    if 'password' in data:
./controllers/user_controller.py:98:        user.set_password(data['password'])
./validators/user_validator.py:36:    password = data.get('password')
./validators/user_validator.py:77:    password = data.get('password')

$ grep -nE 'debug *= *True' <fontes>
(nenhuma ocorrência)

$ grep -nE '^\s*except *:|except Exception' <fontes>
(nenhuma ocorrência)

$ grep -nE 'print\(' <fontes>
./routes/__init__.py:10:        app.register_blueprint(blueprint)
./routes/category_routes.py:6:category_bp = Blueprint('categories', __name__)
./routes/report_routes.py:5:report_bp = Blueprint('reports', __name__)
./routes/system_routes.py:5:system_bp = Blueprint('system', __name__)
./routes/task_routes.py:6:task_bp = Blueprint('tasks', __name__)
./routes/user_routes.py:7:user_bp = Blueprint('users', __name__)
./seed.py:95:        print("Seed concluído com sucesso!")
./seed.py:98:            print(f"  {total} {label}")

$ grep -nE 'utcnow' <fontes>
(nenhuma ocorrência)

$ grep -nE '\.query\.get\(' <fontes>
(nenhuma ocorrência)

$ grep -nE 'fake-jwt' <fontes>
./config/constants.py:43:LOGIN_TOKEN_PREFIX = 'fake-jwt-token-'

$ grep -nE 'is_admin\(\)' <fontes>
(nenhuma ocorrência)

$ python unused-imports
verificação de imports concluída

$ python -m compileall
compile-ok
```
Linhas remanescentes e justificativa:
- `models/user.py:45` md5: só para reconhecer e migrar hashes legados (RF-08); nunca grava MD5.
- `'password'` em controllers/validators: leitura do corpo da requisição; `to_dict` não o expõe.
- `print(`: correspondências de `register_blueprint(`/`Blueprint(` (falso positivo) e saída de CLI do `seed.py`.
- `%s` em `logger.info`: formatação do logger, sem SQL.
- `fake-jwt` em `config/constants.py`: token de login preservado por contrato (autenticação completa em "Not addressed").

## Limpeza
- Servidores encerrados, porta 5050 livre: sim
- Dados restaurados (sem `instance/`): sim
- reports/.tmp removido: sim

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
app.py, seed.py, config/{settings,constants}, models/{db,task,user,category},
validators/, controllers/, services/{report,notification}, routes/ (5 blueprints),
middlewares/{errors,admin_auth}, utils/dates

## Validation
  ✓ Application boots without errors (python app.py)
  ✓ All endpoints respond (22/22)
  ✓ No catalog anti-patterns remaining
  ✗ Pendente: autenticação completa (RF-16 nível 2), escape de LIKE e demais itens de "Not addressed" no plano

## Behavior changes
- Hash de senha removido das respostas; role privilegiado exige X-Admin-Token (403)
- Senhas em scrypt, com migração do MD5 no login
- Debug desligado por padrão; segredos só por ambiente
- Entrada inválida passa a dar 400 (JSON malformado, tipos errados, user_id 0, nome vazio)
================================
