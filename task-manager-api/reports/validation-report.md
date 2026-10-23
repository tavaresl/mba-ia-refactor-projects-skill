# Validation Report

## Ambiente
- Porta usada: 5050 (livre antes do boot: sim; `lsof` mostrava só o processo de outro app em 5051)
- Baseline (app original): `flask --app app run --port $PORT` (porta fixa no código) — 100 chamadas, `reports/baseline-responses.txt`
- Depois (refatorado): `python app.py` com `PORT=5050` — 100 chamadas, `reports/after-responses.txt`
- Log de boot do refatorado:
```
 * Serving Flask app 'app'
 * Debug mode: off
INFO:werkzeug:WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5050
 * Running on http://192.168.15.5:5050
Tracebacks/'Erro não tratado' no log: 0   'Debugger is active': 0
```
- Estado de dados: `instance/tasks.db` copiado para `reports/.tmp/data-backup/`; restaurado + `python seed.py` antes de cada execução; restaurado ao final.

## Baseline × depois
Comando: `diff <(mask baseline) <(mask after)` (mask troca timestamps por `<ts>`). Saída real:
```diff
34,39c34,35
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
51c47
< {"active":true,"created_at":"<ts>","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","password":"81dc9bdb52d04dc20036dbd8313ed055","role":"admin","tasks":[{"category_id":1,"created_at":"<ts>","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"<ts>","id":1,"priority":1,"status":"pending","tags":[],"title":"Implementar autentica\u00e7\u00e3o JWT","updated_at":"<ts>","user_id":1},{"category_id":4,"created_at":"<ts>","description":"Filtro n\u00e3o funciona com caracteres especiais","due_date":"<ts>","id":4,"priority":1,"status":"pending","tags":[],"title":"Corrigir bug no filtro de busca","updated_at":"<ts>","user_id":1},{"category_id":1,"created_at":"<ts>","description":"Endpoints retornam todos os registros","due_date":"<ts>","id":5,"priority":3,"status":"pending","tags":[],"title":"Adicionar pagina\u00e7\u00e3o na API","updated_at":"<ts>","user_id":1},{"category_id":1,"created_at":"<ts>","description":"Usar marshmallow ou pydantic","due_date":null,"id":10,"priority":3,"status":"pending","tags":["improvement","validation"],"title":"Melhorar valida\u00e7\u00f5es de input","updated_at":"<ts>","user_id":1}]}
---
> {"active":true,"created_at":"<ts>","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role":"admin","tasks":[{"category_id":1,"created_at":"<ts>","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"<ts>","id":1,"priority":1,"status":"pending","tags":[],"title":"Implementar autentica\u00e7\u00e3o JWT","updated_at":"<ts>","user_id":1},{"category_id":4,"created_at":"<ts>","description":"Filtro n\u00e3o funciona com caracteres especiais","due_date":"<ts>","id":4,"priority":1,"status":"pending","tags":[],"title":"Corrigir bug no filtro de busca","updated_at":"<ts>","user_id":1},{"category_id":1,"created_at":"<ts>","description":"Endpoints retornam todos os registros","due_date":"<ts>","id":5,"priority":3,"status":"pending","tags":[],"title":"Adicionar pagina\u00e7\u00e3o na API","updated_at":"<ts>","user_id":1},{"category_id":1,"created_at":"<ts>","description":"Usar marshmallow ou pydantic","due_date":null,"id":10,"priority":3,"status":"pending","tags":["improvement","validation"],"title":"Melhorar valida\u00e7\u00f5es de input","updated_at":"<ts>","user_id":1}]}
98,103c94,95
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
114,119c106,107
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
122,127c110,111
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
130,135c114,115
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
138,139c118,119
< status: 201
< {"category_id":null,"created_at":"<ts>","description":"","due_date":null,"id":12,"priority":3,"status":"pending","tags":["5"],"title":"abcd","updated_at":"<ts>","user_id":null}
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
186,191c166,167
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
194,199c170,171
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
223c195
< {"active":true,"created_at":"<ts>","email":"teste@email.com","id":4,"name":"Teste","password":"c7d9eb0d2f54f8c1177976cf2e6ee6d5","role":"manager"}
---
> {"active":true,"created_at":"<ts>","email":"teste@email.com","id":4,"name":"Teste","role":"manager"}
262,267c234,235
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
270,275c238,239
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
279c243
< {"active":true,"created_at":"<ts>","email":"teste@email.com","id":4,"name":"Teste","password":"c7d9eb0d2f54f8c1177976cf2e6ee6d5","role":"manager","tasks":[]}
---
> {"active":true,"created_at":"<ts>","email":"teste@email.com","id":4,"name":"Teste","role":"manager","tasks":[]}
283c247
< {"active":true,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"Teste 2","password":"3806a526e2c7af2ec712718c3de4d4a5","role":"user"}
---
> {"active":true,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"Teste 2","role":"user"}
314,315c278,279
< status: 500
< {"error":"Erro ao atualizar"}
---
> status: 400
> {"error":"Nome \u00e9 obrigat\u00f3rio"}
318,319c282,283
< status: 200
< {"active":true,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"","password":"3806a526e2c7af2ec712718c3de4d4a5","role":"user"}
---
> status: 400
> {"error":"Nome \u00e9 obrigat\u00f3rio"}
322,323c286,287
< status: 500
< {"error":"Erro ao atualizar"}
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
327c291
< {"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,"created_at":"<ts>","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","password":"81dc9bdb52d04dc20036dbd8313ed055","role":"admin"}}
---
> {"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,"created_at":"<ts>","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role":"admin"}}
331c295
< {"message":"Login realizado com sucesso","token":"fake-jwt-token-2","user":{"active":true,"created_at":"<ts>","email":"maria@email.com","id":2,"name":"Maria Santos","password":"e2fc714c4727ee9395f324cd2e7f331f","role":"user"}}
---
> {"message":"Login realizado com sucesso","token":"fake-jwt-token-2","user":{"active":true,"created_at":"<ts>","email":"maria@email.com","id":2,"name":"Maria Santos","role":"user"}}
335c299
< {"message":"Login realizado com sucesso","token":"fake-jwt-token-3","user":{"active":true,"created_at":"<ts>","email":"pedro@email.com","id":3,"name":"Pedro Oliveira","password":"1a1dc91c907325c69271ddf0c944bc72","role":"manager"}}
---
> {"message":"Login realizado com sucesso","token":"fake-jwt-token-3","user":{"active":true,"created_at":"<ts>","email":"pedro@email.com","id":3,"name":"Pedro Oliveira","role":"manager"}}
339c303
< {"message":"Login realizado com sucesso","token":"fake-jwt-token-4","user":{"active":true,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"","password":"3806a526e2c7af2ec712718c3de4d4a5","role":"user"}}
---
> {"message":"Login realizado com sucesso","token":"fake-jwt-token-4","user":{"active":true,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"Teste 2","role":"user"}}
362,367c326,327
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
371c331
< {"active":false,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"","password":"3806a526e2c7af2ec712718c3de4d4a5","role":"user"}
---
> {"active":false,"created_at":"<ts>","email":"teste2@email.com","id":4,"name":"Teste 2","role":"user"}
394,399c354,355
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
422,427c378,379
< status: 500
< <!doctype html>
< <html lang=en>
< <title>500 Internal Server Error</title>
< <h1>Internal Server Error</h1>
< <p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
---
> status: 400
> {"error":"Dados inv\u00e1lidos"}
430,431c382,383
< status: 500
< {"error":"Erro ao atualizar"}
---
> status: 400
> {"error":"Nome \u00e9 obrigat\u00f3rio"}
439c391
< {"generated_at":"<ts>","overdue":{"count":2,"tasks":[{"days_overdue":3,"due_date":"<ts>","id":1,"title":"Implementar autentica\u00e7\u00e3o JWT"},{"days_overdue":1,"due_date":"<ts>","id":4,"title":"Corrigir bug no filtro de busca"}]},"overview":{"total_categories":5,"total_tasks":12,"total_users":4},"recent_activity":{"tasks_completed_last_7_days":2,"tasks_created_last_7_days":12},"tasks_by_priority":{"critical":3,"high":3,"low":2,"medium":4,"minimal":0},"tasks_by_status":{"cancelled":1,"done":2,"in_progress":2,"pending":7},"user_productivity":[{"completed_tasks":0,"completion_rate":0.0,"total_tasks":4,"user_id":1,"user_name":"Jo\u00e3o Silva"},{"completed_tasks":1,"completion_rate":25.0,"total_tasks":4,"user_id":2,"user_name":"Maria Santos"},{"completed_tasks":1,"completion_rate":33.33,"total_tasks":3,"user_id":3,"user_name":"Pedro Oliveira"},{"completed_tasks":0,"completion_rate":0,"total_tasks":0,"user_id":4,"user_name":""}]}
---
> {"generated_at":"<ts>","overdue":{"count":2,"tasks":[{"days_overdue":3,"due_date":"<ts>","id":1,"title":"Implementar autentica\u00e7\u00e3o JWT"},{"days_overdue":1,"due_date":"<ts>","id":4,"title":"Corrigir bug no filtro de busca"}]},"overview":{"total_categories":5,"total_tasks":11,"total_users":4},"recent_activity":{"tasks_completed_last_7_days":2,"tasks_created_last_7_days":11},"tasks_by_priority":{"critical":3,"high":3,"low":2,"medium":3,"minimal":0},"tasks_by_status":{"cancelled":1,"done":2,"in_progress":2,"pending":6},"user_productivity":[{"completed_tasks":0,"completion_rate":0.0,"total_tasks":4,"user_id":1,"user_name":"Jo\u00e3o Silva"},{"completed_tasks":1,"completion_rate":25.0,"total_tasks":4,"user_id":2,"user_name":"Maria Santos"},{"completed_tasks":1,"completion_rate":33.33,"total_tasks":3,"user_id":3,"user_name":"Pedro Oliveira"},{"completed_tasks":0,"completion_rate":0,"total_tasks":0,"user_id":4,"user_name":"Teste 2"}]}
447c399
< {"cancelled":1,"completion_rate":16.67,"done":2,"in_progress":2,"overdue":2,"pending":7,"total":12}
---
> {"cancelled":1,"completion_rate":18.18,"done":2,"in_progress":2,"overdue":2,"pending":6,"total":11}
475c427
< [{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"<ts>","id":1,"overdue":true,"priority":1,"status":"pending","tags":[],"title":"Implementar autentica\u00e7\u00e3o JWT","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":2,"category_name":"Frontend","created_at":"<ts>","description":"Tela de login responsiva","due_date":"<ts>","id":2,"overdue":false,"priority":2,"status":"in_progress","tags":[],"title":"Criar tela de login","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":3,"category_name":"DevOps","created_at":"<ts>","description":"Pipeline com GitHub Actions","due_date":null,"id":3,"overdue":false,"priority":2,"status":"done","tags":["devops","ci","github"],"title":"Configurar CI/CD","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":4,"category_name":"Bug","created_at":"<ts>","description":"Filtro n\u00e3o funciona com caracteres especiais","due_date":"<ts>","id":4,"overdue":true,"priority":1,"status":"pending","tags":[],"title":"Corrigir bug no filtro de busca","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Endpoints retornam todos os registros","due_date":"<ts>","id":5,"overdue":false,"priority":3,"status":"pending","tags":[],"title":"Adicionar pagina\u00e7\u00e3o na API","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Cobertura m\u00ednima de 80%","due_date":null,"id":6,"overdue":false,"priority":2,"status":"pending","tags":[],"title":"Escrever testes unit\u00e1rios","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Gerar documenta\u00e7\u00e3o autom\u00e1tica","due_date":null,"id":7,"overdue":false,"priority":4,"status":"cancelled","tags":[],"title":"Documentar API com Swagger","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Melhorar organiza\u00e7\u00e3o dos models","due_date":null,"id":8,"overdue":false,"priority":3,"status":"in_progress","tags":["refactor","tech-debt"],"title":"Refatorar models","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":3,"category_name":"DevOps","created_at":"<ts>","description":"Prometheus + Grafana","due_date":"<ts>","id":9,"overdue":false,"priority":4,"status":"pending","tags":[],"title":"Configurar monitoramento","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Usar marshmallow ou pydantic","due_date":null,"id":10,"overdue":false,"priority":3,"status":"pending","tags":["improvement","validation"],"title":"Melhorar valida\u00e7\u00f5es de input","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":null,"category_name":null,"created_at":"<ts>","description":"","due_date":null,"id":12,"overdue":false,"priority":3,"status":"pending","tags":["5"],"title":"abcd","updated_at":"<ts>","user_id":null,"user_name":null}]
---
> [{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"<ts>","id":1,"overdue":true,"priority":1,"status":"pending","tags":[],"title":"Implementar autentica\u00e7\u00e3o JWT","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":2,"category_name":"Frontend","created_at":"<ts>","description":"Tela de login responsiva","due_date":"<ts>","id":2,"overdue":false,"priority":2,"status":"in_progress","tags":[],"title":"Criar tela de login","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":3,"category_name":"DevOps","created_at":"<ts>","description":"Pipeline com GitHub Actions","due_date":null,"id":3,"overdue":false,"priority":2,"status":"done","tags":["devops","ci","github"],"title":"Configurar CI/CD","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":4,"category_name":"Bug","created_at":"<ts>","description":"Filtro n\u00e3o funciona com caracteres especiais","due_date":"<ts>","id":4,"overdue":true,"priority":1,"status":"pending","tags":[],"title":"Corrigir bug no filtro de busca","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Endpoints retornam todos os registros","due_date":"<ts>","id":5,"overdue":false,"priority":3,"status":"pending","tags":[],"title":"Adicionar pagina\u00e7\u00e3o na API","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Cobertura m\u00ednima de 80%","due_date":null,"id":6,"overdue":false,"priority":2,"status":"pending","tags":[],"title":"Escrever testes unit\u00e1rios","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Gerar documenta\u00e7\u00e3o autom\u00e1tica","due_date":null,"id":7,"overdue":false,"priority":4,"status":"cancelled","tags":[],"title":"Documentar API com Swagger","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Melhorar organiza\u00e7\u00e3o dos models","due_date":null,"id":8,"overdue":false,"priority":3,"status":"in_progress","tags":["refactor","tech-debt"],"title":"Refatorar models","updated_at":"<ts>","user_id":2,"user_name":"Maria Santos"},{"category_id":3,"category_name":"DevOps","created_at":"<ts>","description":"Prometheus + Grafana","due_date":"<ts>","id":9,"overdue":false,"priority":4,"status":"pending","tags":[],"title":"Configurar monitoramento","updated_at":"<ts>","user_id":3,"user_name":"Pedro Oliveira"},{"category_id":1,"category_name":"Backend","created_at":"<ts>","description":"Usar marshmallow ou pydantic","due_date":null,"id":10,"overdue":false,"priority":3,"status":"pending","tags":["improvement","validation"],"title":"Melhorar valida\u00e7\u00f5es de input","updated_at":"<ts>","user_id":1,"user_name":"Jo\u00e3o Silva"}]
```

