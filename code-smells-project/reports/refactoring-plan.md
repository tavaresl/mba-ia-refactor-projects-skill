# Refactoring Plan — code-smells-project

## Context

A skill `refactor-arch` auditou o projeto (Flask 3.1.1, 4 arquivos, 780 linhas) e
encontrou 21 problemas: 6 CRITICAL, 5 HIGH, 6 MEDIUM e 4 LOW (`reports/audit-report.md`).
Os principais são: SQL injection em 19 queries, `/admin/query` e `/admin/reset-db`
abertos, senhas em texto puro e expostas em `/usuarios`, `SECRET_KEY` no código e no
`/health`, debug ligado e nenhuma separação de camadas. Este plano leva o projeto ao
MVC e corrige todos os findings, mantendo o contrato HTTP (paths, métodos, campos,
mensagens) e o comando de boot `python app.py`. Só entram mudanças de comportamento
de "segurança" ou de "entrada inválida", listadas abaixo.

## Refactoring Plan

Target structure:
```
code-smells-project/
├── app.py                      # composition root: create_app(settings) + boot `python app.py`
├── config/
│   ├── __init__.py
│   ├── settings.py             # SECRET_KEY, DEBUG, HOST, PORT, DB_PATH, APP_ENV, ADMIN_TOKEN (ambiente)
│   └── constants.py            # versão, categorias, status, faixas de desconto, limites do nome
├── db/
│   ├── __init__.py
│   ├── connection.py           # get_db() por requisição (flask.g) + teardown, transacao(), conexão somente-leitura
│   └── schema.py               # DDL (idêntico ao atual), seed, migração de senhas em texto puro
├── models/                     # só SQL parametrizado + serialização; recebem a conexão por parâmetro
│   ├── __init__.py
│   ├── produto_model.py
│   ├── usuario_model.py
│   ├── pedido_model.py
│   └── admin_model.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # hash/verificação de senha (werkzeug.security)
│   ├── pedido_service.py       # invariantes do pedido + transação
│   ├── relatorio_service.py    # faixas de desconto / ticket médio
│   └── notificacao_service.py  # notificações simuladas via logger
├── controllers/                # orquestram o caso de uso; devolvem (payload, status)
│   ├── __init__.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py   # GET / e GET /health
│   └── admin_controller.py
├── routes/                     # Blueprints por domínio, paths idênticos; get_json(silent=True) + jsonify
│   ├── __init__.py             # register_routes(app)
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── admin_routes.py
├── validators/
│   ├── __init__.py
│   └── payloads.py             # validação de forma/tipo, sem Flask; levanta ApiError com a mensagem da rota
├── middlewares/
│   ├── __init__.py
│   ├── errors.py               # ApiError(status, payload) + @errorhandler central
│   └── admin_auth.py           # admin_required (ADMIN_TOKEN + X-Admin-Token, hmac.compare_digest)
├── .env.example                # todas as variáveis, sem valores reais
├── requirements.txt            # inalterado (flask, flask-cors)
└── README.md                   # variáveis de ambiente e política de /admin/*
```
Removidos ao final: `controllers.py`, `models.py`, `database.py` (substituídos pelos pacotes).

