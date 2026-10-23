# Refactoring Plan — ecommerce-api-legacy

## Context

A auditoria (`reports/audit-report.md`) encontrou 19 findings (CRITICAL 5 | HIGH 5 | MEDIUM 5 | LOW 4) num monólito Express de 3 arquivos: segredos no código, cartão e chave do gateway em log, hash de senha caseiro, endpoints admin abertos, God Class `AppManager`, crash do processo com `card` numérico, stack trace no JSON malformado, N+1, callback hell e estado global. O objetivo é levar o projeto a MVC e resolver todos os findings possíveis **sem mudar o contrato externo** (mesmas rotas, campos, mensagens e `npm start`), exceto as mudanças intencionais listadas abaixo.

## Refactoring Plan

Target structure:
```
src/
├── app.js                         # composition root (cria db, models, services, controllers, rotas; listen)
├── config/
│   ├── index.js                   # PORT (default 3000), PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL via process.env
│   └── constants.js               # PAYMENT_STATUS, APPROVED_CARD_PREFIX, COURSE_ACTIVE, DB_FILENAME (':memory:')
├── db/
│   ├── connection.js              # cria sqlite3.Database; wrappers get/all/run em Promise; transaction(fn) serializada
│   └── schema.js                  # CREATE TABLE + seed (mesmos valores; senha '123' gravada com scrypt)
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   ├── enrollmentModel.js         # inclui a query única do relatório (LEFT JOIN users/payments)
│   ├── paymentModel.js
│   └── auditLogModel.js
├── services/
│   ├── passwordHasher.js          # hash scrypt$sal$hash; verify aceita legado (texto puro / badCrypto) e pede rehash
│   ├── paymentGateway.js          # regra do prefixo "4" → PAID/DENIED; recebe chave por injeção; log com cartão mascarado
│   ├── checkoutService.js         # fluxo do checkout em transação; cache de instância (Map) injetado
│   ├── reportService.js           # agrega relatório preservando ordem e cálculos originais
│   └── userService.js             # exclusão de usuário
├── controllers/
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── index.js                   # monta os routers
│   ├── checkoutRoutes.js          # POST /api/checkout
│   ├── adminRoutes.js             # GET  /api/admin/financial-report (adminAuth)
│   └── userRoutes.js              # DELETE /api/users/:id (adminAuth)
├── validators/
│   ├── checkoutValidator.js
│   └── idValidator.js
├── middlewares/
│   ├── adminAuth.js               # X-Admin-Token × ADMIN_TOKEN, timingSafeEqual, 403 "Acesso negado"
│   ├── appError.js                # AppError(status, message)
│   └── errorHandler.js            # handler central: texto puro, sem stack; JSON inválido → 400 "Bad Request"
└── utils/
    └── logger.js                  # info/warn/error com nível (LOG_LEVEL)
.env.example                       # PORT, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL (sem valores reais)
```
`src/AppManager.js` e `src/utils.js` são removidos (com `rm`) ao final da migração. `package.json` (`start: node src/app.js`) não muda; nenhuma dependência nova (só `crypto` nativo).

