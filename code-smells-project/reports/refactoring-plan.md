# Refactoring Plan — code-smells-project

## Context

A auditoria (`reports/audit-report.md`) encontrou 20 findings (6 CRITICAL, 5 HIGH,
5 MEDIUM, 4 LOW) numa API Flask de e-commerce com 4 arquivos na raiz: SQL injection
em todas as queries, endpoints admin sem auth (SQL arbitrário e reset do banco),
senhas em texto puro e devolvidas pela API, SECRET_KEY hardcoded e exposta no
/health, debug ligado, conexão global compartilhada, regra de negócio no model,
N+1 e validação fraca. O objetivo é levar o projeto ao MVC e resolver todos os
findings sem quebrar o contrato externo (paths, métodos, campos, mensagens, boot
`python app.py`).

## Refactoring Plan

Target structure:
```
code-smells-project/
├── app.py                         # composition root: create_app() + boot (python app.py)
├── config/
│   ├── __init__.py
│   ├── settings.py                # env: SECRET_KEY, DEBUG, HOST, PORT, DB_PATH, ADMIN_TOKEN, APP_ENV
│   └── constants.py               # categorias, status, faixas/taxas de desconto, versão
├── db/
│   ├── __init__.py
│   ├── connection.py              # get_db() por requisição (flask.g), close_db, transaction(), conexão read-only
│   └── schema.py                  # CREATE TABLE, seed (senhas com hash), migração de senhas legadas
├── models/
│   ├── __init__.py
│   ├── produto_model.py           # SQL parametrizado + serializer único de produto
│   ├── usuario_model.py           # SQL parametrizado + serializer sem senha
│   ├── pedido_model.py            # SQL parametrizado + listagem com JOIN (sem N+1)
│   └── admin_model.py             # reset com SQL fixo + consulta read-only
├── services/
│   ├── __init__.py
│   ├── auth_service.py            # hash/verify (werkzeug.security) + rehash de legado
│   ├── pedido_service.py          # criação de pedido (invariantes + transação), status
│   ├── relatorio_service.py       # faixas de desconto
│   └── notificacao_service.py     # email/SMS/push simulados via logger
├── validators/
│   ├── __init__.py
│   └── payloads.py                # validação de tipo/obrigatoriedade (produto, usuário, login, pedido, busca, status)
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py      # / e /health
│   └── admin_controller.py
├── routes/                         # views: método + path -> controller (Blueprints)
│   ├── __init__.py                # register_routes(app)
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── admin_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── errors.py                  # ApiError + handler central (preserva formato por rota)
│   └── admin_auth.py              # @admin_required (X-Admin-Token, compare_digest)
├── .env.example
├── README.md                      # documenta variáveis de ambiente
└── requirements.txt               # sem dependências novas
```
`controllers.py`, `models.py` e `database.py` são removidos (substituídos pelos
pacotes); o `__pycache__/` antigo da raiz é apagado.

