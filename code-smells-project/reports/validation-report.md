# Validation Report

## Ambiente
- Porta usada: 5050 (livre antes do boot: sim, verificada em /dev/tcp; 5000 também estava livre)
- Baseline: app original em `reports/.tmp/original-src/` com `.venv/bin/python -m flask --app app run --port 5050` (o original fixa a 5000 no código)
- Depois: comando de boot original `python app.py` (`.venv/bin/python app.py`, `PORT=5050`, `ADMIN_TOKEN` de teste) — sobe sem erro; log de boot sem "Debugger is active"
- Estado de dados: `loja.db` não existia antes; removido antes e depois de cada execução (trap no script)

Trecho do log de boot do app refatorado (última linhas):
```
2026-10-28 19:15:17,169 INFO werkzeug: 127.0.0.1 - - [28/Oct/2026 19:15:17] "GET /health HTTP/1.1" 200 -
2026-10-28 19:15:17,197 INFO controllers.produto_controller: Listando 0 produtos
2026-10-28 19:15:17,197 INFO werkzeug: 127.0.0.1 - - [28/Oct/2026 19:15:17] "GET /produtos HTTP/1.1" 200 -
```

## Baseline × depois
Comando: `diff <(mask reports/baseline-responses.txt) <(mask reports/after-responses.txt)` (mask = timestamps → `<ts>`; corpos JSON normalizados por `json.dumps`, pois o original, com DEBUG ligado, imprimia JSON indentado). Saída real completa:

```diff
7c7
< {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 10, "usuarios": 3}, "database": "connected", "db_path": "loja.db", "debug": true, "secret_key": "minha-chave-super-secreta-123", "status": "ok", "versao": "1.0.0"}
---
> {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 10, "usuarios": 3}, "database": "connected", "status": "ok", "versao": "1.0.0"}
34,35c34,35
< status: 500
< {"erro": "could not convert string to float: 'abc'"}
---
> status: 400
> {"erro": "Filtro de preço inválido"}
39c39
< {"dados": [], "sucesso": true, "total": 0}
---
> {"dados": [{"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Monitor 27 polegadas 144hz", "estoque": 15, "id": 4, "nome": "Monitor 27''", "preco": 1899.9}], "sucesso": true, "total": 1}
43c43
< {"dados": [{"ativo": 1, "categoria": "admin", "criado_em": "<ts>", "descricao": "admin@loja.com", "estoque": 0, "id": 1, "nome": "Admin", "preco": "admin123"}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Notebook potente para jogos", "estoque": 10, "id": 1, "nome": "Notebook Gamer", "preco": 5999.99}, {"ativo": 1, "categoria": "cliente", "criado_em": "<ts>", "descricao": "joao@email.com", "estoque": 0, "id": 2, "nome": "João Silva", "preco": "123456"}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Mouse sem fio ergonômico", "estoq
---
> {"dados": [], "sucesso": true, "total": 0}
54,55c54,55
< status: 500
< {"erro": "near \"agua\": syntax error"}
---
> status: 201
> {"dados": {"id": 12}, "mensagem": "Produto criado", "sucesso": true}
82,83c82,83
< status: 500
< {"erro": "'<' not supported between instances of 'str' and 'int'"}
---
> status: 400
> {"erro": "Preço deve ser um número"}
86,87c86,87
< status: 201
< {"dados": {"id": 12}, "mensagem": "Produto criado", "sucesso": true}
---
> status: 400
> {"erro": "Estoque deve ser um número inteiro"}
90,91c90,91
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Dados inválidos"}
106,107c106,107
< status: 200
< {"mensagem": "Produto atualizado", "sucesso": true}
---
> status: 400
> {"erro": "Nome muito curto"}
110,111c110,111
< status: 200
< {"mensagem": "Produto atualizado", "sucesso": true}
---
> status: 400
> {"erro": "Categoria inválida. Válidas: ['informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros']"}
118,119c118,119
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Dados inválidos"}
126,127c126,127
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 404
> {"erro": "Produto não encontrado"}
131c131
< {"dados": [{"criado_em": "<ts>", "email": "admin@loja.com", "id": 1, "nome": "Admin", "senha": "admin123", "tipo": "admin"}, {"criado_em": "<ts>", "email": "joao@email.com", "id": 2, "nome": "João Silva", "senha": "123456", "tipo": "cliente"}, {"criado_em": "<ts>", "email": "maria@email.com", "id": 3, "nome": "Maria Santos", "senha": "senha123", "tipo": "cliente"}], "sucesso": true}
---
> {"dados": [{"criado_em": "<ts>", "email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, {"criado_em": "<ts>", "email": "joao@email.com", "id": 2, "nome": "João Silva", "tipo": "cliente"}, {"criado_em": "<ts>", "email": "maria@email.com", "id": 3, "nome": "Maria Santos", "tipo": "cliente"}], "sucesso": true}
135c135
< {"dados": {"criado_em": "<ts>", "email": "admin@loja.com", "id": 1, "nome": "Admin", "senha": "admin123", "tipo": "admin"}, "sucesso": true}
---
> {"dados": {"criado_em": "<ts>", "email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, "sucesso": true}
147c147
< {"dados": {"criado_em": "<ts>", "email": "ana@teste.com", "id": 4, "nome": "Ana Teste", "senha": "segredo1", "tipo": "cliente"}, "sucesso": true}
---
> {"dados": {"criado_em": "<ts>", "email": "ana@teste.com", "id": 4, "nome": "Ana Teste", "tipo": "cliente"}, "sucesso": true}
155c155
< {"dados": {"criado_em": "<ts>", "email": "eva@teste.com", "id": 5, "nome": "Eva Admin", "senha": "segredo2", "tipo": "cliente"}, "sucesso": true}
---
> {"dados": {"criado_em": "<ts>", "email": "eva@teste.com", "id": 5, "nome": "Eva Admin", "tipo": "cliente"}, "sucesso": true}
162,163c162,163
< status: 500
< {"erro": "can only concatenate str (not \"int\") to str"}
---
> status: 400
> {"erro": "Nome, email e senha devem ser texto"}
166,167c166,167
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Dados inválidos"}
194,195c194,195
< status: 200
< {"dados": {"email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, "mensagem": "Login OK", "sucesso": true}
---
> status: 401
> {"erro": "Email ou senha inválidos", "sucesso": false}
202,203c202,203
< status: 500
< {"erro": "can only concatenate str (not \"int\") to str"}
---
> status: 400
> {"erro": "Email e senha devem ser texto"}
206,207c206,207
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Email e senha são obrigatórios"}
222,223c222,223
< status: 201
< {"dados": {"pedido_id": 2, "total": 12999.0}, "mensagem": "Pedido criado com sucesso", "sucesso": true}
---
> status: 400
> {"erro": "Estoque insuficiente para Cadeira Gamer", "sucesso": false}
226,227c226,227
< status: 201
< {"dados": {"pedido_id": 3, "total": -6499.5}, "mensagem": "Pedido criado com sucesso", "sucesso": true}
---
> status: 400
> {"erro": "Quantidade deve ser um número inteiro maior que zero"}
230,231c230,231
< status: 201
< {"dados": {"pedido_id": 4, "total": 0.0}, "mensagem": "Pedido criado com sucesso", "sucesso": true}
---
> status: 400
> {"erro": "Quantidade deve ser um número inteiro maior que zero"}
242,243c242,243
< status: 201
< {"dados": {"pedido_id": 5, "total": 1299.9}, "mensagem": "Pedido criado com sucesso", "sucesso": true}
---
> status: 400
> {"erro": "Usuário não encontrado", "sucesso": false}
246,247c246,247
< status: 500
< {"erro": "string indices must be integers, not 'str'"}
---
> status: 400
> {"erro": "Itens do pedido inválidos"}
250,251c250,251
< status: 201
< {"dados": {"pedido_id": 6, "total": 5999.99}, "mensagem": "Pedido criado com sucesso", "sucesso": true}
---
> status: 400
> {"erro": "Itens do pedido inválidos"}
254,255c254,255
< status: 500
< {"erro": "no such column: abc"}
---
> status: 400
> {"erro": "Usuario ID inválido"}
266,267c266,267
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Dados inválidos"}
275c275
< {"dados": [{"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Notebook potente para jogos", "estoque": 7, "id": 1, "nome": "Notebook Gamer", "preco": 5999.99}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Mouse sem fio ergonômico", "estoque": 48, "id": 2, "nome": "Mouse Wireless", "preco": 89.9}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Teclado mecânico RGB", "estoque": 29, "id": 3, "nome": "Teclado Mecânico", "preco": 299.9}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "
---
> {"dados": [{"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Notebook potente para jogos", "estoque": 8, "id": 1, "nome": "Notebook Gamer", "preco": 5999.99}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Mouse sem fio ergonômico", "estoque": 49, "id": 2, "nome": "Mouse Wireless", "preco": 89.9}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "Teclado mecânico RGB", "estoque": 30, "id": 3, "nome": "Teclado Mecânico", "preco": 299.9}, {"ativo": 1, "categoria": "informatica", "criado_em": "<ts>", "descricao": "
279c279
< {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Notebook Gamer", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "pendente", "total": 12089.88, "usuario_id": 2}, {"criado_em": "<ts>", "id": 2, "itens": [{"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}, {"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}], "status": "pendente", "total": 12999.0, "usuario_id": 2}, {"cri
---
> {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Notebook Gamer", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "pendente", "total": 12089.88, "usuario_id": 2}], "sucesso": true}
283c283
< {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Notebook Gamer", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "pendente", "total": 12089.88, "usuario_id": 2}, {"criado_em": "<ts>", "id": 2, "itens": [{"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}, {"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}], "status": "pendente", "total": 12999.0, "usuario_id": 2}, {"cri
---
> {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Notebook Gamer", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "pendente", "total": 12089.88, "usuario_id": 2}], "sucesso": true}
287c287
< {"dados": [{"criado_em": "<ts>", "id": 5, "itens": [{"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 1}], "status": "pendente", "total": 1299.9, "usuario_id": 9999}], "sucesso": true}
---
> {"dados": [], "sucesso": true}
306,307c306,307
< status: 500
< {"erro": "400 Bad Request: The browser (or proxy) sent a request that this server could not understand."}
---
> status: 400
> {"erro": "Status inválido"}
310,311c310,311
< status: 200
< {"mensagem": "Status atualizado", "sucesso": true}
---
> status: 404
> {"erro": "Pedido não encontrado"}
315c315
< {"dados": {"desconto_aplicavel": 2588.93, "faturamento_bruto": 25889.27, "faturamento_liquido": 23300.34, "pedidos_aprovados": 0, "pedidos_cancelados": 1, "pedidos_pendentes": 5, "ticket_medio": 4314.88, "total_pedidos": 6}, "sucesso": true}
---
> {"dados": {"desconto_aplicavel": 1208.99, "faturamento_bruto": 12089.88, "faturamento_liquido": 10880.89, "pedidos_aprovados": 0, "pedidos_cancelados": 1, "pedidos_pendentes": 0, "ticket_medio": 12089.88, "total_pedidos": 1}, "sucesso": true}
335c335
< {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Desconhecido", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "cancelado", "total": 12089.88, "usuario_id": 2}, {"criado_em": "<ts>", "id": 2, "itens": [{"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}, {"preco_unitario": 1299.9, "produto_id": 6, "produto_nome": "Cadeira Gamer", "quantidade": 5}], "status": "pendente", "total": 12999.0, "usuario_id": 2}, {"cria
---
> {"dados": [{"criado_em": "<ts>", "id": 1, "itens": [{"preco_unitario": 5999.99, "produto_id": 1, "produto_nome": "Desconhecido", "quantidade": 2}, {"preco_unitario": 89.9, "produto_id": 2, "produto_nome": "Mouse Wireless", "quantidade": 1}], "status": "cancelado", "total": 12089.88, "usuario_id": 2}], "sucesso": true}
354,355c354,355
< status: 200
< {"dados": [{"id": 2, "nome": "Mouse Wireless"}], "sucesso": true}
---
> status: 403
> {"erro": "Acesso negado"}
358,359c358,359
< status: 200
< {"dados": [{"id": 2, "nome": "Mouse Wireless"}], "sucesso": true}
---
> status: 403
> {"erro": "Acesso negado"}
367c367
< {"dados": [{"email": "admin@loja.com", "senha": "admin123"}], "sucesso": true}
---
> {"dados": [{"email": "admin@loja.com", "senha": "scrypt:32768:8:1$DnqVZZwDGRt5CQ4U$03a6e82f4b0e5bca444105e6e99439fa578fdb2682e9cdb8985fee7a3cb36862e18e3af4099af8591e1be5f38e5cc51004ed7cb4deae7e6209719ef0e37db539"}], "sucesso": true}
370,371c370,371
< status: 200
< {"mensagem": "Query executada", "sucesso": true}
---
> status: 400
> {"erro": "Consulta inválida ou não permitida"}
374,375c374,375
< status: 500
< {"erro": "near \"SELEC\": syntax error"}
---
> status: 400
> {"erro": "Consulta inválida ou não permitida"}
383,387c383
< <!doctype html>
< <html lang=en>
< <title>400 Bad Request</title>
< <h1>Bad Request</h1>
< <p>The browser (or proxy) sent a request that this server could not understand.</p>
---
> {"erro": "Query não informada"}
390,391c386,387
< status: 200
< {"mensagem": "Banco de dados resetado", "sucesso": true}
---
> status: 403
> {"erro": "Acesso negado"}
394,395c390,391
< status: 200
< {"mensagem": "Banco de dados resetado", "sucesso": true}
---
> status: 403
> {"erro": "Acesso negado"}
399c395
< {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 0, "usuarios": 0}, "database": "connected", "db_path": "loja.db", "debug": true, "secret_key": "minha-chave-super-secreta-123", "status": "ok", "versao": "1.0.0"}
---
> {"ambiente": "producao", "counts": {"pedidos": 1, "produtos": 10, "usuarios": 5}, "database": "connected", "status": "ok", "versao": "1.0.0"}
407c403
< {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 0, "usuarios": 0}, "database": "connected", "db_path": "loja.db", "debug": true, "secret_key": "minha-chave-super-secreta-123", "status": "ok", "versao": "1.0.0"}
---
> {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 0, "usuarios": 0}, "database": "connected", "status": "ok", "versao": "1.0.0"}
```

