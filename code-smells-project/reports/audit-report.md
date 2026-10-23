# Audit Report — code-smells-project

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (.venv: 3.11.17)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib), werkzeug 3.1.9 (via Flask)
Domain:        API REST de e-commerce (loja): produtos, usuários/login, pedidos com itens e baixa de estoque, relatório de vendas
Architecture:  Monólito em camadas parciais — 4 arquivos na raiz; controllers.py e models.py existem, mas rotas admin com SQL ficam em app.py, controllers acessam o banco, models misturam SQL e regra de negócio, não há config nem views
Source files:  4 files analyzed (app.py, controllers.py, database.py, models.py — 780 linhas)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py (boot: python app.py, porta 5000 fixa em app.py:88; alternativa sem editar código: flask --app app run --port <porta>)
Setup:         none — loja.db é criado e populado no primeiro get_db() (database.py:7-86); a seed só roda se a tabela produtos estiver vazia
================================
```

Inventário de rotas (19):

```
GET    /
GET    /produtos
GET    /produtos/busca
GET    /produtos/<int:id>
POST   /produtos
PUT    /produtos/<int:id>
DELETE /produtos/<int:id>
GET    /usuarios
GET    /usuarios/<int:id>
POST   /usuarios
POST   /login
POST   /pedidos
GET    /pedidos
GET    /pedidos/usuario/<int:usuario_id>
PUT    /pedidos/<int:pedido_id>/status
GET    /relatorios/vendas
GET    /health
POST   /admin/reset-db
POST   /admin/query
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] AP-SEC-05 — Endpoints administrativos perigosos sem autenticação
File: app.py:59-78 (POST /admin/query), app.py:47-57 (POST /admin/reset-db)
Description: /admin/query executa qualquer SQL recebido no corpo (`cursor.execute(query)`, app.py:69) e faz commit de escritas (app.py:75), sem nenhuma autenticação; erros do banco voltam ao cliente (`str(e)`, app.py:78). /admin/reset-db apaga as 4 tabelas (app.py:51-54) para qualquer chamador anônimo.
Impact: backdoor completo ao banco: qualquer pessoa lê as senhas (`SELECT * FROM usuarios`), altera preços/pedidos, faz DROP TABLE ou apaga todos os dados com um POST.
Recommendation: RF-15 — rota mantida, mas desligada por padrão: exige ADMIN_TOKEN do ambiente no header X-Admin-Token (comparação em tempo constante, 403 sem ele); /admin/query em conexão somente-leitura, recusando escrita com 400 e sem devolver a mensagem do banco; reset com SQL fixo e log do evento.

### [CRITICAL] AP-SEC-02 — SQL Injection (queries montadas por concatenação)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299 (19 chamadas a execute)
Description: todas as queries do módulo de dados concatenam valores na string SQL. Entradas do cliente chegam sem escape: login (`email`/`senha`, models.py:110), criação/edição de produto (`nome`, `descricao`, `categoria`, models.py:48-49, 58-60), criação de usuário (models.py:127-128), busca (`q` e `categoria` da query string, models.py:291-293), status de pedido (models.py:280) e itens do pedido (`produto_id`/`quantidade` vindos do JSON, models.py:140, 158-165).
Impact: bypass de login (`email = "' OR '1'='1' --"` autentica como o primeiro usuário), leitura/alteração arbitrária do banco via qualquer campo de texto, e erro 500 com qualquer apóstrofo legítimo (ex.: busca por "Monitor 27''").
Recommendation: RF-02 — queries parametrizadas com placeholders `?` em todas as chamadas (inclusive LIKE e filtros dinâmicos).

### [CRITICAL] AP-SEC-04 — Senha devolvida pela API
File: models.py:72-87 (`get_todos_usuarios`, campo "senha" na linha 83), models.py:89-103 (`get_usuario_por_id`, linha 99)
Description: GET /usuarios e GET /usuarios/<id> serializam a coluna `senha` (em texto puro) na resposta.
Impact: qualquer cliente anônimo obtém a senha de todos os usuários, inclusive do admin.
Recommendation: RF-13 — serializer único de usuário sem o campo senha/hash.