Steps (CRITICAL → LOW):
1. [CRITICAL] Proteger /admin/query e /admin/reset-db: rota mantida, `@admin_required` (ADMIN_TOKEN do ambiente, header `X-Admin-Token`, `hmac.compare_digest`, 403 `{"erro": "Acesso negado"}` sem token configurado ou com token errado); query em conexão `file:...?mode=ro`, falha/escrita → 400 `{"erro": "Consulta inválida ou não permitida"}` com detalhe só no log; reset com tupla fixa de `DELETE` + log — resolve AP-SEC-05 — padrão RF-15
2. [CRITICAL] Reescrever todas as 19 queries com placeholders `?` (inclusive LIKE `'%' || ? || '%'` e filtros dinâmicos com lista de parâmetros) — resolve AP-SEC-02 — RF-02
3. [CRITICAL] Serializer único de usuário sem `senha` (GET /usuarios, /usuarios/<id>) — resolve AP-SEC-04 (senha) — RF-13
4. [CRITICAL] /health sem `secret_key`; `debug`, `db_path`, `ambiente`, `versao` vindos de config/constantes (defaults `"loja.db"`, `"producao"`, `"1.0.0"`) — resolve AP-SEC-04 (health) — RF-13 + RF-01
5. [CRITICAL] Hash de senha com `werkzeug.security` (já vem com o Flask): seed grava hash das mesmas senhas; no boot, senhas sem prefixo de hash (`scrypt:`/`pbkdf2:`) são convertidas; login busca por e-mail (parametrizado) e verifica cada usuário com aquele e-mail na ordem do id (preserva o “primeiro que bate” do original); valor legado em texto puro é aceito uma vez via `compare_digest` e regravado com hash — resolve AP-SEC-03 — RF-08
6. [CRITICAL] `config/settings.py` lendo do ambiente; SECRET_KEY = env ou `secrets.token_hex(32)` gerado no boot (nada na app depende de chave persistente — sem sessões — e ela nunca é logada nem devolvida), para o boot `python app.py` continuar funcionando sem variáveis; `.env.example` documenta tudo — resolve AP-SEC-01 — RF-01
7. [HIGH] DEBUG do ambiente com default `false`; HOST default `0.0.0.0`, PORT default `5000` — resolve AP-SEC-06 — RF-01
8. [HIGH] Mover o caso de uso de pedido para `services/pedido_service.py` (transação `BEGIN IMMEDIATE` / commit / rollback), desconto para `relatorio_service.py`, notificações para `notificacao_service.py` — resolve AP-ARCH-02 (models) — RF-04
9. [HIGH] Separar camadas (routes → controllers → services → models → db), app.py como composition root com `create_app()`; health e admin sem SQL fora de models — resolve AP-ARCH-02 (app.py/health) — RF-03
10. [HIGH] Conexão por requisição em `flask.g` + `teardown_appcontext`, sem `check_same_thread=False`; conexão em modo autocommit (`isolation_level=None`) com transações explícitas nas escritas multi-etapa — resolve AP-ARCH-03 — RF-05
11. [HIGH] `create_app()` lê DB_PATH da config (default `loja.db`, resolvido relativo à pasta do app.py) e inicializa schema/seed/migração explicitamente no boot — resolve AP-ARCH-04 — RF-05/RF-03
12. [MEDIUM] Invariantes do pedido no serviço: `itens` lista não vazia; `usuario_id`, `produto_id`, `quantidade` inteiros (não bool), `quantidade > 0`; usuário precisa existir; estoque checado contra a soma acumulada por produto (mesma mensagem “Estoque insuficiente para <nome>”); total, itens_pedido e baixa continuam por item, na ordem enviada — resolve AP-QUAL-02 (pedido) — RF-14 + RF-04
13. [MEDIUM] `validators/payloads.py`: corpo lido com `get_json(silent=True)`; corpo ausente/malformado/não-objeto e tipos errados → 400 com mensagem já existente na rota; PUT /produtos aplica as mesmas regras do POST (nome 2–200, categoria válida), mantendo a checagem 404 antes da validação do corpo; busca com preço não numérico → 400; status de pedido inexistente → 404 — resolve AP-QUAL-02 (rotas) — RF-14
14. [MEDIUM] `middlewares/errors.py`: `ApiError(payload, status)` + `@app.errorhandler(Exception)` só para exceções não-HTTP → 500 `{"erro": "Erro interno do servidor"}` (no /health: `{"status": "erro", "detalhes": "Erro interno do servidor"}`), detalhe via `logger.exception`; `HTTPException` (404/405 de rota inexistente) segue o padrão do Flask como hoje; controllers sem `try/except Exception` — resolve AP-QUAL-01 — RF-07
15. [MEDIUM] Listagem de pedidos com 2 queries (pedidos + itens LEFT JOIN produtos `ORDER BY pedido_id, id`), agrupadas em memória, `"Desconhecido"` quando o produto não existe; relatório com uma query de agregação condicional (`COUNT`, `SUM`, `SUM(CASE ...)`); produto lido uma vez por item na criação — resolve AP-PERF-01 — RF-06
16. [MEDIUM] Serializer único por entidade, montagem única de pedidos, validador único de produto — resolve AP-QUAL-03 — RF-04/RF-13
17. [LOW] `logging` (logger por módulo, `basicConfig` no app.py) no lugar de todos os `print`; login loga id do usuário, não o e-mail — resolve AP-QUAL-04 — RF-12
18. [LOW] Constantes nomeadas em `config/constants.py` (categorias, status, faixas/taxas, versão, porta padrão) — resolve AP-QUAL-05 — RF-11
19. [LOW] Nomes descritivos (`produto_id`, `pedido_id`, sem `cursor2/3`, sem `e` genérico) — resolve AP-QUAL-06 — renomeação interna
20. [LOW] Remover imports mortos (`os` em database.py, `sqlite3` em models.py) — resolve AP-QUAL-07 — limpeza

