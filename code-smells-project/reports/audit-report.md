# Audit Report — code-smells-project

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.11 (.venv/bin/python 3.11.17)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1 (transitivas: werkzeug 3.1.9, jinja2 3.1.6, itsdangerous 2.2.0, click, blinker); sqlite3 (stdlib)
Domain:        API REST de e-commerce ("Loja") — catálogo de produtos, usuários/login, pedidos com baixa de estoque, relatório de vendas e endpoints administrativos
Architecture:  Monolítica sem camadas — 4 arquivos na raiz; app.py mistura config, rotas e SQL; controllers.py mistura HTTP, validação, notificações e SQL; models.py concentra SQL concatenado + regras de negócio; database.py cria conexão global, schema e seed
Source files:  4 files analyzed (app.py, controllers.py, database.py, models.py — 780 linhas)
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, arquivo loja.db)
Entry point:   app.py (boot: python app.py, porta 5000 fixa no código; alternativa sem editar código: flask --app app run --port <porta>)
Setup:         nenhum passo manual — loja.db é criado e populado (10 produtos, 3 usuários) automaticamente no primeiro get_db()
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

Fora da contagem: `requirements.txt`, `README.md`, `.env.example` (não lido por nenhum código atual). `loja.db` não existe antes do primeiro boot.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Execução arbitrária de SQL e reset do banco sem autenticação (AP-SEC-05)
File: app.py:47-78
Description: POST /admin/query executa qualquer SQL recebido em {"sql": ...} (cursor.execute(query), app.py:69) e faz commit quando não é SELECT (app.py:74-76). POST /admin/reset-db apaga as 4 tabelas (app.py:51-55). Nenhuma das duas rotas exige credencial, e a mensagem de erro do banco volta na resposta (app.py:77-78).
Impact: qualquer cliente anônimo lê a tabela usuarios com as senhas, altera preços/estoque, promove contas a admin (UPDATE usuarios SET tipo='admin') ou apaga todos os dados com uma única requisição.
Recommendation: RF-15 — rotas mantidas, mas desligadas por padrão: só funcionam com ADMIN_TOKEN do ambiente enviado em X-Admin-Token (comparação em tempo constante), senão 403; /admin/query em conexão somente-leitura (escrita → 400), sem devolver a mensagem do banco; reset com SQL fixo e log do evento.

### [CRITICAL] SQL Injection por concatenação de strings (AP-SEC-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: 19 chamadas execute montam SQL concatenando valores ("... WHERE id = " + str(id), "... email = '" + email + "' AND senha = '" + senha + "'"). Entradas do cliente chegam cruas ao SQL: corpo de POST/PUT /produtos (nome, descricao; categoria no PUT), POST /usuarios (nome, email, senha), POST /login (email, senha), POST /pedidos (usuario_id, produto_id, quantidade sem checagem de tipo) e a query string de GET /produtos/busca (q, categoria). Exemplos: POST /login com {"email": "admin@loja.com' --", "senha": "x"} autentica como admin sem senha; GET /produtos/busca?q=%') UNION SELECT id,nome,email,senha,0,tipo,1,criado_em FROM usuarios -- devolve emails e senhas; POST /pedidos com "produto_id": "1 OR 1=1" faz o UPDATE de estoque (models.py:163-166) baixar o estoque de todos os produtos.
Impact: bypass de autenticação, leitura de toda a base (inclusive senhas) e alteração em massa de dados.
Recommendation: RF-02 — placeholders ? em todas as queries (na busca dinâmica, só trechos fixos são concatenados e os valores vão em tupla); tipos validados antes (RF-14).