Steps (CRITICAL → LOW):
1. [CRITICAL] `config/settings.py` lê `SECRET_KEY` do ambiente (ausente → `secrets.token_hex(32)` por boot, nunca logada nem devolvida); literal removido do código e do `/health`; `.env.example` documenta tudo — resolve AP-SEC-01 — padrão RF-01
2. [CRITICAL] Todas as queries com placeholders `?`; a busca dinâmica concatena só trechos SQL fixos e passa os valores em tupla; reset usa `RESET_STATEMENTS` fixos — resolve AP-SEC-02 — padrão RF-02
3. [CRITICAL] `/admin/reset-db` e `/admin/query` continuam existindo, protegidos por `admin_required`: sem `ADMIN_TOKEN` configurado ou header `X-Admin-Token` errado → 403 `{"erro": "Acesso negado"}`; `/admin/query` roda em conexão `file:...?mode=ro` + `PRAGMA query_only=ON`, escrita/erro → 400 `{"erro": "Consulta inválida ou não permitida"}` (detalhe só no log); reset com SQL fixo e `logger.warning` — resolve AP-SEC-05 — padrão RF-15
4. [CRITICAL] Serializer público de usuário sem `senha` (listagem/detalhe) e serializer de login com os mesmos 4 campos de hoje; `/health` devolve só `status`, `database`, `counts`, `versao`, `ambiente` — resolve AP-SEC-04 — padrão RF-13
5. [CRITICAL] `services/auth_service.py` com `generate_password_hash`/`check_password_hash`; cadastro grava hash; login busca por email (`ORDER BY id`) e verifica o hash em Python; `schema.migrar_senhas_texto_puro()` no boot converte senhas em claro para hash; fallback no login aceita texto puro com `hmac.compare_digest` e regrava como hash; seed grava hash das mesmas senhas — resolve AP-SEC-03 — padrão RF-08
6. [CRITICAL] Quebrar os 4 arquivos na estrutura alvo; `app.py` só compõe (`create_app()`), mantém `app = create_app()` em nível de módulo e o bloco `__main__` — resolve AP-ARCH-01 — padrão RF-03
7. [HIGH] `DEBUG` do ambiente com default `false`; `HOST`/`PORT` do ambiente com defaults `0.0.0.0`/`5000`; `app.run(host, port, debug)` lido da config — resolve AP-SEC-06 — padrão RF-01
8. [HIGH] RF-16 nível 1: `POST /usuarios` continua ignorando `tipo` do corpo (sempre `TIPO_USUARIO_PADRAO = "cliente"`), coberto por chamada de teste; nível 2 vai para "Not addressed" — resolve AP-SEC-07 (nível 1) — padrão RF-16
9. [HIGH] Regra de negócio para `services/`: `pedido_service` (validação de itens, total, estoque), `relatorio_service` (faixas de desconto), `notificacao_service` (e-mail/SMS/push/status); `/health` e admin usam models — resolve AP-ARCH-02 — padrão RF-04
10. [HIGH] Conexão por requisição em `flask.g` com `teardown_appcontext` (fecha e descarta o que não foi commitado); `transacao(conn, immediate=False)` faz commit/rollback; pedido usa `BEGIN IMMEDIATE` (checagem e baixa de estoque atômicas) — resolve AP-ARCH-03 — padrão RF-05
11. [HIGH] Models recebem `conn` por parâmetro (não importam `db`); `DB_PATH` vem da config (default `loja.db` na pasta do projeto); `create_app(settings=None)` permite injetar outra config/banco — resolve AP-ARCH-04 — padrão RF-05/RF-03
12. [MEDIUM] Invariantes do pedido: `usuario_id` e `produto_id` inteiros; `quantidade` inteiro > 0; passada única nos itens, na ordem do pedido, checando existência do produto e estoque contra a quantidade **acumulada** do produto (mesmas mensagens "Produto X não encontrado"/"Estoque insuficiente para <nome>"); usuário inexistente → 400 `{"erro": "Usuário não encontrado", "sucesso": false}`; total somado na mesma ordem de hoje (mesmo float); pedido + itens (uma linha por item, como hoje) + baixa numa transação — resolve AP-QUAL-02 (invariantes) — padrão RF-14 + RF-04
13. [MEDIUM] `validators/payloads.py`: um validator de produto usado no POST e no PUT, validators de usuário, login, pedido, status e filtros de busca; as checagens originais rodam primeiro e na mesma ordem (mesmas mensagens), e as checagens de tipo entram no ponto onde o original quebrava com 500 — resolve AP-QUAL-02 (validação) — padrão RF-14
14. [MEDIUM] Integridade: aplicar só o que rejeita entrada (usuário inexistente no pedido → 400; status de pedido inexistente → 404); FKs, UNIQUE(email) e exclusão lógica vão para "Not addressed" — resolve AP-QUAL-02 (integridade), parcialmente — padrão RF-14
15. [MEDIUM] `middlewares/errors.py`: `ApiError(status, payload)` carrega o corpo exato da rota; `@errorhandler(Exception)` devolve `HTTPException` intacta (404/405 HTML do Flask continuam iguais) e, para o resto, loga e responde 500 `{"erro": "Erro interno do servidor"}` (no `/health`: `{"status": "erro", "detalhes": "Banco de dados indisponível"}`); os 17 `except Exception` saem — resolve AP-QUAL-01 — padrão RF-07
16. [MEDIUM] Listagens de pedidos em uma query (`LEFT JOIN itens_pedido` + `LEFT JOIN produtos`, `ORDER BY p.id, i.id`, agrupada em memória; "Desconhecido" só quando o produto não existe); pedido lê cada produto uma vez; relatório em uma query agregada (`COUNT`, `SUM`, `SUM(CASE ...)`) — resolve AP-PERF-01 — padrão RF-06
17. [MEDIUM] Um serializer por entidade, uma função de montagem de pedidos, um validator de produto — resolve AP-QUAL-03 — padrão RF-04/RF-13
18. [LOW] `logging` configurado no `app.py`; `print` → `logger` com nível; sem email/senha nos logs (login loga o id do usuário) — resolve AP-QUAL-04 — padrão RF-12
19. [LOW] `config/constants.py`: `VERSAO_API`, `CATEGORIAS_VALIDAS` (lista, mesma ordem — a mensagem usa `str(lista)`), `STATUS_PEDIDO_VALIDOS`, `FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))`, `NOME_PRODUTO_MIN/MAX`, `TIPO_USUARIO_PADRAO` — resolve AP-QUAL-05 — padrão RF-11
20. [LOW] Renomear internamente `id` → `produto_id`/`usuario_id`, `cursor2/3`/`prod` → nomes descritivos; parâmetros de rota renomeados sem mudar o path — resolve AP-QUAL-06
21. [LOW] Remover `import os`/`import sqlite3` sem uso, `SELECT 1` redundante e `return True` não lidos — resolve AP-QUAL-07