| Diferença (linha do diff) | Esperada? | Mudança intencional do plano |
|---|---|---|
| 7, 395, 403 `/health` sem `secret_key`/`db_path`/`debug` | sim | [segurança] /health |
| 34-35 `busca?preco_min=abc` 500 → 400 | sim | [entrada inválida] filtro de preço |
| 39, 43 `busca?q=%27` e UNION: `[]` → resultado legítimo / `[]` (sem vazar senhas) | sim | [segurança] SQL injection fechada (aspas passam a funcionar; UNION não devolve usuários) |
| 54-55 produto `Caneca D'agua` 500 → 201 | sim | [segurança] SQL injection fechada |
| 82-87 `preco:"abc"` 500 → 400; `estoque:1.5` 201 → 400 | sim | [entrada inválida] tipos de produto |
| 90, 118, 126, 166, 206, 266, 306, 383 JSON malformado 500/HTML → 400 `Dados inválidos` (ou mensagem da rota) | sim | [entrada inválida] corpo malformado. Em `PUT /produtos/9999 {` a resposta passa a ser 404 (a existência é checada antes do corpo, como na ordem original) |
| 106-111 PUT com `nome:"X"` / `categoria:"xyz"` 200 → 400 | sim | [entrada inválida] PUT aplica as regras do POST |
| 131, 135, 147, 155 `/usuarios` sem `senha` | sim | [segurança] senha não exposta |
| 155 usuário com `"tipo":"admin"` continua `cliente` | sim (igual ao original) | RF-16 nível 1 |
| 162-163, 202-203 `senha:123`, `email:1` 500 → 400 | sim | [entrada inválida] usuário/login não texto |
| 194-195 login com `admin@loja.com' --` 200 → 401 | sim | [segurança] SQL injection fechada |
| 222-231 pedido com produto repetido, `quantidade` -5 e 0: 201 → 400 | sim | [entrada inválida] invariantes do pedido |
| 242-243 `usuario_id` 9999 201 → 400 | sim | [entrada inválida] usuário inexistente |
| 246-255 `itens:"abc"`, `produto_id:"1 OR 1=1"`, `usuario_id:"abc"` 500/201 → 400 | sim | [entrada inválida] + [segurança] injeção |
| 275-287, 315 estoque, listagens de pedidos e relatório com menos pedidos | sim, consequência | os pedidos extras do baseline (ids 2-6) foram recusados acima; o pedido #1 é idêntico nos dois (mesmo total 12089.88, itens, "Desconhecido" após DELETE do produto 1) |
| 310-311 `PUT /pedidos/9999/status` 200 → 404 | sim | [entrada inválida] pedido inexistente |
| 354-359, 387-395 admin sem token / token errado → 403 | sim | [segurança] endpoints perigosos |
| 367 `senha` no banco com prefixo `scrypt:` | sim | [segurança] hash de senha |
| 370-375 admin com token: `DELETE` e `SELEC x` → 400 mensagem fixa | sim | [segurança] consulta somente-leitura, sem mensagem do banco |
| 395 `/health` após reset sem token: contagens preservadas (reset negado) | sim, consequência | [segurança] reset exige token |