### [CRITICAL] AP-SEC-04 — Health check expõe SECRET_KEY e configuração interna
File: controllers.py:276-290 (linha 289: "secret_key"; 287-288: db_path, debug)
Description: GET /health devolve a SECRET_KEY da aplicação, o caminho do banco e o flag de debug.
Impact: vazamento do segredo da aplicação para qualquer chamador (permite forjar sessões/assinaturas se forem usadas) e informação para ataque.
Recommendation: RF-13 + RF-01 — remover "secret_key" da resposta; demais campos vêm da config (sem segredo).

### [CRITICAL] AP-SEC-03 — Senhas armazenadas e comparadas em texto puro
File: database.py:27-35 (coluna senha), database.py:75-83 (seed), models.py:109-111 (comparação no SQL), models.py:122-131 (gravação)
Description: senhas são gravadas como texto puro e o login compara `senha = '<valor>'` direto no SQL. Não há hashing.
Impact: qualquer vazamento do banco (ou do /admin/query, ou do GET /usuarios) expõe as senhas reais dos usuários, reutilizáveis em outros serviços.
Recommendation: RF-08 — `werkzeug.security` (generate/check_password_hash, já disponível com o Flask); seed grava hash com as mesmas senhas documentadas; senhas em texto puro existentes migradas no boot e aceitas uma vez no login ("rehash on login").

### [CRITICAL] AP-SEC-01 — SECRET_KEY hardcoded
File: app.py:7, controllers.py:289
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` literal no código, repetida na resposta do /health.
Impact: segredo versionado; impossível rotacionar por ambiente; já está exposto publicamente pelo /health.
Recommendation: RF-01 — config via variável de ambiente (`SECRET_KEY`), com `.env.example`; sem segredo literal no código. (As credenciais de exemplo do seed — database.py:76-78 — são dados de demonstração documentados no README e ficam preservadas, só passam a ser gravadas com hash.)

### [HIGH] AP-SEC-06 — Debug do Flask ligado por padrão em host público
File: app.py:8, app.py:88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)`.
Impact: com host 0.0.0.0, o debugger do Werkzeug fica acessível na rede e permite execução de código remoto quando uma exceção não tratada ocorre; reloader e stack traces habilitados em "producao".
Recommendation: RF-01 — DEBUG, HOST e PORT vindos do ambiente, DEBUG desligado por padrão (porta padrão 5000 preservada).

### [HIGH] AP-ARCH-02 — Regra de negócio dentro da camada de dados
File: models.py:133-169 (criar_pedido), models.py:235-273 (relatorio_vendas)
Description: o "model" `criar_pedido` valida existência e estoque, calcula o total, cria o pedido, os itens e baixa o estoque — o caso de uso inteiro dentro do acesso a dados, sem transação explícita. `relatorio_vendas` aplica faixas de desconto (regra comercial) junto das queries. Em contrapartida, a reação a mudanças de status (notificações, controllers.py:247-250) e o envio de "email/SMS/push" (controllers.py:208-210) ficam no controller.
Impact: regra de pedido e de desconto não testável sem banco; mistura de responsabilidades torna qualquer mudança arriscada.
Recommendation: RF-04 — services/pedido_service.py (criação com transação), services/relatorio_service.py (desconto), services/notificacao_service.py; models só com SQL.

### [HIGH] AP-ARCH-02 — Acesso a dados fora dos models e app.py com múltiplas responsabilidades
File: app.py:6-88 (config + registro de rotas + handlers com SQL + boot), app.py:47-78 (SQL inline), controllers.py:264-274 (health_check com SQL), controllers.py:3 (import de get_db)
Description: app.py concentra configuração hardcoded, tabela de rotas, dois handlers com SQL direto e o boot; o controller de health executa queries próprias. Não existe camada de views/rotas nem de config; os handlers HTTP misturam leitura do request, validação e resposta.
Impact: não há fronteira de camadas: SQL aparece em 3 dos 4 arquivos, o que impede trocar a persistência ou testar controllers isoladamente.
Recommendation: RF-03 — separar em config/, db/, models/, services/, controllers/, routes/, middlewares/; app.py vira composition root (create_app).