Not addressed:
- AP-SEC-07 nível 2 (login com token assinado + `login_required`/`role_required` + checagem de dono do recurso): muda o contrato de todas as rotas e a resposta do `/login`. Recomendação: token itsdangerous/JWT com `SECRET_KEY` do ambiente e expiração; aplicar só se o usuário pedir.
- Integridade referencial (FKs, `UNIQUE(email)`, exclusão lógica via `ativo` no DELETE de produto): muda o contrato (DELETE e listagens) ou exige tratar dados existentes. Recomendação: migração com exclusão lógica e índices únicos após limpar duplicados.
- Validação de formato de email e rejeição de email duplicado: regra de negócio nova. Recomendação: validar formato e unicidade no cadastro.
- Máquina de estados do pedido (ex.: `entregue` → `pendente`) e devolução de estoque ao cancelar (o log "Devolver estoque" é mantido, mas nada é devolvido, como hoje): regra/efeito colateral novo. Recomendação: transições válidas em `pedido_service` e devolução transacional.
- Relatório soma pedidos cancelados no faturamento: decisão de negócio; mudar alteraria os números.
- `preco_min=0`/`preco_max=0` ignorados na busca (checagem por valor "truthy"): mantido por contrato. Recomendação: `is not None`.
- CORS liberado para qualquer origem: mantido (contrato com clientes de navegador). Recomendação: origens via ambiente.