Not addressed (fora das duas categorias de mudança aceitas — viram recomendação):
- Sem autenticação nas rotas de leitura de usuários/pedidos (GET /usuarios, /pedidos): exigir auth seria regra nova e quebraria o contrato. Recomendação: token de sessão/JWT a partir do login.
- E-mail duplicado e formato de e-mail não validados em POST /usuarios; schema sem UNIQUE(email) e sem FOREIGN KEY: seria regra nova e/ou exigiria migrar dados existentes. Recomendação: índice único após deduplicar.
- DELETE /produtos apaga fisicamente e deixa itens de pedido apontando para produto inexistente ("Desconhecido"): corrigir exigiria exclusão lógica (comportamento novo) ou apagar histórico. Recomendação: soft delete via coluna `ativo`.
- Cancelar pedido não devolve o estoque (só loga "Devolver estoque"): implementar seria regra nova. Recomendação: devolver estoque na transição para "cancelado".
- `preco_min=0`/`preco_max=0` ignorados pela busca: corrigir muda o resultado de uma chamada válida. Recomendação: testar `is not None`.
- CORS aberto para qualquer origem: mantido (não há sessão/cookie); recomendação: restringir por config.

Contract to preserve:
- Rotas: GET /, GET /produtos, GET /produtos/busca, GET /produtos/<int:id>, POST /produtos, PUT /produtos/<int:id>, DELETE /produtos/<int:id>, GET /usuarios, GET /usuarios/<int:id>, POST /usuarios, POST /login, POST /pedidos, GET /pedidos, GET /pedidos/usuario/<int:usuario_id>, PUT /pedidos/<int:pedido_id>/status, GET /relatorios/vendas, GET /health, POST /admin/reset-db, POST /admin/query
- Respostas: mesmos campos, status e mensagens de sucesso e erro de cada rota (ex.: `{"erro": "Produto não encontrado", "sucesso": false}` 404 no GET por id, mas `{"erro": "Produto não encontrado"}` no PUT/DELETE; `{"erro": ..., "sucesso": false}` 400 nos erros de negócio do pedido; 401 no login inválido); ordem dos resultados (por id).
- Boot: `python app.py` (porta padrão 5000, agora sobrescrevível por `PORT`)

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] GET /usuarios e /usuarios/<id> não devolvem mais `senha` — dado sensível — prova: `GET /usuarios`
- [segurança] GET /health não devolve mais `secret_key`; `debug` passa a refletir a config (false por padrão) — segredo exposto / debug desligado — prova: `GET /health`
- [segurança] Debug do Flask desligado por padrão — RCE via debugger — prova: log de boot sem "Debugger is active"
- [segurança] /admin/query e /admin/reset-db respondem 403 `{"erro": "Acesso negado"}` sem ADMIN_TOKEN configurado ou com token errado — backdoor — prova: chamadas sem token e com token errado
- [segurança] Com token válido: /admin/query só executa leitura (SELECT continua `{"dados": [...], "sucesso": true}`); escrita ou SQL inválido → 400 `{"erro": "Consulta inválida ou não permitida"}` em vez de commit/500 com mensagem do banco — prova: SELECT e UPDATE com token
- [segurança] SQL injection fechada: login com `' OR '1'='1' --` passa a 401; busca com apóstrofo (`q=27''`) passa de 500 a 200 com busca literal — prova: as duas chamadas
- [segurança] Erros inesperados respondem 500 com mensagem fixa (`"Erro interno do servidor"`) em vez de `str(e)` — vazamento de internals — prova: coberta pelas chamadas abaixo que antes davam 500 com mensagem interna
- [segurança] Senhas gravadas com hash (seed e novos usuários; legado migrado no boot) — prova: login com as credenciais do seed + login de usuário criado no teste; `SELECT senha` via /admin/query com token mostra hash
- [entrada inválida] Corpo ausente, JSON malformado ou não-objeto → 400 com a mensagem existente da rota (antes 500): POST/PUT /produtos, POST /usuarios, POST /pedidos → `{"erro": "Dados inválidos"}`; POST /login → `{"erro": "Email e senha são obrigatórios"}`; PUT /pedidos/<id>/status → `{"erro": "Status inválido"}`; POST /admin/query (com token) → `{"erro": "Query não informada"}` — prova: `-d '{'` e corpo vazio em cada uma
- [entrada inválida] Tipos errados em produto (`preco` não numérico, `estoque` não inteiro, `nome`/`descricao`/`categoria` não string) e em usuário/login (campos não string) → 400 `{"erro": "Dados inválidos"}` (usuário/produto) ou `{"erro": "Email e senha são obrigatórios"}` (login) — antes 500 — prova: `{"nome":"X","preco":"abc","estoque":1}`
- [entrada inválida] PUT /produtos/<id> passa a aplicar as regras do POST: “Nome muito curto”, “Nome muito longo”, “Categoria inválida. Válidas: [...]” — prova: PUT com `nome:"A"` e `categoria:"xyz"`
- [entrada inválida] POST /pedidos: quantidade ≤ 0 ou não inteira, `produto_id`/`usuario_id` não inteiros, item sem campo → 400 `{"erro": "Dados inválidos"}`; usuário inexistente → 400 `{"erro": "Usuário não encontrado", "sucesso": false}`; itens repetidos que somados excedem o estoque → 400 `{"erro": "Estoque insuficiente para <nome>", "sucesso": false}` — prova: quantidade -5, usuario_id 9999, 2× produto 6 com quantidade 5 (estoque 8)
- [entrada inválida] GET /produtos/busca com `preco_min`/`preco_max` não numérico → 400 `{"erro": "Dados inválidos"}` (antes 500) — prova: `?preco_min=abc`
- [entrada inválida] PUT /pedidos/<id>/status com pedido inexistente → 404 `{"erro": "Pedido não encontrado"}` (antes 200 sucesso falso) — prova: `/pedidos/9999/status`
- [entrada inválida] Corpo enviado sem `Content-Type: application/json` passa de 500 (415 embrulhado) a 400 com a mensagem da rota — prova: POST /produtos com `-H 'Content-Type: text/plain'`