### [CRITICAL] Exposição de dados sensíveis nas respostas (AP-SEC-04)
File: models.py:79-86, 95-102; controllers.py:276-290
Description: GET /usuarios e GET /usuarios/<id> serializam o campo senha (models.py:83, 99) — com o seed, devolvem "admin123" do admin. GET /health, público, devolve "secret_key" (a própria SECRET_KEY), "db_path" e "debug" (controllers.py:287-289).
Impact: qualquer cliente obtém as senhas de todos os usuários e a chave da aplicação (permite forjar cookies/assinaturas do Flask), além de detalhes internos de configuração.
Recommendation: RF-13 — um único serializer de usuário, sem senha; /health devolve só status, database, contagens e os campos de contrato não sensíveis (versao, ambiente); secret_key, db_path e debug saem da resposta.

### [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP-SEC-03)
File: database.py:31, 75-83; models.py:105-131
Description: a coluna senha TEXT guarda a senha crua; o seed grava "admin123", "123456" e "senha123" em claro (database.py:76-78); POST /usuarios grava a senha recebida sem hash (models.py:126-129); o login compara a senha dentro do SQL (AND senha = '...', models.py:110).
Impact: qualquer leitura do banco (backup, /admin/query, SQL injection, GET /usuarios) expõe as senhas reais, reutilizáveis em outros serviços.
Recommendation: RF-08 — werkzeug.security.generate_password_hash/check_password_hash; login busca por email e verifica o hash em Python; migração no boot dos registros em texto puro para hash (as mesmas senhas continuam válidas); o seed passa a gravar o hash das mesmas senhas documentadas.

### [CRITICAL] Segredo hardcoded no código-fonte (AP-SEC-01)
File: app.py:7; controllers.py:289
Description: SECRET_KEY = "minha-chave-super-secreta-123" fixo no código e repetido como literal na resposta do /health.
Impact: segredo versionado, idêntico em todos os ambientes, impossível de rotacionar sem deploy — e já público via /health.
Recommendation: RF-01 — config/settings.py lê SECRET_KEY do ambiente; se ausente, gera uma chave aleatória por boot (secrets.token_hex), nunca um literal; documentada no .env.example.

### [CRITICAL] God Module / ausência de camadas (AP-ARCH-01)
File: app.py:1-88; models.py:1-314; controllers.py:1-292; database.py:1-86
Description: app.py concentra configuração (7-9), registro de todas as rotas (11-45), handlers administrativos com SQL direto (47-78) e boot (80-88). models.py reúne o acesso a dados das 4 entidades, a serialização e regras de negócio (total do pedido, baixa de estoque, faixas de desconto). controllers.py mistura HTTP, validação, notificações e SQL (health_check). database.py junta conexão global, DDL e seed.
Impact: nenhuma parte é testável isoladamente; mudar um domínio arrisca os outros; não há lugar para autenticação, validação ou tratamento de erro centralizados.
Recommendation: RF-03 — separar em config/, db/, models/ (uma entidade por arquivo), services/, controllers/, routes/ (Blueprints por domínio), validators/ e middlewares/; app.py vira composition root com create_app().

### [HIGH] Debug ligado no código e servidor exposto em 0.0.0.0 (AP-SEC-06)
File: app.py:8, 88; controllers.py:288
Description: app.config["DEBUG"] = True e app.run(host="0.0.0.0", port=5000, debug=True): o debugger interativo e o reloader do Werkzeug ficam ativos e acessíveis pela rede; modo, host e porta fixos no código.
Impact: qualquer exceção que escape dos handlers mostra stack trace e abre o console do Werkzeug (execução de código Python no servidor, protegida apenas por PIN).
Recommendation: RF-01 — DEBUG lido do ambiente com default false; HOST e PORT do ambiente com os defaults originais (0.0.0.0 e 5000).