Nenhuma regressão: toda diferença está na lista de mudanças intencionais do plano.

## Rotas protegidas
Resposta real (de `reports/after-responses.txt`; `ADMIN_TOKEN=tok-teste-123`):

| Rota | Sem token | Token errado | Com token |
|---|---|---|---|
| POST /admin/query (SELECT) | 403 `{"erro": "Acesso negado"}` | 403 | 200 `{"dados": [...], "sucesso": true}` |
| POST /admin/query (DELETE) | — | — | 400 `{"erro": "Consulta inválida ou não permitida"}` |
| POST /admin/reset-db | 403 `{"erro": "Acesso negado"}` | 403 | 200 `{"mensagem": "Banco de dados resetado", "sucesso": true}` |

Sem `ADMIN_TOKEN` configurado, mesmo com header, as duas rotas respondem 403 (ver "Migração").

## Migração de senhas e seed
Saída real de `reports/.tmp/migracao.sh` (banco criado pelo app ORIGINAL com senhas em texto puro, depois aberto pelo app refatorado):
```
== 1. app ORIGINAL cria banco legado (senha em texto puro)
{"dados":{"id":4},"sucesso":true}
 [201]
antes : [(1, 'admin@loja.com', 'admin123'), (2, 'joao@email.com', '123456'), (3, 'maria@email.com', 'senha123'), (4, 'legado@teste.com', 'minhasenha')]
== 2. app REFATORADO sobre o banco legado (DB_PATH)
login admin@loja.com/admin123 -> {"dados":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"mensagem":"Login OK","sucesso":true}
 [200]
login joao@email.com/123456 -> {"dados":{"email":"joao@email.com","id":2,"nome":"Jo\u00e3o Silva","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
 [200]
login maria@email.com/senha123 -> {"dados":{"email":"maria@email.com","id":3,"nome":"Maria Santos","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
 [200]
login legado@teste.com/minhasenha -> {"dados":{"email":"legado@teste.com","id":4,"nome":"Legado","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
 [200]
login legado@teste.com/errada -> {"erro":"Email ou senha inv\u00e1lidos","sucesso":false}
 [401]
== 3. sem ADMIN_TOKEN configurado: /admin/* desligado (mesmo com header)
{"erro":"Acesso negado"}
 [403]
{"erro":"Acesso negado"}
 [403]
== 4. rota 404/405 padrão e health sem campos internos
{"ambiente":"producao","counts":{"pedidos":0,"produtos":10,"usuarios":4},"database":"connected","status":"ok","versao":"1.0.0"}
 [200]
depois: 1 admin@loja.com scrypt:32768:8:1$441UR...
depois: 2 joao@email.com scrypt:32768:8:1$YtzQ5...
depois: 3 maria@email.com scrypt:32768:8:1$O59pr...
depois: 4 legado@teste.com scrypt:32768:8:1$k4Blq...
porta 5050 livre: sim
```