Data preservation:
- Seeds: mesmos 10 produtos e 3 usuários com as mesmas senhas documentadas (admin@loja.com/admin123, joao@email.com/123456, maria@email.com/senha123); muda só o armazenamento (hash). Seed só roda com `produtos` vazia, como hoje.
- Credenciais existentes: senhas em texto puro no `loja.db` são convertidas para hash no boot; login ainda aceita valor legado uma vez e regrava com hash — nenhum banco precisa ser recriado.
- Registros persistidos: nenhuma correção apaga ou altera registros (fora a conversão da coluna `senha` para hash); reset-db só com token e com o mesmo SQL de antes.
- Segredos: SECRET_KEY e ADMIN_TOKEN nunca vão para log ou resposta; SECRET_KEY gerada no boot quando ausente não é logada.

Validation (segundo `validation-protocol.md`):
- Copiar fontes originais para `reports/.tmp/original-src/` e `loja.db` para `reports/.tmp/data-backup/` antes de qualquer alteração.
- Script `reports/.tmp/validate.sh`: porta livre em 5050–5099 (o app original roda via `flask --app app run --port $PORT`, o refatorado via `PORT=$PORT python app.py`), `trap` para encerrar o servidor, restauração do `loja.db` antes de cada execução.
- Mesmas chamadas, mesma ordem, mesmo estado inicial → `reports/baseline-responses.txt` e `reports/after-responses.txt`: sucesso de cada uma das 19 rotas; ID inexistente em cada rota com parâmetro; corpo válido / sem campo obrigatório / JSON malformado em cada POST/PUT; uma chamada por mudança intencional; admin sem token, token errado e com token (ADMIN_TOKEN só na execução “depois”); login com credenciais do seed; IDs criados capturados da resposta; DELETE e reset por último.
- `diff` mascarado (timestamps) — cada diferença classificada na tabela do `validation-report.md`; diferença não listada acima = regressão a corrigir.
- App sobe sem erros com `python app.py` (log de boot salvo); todos os endpoints da Fase 1 respondem.
- Reverificação do catálogo com `grep` (concatenação em `execute`, `print(`, `except Exception`, `str(e)`, `SECRET`, `debug=True`, `check_same_thread`, `global`, `"senha"` em serializers) com saída real copiada; remanescentes justificados.
- Limpeza: servidores encerrados e porta livre confirmada, `loja.db` restaurado, `reports/.tmp/` apagado; `reports/validation-report.md` + bloco PHASE 3.