Steps (CRITICAL → LOW):
1. [CRITICAL] Criar `config/index.js` lendo do ambiente; remover `dbUser`/`dbPass`/`smtpUser` (não usados); `.env.example` — resolve AP-SEC-01 (+ parte de AP-QUAL-07) — padrão RF-01
2. [CRITICAL] `paymentGateway.js` sem log do cartão completo nem da chave; logger registra `cartão final 4444` — resolve AP-SEC-04 — padrão RF-13 + RF-12
3. [CRITICAL] `passwordHasher.js` com `crypto.scryptSync` + sal aleatório; seed grava `'123'` com scrypt; `verify()` reconhece texto puro e formato `badCrypto` (10 chars sem prefixo `scrypt$`), compara em tempo constante e sinaliza rehash — resolve AP-SEC-03 — padrão RF-08
4. [CRITICAL] `middlewares/adminAuth.js` aplicado a `GET /api/admin/financial-report` e `DELETE /api/users/:id`: sem `ADMIN_TOKEN` configurado ou header `X-Admin-Token` errado → `403` texto `Acesso negado` — resolve AP-SEC-05 — padrão RF-15
5. [CRITICAL] Quebrar `AppManager`/`utils` nas camadas acima; `app.js` vira composition root — resolve AP-ARCH-01 — padrão RF-03
6. [HIGH] `validators/checkoutValidator.js` valida tipos antes do serviço (`card` string não vazia etc.); todo acesso a banco em `async/await` com erro propagado ao `next(err)` — resolve "Entrada inválida derruba o processo" — padrões RF-14 + RF-09 + RF-07
7. [HIGH] `middlewares/errorHandler.js` (4 args) registrado por último: `AppError` → status + mensagem original; erro do `express.json` (`entity.parse.failed`) → `400 Bad Request`; demais `err.status` 4xx → texto do status HTTP; resto → `500 Erro interno`; detalhe só no log — resolve AP-SEC-06 — padrão RF-07
8. [HIGH] Regra de negócio para `checkoutService`, `paymentGateway` e `reportService`; controllers só orquestram e montam a resposta; rotas só ligam path → middleware → controller — resolve AP-ARCH-02 — padrão RF-04
9. [HIGH] `globalCache` vira `Map` criado no composition root e injetado no `checkoutService` (mesma chave `last_checkout_<userId>` = título do curso); remover `totalRevenue` — resolve AP-ARCH-03 — padrão RF-05
10. [HIGH] Conexão criada uma vez no composition root e injetada nos models (banco `:memory:` exige conexão única — cada conexão seria outro banco); services recebem models/gateway/cache/logger por construtor — resolve AP-ARCH-04 — padrão RF-05/RF-03
11. [MEDIUM] Invariantes do checkout no `checkoutService`: decisão do pagamento **antes** de qualquer escrita; usuário (se novo) + matrícula + pagamento + auditoria em uma transação (`BEGIN`/`COMMIT`/`ROLLBACK`, serializada por fila para não intercalar requisições); validação de `eml`, `c_id`, `pwd`; DELETE valida o id e responde 404 para inexistente — resolve AP-QUAL-02 (validação/invariantes) — padrões RF-14 + RF-04
12. [MEDIUM] `AppError` + handler central; nenhum `err` ignorado; mensagens de erro de cada etapa preservadas (`Curso não encontrado`, `Erro DB`, `Erro ao criar usuário`, `Erro Matrícula`, `Erro Pagamento`) — resolve AP-QUAL-01 — padrão RF-07
13. [MEDIUM] Relatório com 2 queries: cursos (`SELECT * FROM courses`, ordem de rowid) + matrículas `LEFT JOIN users LEFT JOIN payments ORDER BY e.id, p.id` (1º pagamento por matrícula, como o `db.get` original) — resolve AP-PERF-01 — padrão RF-06
14. [MEDIUM] Remover callbacks aninhados e contadores; reproduzir de forma determinística a ordem original da resposta: cursos **sem** matrícula primeiro, depois os com matrícula, cada grupo na ordem dos cursos; alunos na ordem das matrículas; `revenue` somando só `PAID` na mesma ordem; `paid` = valor do pagamento ou 0; `student` = nome ou `'Unknown'` — resolve AP-ARCH-05 (+ duplicação do bloco de finalização) — padrão RF-09
15. [LOW] `utils/logger.js`; mensagem de boot `Frankenstein LMS rodando na porta <porta>...` mantida — resolve AP-QUAL-04 — padrão RF-12
16. [LOW] `config/constants.js` (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX = "4"`, `COURSE_ACTIVE = 1`) — resolve AP-QUAL-05 — padrão RF-11
17. [LOW] Nomes internos descritivos (`name`, `email`, `password`, `courseId`, `cardNumber`, `enrollmentId`); campos externos `usr`/`eml`/`pwd`/`c_id`/`card` mantidos — resolve AP-QUAL-06
18. [LOW] Remover código morto (`totalRevenue`, export de `globalCache`, chaves de config não usadas, `email` não usado na query do relatório) — resolve AP-QUAL-07
19. [doc] Atualizar `README.md` e `api.http` com `ADMIN_TOKEN` / header `X-Admin-Token` para as rotas admin.

Not addressed:
- **Integridade — órfãos ao excluir usuário** (finding MEDIUM): corrigir exigiria apagar ou alterar matrículas/pagamentos (histórico financeiro). Recomendação: exclusão lógica (`deleted_at`) ou `FOREIGN KEY ... ON DELETE RESTRICT`. A mensagem `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` é mantida palavra por palavra (corrigir o texto é recomendação).
- **E-mail existente reaproveita a conta ignorando `usr`/`pwd`** e **compra duplicada do mesmo curso** (parte do AP-QUAL-02 MEDIUM): bloquear seria regra de negócio nova (autenticar comprador / impedir recompra). Recomendação: exigir senha (com `passwordHasher.verify`) para e-mail existente e índice único `(user_id, course_id)`.

Contract to preserve:
- Rotas: `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`
- Respostas: checkout sucesso `200 {"msg":"Sucesso","enrollment_id":<n>}`; erros em texto puro com os mesmos textos e status (`400 Bad Request`, `404 Curso não encontrado`, `400 Pagamento recusado`, `500 Erro ...`); relatório `200 [{"course","revenue","students":[{"student","paid"}]}]` na mesma ordem; DELETE `200 Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.`; rotas inexistentes seguem com o 404 padrão do Express.
- Boot: `npm start` (`node src/app.js`), porta 3000 por padrão (agora sobrescrevível por `PORT`).
- Seed: Leonan / leonan@fullcycle.com.br / senha `123`; cursos Clean Architecture 997 e Docker 497 ativos; matrícula 1 com pagamento 997 PAID.

Intentional behavior changes (só "segurança" ou "entrada inválida"):
- [segurança] Relatório financeiro exige `X-Admin-Token` igual a `ADMIN_TOKEN`; sem token configurado ou token errado → `403 Acesso negado` — dados financeiros/pessoais abertos — prova: `GET /api/admin/financial-report` sem header (403) e com header (200, mesmo corpo do baseline)
- [segurança] `DELETE /api/users/:id` exige o mesmo token → `403 Acesso negado` — operação destrutiva aberta — prova: DELETE sem header (403) e com header (200, mesma mensagem)
- [segurança] Log do checkout não contém mais o cartão completo nem a chave do gateway (só `final 4444`) — prova: `grep` no log do boot após um checkout
- [segurança] Senha armazenada com scrypt + sal no seed e em usuários novos (não visível na API) — prova: inspeção do valor gravado via script de verificação
- [segurança + entrada inválida] JSON malformado em `POST /api/checkout` → `400 Bad Request` (texto) em vez da página HTML com stack trace — prova: `POST /api/checkout -d '{'`
- [entrada inválida] `card` não string (ex.: `4111`) → `400 Bad Request` em vez de derrubar o processo — prova: checkout com `"card": 4111` e, em seguida, outra chamada que responde normalmente
- [entrada inválida] `usr`/`eml` não string, `eml` sem `@`, `c_id` que não seja inteiro ≥ 1 (número ou string de dígitos, ex.: `2` ou `"2"` continuam aceitos), `pwd` não string → `400 Bad Request` — prova: checkout com `"eml": "sem-arroba"` e com `"c_id": "abc"` (baseline: 200/404)
- [entrada inválida] Usuário novo sem `pwd` → `400 Bad Request` em vez de criar conta com a senha fixa `123456` — prova: checkout com e-mail novo sem `pwd`
- [entrada inválida] Cartão recusado não grava mais nada (antes o usuário novo ficava criado) — prova: checkout recusado com e-mail novo + checkout aprovado com o mesmo e-mail e outro `usr`; o relatório mostra o novo `usr` (baseline mostra o `usr` da tentativa recusada)
- [entrada inválida] `DELETE /api/users/:id` com id não inteiro → `400 Bad Request`; id inexistente → `404 Usuário não encontrado` (antes: 200 com a mensagem de sucesso) — prova: DELETE `/api/users/abc` e `/api/users/9999` com token

Data preservation:
- Seeds: mesmos valores (usuário Leonan com senha documentada `123`, cursos, matrícula e pagamento); só a senha passa a ser gravada com scrypt.
- Credenciais existentes: o banco é `:memory:` e recriado a cada boot, então não há hash legado persistido; ainda assim `passwordHasher.verify` aceita texto puro e o formato `badCrypto`, e indica rehash para o formato novo (RF-08). Nenhuma rota atual verifica senha.
- Registros persistidos: nenhum é apagado ou alterado como efeito colateral; DELETE continua removendo só a linha de `users`.
- Segredos: nenhum em log ou resposta (`PAYMENT_GATEWAY_KEY` e `ADMIN_TOKEN` só lidos do ambiente).

Validation (segundo `validation-protocol.md`):
- Antes de alterar: copiar fontes para `reports/.tmp/original-src/`; rodar o app original (porta 3000, fixa no código, confirmada livre) e gravar `reports/baseline-responses.txt`. Como o original morre com `card` numérico, essa chamada vai por último no baseline (ou com reinício do processo) para não contaminar as demais.
- Cobertura: checkout sucesso (novo usuário), sucesso com e-mail do seed, recusado, sem campo obrigatório, JSON malformado, `card` numérico, `eml` inválido, `c_id` inexistente/`"abc"`/`"2"`, sem `pwd`; relatório sem token e com token (seed + após checkouts); DELETE sem token, com token (id existente, inexistente, `abc`) — destrutivas por último; IDs dinâmicos capturados da resposta.
- Depois: app refatorado sobe com `npm start` (porta livre via `PORT`, `ADMIN_TOKEN` de teste), mesmas chamadas → `reports/after-responses.txt`; `diff` mascarado; cada diferença casada com a lista acima, o resto é regressão e é corrigido.
- Reverificar com `grep` os sinais do catálogo (segredos, `console.log` de cartão/chave, `globalCache`, `new sqlite3.Database` fora do composition root, query em laço, `err` ignorado, magic strings) e registrar saída real.
- Limpeza: servidores encerrados, porta livre, `reports/.tmp/` apagado; evidências em `reports/validation-report.md`.
