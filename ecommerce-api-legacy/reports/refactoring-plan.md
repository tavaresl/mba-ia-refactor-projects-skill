# Plano de refatoração — ecommerce-api-legacy

## Context

A auditoria (`reports/audit-report.md`) encontrou 19 findings (6 CRITICAL, 5 HIGH, 4 MEDIUM,
4 LOW) numa API Express de 3 arquivos: segredos e chave `pk_live` no código, cartão e chave
gravados em log, rotas administrativas abertas, hash de senha caseiro, um `card`/`pwd`
numérico derrubando o processo (e apagando o banco em memória) e uma God Class
(`src/AppManager.js`) com conexão, schema, seed, rotas e regra de negócio. O objetivo é levar
o projeto ao MVC e resolver os findings sem quebrar o contrato externo: mesmas rotas, mesmas
mensagens e o mesmo `npm start`. Nada é alterado antes do gate de confirmação da Fase 3.

## Refactoring Plan

Target structure:
```
src/
├── app.js                       # composition root: config → db → schema/seed → models → services → controllers → routes → errorHandler → listen
├── config/
│   ├── index.js                 # PORT (padrão 3000), PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL — tudo de process.env
│   ├── constants.js             # PAYMENT_STATUS, APPROVED_CARD_PREFIX ("4"), COURSE_ACTIVE (1), DEFAULT_PORT, MESSAGES (textos do contrato)
│   └── logger.js                # logger com nível (debug|info|warn|error)
├── db/
│   ├── connection.js            # sqlite3 ':memory:' com Promises (run/get/all) + fila única + transaction(work) com BEGIN/COMMIT/ROLLBACK
│   └── schema.js                # mesmos CREATE TABLE + seed com os mesmos valores (senha '123' gravada com scrypt)
├── models/                      # uma entidade por arquivo; SQL fixo e parametrizado; executor opcional (tx) nas escritas
│   ├── userModel.js             # findByEmail, create, deleteById → { changes }
│   ├── courseModel.js           # findActiveById, findAll (ORDER BY id)
│   ├── enrollmentModel.js       # create, listForFinancialReport (1 query com LEFT JOIN users/payments)
│   ├── paymentModel.js          # create
│   └── auditLogModel.js         # create
├── services/
│   ├── passwordHasher.js        # scrypt + sal aleatório → "scrypt$<sal>$<hash>"
│   ├── paymentGateway.js        # simulação atual (prefixo "4" → PAID), chave injetada, log com cartão mascarado (****4444)
│   ├── checkoutService.js       # regra do checkout (valida, decide pagamento, grava em transação, auditoria)
│   ├── financialReportService.js# agrega o relatório em memória (mesmos campos e ordem)
│   └── userService.js           # exclusão (400/404/mensagem original)
├── controllers/
│   ├── checkoutController.js    # req.input → service → res.status(200).json(...)
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── index.js                 # monta os routers
│   ├── checkoutRoutes.js        # POST /api/checkout
│   ├── adminRoutes.js           # GET /api/admin/financial-report (adminRequired)
│   └── userRoutes.js            # DELETE /api/users/:id (adminRequired)
├── validators/
│   ├── checkoutValidator.js     # função pura: body → { name, email, password, courseId, cardNumber } ou AppError(400, "Bad Request")
│   └── userValidator.js         # params → { id } ou AppError(400, "Bad Request")
├── middlewares/
│   ├── adminAuth.js             # adminRequired: X-Admin-Token × ADMIN_TOKEN (timingSafeEqual sobre sha256); sem token → 403 "Acesso negado"
│   ├── validate.js              # aplica um validator e guarda o resultado em req.input
│   ├── asyncHandler.js          # encaminha rejeições para next(err)
│   └── errorHandler.js          # JSON inválido → 400 "Bad Request"; AppError → status + texto; resto → log + 500
└── exceptions/
    └── AppError.js              # erro com status HTTP e mensagem do contrato
```
Removidos: `src/AppManager.js`, `src/utils.js`. Todas as respostas de erro continuam em texto
puro via `res.send(texto)`, como no original; sucesso continua em JSON.