| Diferença (linhas do diff) | Esperada? | Mudança intencional do plano |
|---|---|---|
| `GET /users/1`, `POST /users`, `PUT /users/<id>`, `POST /login` (4 logins): campo `password` some de `user` | sim | [segurança] hash não é mais exposto |
| `POST /tasks` `[1,2]`, `priority:"3"`, `title:123`, `tags:[1,2]`: 500 HTML → 400 `Dados inválidos` | sim | [entrada inválida] tipos errados em tasks |
| `POST /tasks` `tags:5`: 201 → 400 `Dados inválidos` | sim | [entrada inválida] tags de tipo errado |
| `PUT /tasks/<id>` `priority:null`, `title:null`: 500 HTML → 400 `Dados inválidos` | sim | [entrada inválida] tipos errados em tasks |
| `GET /tasks/search?priority=abc`: 500 HTML → 400 `Dados inválidos` | sim | [entrada inválida] filtros não inteiros |
| `POST /users` `[1]` e `password:12345`: 500 HTML → 400 `Dados inválidos` | sim | [entrada inválida] POST /users |
| `PUT /users/<id>` `name:null`: 500 → 400 `Nome é obrigatório`; `name:""`: 200 → 400 `Nome é obrigatório`; `active:"abc"`: 500 → 400 `Dados inválidos` | sim | [entrada inválida] PUT /users |
| `POST /login` `password:1234`: 500 HTML → 400 `Dados inválidos` | sim | [entrada inválida] login |
| `POST /categories` `[1]`, `PUT /categories/<id>` `null`: 500 HTML → 400 `Dados inválidos`; `name:null`: 500 → 400 `Nome é obrigatório` | sim | [entrada inválida] categorias |
| Logins/`PUT` seguintes mostram `name:"Teste 2"` em vez de `""` | sim (efeito derivado) | o baseline gravou `name:""` via `PUT /users {"name":""}`, que agora é rejeitado |
| `GET /reports/summary` (total 12→11, pending 7→6, medium 4→3, created_last_7_days 12→11, `user_name` do usuário 4), `GET /tasks/stats` (total/pending/completion_rate) e `GET /tasks` final (11→10 itens) | sim (efeito derivado) | o baseline criou a task id 12 (`tags:5`), agora rejeitada; conferido em Python: a única task a mais no baseline é a id 12 e as demais são idênticas |