### [HIGH] API sem autenticação de base (AP-SEC-07)
File: app.py:11-30; controllers.py:167-186; models.py:105-131
Description: nenhuma rota verifica credencial (não há before_request, decorator, header Authorization nem sessão). POST /login só devolve os dados do usuário — não emite token nem sessão que outra rota valide. Rotas de escrita/exclusão abertas: POST, PUT e DELETE /produtos, POST /pedidos (com qualquer usuario_id) e PUT /pedidos/<id>/status; listagens de terceiros abertas: GET /usuarios, GET /pedidos e GET /pedidos/usuario/<id>. O papel tipo='admin' existe no banco, mas nunca é consultado. Não há escalada de privilégio por campo do corpo: POST /usuarios ignora tipo (models.py:122 usa o default "cliente") — por isso HIGH, não CRITICAL.
Impact: qualquer cliente cria, altera e apaga produtos, muda o status de qualquer pedido e lê dados de todos os usuários e pedidos.
Recommendation: RF-16 — nível 1: manter tipo fora do alcance do cliente anônimo (já é assim; provar com teste); nível 2 (login com token assinado + login_required/role_required nas rotas de escrita) proposto em "Not addressed", porque muda o contrato de todas as rotas.

### [HIGH] Regra de negócio na camada errada (AP-ARCH-02)
File: models.py:133-169, 235-273; controllers.py:205-210, 247-250, 264-274; app.py:47-78
Description: o módulo de dados calcula o total do pedido, valida e baixa estoque (models.py:133-169) e aplica as faixas de desconto do relatório (models.py:256-262); o controller dispara as notificações de e-mail/SMS/push e de status (controllers.py:208-210, 247-250) e executa SQL direto no health check (controllers.py:266-274); as rotas admin executam SQL dentro do handler (app.py:49-55, 66-76).
Impact: regra de preço/estoque presa ao SQL e impossível de testar sem banco; notificações acopladas ao HTTP; qualquer mudança de regra mexe em várias camadas.
Recommendation: RF-04 — services/pedido_service.py (validação de itens, total, estoque, transação), services/relatorio_service.py (descontos), services/notificacao_service.py (notificações); models só persistem; health e admin passam a usar models.

### [HIGH] Conexão de banco global compartilhada entre threads (AP-ARCH-03)
File: database.py:4-11, 86
Description: db_connection é uma variável global de módulo, criada uma vez com check_same_thread=False e reutilizada por todas as requisições (o servidor do Flask atende em várias threads); nunca é fechada; não há transação por requisição.
Impact: requisições concorrentes compartilham o mesmo estado transacional — o commit() de uma requisição grava escritas pela metade de outra (ex.: criar_pedido entre o INSERT do pedido e a baixa de estoque); a checagem e a baixa de estoque não são atômicas (corrida → estoque negativo).
Recommendation: RF-05 — conexão por requisição em flask.g com teardown_appcontext e caminho vindo da config; criação de pedido numa transação única (BEGIN IMMEDIATE) com rollback.

### [HIGH] Acoplamento forte sem injeção de dependência (AP-ARCH-04)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286; database.py:5; controllers.py:2-3, 266; app.py:3-4
Description: cada uma das 15 funções de models.py chama get_db() do módulo global, que abre sempre "loja.db" relativo ao diretório de execução (database.py:5); controllers importam os módulos concretos models e database; não há ponto para trocar o banco (ex.: banco de teste) nem para configurar o caminho.
Impact: impossível testar com banco isolado; rodar python app.py de outra pasta cria silenciosamente outro loja.db.
Recommendation: RF-05/RF-03 — DB_PATH na config (default loja.db na pasta do projeto); create_app() compõe as peças e a conexão vem do app context.

### [MEDIUM] Invariantes de negócio do pedido violáveis (AP-QUAL-02)
File: models.py:133-169; controllers.py:188-206
Description: (1) quantidade não é validada: 0, negativa ou fracionada passam — quantidade -5 gera total negativo e AUMENTA o estoque (estoque - (-5)); (2) o estoque é checado item a item contra o valor atual, então o mesmo produto repetido no pedido fura o limite (2 itens de 5 unidades com estoque 8 → estoque -2); (3) usuario_id inexistente é aceito e grava pedido órfão; (4) usuario_id, produto_id e quantidade não têm tipo checado (string vira 500 ou SQL injection); itens que não são lista de objetos com produto_id/quantidade viram 500; (5) a gravação não é transacional — falha no meio deixa pedido parcial na conexão compartilhada.
Impact: estoque negativo, faturamento distorcido e pedidos de usuários inexistentes.
Recommendation: RF-14 + RF-04 — usuario_id e produto_id inteiros, quantidade inteiro > 0; somar quantidades por produto antes de checar estoque; usuário inexistente rejeitado com 400 {"erro": "Usuário não encontrado", "sucesso": false} (mesmo formato de "Produto X não encontrado"); pedido + itens + baixa de estoque numa transação com rollback.