## Reverificação do catálogo
Saída real de `reports/.tmp/catalogo.sh` (todos os `.py` do projeto, exceto `.venv`, `.claude`, `reports`):
```
arquivos: 37 | linhas: 1112

$ grep -nE 'execute\([^)]*(\+|%|f"|f')' (fontes .py)
(sem ocorrências)

$ grep -nE '"\s*\+\s*(str\()?[a-z_]+\s*\+|\+\s*str\(' (fontes .py)
./validators/payloads.py:66:        raise ApiError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

$ grep -nE 'minha-chave|SECRET_KEY\s*=\s*"|admin123.*#' (fontes .py)
(sem ocorrências)

$ grep -nE 'debug\s*=\s*True|DEBUG"\]\s*=\s*True' (fontes .py)
(sem ocorrências)

$ grep -nE 'check_same_thread|^\s*global ' (fontes .py)
(sem ocorrências)

$ grep -nE 'except Exception|except:|str\(e\)|str\(erro\)' (fontes .py)
(sem ocorrências)

$ grep -nE '\bprint\(' (fontes .py)
(sem ocorrências)

$ grep -nE '"senha"\s*:\s*row|\["senha"\]\s*,?\s*$|secret_key|db_path' (fontes .py)
./controllers/admin_controller.py:15:def executar_query(db_path, dados):
./controllers/admin_controller.py:17:    return {"dados": admin_model.consultar(db_path, sql), "sucesso": True}, 200
./db/connection.py:16:def conectar(db_path):
./db/connection.py:18:    conn = sqlite3.connect(db_path, isolation_level=None)
./db/connection.py:23:def conectar_somente_leitura(db_path):
./db/connection.py:25:    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None)
./models/admin_model.py:26:def consultar(db_path, sql):
./models/admin_model.py:28:    conn = conectar_somente_leitura(db_path)

$ grep -nE 'utcnow|before_first_request|\.query\.get' (fontes .py)
(sem ocorrências)

$ grep -nE '^import os|^import sqlite3' (fontes .py)
./config/settings.py:2:import os
./controllers/sistema_controller.py:2:import sqlite3
./db/connection.py:2:import sqlite3
./models/admin_model.py:3:import sqlite3

$ grep -nE "senha|SECRET|ADMIN_TOKEN" em logger.* (segredos em log)
(sem ocorrências)

$ grep -nE "execute\(" restantes (valores constantes ou parametrizados)
./db/connection.py:27:    conn.execute("PRAGMA query_only = ON")
./db/connection.py:49:    conn.execute("BEGIN IMMEDIATE" if imediata else "BEGIN")
./db/connection.py:53:        conn.execute("ROLLBACK")
./db/connection.py:55:    conn.execute("COMMIT")
./db/schema.py:71:        conn.execute(ddl)
./db/schema.py:74:        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
./db/schema.py:88:    for usuario in conn.execute("SELECT id, senha FROM usuarios").fetchall():
./db/schema.py:90:            conn.execute(
./models/admin_model.py:23:            conn.execute(instrucao)
./models/admin_model.py:30:        cursor = conn.execute(sql)
./models/pedido_model.py:8:    cursor = conn.execute(
./models/pedido_model.py:16:    conn.execute(
./models/pedido_model.py:24:    return conn.execute(
./models/pedido_model.py:46:    for linha in conn.execute(sql, parametros).fetchall():
./models/pedido_model.py:66:    linha = conn.execute(
./models/pedido_model.py:81:    return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
./models/produto_model.py:11:    return [serializar(linha) for linha in conn.execute("SELECT * FROM produtos").fetchall()]
./models/produto_model.py:15:    linha = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
./models/produto_model.py:20:    cursor = conn.execute(
./models/produto_model.py:28:    conn.execute(
./models/produto_model.py:35:    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
./models/produto_model.py:39:    conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))
./models/produto_model.py:58:    return [serializar(linha) for linha in conn.execute(sql, parametros).fetchall()]
./models/produto_model.py:62:    return conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
./models/usuario_model.py:16:    return [serializar(linha) for linha in conn.execute("SELECT * FROM usuarios").fetchall()]
./models/usuario_model.py:20:    linha = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
./models/usuario_model.py:25:    return conn.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None
./models/usuario_model.py:30:    return conn.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
./models/usuario_model.py:34:    cursor = conn.execute(
./models/usuario_model.py:42:    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
./models/usuario_model.py:46:    return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
```
Linhas remanescentes e justificativa:
- `validators/payloads.py:66` `"Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)`: concatenação só de mensagem de erro (texto fixo do contrato), não é SQL.
- `models/produto_model.py` e `models/pedido_model.py` `conn.execute(sql, parametros)`: o `sql` é montado só com trechos fixos (`AND categoria = ?` etc.); todos os valores vão em `parametros`.
- `models/admin_model.py:30` `conn.execute(sql)`: SQL do administrador, mas em conexão `mode=ro` + `PRAGMA query_only` + authorizer que só permite SELECT/READ/FUNCTION; exige `ADMIN_TOKEN`.
- `db/connection.py` `conn.execute("BEGIN ...")`/`"COMMIT"`: instruções fixas.
- `import sqlite3`/`import os` restantes são todos usados.
- Magic numbers: faixas de desconto, categorias, status, limites de nome e versão agora em `config/constants.py`.
- N+1: `pedido_model.listar` faz uma única query com JOIN; `resumo_vendas` uma query agregada.
- AP-SEC-07 nível 2 e integridade referencial ficam em "Not addressed" no plano.