Steps (CRITICAL → LOW):
1. [CRITICAL] Criar `config/index.js` lendo `process.env` (`PORT` com padrão 3000; `PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN` sem padrão; `LOG_LEVEL` padrão `info`) e apagar `dbUser`/`dbPass`/`smtpUser`/`pk_live` do código; `.env.example` já documenta as 4 variáveis (revisar) — resolve AP-SEC-01 — padrão RF-01
2. [CRITICAL] `paymentGateway` recebe a chave por injeção e nunca a loga; o log do checkout mostra só os 4 últimos dígitos do cartão — resolve AP-SEC-04 — padrão RF-13 + RF-12
3. [CRITICAL] Middleware `adminRequired` nas rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id`: sem `ADMIN_TOKEN` configurado, sem header ou com token errado → 403 `Acesso negado`; roda antes de qualquer validação ou acesso ao banco — resolve AP-SEC-05 (e a parte administrativa de AP-SEC-07) — padrão RF-15
4. [CRITICAL] `checkoutValidator` checa tipo e obrigatoriedade antes de qualquer acesso ao banco: `usr`, `eml`, `card` strings não vazias; `pwd` ausente/null ou string; `c_id` inteiro positivo (número ou string só de dígitos — `"2"` continua aceito). Falha → 400 `Bad Request`. Com async/await + `asyncHandler` + `errorHandler`, nenhuma exceção escapa e derruba o processo — resolve AP-QUAL-02 (CRITICAL) — padrão RF-14 + RF-09 + RF-07
5. [CRITICAL] `passwordHasher` com `crypto.scrypt` + sal de 16 bytes, usado no cadastro do checkout e no seed (mesma senha `123`); `badCrypto` removido — resolve AP-SEC-03 — padrão RF-08
6. [CRITICAL] Quebrar `AppManager` nas camadas da árvore acima; `src/app.js` vira o composition root e mantém `node src/app.js` — resolve AP-ARCH-01 — padrão RF-03
7. [HIGH] Error handler central: `entity.parse.failed` → 400 `Bad Request` (texto), sem stack trace; outros erros 4xx do body-parser → status + texto padrão do HTTP; erros inesperados → log + 500 `Internal Server Error` — resolve AP-SEC-06 — padrão RF-07
8. [HIGH] AP-SEC-07: rotas admin cobertas pelo passo 3; RF-16 nível 1 não se aplica (não há campos de privilégio); verificação de identidade no checkout fica em "Not addressed" (nível 2) — padrão RF-15/RF-16
9. [HIGH] Mover a regra para `checkoutService` (cartão → status, usuário, matrícula, pagamento, auditoria) e `financialReportService` (soma PAID, lista de alunos); controllers só leem `req.input`, chamam o service e respondem — resolve AP-ARCH-02 — padrão RF-04
10. [HIGH] Remover `globalCache`, `logAndCache` e `totalRevenue` (nenhuma rota os lê); o evento vira um `logger.info` — resolve AP-ARCH-03 — padrão RF-05
11. [HIGH] `db`, `paymentGateway`, `passwordHasher` e o logger são criados em `app.js` e injetados por factory (`createXModel(db)`, `createCheckoutService({...})`) — resolve AP-ARCH-04 — padrão RF-05/RF-03
12. [MEDIUM] Relatório com número fixo de queries: `courseModel.findAll()` + `enrollmentModel.listForFinancialReport()` (`enrollments LEFT JOIN users LEFT JOIN payments` no pagamento de menor id da matrícula, igual ao `db.get` original), agrupados em memória com os mesmos campos (`course`, `revenue`, `students[{student, paid}]`, `'Unknown'` para usuário apagado, `paid: 0` sem pagamento). A ordem reproduz a do original, confirmada pelo baseline: cursos sem matrícula primeiro, depois os com matrícula, por id; alunos por id da matrícula — resolve AP-PERF-01 — padrão RF-06
13. [MEDIUM] `db/connection.js`: wrapper de Promises, fila única de operações (o banco em memória é uma conexão só) e `transaction(work)` que segura a fila durante `BEGIN…COMMIT/ROLLBACK`, para checkouts simultâneos não se misturarem — resolve AP-ARCH-05 — padrão RF-09
14. [MEDIUM] Erros propagados como `AppError` com a mensagem original de cada etapa (`Erro DB`, `Erro ao criar usuário`, `Erro Matrícula`, `Erro Pagamento`) e rollback; toda falha de banco passa a ser logada. As respostas originais dos caminhos de falha de banco são mantidas por contrato (ver "Not addressed") — resolve AP-QUAL-01 — padrão RF-07
15. [MEDIUM] Invariantes no `checkoutService`, nesta ordem: curso ativo (404 `Curso não encontrado`) → busca do usuário (500 `Erro DB`) → usuário novo sem `pwd` → 400 `Bad Request` → decisão do pagamento (recusado → 400 `Pagamento recusado`, **sem nenhuma escrita**) → transação (usuário novo, matrícula, pagamento) → auditoria após o commit (falha só é logada; resposta 200 como no original). `eml` precisa casar com `^[^\s@]+@[^\s@]+$`. DELETE: id fora de `^[1-9][0-9]*$` → 400 `Bad Request`; nenhuma linha apagada → 404 `Usuário não encontrado`; só a linha de `users` é apagada — resolve AP-QUAL-02 (MEDIUM, itens a/b/c/e-parcial) — padrão RF-14 + RF-04
16. [LOW] Trocar os `console.log` soltos pelo `config/logger.js` (nível via `LOG_LEVEL`); mensagem de boot mantida (`Frankenstein LMS rodando na porta <porta>...`) — resolve AP-QUAL-04 — padrão RF-12
17. [LOW] Constantes nomeadas em `config/constants.js` (`PAYMENT_STATUS.PAID/DENIED`, `APPROVED_CARD_PREFIX`, `COURSE_ACTIVE`, `DEFAULT_PORT`, parâmetros do scrypt) — resolve AP-QUAL-05 — padrão RF-11
18. [LOW] Nomes descritivos internos (`name`, `email`, `password`, `courseId`, `cardNumber`, `enrollment`); os campos `usr`/`eml`/`pwd`/`c_id`/`card` continuam sendo os da API — resolve AP-QUAL-06
19. [LOW] Remover código morto (`totalRevenue`, `globalCache`, `dbUser`/`dbPass`/`smtpUser`) — resolve AP-QUAL-07
20. [docs] `README.md`: estrutura nova, variáveis de ambiente e uso de `X-Admin-Token`; `api.http`: header `X-Admin-Token: {{adminToken}}` nas duas chamadas administrativas

Not addressed:
- AP-SEC-07 (parcial) — checkout com e-mail já cadastrado continua sem conferir `pwd`, e não há autenticação de base. Exigir senha ou token muda o contrato (RF-16 nível 2). Recomendação: login com token assinado e conferência da senha no checkout de usuário existente.
- AP-QUAL-02 (d) — matrícula duplicada no mesmo curso continua aceita (proibir é regra de negócio nova). Recomendação: `UNIQUE(user_id, course_id)` + 409.
- AP-QUAL-02 (e, parcial) — matrículas e pagamentos de usuário apagado continuam no banco (aparecem como `'Unknown'`); corrigir exigiria apagar histórico financeiro. A mensagem `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` fica palavra por palavra. Recomendação: exclusão lógica (`deleted_at`) e revisar o texto.
- AP-QUAL-01 (parcial) — os caminhos de falha de banco mantêm a resposta original: falha na busca do curso → 404 `Curso não encontrado`; falha na auditoria → 200 `Sucesso`; falha no DELETE → mensagem de sucesso. Agora são logados. Recomendação: 500 `Erro DB`.
- Ordem do relatório — reproduzida do original (consequência da ordem dos callbacks). Recomendação: ordenar explicitamente por id do curso (muda a ordem, decisão do usuário).
- Gateway de pagamento — a simulação (cartão começando com "4" é aprovado) é mantida; integração real fora de escopo.

Contract to preserve:
- Rotas: `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`
- `POST /api/checkout`: 200 JSON `{"msg":"Sucesso","enrollment_id":<n>}`; texto: 400 `Bad Request`, 404 `Curso não encontrado`, 400 `Pagamento recusado`, 500 `Erro DB` / `Erro ao criar usuário` / `Erro Matrícula` / `Erro Pagamento`
- `GET /api/admin/financial-report`: 200 JSON `[{"course","revenue","students":[{"student","paid"}]}]` (mesma ordem); texto 500 `Erro DB`
- `DELETE /api/users/:id`: 200 texto `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.`
- Rotas inexistentes: 404 padrão do Express (`Cannot GET /...`)
- Boot: `npm start` (`node src/app.js`), porta padrão 3000 (agora também via `PORT`)

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token` igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` configurado, sem header ou com token errado → 403 `Acesso negado` (texto). Com token, a resposta original — motivo: AP-SEC-05 — prova: as duas rotas sem header, com token errado e com token certo
- [segurança] JSON malformado → 400 `Bad Request` em texto, no lugar do HTML com stack trace (o status 400 é o mesmo) — motivo: AP-SEC-06 — prova: `POST /api/checkout -d '{'`
- [segurança] Log do checkout sem número completo do cartão (só `****<4 últimos>`) e sem a chave do gateway — motivo: AP-SEC-04 — prova: grep do número do cartão e de `pk_live` no log do servidor, nas duas execuções
- [segurança] Senhas gravadas com scrypt + sal; o seed continua com a senha `123` — motivo: AP-SEC-03 — prova: script em `reports/.tmp/` que monta o banco com `db/schema.js` e confere scrypt(`123`, sal) contra o hash gravado de `leonan@fullcycle.com.br`
- [entrada inválida] Tipo errado no checkout → 400 `Bad Request`: `card`/`usr`/`eml`/`pwd` que não sejam string; `c_id` que não seja inteiro positivo. Antes: `card` ou `pwd` numéricos derrubavam o servidor (conexão cai, processo morre, banco perdido); `c_id` `"abc"`/`-1` davam 404 `Curso não encontrado` — motivo: AP-QUAL-02 CRITICAL — prova: `card: 4111222233334444` e `pwd: 123` (cada um num boot próprio, no fim), `c_id: "abc"`
- [entrada inválida] `eml` fora do formato `texto@texto` → 400 `Bad Request` (antes criava o usuário) — motivo: AP-QUAL-02 — prova: `eml: "invalido"`
- [entrada inválida] Usuário novo sem `pwd` (ou vazio) → 400 `Bad Request` (antes criava a conta com a senha fixa `123456`); e-mail já cadastrado continua aceitando checkout sem `pwd` — motivo: AP-QUAL-02 — prova: e-mail novo sem `pwd`; e-mail existente sem `pwd` (200 nas duas execuções)
- [entrada inválida] Checkout recusado continua 400 `Pagamento recusado`, mas não grava mais o usuário novo (pagamento decidido antes de qualquer escrita, escritas em transação). Efeito visível: um checkout aprovado depois, com o mesmo e-mail, grava o nome enviado nesse checkout (antes ficava o nome da tentativa recusada) — motivo: AP-QUAL-02 — prova: recusado com `usr` "Maria Recusada" e aprovado com `usr` "Maria" no mesmo e-mail → relatório mostra "Maria" (baseline: "Maria Recusada")
- [entrada inválida] `DELETE /api/users/:id` (com token): id que não é inteiro positivo → 400 `Bad Request`; id inexistente → 404 `Usuário não encontrado` (antes: mensagem de sucesso nos dois casos) — motivo: AP-QUAL-02 (e) — prova: `DELETE /api/users/abc`, `/api/users/999` e um segundo `DELETE /api/users/1`

Data preservation:
- Seeds: Leonan / `leonan@fullcycle.com.br` / senha `123` (só passa a ser gravada com scrypt); cursos `Clean Architecture` 997.00 e `Docker` 497.00 ativos; matrícula (1, 1); pagamento 997.00 `PAID` — mesmos valores e ids
- Credenciais existentes: o banco é `:memory:` e é recriado a cada boot, então nenhum hash legado sobrevive ao restart; nenhuma rota verifica senha hoje; o seed regrava a mesma senha no formato novo. Não há hash antigo para migrar
- Registros persistidos: `DELETE /api/users/:id` continua apagando só a linha de `users` (matrículas e pagamentos ficam, com a mesma mensagem); nenhuma correção apaga nem altera registros existentes; o pagamento recusado só deixa de criar um usuário novo
- Segredos: `PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN` vêm só do ambiente e nunca vão para log nem resposta; cartão mascarado no log

Validation:
- Dependências: `npm ci` dentro do projeto (cria `node_modules/` sem alterar `package-lock.json`)
- Antes de alterar qualquer arquivo: copiar os originais para `reports/.tmp/original-src/` e capturar `reports/baseline-responses.txt` com o app original na porta 3000 (fixa no código; conferir que está livre)
- `reports/.tmp/validate.sh` (via `bash`, `trap` para encerrar o servidor, `ADMIN_TOKEN` de teste no ambiente das duas execuções; o original ignora a variável). Mesma sequência nas duas execuções:
  relatório sem token / token errado / com token (seed) → checkout sucesso (Guilherme, `api.http`) → mesmo e-mail sem `pwd` → recusado (João, `api.http`) → "Maria Recusada" recusado + "Maria" aprovado → sem campo obrigatório, corpo vazio, JSON `{` → `c_id` 999, `"abc"`, `"2"`, `eml` inválido, e-mail novo sem `pwd` → relatório com token → DELETE sem token / token errado / com token `1`, `999`, `abc`, `1` de novo → relatório com token (`'Unknown'`) → `GET /` (404 padrão) → em boots separados, no fim: `card` numérico e `pwd` numérico (registra status e se o processo continua vivo)
- App refatorado: sobe com `npm start` (porta via `PORT`) → `reports/after-responses.txt` → diff mascarado contra o baseline; cada diferença é ligada a um item da lista acima, e o resto é regressão a corrigir
- Grep no log do servidor (cartão completo, `pk_live`) e script de conferência do hash do seed
- Reverificação do catálogo (`scan.sh` adaptado à nova árvore), com a saída real no relatório
- Limpeza: servidores encerrados, porta livre, `reports/.tmp/` apagado (não há arquivo de dados a restaurar: o banco é em memória)
- Evidências em `reports/validation-report.md` + bloco `PHASE 3: REFACTORING COMPLETE`