Nenhuma diferença fora dessa lista: não há regressão.

## Rotas protegidas
Nenhuma rota usa a política de endpoints perigosos (não existe endpoint administrativo/SQL arbitrário); a falta de autenticação geral ficou em "Not addressed" no plano.

## Migração de hash MD5 (credenciais existentes)
Banco original (hashes MD5 do seed antigo) copiado para `reports/.tmp/legacy.db` e usado via `DATABASE_URL`:
```
antes : scrypt:32768:8:1$HXUbeUHbPUU9QbkN$5dd0411e462fa897008000a261acdd1b9082db4da27c0dba5e821e084cb0b2c5f55425b192b68db589a34d0b9564f0e496741067970b80126d21cc7e12cf00e4
login legado: 200 False
depois: scrypt:32768:8:1$HXUbeUHbPUU9QbkN$5dd041...
login novo hash: 200
senha errada: 401 {'error': 'Credenciais inválidas'}
maria (nao logou) ainda MD5: False
login maria legado: 200 scrypt:32768
```

## Reverificação do catálogo
```
arquivos: 29
    1317 total

$ SEC-01 segredos
(nenhuma ocorrência)

$ SEC-02 SQL por concatenação
./app.py:37:    with app.app_context():
./seed.py:45:    with app.app_context():

$ SEC-03 hash fraco
./models/user.py:47:            legacy_digest = hashlib.md5(password.encode()).hexdigest()

$ SEC-04 password na serialização
./seed.py:13:    {'name': 'João Silva', 'email': 'joao@email.com', 'password': '1234', 'role': 'admin'},
./seed.py:14:    {'name': 'Maria Santos', 'email': 'maria@email.com', 'password': 'abcd', 'role': 'user'},
./seed.py:15:    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'password': 'pass', 'role': 'manager'},
./validators/inputs.py:207:    return {'name': name, 'email': email, 'password': password, 'role': role}

$ SEC-06 debug fixo
(nenhuma ocorrência)

$ PERF N+1 / Query legada
./controllers/user_controller.py:34:        data['task_count'] = len(user.tasks)

$ QUAL-01 except genérico
(nenhuma ocorrência)

$ DEPR utcnow / query.get
./models/database.py:9:    """Data/hora UTC sem fuso (mesmo formato que datetime.utcnow() gravava)."""

$ QUAL-04 print
./app.py:34:        app.register_blueprint(blueprint)
./routes/category_routes.py:5:category_bp = Blueprint('categories', __name__)
./routes/main_routes.py:5:main_bp = Blueprint('main', __name__)
./routes/report_routes.py:5:report_bp = Blueprint('reports', __name__)
./routes/task_routes.py:5:task_bp = Blueprint('tasks', __name__)
./routes/user_routes.py:5:user_bp = Blueprint('users', __name__)
./seed.py:66:        print("Seed concluído com sucesso!")
./seed.py:67:        print(f"  {User.count_all()} usuários")
./seed.py:68:        print(f"  {Category.count_all()} categorias")
./seed.py:69:        print(f"  {Task.count_all()} tasks")

$ QUAL-05 literais de negócio
./models/category.py:5:DEFAULT_COLOR = '#000000'
./models/task.py:6:TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')

$ ARCH-03 estado global mutável
(nenhuma ocorrência)

```
Imports não usados (script AST em `reports/.tmp`): só `app.py:6 import models`, intencional (`# noqa`, registra os models antes do `create_all`).