### [MEDIUM] Validação de entrada ausente ou fraca (AP-QUAL-02)
File: controllers.py:26-50, 66-90, 113-121, 148-158, 169-174, 239-245; app.py:61-62
Description: (1) corpo ausente ou JSON malformado: request.get_json() lança exceção que vira 500 com a mensagem do Werkzeug em todas as rotas POST/PUT; em /login, PUT /pedidos/<id>/status e /admin/query, dados.get sobre None também vira 500; (2) tipos não checados em produto: preco/estoque string → TypeError 500, nome numérico → len() 500, estoque fracionado ou booleano aceito; (3) PUT /produtos/<id> não aplica as regras do POST: aceita nome de 1 caractere ou com mais de 200 e qualquer categoria (controllers.py:81-90 × 47-54); (4) POST /usuarios e /login com campos não-string → TypeError 500; email sem formato checado; (5) GET /produtos/busca?preco_min=abc → float() → 500 (controllers.py:118-121); (6) PUT /pedidos/<id>/status em pedido inexistente responde 200 "Status atualizado" (o UPDATE atinge 0 linhas).
Impact: entradas inválidas viram 500 com mensagem interna ou gravam dados inconsistentes; regras divergentes entre criar e atualizar o mesmo recurso.
Recommendation: RF-14 — validators/ por recurso, reutilizados em criar e atualizar, respondendo 400 no formato {"erro": ...} da rota (mesmas mensagens existentes); recurso inexistente → 404.

### [MEDIUM] Integridade referencial ausente (AP-QUAL-02)
File: database.py:14-53; models.py:65-70, 187-197, 219-229
Description: as tabelas não têm FOREIGN KEY nem UNIQUE (pedidos.usuario_id, itens_pedido.pedido_id/produto_id, usuarios.email); DELETE /produtos/<id> apaga fisicamente o produto mesmo se referenciado por itens de pedido, e o histórico passa a mostrar "produto_nome": "Desconhecido"; a coluna ativo (database.py:22) existe, mas nunca é usada para exclusão lógica; emails duplicados são aceitos e o login devolve o primeiro que casar.
Impact: histórico de pedidos perde a referência ao produto; dados órfãos; identidade ambígua no login.
Recommendation: exclusão lógica via ativo, FKs e UNIQUE(email) mudam o contrato ou exigiriam tratar dados existentes → "Not addressed" no plano, com a recomendação; as checagens que só rejeitam entrada (usuario_id inexistente) entram pelo RF-14.

### [MEDIUM] Tratamento de erro genérico, sem handler central (AP-QUAL-01)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: 17 blocos except Exception as e devolvem {"erro": str(e)} com 500 ({"status": "erro", "detalhes": str(e)} no health); a mensagem da exceção (erro do SQLite, do Werkzeug ou do Python) vai ao cliente; não existe @app.errorhandler.
Impact: vaza detalhes internos (tabelas, SQL, tipos), erros do cliente viram 500 e o comportamento é inconsistente entre rotas.
Recommendation: RF-07 — exceção de aplicação ApiError(mensagem, status, campos extras) + @app.errorhandler em middlewares/errors.py; erros inesperados vão para o log e a resposta usa mensagem fixa no formato da rota.