### [HIGH] AP-ARCH-03 — Conexão global compartilhada entre requisições/threads
File: database.py:4-11
Description: `db_connection` global criado com `check_same_thread=False` e reutilizado por todas as requisições do servidor multi-thread do Flask.
Impact: condições de corrida; o commit de uma requisição confirma alterações parciais de outra; um erro no meio de `criar_pedido` deixa escritas pendentes que a próxima requisição confirma.
Recommendation: RF-05 — conexão por requisição em `flask.g` com fechamento no teardown; transações explícitas.

### [HIGH] AP-ARCH-04 — Acoplamento direto sem injeção / caminho do banco fixo
File: database.py:5, database.py:7-86, models.py:1, controllers.py:2-3, app.py:3-4
Description: o caminho do banco é literal e relativo ao diretório corrente (`db_path = "loja.db"`); schema e seed rodam como efeito colateral da primeira chamada a `get_db()`; models e controllers importam a conexão concreta; a app é montada no import do módulo, sem factory.
Impact: impossível apontar para outro banco (teste, outro ambiente) sem editar código; rodar a partir de outro diretório cria um banco novo vazio; inicialização implícita e difícil de testar.
Recommendation: RF-05/RF-03 — create_app() lendo DB_PATH da config, inicialização explícita do banco no composition root, models recebendo a conexão via get_db() da camada db.

### [MEDIUM] AP-QUAL-02 — Invariantes de negócio do pedido não garantidos
File: models.py:139-146 (checagem item a item), models.py:163-166 (baixa de estoque), controllers.py:188-206
Description: (1) `quantidade` não é validada: zero ou negativa é aceita — quantidade -5 aumenta o estoque e reduz o total; (2) itens repetidos do mesmo produto furam a checagem de estoque (cada item é comparado com o estoque inteiro, ex.: 2 itens de 8 unidades com estoque 10 deixam o estoque em -6); (3) `usuario_id` inexistente gera pedido órfão; (4) `quantidade`/`produto_id` como string ou ausentes viram erro 500 (ou vão concatenados no SQL); (5) sem transação explícita.
Impact: estoque negativo, totais negativos, pedidos para usuários inexistentes e erros 500 para entrada inválida.
Recommendation: RF-14 + RF-04 — validar tipos (inteiros positivos), somar quantidades por produto antes da checagem, verificar usuário, tudo dentro de uma transação no serviço.

### [MEDIUM] AP-QUAL-02 — Validação de entrada ausente/fraca nas demais rotas
File: controllers.py:24-62 vs 64-96 (criar × atualizar produto), controllers.py:118-121 (busca), controllers.py:146-165 (criar usuário), controllers.py:167-174 (login), controllers.py:237-245 (status), models.py:275-283
Description: corpo ausente ou JSON malformado vira 500 com mensagem interna (login e status: `'NoneType' object has no attribute 'get'`; demais: `400 Bad Request: ...` devolvido com status 500); `preco`/`estoque`/`nome` com tipo errado viram 500 (TypeError); PUT /produtos não aplica as regras do POST (tamanho do nome, categoria válida); `preco_min`/`preco_max` não numéricos viram 500; PUT /pedidos/<id>/status responde sucesso para pedido inexistente. Também: `preco_min=0`/`preco_max=0` são ignorados pelo filtro (models.py:294-297) e o schema não tem UNIQUE(email) nem chaves estrangeiras (database.py:14-53).
Impact: dados inválidos aceitos, respostas 500 com detalhes internos, sucesso falso em atualização de recurso inexistente.
Recommendation: RF-14 — validators/ com checagem de tipo/obrigatoriedade, mesmas regras para criar e atualizar, 4xx no formato original da rota; 404 para pedido inexistente.