Ocorrências remanescentes e justificativa:
- `SEC-02 app.app_context()`: falso positivo do grep (`with app.app_context()`); nenhuma query montada por texto.
- `SEC-03 models/user.py:47`: MD5 usado só para **verificar** hashes legados e migrá-los no primeiro login (RF-08); nada novo é gravado em MD5.
- `SEC-04`: `seed.py` (senhas de exemplo documentadas, entrada do seed) e `validators/inputs.py:207` (entrada validada); nenhum serializador devolve `password`.
- `PERF len(user.tasks)`: `selectinload(User.tasks)` carrega tudo em 2 queries (sem N+1).
- `DEPR`: apenas o texto de um docstring.
- `QUAL-04 print`: o grep casou `register_blueprint(`/`Blueprint(` (falso positivo) e os `print` de `seed.py`, que são a saída de CLI do script.
- `QUAL-05`: são as próprias definições das constantes nomeadas.

## Limpeza
- Servidores encerrados: o `validate.sh` mata o grupo de processos no `trap EXIT`; `pgrep -fl "app.py|flask --app"` → nenhum processo; porta 5050 livre: sim (`lsof` sem listener).
- Dados restaurados: sim (`cmp` entre o backup e `instance/tasks.db` sem diferença).
- reports/.tmp removido: sim.