Contract to preserve:
- Rotas (19): `GET /`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<int:id>`, `POST /produtos`, `PUT /produtos/<int:id>`, `DELETE /produtos/<int:id>`, `GET /usuarios`, `GET /usuarios/<int:id>`, `POST /usuarios`, `POST /login`, `POST /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<int:usuario_id>`, `PUT /pedidos/<int:pedido_id>/status`, `GET /relatorios/vendas`, `GET /health`, `POST /admin/reset-db`, `POST /admin/query`.
- Respostas: mesmos campos e mensagens de sucesso e erro, inclusive as diferenças entre rotas — ex.: 404 de `GET /produtos/<id>` tem `"sucesso": false`, mas o de `PUT`/`DELETE /produtos/<id>` e `GET /usuarios/<id>` não; erros de negócio do pedido têm `"sucesso": false`, os de validação não; `"Categoria inválida. Válidas: ['informatica', ...]"` no mesmo formato; PUT sem `categoria`/`descricao` continua gravando `"geral"`/`""`; ordem das checagens (no PUT, 404 vem antes da validação do corpo).
- `GET /pedidos/usuario/<id>` de usuário sem pedidos continua 200 com lista vazia; DELETE de produto continua físico; rotas desconhecidas e métodos errados continuam com o 404/405 padrão do Flask.
- Boot: `python app.py` (porta padrão 5000, host 0.0.0.0; `PORT`/`HOST` opcionais). `flask --app app run` continua funcionando.

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] `GET /usuarios` e `GET /usuarios/<id>` deixam de devolver `senha` — senha exposta — prova: `GET /usuarios/1`
- [segurança] `GET /health` deixa de devolver `secret_key`, `db_path` e `debug` (mantém `versao` e `ambiente`, campos de contrato não sensíveis; `ambiente` = `APP_ENV`, default `"producao"`) — configuração interna exposta — prova: `GET /health`
- [segurança] SQL injection fechada: `POST /login {"email": "admin@loja.com' --", "senha": "x"}` → 401 (hoje 200 como admin); `GET /produtos/busca?q=%') UNION SELECT ... FROM usuarios --` → 200 com `dados: []` (hoje devolve senhas); `POST /pedidos` com `"produto_id": "1 OR 1=1"` → 400 (hoje 201 e baixa o estoque de todos); textos com aspas (`"nome": "Caneca D'água"`, `q='`) passam a funcionar em vez de 500 — prova: essas chamadas
- [segurança] `/admin/reset-db` e `/admin/query` → 403 `{"erro": "Acesso negado"}` sem `ADMIN_TOKEN` configurado ou com token errado; com token correto, o comportamento original (reset 200; `SELECT` 200) — endpoint perigoso — prova: chamadas sem token, com token errado e com token
- [segurança] `/admin/query` (com token): escrita → 400 `{"erro": "Consulta inválida ou não permitida"}` (hoje executa e faz commit); SQL inválido → 400 com a mesma mensagem fixa (hoje 500 com a mensagem do SQLite) — prova: `{"sql": "DELETE FROM produtos"}` e `{"sql": "SELEC x"}` com token
- [segurança] Erros inesperados respondem 500 com mensagem fixa (`"Erro interno do servidor"`; no `/health`, `"detalhes": "Banco de dados indisponível"`) em vez de `str(e)` — vazamento de detalhes internos — prova: os casos que hoje vazam mensagem viram 4xx (abaixo); a reverificação do catálogo mostra que não há mais `str(e)` em resposta
- [segurança] Senhas gravadas com hash (werkzeug/scrypt); as em texto puro são migradas no boot; as mesmas credenciais continuam válidas — prova: `POST /login` com `admin@loja.com`/`admin123` e `joao@email.com`/`123456`; `/admin/query` (com token) mostrando `senha` com prefixo `scrypt:`; login com usuário gravado pelo app original
- [segurança] Debug desligado por padrão e `SECRET_KEY` fora do código — prova: log de boot sem "Debugger is active"; `grep` sem o literal da chave
- [entrada inválida] JSON malformado, `Content-Type` não JSON ou corpo que não é objeto (hoje 500 com mensagem do Werkzeug): `POST /produtos`, `PUT /produtos/<id>`, `POST /usuarios`, `POST /pedidos` → 400 `{"erro": "Dados inválidos"}`; `POST /login` → 400 `{"erro": "Email e senha são obrigatórios"}`; `PUT /pedidos/<id>/status` → 400 `{"erro": "Status inválido"}`; `/admin/query` com token → 400 `{"erro": "Query não informada"}` — prova: `-d '{'` em cada rota
- [entrada inválida] Produto (POST e PUT) com tipo errado (hoje 500 ou gravado): `preco` não numérico/booleano/NaN → 400 `{"erro": "Preço deve ser um número"}`; `estoque` não inteiro → `{"erro": "Estoque deve ser um número inteiro"}`; `nome` não texto → `{"erro": "Nome deve ser um texto"}`; `descricao` não texto → `{"erro": "Descrição deve ser um texto"}` — prova: `POST /produtos` com `"preco": "abc"` e com `"estoque": 1.5`
- [entrada inválida] `PUT /produtos/<id>` passa a aplicar as regras do POST: nome com 2–200 caracteres (`"Nome muito curto"`/`"Nome muito longo"`) e categoria válida (`"Categoria inválida. Válidas: [...]"`) — hoje 200 — prova: PUT com `"nome": "X"` e com `"categoria": "xyz"`
- [entrada inválida] `POST /usuarios` com nome/email/senha não texto → 400 `{"erro": "Nome, email e senha devem ser texto"}`; `POST /login` com email/senha não texto → 400 `{"erro": "Email e senha devem ser texto"}` — hoje 500 — prova: `"senha": 123`
- [entrada inválida] `POST /pedidos`: `usuario_id` não inteiro → 400 `{"erro": "Usuario ID inválido"}`; `itens` que não é lista, item sem `produto_id`/`quantidade` ou `produto_id` não inteiro → 400 `{"erro": "Itens do pedido inválidos"}`; `quantidade` não inteira ou ≤ 0 → 400 `{"erro": "Quantidade deve ser um número inteiro maior que zero"}` — hoje 201 com total negativo e estoque aumentando, ou 500 — prova: `"quantidade": -5`, `"quantidade": 0`, `"itens": "abc"`
- [entrada inválida] `POST /pedidos` com o mesmo produto repetido somando mais que o estoque → 400 `{"erro": "Estoque insuficiente para <nome>", "sucesso": false}` — hoje 201 e estoque negativo — prova: produto 6 (estoque 8) em 2 itens de 5
- [entrada inválida] `POST /pedidos` com `usuario_id` inexistente → 400 `{"erro": "Usuário não encontrado", "sucesso": false}` — hoje 201 com pedido órfão — prova: `"usuario_id": 9999`
- [entrada inválida] `PUT /pedidos/<id>/status` em pedido inexistente → 404 `{"erro": "Pedido não encontrado"}` — hoje 200 "Status atualizado" — prova: `PUT /pedidos/9999/status`
- [entrada inválida] `GET /produtos/busca` com `preco_min`/`preco_max` não numérico ou não finito → 400 `{"erro": "Filtro de preço inválido"}` — hoje 500 — prova: `?preco_min=abc`