### [MEDIUM] AP-QUAL-01 — Tratamento de erro genérico devolvendo str(e)
File: controllers.py (16 blocos `except Exception`: 10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292), app.py:77-78
Description: cada handler captura `Exception` e devolve a mensagem crua da exceção com 500 (20 ocorrências de `str(e)`), inclusive erros de SQL e de parsing; não existe handler central.
Impact: vaza detalhes internos (SQL, tipos, caminhos), mascara erros de entrada como 500 e duplica o mesmo bloco 17 vezes.
Recommendation: RF-07 — exceção de aplicação (ApiError) + error handler central que preserva o formato de erro de cada rota e responde mensagem fixa para erros inesperados, logando o detalhe.

### [MEDIUM] AP-PERF-01 — Queries N+1 na listagem de pedidos
File: models.py:171-201 (get_pedidos_usuario), models.py:203-233 (get_todos_pedidos), models.py:139-161 (criar_pedido relê cada produto 2x), models.py:239-254 (5 queries no relatório)
Description: para cada pedido, uma query de itens; para cada item, uma query do nome do produto (1 + P + I queries). criar_pedido faz SELECT do mesmo produto duas vezes por item; o relatório faz 5 queries de agregação separadas.
Impact: número de queries cresce linearmente com pedidos e itens; GET /pedidos degrada com o volume.
Recommendation: RF-06 — JOIN itens_pedido × produtos com agrupamento em memória; agregação condicional numa única query no relatório; leitura única do produto no pedido.

### [MEDIUM] AP-QUAL-03 — Duplicação de código
File: models.py:12-21, 31-40, 304-313 (serialização de produto 3x); models.py:79-86, 95-102 (usuário 2x); models.py:171-201 ≡ 203-233 (montagem de pedidos idêntica); controllers.py:28-46 ≡ 72-90 (validação de produto)
Description: os mesmos mapeamentos e validações copiados em vários pontos.
Impact: correções precisam ser feitas em N lugares (ex.: remover a senha exigiria editar dois serializers); divergência já existe entre criar e atualizar produto.
Recommendation: RF-04/RF-13 — um serializer por entidade, uma montagem de pedidos, um validador de produto reutilizado.

### [LOW] AP-QUAL-04 — print como logging
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250 (19 ocorrências)
Description: eventos, erros e "notificações" (email/SMS/push simulados) registrados com print; o login registra o e-mail do usuário.
Impact: sem nível, sem timestamp, sem destino configurável; dados pessoais no stdout.
Recommendation: RF-12 — logging com logger por módulo; notificações em serviço próprio.

### [LOW] AP-QUAL-05 — Magic numbers e enumerações soltas
File: models.py:256-262 (faixas 10000/5000/1000 e taxas 0.1/0.05/0.02), controllers.py:52 (categorias), controllers.py:242, 247, 249 e models.py:150, 247-253 (status), app.py:88 (porta 5000), app.py:36 e controllers.py:285 ("1.0.0" duplicado)
Description: regras comerciais e listas de domínio literais no meio da lógica.
Impact: mudar uma faixa de desconto ou um status exige caçar literais; risco de divergência.
Recommendation: RF-11 — constantes nomeadas em config/constants.py.

### [LOW] AP-QUAL-06 — Nomes ruins
File: controllers.py:14, 56, 64, 98, 160 e models.py:24, 54, 65, 89 (`id` sombreando builtin); models.py:187-192, 219-224 (`cursor2`, `cursor3`); `e` em todos os except
Description: nomes genéricos ou que sombreiam builtins.
Impact: leitura mais difícil; sombra de `id` pode causar bugs sutis.
Recommendation: renomear internamente (`produto_id`, `itens_cursor`...), sem mudar paths nem campos do contrato.

### [LOW] AP-QUAL-07 — Imports não usados
File: database.py:2 (`import os`), models.py:2 (`import sqlite3`)
Description: módulos importados e nunca usados.
Impact: ruído e falsa dependência.
Recommendation: remover (limpeza).

================================
Total: 20 findings
================================
```

APIs deprecated: nenhuma encontrada (sem `datetime.utcnow`, `Query.get`, `before_first_request` ou similares; Flask 3.1.1 / Werkzeug 3.1.9 atuais).