## Itens abertos (ver "Not addressed" no plano)
- Sem autenticação real (token `fake-jwt-token-<id>` mantido), `role` autoatribuível.
- DELETE /users apaga as tasks do usuário; DELETE /categories deixa tasks órfãs.
- Respostas HTML padrão do Flask para JSON malformado (400), sem content-type (415), 404 e 405.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
app.py  seed.py  requirements.txt  .env.example  README.md
config/       settings.py
models/       database.py user.py task.py category.py
validators/   inputs.py
routes/       main_routes.py task_routes.py user_routes.py category_routes.py report_routes.py
controllers/  common.py task_controller.py user_controller.py category_controller.py report_controller.py
services/     auth_service.py report_service.py notification_service.py
middlewares/  errors.py

## Validation
  ✓ Application boots without errors (python app.py)
  ✓ All endpoints respond (22/22; 100 chamadas comparadas com o baseline)
  ✓ No catalog anti-patterns remaining
  ✗ Pendente de propósito: autenticação real, exclusões que apagam/orfanam dados (ver Not addressed)

## Behavior changes
- [segurança] `password` (hash) removido das respostas de usuário e login
- [segurança] senhas novas com scrypt (werkzeug); hashes MD5 antigos aceitos e migrados no primeiro login
- [segurança] debug desligado por padrão; SECRET_KEY e SMTP vêm do ambiente
- [entrada inválida] corpo não-objeto e tipos errados em tasks, users, login e categories → 400 (antes 500 ou aceito)
- [entrada inválida] PUT /users e PUT /categories com name null/"" → 400 "Nome é obrigatório"
- [entrada inválida] GET /tasks/search com priority/user_id não inteiros → 400
================================
```