## Limpeza
- Servidores encerrados: todos (scripts com `trap ... EXIT`; `pgrep` sem processos) — portas 5000 e 5050-5099 livres: sim
- Dados restaurados: sim (`loja.db` não existia antes; removido; `__pycache__/` removidos)
- reports/.tmp removido: sim (cópia dos originais, scripts, logs e banco legado de teste)

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
app.py  .env.example  requirements.txt  README.md
config/       settings.py, constants.py
db/           connection.py, schema.py
models/       produto_model.py, usuario_model.py, pedido_model.py, admin_model.py
services/     auth_service.py, pedido_service.py, relatorio_service.py, notificacao_service.py
controllers/  produto_, usuario_, pedido_, relatorio_, sistema_, admin_controller.py
routes/       produto_, usuario_, pedido_, relatorio_, sistema_, admin_routes.py (+ _http.py)
validators/   payloads.py
middlewares/  errors.py, admin_auth.py
reports/      audit-report.md, refactoring-plan.md, baseline-responses.txt, after-responses.txt, validation-report.md

## Validation
  ✓ Application boots without errors (python app.py)
  ✓ All endpoints respond (19/19)
  ✓ No catalog anti-patterns remaining
  ✗ Pendentes por decisão (Not addressed): autenticação completa (RF-16 nível 2), FKs/UNIQUE/exclusão lógica, validação de formato/duplicidade de email

## Behavior changes
- [segurança] /usuarios e /health não expõem senha, secret_key, db_path, debug
- [segurança] SQL injection fechada; senhas com hash (migração no boot); debug off; SECRET_KEY do ambiente
- [segurança] /admin/* desligado sem ADMIN_TOKEN (403); /admin/query somente leitura, erro com mensagem fixa
- [entrada inválida] JSON malformado, tipos errados, quantidade <= 0, produto repetido acima do estoque, usuário/pedido inexistente, filtros de preço inválidos → 4xx
- [entrada inválida] PUT /produtos/<id> aplica as mesmas regras do POST
================================
```