### [MEDIUM] Queries N+1 na listagem de pedidos (AP-PERF-01)
File: models.py:171-201, 203-233, 139-166, 239-254
Description: GET /pedidos e GET /pedidos/usuario/<id> fazem 1 query de pedidos + 1 por pedido (itens) + 1 por item (nome do produto): 1+P+I queries. criar_pedido consulta cada produto duas vezes (models.py:140 e 155). relatorio_vendas faz 5 consultas separadas na mesma tabela (239-254).
Impact: o tempo de resposta cresce linearmente com o histórico de pedidos.
Recommendation: RF-06 — uma query com LEFT JOIN itens_pedido + LEFT JOIN produtos, agrupada em memória (mesma ordem, mesmo "Desconhecido"); relatório com uma única query agregada.

### [MEDIUM] Duplicação de código (AP-QUAL-03)
File: models.py:12-21, 31-40, 304-313; models.py:79-86, 95-102, 114-119; models.py:171-201 × 203-233; controllers.py:28-50 × 72-90; app.py:7 × controllers.py:289
Description: o mapeamento produto→dict está copiado 3 vezes e o de usuário 3 vezes; a montagem de pedidos é idêntica nas duas listagens (muda só o WHERE); a validação de produto está duplicada entre criar e atualizar (e já divergiu); o literal da SECRET_KEY aparece duas vezes.
Impact: correções precisam ser feitas em vários lugares e já divergiram (PUT sem as regras de nome/categoria do POST).
Recommendation: RF-04/RF-13 — um serializer por entidade no model, uma função de montagem de pedidos, um validator de produto compartilhado.

### [LOW] print usado como log, inclusive com dados pessoais (AP-QUAL-04)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: 19 print registram eventos, erros, "notificações" simuladas e emails de usuários (controllers.py:161, 179, 182) em stdout, sem nível, timestamp ou filtro.
Impact: logs sem estrutura nem nível; dado pessoal (email) espalhado no stdout.
Recommendation: RF-12 — logging.getLogger(__name__) com níveis; sem email/senha nos logs; notificações via services/notificacao_service.py.

### [LOW] Magic numbers e enumerações soltas (AP-QUAL-05)
File: models.py:256-262; controllers.py:47-52, 242, 247-250, 285-286; models.py:150, 247-253; app.py:36, 85, 88; database.py:5
Description: faixas e taxas de desconto (10000/0.1, 5000/0.05, 1000/0.02), limites do nome (2/200), lista de categorias e de status, versão "1.0.0" em dois lugares, "producao", "loja.db", porta 5000 e host fixos.
Impact: regras de negócio escondidas no meio do código; mudar uma faixa ou status exige caçar literais.
Recommendation: RF-11 — config/constants.py (categorias, status, faixas de desconto, limites, versão) e config/settings.py (porta, host, banco, ambiente).

### [LOW] Nomes ruins e builtin sombreado (AP-QUAL-06)
File: controllers.py:14, 56, 64, 98, 136, 160; models.py:24, 54, 65, 89, 187-193, 219-225
Description: parâmetro/variável id sombreia o builtin em 10 pontos; cursor2/cursor3/prod sem significado; buscar_produto × buscar_produtos (rotas diferentes) quase homônimos.
Impact: leitura e manutenção mais difíceis; risco de usar o builtin sombreado por engano.
Recommendation: renomear internamente (produto_id, usuario_id, obter_produto/buscar_produtos...), sem alterar paths nem campos de request/response.

### [LOW] Imports não usados e código morto (AP-QUAL-07)
File: database.py:2; models.py:2; controllers.py:268; models.py:63, 70, 283
Description: import os (database.py) e import sqlite3 (models.py) não são usados; SELECT 1 redundante antes dos COUNT no health; return True de atualizar_produto, deletar_produto e atualizar_status_pedido nunca é lido.
Impact: ruído; sugere dependências que não existem.
Recommendation: remover.

================================
Total: 21 findings
================================
```

APIs deprecated: nenhuma encontrada. Varredura de `utcnow`, `datetime`, `.query.get`, `before_first_request`, `JSONEncoder`, `_app_ctx_stack`/`_request_ctx_stack` e `escape`/`Markup` sem ocorrências; Flask 3.1 e flask-cors 5.0 são usados só com APIs atuais (`add_url_rule`, `route`, `jsonify`, `request.get_json`, `CORS`).