Data preservation:
- Seeds: os mesmos 10 produtos e 3 usuários, mesma ordem/ids, mesma condição de disparo (tabela `produtos` vazia); senhas documentadas mantidas (`admin123`, `123456`, `senha123`), gravadas como hash.
- Credenciais existentes: senhas em texto puro de um `loja.db` existente são convertidas para hash no boot (mesma senha); o login ainda aceita e regrava qualquer texto puro remanescente. Nenhuma recriação de banco.
- Registros persistidos: DDL idêntico (sem constraints novas), então um `loja.db` existente funciona sem migração de schema; nenhuma correção apaga ou altera registros além da troca do formato da senha; DELETE de produto e reset continuam fazendo só o que já faziam.
- Segredos: `SECRET_KEY`, `ADMIN_TOKEN` e senhas nunca vão para log ou resposta; a chave aleatória gerada sem `SECRET_KEY` não é impressa.

Validation:
- Antes de mudar código: copiar os fontes para `reports/.tmp/original-src/`; `loja.db` não existe → garantir ausência antes de cada execução; baseline do app original numa porta livre (5050–5099) com `.venv/bin/python -m flask --app app run --port $PORT` (o original fixa 5000) → `reports/baseline-responses.txt`.
- Depois: boot com o comando original `python app.py` (`.venv/bin/python app.py`, `PORT=<livre>`, `ADMIN_TOKEN` de teste) → mesmas chamadas → `reports/after-responses.txt`; diff mascarado (timestamps); cada diferença classificada contra a lista acima; o que não estiver na lista é regressão e é corrigido.
- Cobertura: todas as 19 rotas no caso de sucesso; ID inexistente em toda rota com parâmetro; corpo válido, sem campo obrigatório e `-d '{'` em todo POST/PUT; uma chamada por mudança intencional; admin sem token, com token errado e com token; login com credenciais do seed; anônimo com `"tipo": "admin"` → criado como `cliente`; rotas destrutivas por último.
- Migração de senha: rodar o app original a partir de `reports/.tmp/original-src/` para gerar um banco com senhas em texto puro (seed + 1 usuário criado via API), subir o app refatorado com `DB_PATH` apontando para ele, fazer login com o seed e com o usuário legado e conferir que a coluna passou a ter hash.
- Reverificação dos sinais do catálogo (SQL concatenado, `print(`, `except Exception`, `str(e)`, `"senha"` em serializer, literal da chave, `debug=True`, `check_same_thread`, `global`) com saída real no `validation-report.md`.
- Limpeza: servidores encerrados e porta livre; `loja.db` e `__pycache__/` criados nos testes removidos (não existiam antes); `reports/.tmp/` apagado.
