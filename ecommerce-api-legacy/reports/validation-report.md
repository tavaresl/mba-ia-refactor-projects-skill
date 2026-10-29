# Validation Report

## Ambiente
- Porta usada: 5050 (baseline, app original) e 5051 (app refatorado); concorrência em 5052. Todas livres antes do boot: sim (script confere via `/dev/tcp`).
- Porta 3000 (padrão): ocupada por um processo `ssh` do usuário (PID 57123), que **não foi encerrado**. O app original fixa a porta no código (`src/utils.js:6`), então o baseline foi capturado com um pré-carregamento (`node -r reports/.tmp/port-override.js`) que só redireciona `listen(3000)` para `PORT`, sem editar o código original. O app refatorado lê `PORT` (padrão 3000).
- Boot refatorado: `node src/app.js` (= `npm start`) com `PORT=5051`:
```
[INFO] Frankenstein LMS rodando na porta 5051...
```
- Dependências: `npm ci` (lock inalterado: `cmp package-lock.json` e `cmp package.json` contra a cópia original = idênticos). O `sqlite3` precisou de `prebuild-install -r napi` dentro de `node_modules/sqlite3`, porque o npm 12 não executa scripts de instalação por padrão.
- Estado de dados: banco SQLite em memória, recriado a cada boot (nada a restaurar). `ADMIN_TOKEN=teste-admin-token` e `PAYMENT_GATEWAY_KEY=pk_test_fake_key_for_validation` definidos só nas execuções de teste (o original ignora as duas).
- Chamadas: 25 no fluxo principal + 2 boots separados (`card` numérico e `pwd` numérico), mesma sequência no original e no refatorado (`reports/.tmp/validate.sh`).

## Baseline × depois
Comando: `diff <(mask baseline-responses.txt) <(mask after-responses.txt)` (máscara de datas e caminhos absolutos). Saída real:

```
2,3c2,3
< status: 200
< [{"course":"Docker","revenue":0,"students":[]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]
---
> status: 403
> Acesso negado
6,7c6,7
< status: 200
< [{"course":"Docker","revenue":0,"students":[]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]
---
> status: 403
> Acesso negado
47,56c47
< <!DOCTYPE html>
< <html lang="en">
< <head>
< <meta charset="utf-8">
< <title>Error</title>
< </head>
< <body>
< <pre>SyntaxError: Expected property name or &#39;}&#39; in JSON at position 1 (line 1 column 2)<br> &nbsp; &nbsp;at JSON.parse (&lt;anonymous&gt;)<br> &nbsp; &nbsp;at parse (<path>/node_modules/body-parser/lib/types/json.js:92:19)<br> &nbsp; &nbsp;at <path>/node_modules/body-parser/lib/read.js:128:18<br> &nbsp; &nbsp;at AsyncResource.runInAsyncScope (node:async_hooks:226:14)<br> &nbsp; &nbsp;at invokeCallback (<path>/node_modules/raw-body/index.js:238:16)<br> &nbsp; &nbsp;at done (<path>/node_modules/raw-body/index.js:227:7)<br> &nbsp; &nbsp;at IncomingMessage.onEnd (<path>/node_modules/raw-body/index.js:287:7)<br> &nbsp; &nbsp;at IncomingMessage.emit (node:events:509:20)<br> &nbsp; &nbsp;at endReadableNT (node:internal/streams/readable:1753:12)<br> &nbsp; &nbsp;at process.processTicksAndRejections (node:internal/process/task_queues:90:21)</pre>
< </body>
< </html>
---
> Bad Request
63,64c54,55
< status: 404
< Curso não encontrado
---
> status: 400
> Bad Request
71,72c62,63
< status: 200
< {"msg":"Sucesso","enrollment_id":6}
---
> status: 400
> Bad Request
75,76c66,67
< status: 200
< {"msg":"Sucesso","enrollment_id":7}
---
> status: 400
> Bad Request
80c71
< [{"course":"Docker","revenue":2485,"students":[{"student":"Str","paid":497},{"student":"Inv","paid":497},{"student":"SemPwd","paid":497},{"student":"Maria Recusada","paid":497},{"student":"Guilherme","paid":497}]},{"course":"Clean Architecture","revenue":1994,"students":[{"student":"Guilherme","paid":997},{"student":"Leonan","paid":997}]}]
---
> [{"course":"Clean Architecture","revenue":1994,"students":[{"student":"Leonan","paid":997},{"student":"Guilherme","paid":997}]},{"course":"Docker","revenue":1491,"students":[{"student":"Guilherme","paid":497},{"student":"Maria","paid":497},{"student":"Str","paid":497}]}]
83,84c74,75
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 403
> Acesso negado
87,88c78,79
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 403
> Acesso negado
95,96c86,87
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 404
> Usuário não encontrado
99,100c90,91
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 400
> Bad Request
103,104c94,95
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 404
> Usuário não encontrado
108c99
< [{"course":"Clean Architecture","revenue":1994,"students":[{"student":"Unknown","paid":997},{"student":"Guilherme","paid":997}]},{"course":"Docker","revenue":2485,"students":[{"student":"Guilherme","paid":497},{"student":"Inv","paid":497},{"student":"SemPwd","paid":497},{"student":"Maria Recusada","paid":497},{"student":"Str","paid":497}]}]
---
> [{"course":"Clean Architecture","revenue":1994,"students":[{"student":"Unknown","paid":997},{"student":"Guilherme","paid":997}]},{"course":"Docker","revenue":1491,"students":[{"student":"Guilherme","paid":497},{"student":"Maria","paid":497},{"student":"Str","paid":497}]}]
124c115,116
< status: 000
---
> status: 400
> Bad Request
125a118
> processo vivo após card numérico: sim
127,128d119
< processo vivo após card numérico: NAO (servidor caiu)
< 
130c121,122
< status: 000
---
> status: 400
> Bad Request
132,133c124
< 
< processo vivo após pwd numérico: NAO (servidor caiu)
---
> processo vivo após pwd numérico: sim
```

| Diferença (linhas do diff) | Esperada? | Mudança intencional do plano |
|---|---|---|
| `GET /api/admin/financial-report` sem token e com token errado: 200 → 403 `Acesso negado` (2–3, 6–7) | sim | [segurança] rotas admin exigem `X-Admin-Token` (AP-SEC-05) |
| `POST /api/checkout` com `{`: HTML com stack trace → `Bad Request` (status 400 igual) (47) | sim | [segurança] AP-SEC-06 |
| `c_id: "abc"`: 404 `Curso não encontrado` → 400 `Bad Request` (63–64) | sim | [entrada inválida] `c_id` não inteiro positivo |
| `eml: "invalido"`: 200 → 400 `Bad Request` (71–72) | sim | [entrada inválida] formato de e-mail |
| e-mail novo sem `pwd`: 200 → 400 `Bad Request` (75–76) | sim | [entrada inválida] usuário novo exige `pwd` (e-mail existente sem `pwd` segue 200: sem diff na chamada 2 do checkout) |
| Relatório (80, 108): "Maria Recusada" → "Maria"; "Inv" e "SemPwd" ausentes (receita Docker 2485 → 1491 = −2×497); ordem dos cursos/alunos | sim | [entrada inválida] recusa não grava usuário; as duas matrículas somem porque seus checkouts agora são rejeitados (linhas 71–76). A ordem do original é não determinística (Docker primeiro nesta captura, Clean Architecture primeiro em outra; alunos em ordens diferentes entre os dois relatórios da mesma execução); passou a ser determinística (cursos sem matrícula primeiro, depois por id; alunos por id da matrícula) |
| `DELETE /api/users/1` sem token e com token errado: 200 → 403 (83–84, 87–88) | sim | [segurança] AP-SEC-05 |
| `DELETE /api/users/999` com token: 200 → 404 `Usuário não encontrado` (95–96) | sim | [entrada inválida] id inexistente |
| `DELETE /api/users/abc` com token: 200 → 400 `Bad Request` (99–100) | sim | [entrada inválida] id não numérico |
| segundo `DELETE /api/users/1` com token: 200 → 404 (103–104) | sim | [entrada inválida] id inexistente |
| `card` numérico e `pwd` numérico: conexão derrubada (status 000, servidor morto) → 400 `Bad Request`, servidor vivo (124–133) | sim | [entrada inválida] tipo errado (AP-QUAL-02 CRITICAL) |

Sem diferença (comportamento preservado): checkout de sucesso (`enrollment_id` 2), checkout de e-mail existente sem `pwd` (200), pagamento recusado, campo obrigatório ausente, `{}`, corpo vazio, `c_id` 999, `c_id: "2"`, `DELETE /api/users/1` com token (mensagem original palavra por palavra), relatório com `'Unknown'` após a exclusão, `GET /` (404 padrão do Express). Nenhuma regressão encontrada.

## Rotas protegidas
| Rota | Sem token | Token errado | Com token |
|---|---|---|---|
| `GET /api/admin/financial-report` | 403 `Acesso negado` | 403 `Acesso negado` | 200 JSON (relatório) |
| `DELETE /api/users/1` | 403 `Acesso negado` | 403 `Acesso negado` | 200 `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` |

Trechos de `reports/after-responses.txt`:

```
### GET /api/admin/financial-report  
status: 403
Acesso negado

### GET /api/admin/financial-report  [hdr: X-Admin-Token]
status: 403
Acesso negado

### GET /api/admin/financial-report  [hdr: X-Admin-Token]
status: 200
[{"course":"Docker","revenue":0,"students":[]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]


### DELETE /api/users/1  [hdr: X-Admin-Token]
status: 200
Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.

### DELETE /api/users/999  [hdr: X-Admin-Token]
status: 404
Usuário não encontrado

### DELETE /api/users/abc  [hdr: X-Admin-Token]
status: 400
Bad Request

### DELETE /api/users/1  [hdr: X-Admin-Token]
status: 404
Usuário não encontrado
```

## Segredos e senha
Log do servidor (contagem de linhas com número de cartão completo, `pk_live` ou a chave de teste):
```
original:    linhas do log com cartão completo ou chave: 8
refatorado:  linhas do log com cartão completo ou chave: 0
--- original (reports/.tmp/boot-orig-main.log):
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef
--- refatorado (reports/.tmp/boot-new-main.log):
[INFO] Processando cartão ****4444
[INFO] Processando cartão ****4444
```
Hash do seed (`node reports/.tmp/seedcheck.js`, monta o banco com `src/db/schema.js`):
```
formato gravado: scrypt$<sal>$<hash>
senha 123 confere: true
senha errada confere: false
texto puro no banco: false
seed contagens: {"c":2,"e":1,"p":1}
```

Concorrência (`bash reports/.tmp/concurrency.sh`: 8 checkouts simultâneos, transação serializada):
```
200 200 200 200 200 200 200 200 
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":3976,"students":[{"student":"U1","paid":497},{"student":"U3","paid":497},{"student":"U2","paid":497},{"student":"U6","paid":497},{"student":"U4","paid":497},{"student":"U5","paid":497},{"student":"U7","paid":497},{"student":"U8","paid":497}]}]
```

## Reverificação do catálogo
Comando: `bash reports/.tmp/rescan.sh` (grep dos sinais de todas as severidades sobre `src/`). Saída real:

```

$ grep -rnE 'pk_live|pk_test|senha_super|dbPass|dbUser|smtpUser' src   # AP-SEC-01 segredos
(nenhuma ocorrência)

$ grep -rnE '\.(run|get|all)\([^)]*(\$\{|["'] *\+)' src   # AP-SEC-02 SQL concatenado
(nenhuma ocorrência)

$ grep -rnE 'createHash\(.(md5|sha1)|badCrypto|base64' src   # AP-SEC-03 hash fraco
(nenhuma ocorrência)

$ grep -rnE 'console\.(log|info|warn|error)' src   # AP-SEC-04/AP-QUAL-04 console.*
src/config/logger.js:9:        const sink = levelName === 'error' ? console.error : console.log;
src/app.js:60:    console.error('Falha ao iniciar a aplicação:', err);

$ grep -rnE '^(let|var) |globalCache|totalRevenue|logAndCache' src   # AP-ARCH-03 globais mutáveis
(nenhuma ocorrência)

$ grep -rnE 'new Buffer\(|body-parser|url\.parse|createCipher\(' src   # AP-DEPR-01 deprecated
(nenhuma ocorrência)

$ grep -rnE 'debug *[:=] *true|NODE_ENV' src   # AP-SEC-06 debug
(nenhuma ocorrência)

$ grep -rnE 'for *\(|forEach|while *\(' src   # AP-PERF-01 laço com query
src/services/financialReportService.js:21:        rows.forEach((row) => {

$ grep -rnE 'startsWith\(.4.\)|active = 1|123456' src   # AP-QUAL-05 magic
(nenhuma ocorrência)

$ grep -rnE "adminRequired|errorHandler" src/app.js src/routes   # auth e handler presentes
src/app.js:20:const { createErrorHandler } = require('./middlewares/errorHandler');
src/app.js:50:        adminRequired: createAdminAuth({ adminToken: config.adminToken }),
src/app.js:52:    app.use(createErrorHandler({ logger }));
src/routes/userRoutes.js:6:function createUserRoutes({ userController, adminRequired }) {
src/routes/userRoutes.js:8:    router.delete('/users/:id', adminRequired, validate(validateUserId, 'params'), asyncHandler(userController.remove));
src/routes/adminRoutes.js:4:function createAdminRoutes({ reportController, adminRequired }) {
src/routes/adminRoutes.js:6:    router.get('/admin/financial-report', adminRequired, asyncHandler(reportController.financial));

$ wc -l (fontes)
     637 total
      30
```

Linhas remanescentes e justificativa:
- `src/config/logger.js:9`: é o próprio logger (RF-12), único ponto que escreve no console, com nível controlado por `LOG_LEVEL`.
- `src/app.js:60`: erro fatal de boot, antes de o logger existir no escopo do `catch`; imprime só o erro, sem dados de requisição.
- `src/services/financialReportService.js:21`: `forEach` em memória sobre o resultado de **uma** query (sem query dentro do laço): não é N+1.
- Nenhuma API deprecated (AP-DEPR-01), SQL concatenado, segredo, hash fraco, estado global ou magic number remanescente.

## Findings × resultado
| Finding | Resultado |
|---|---|
| AP-SEC-01 segredos hardcoded | Resolvido (`src/config/index.js`, só `process.env`) |
| AP-SEC-04 cartão/chave em log | Resolvido (`****4444`, chave nunca logada) |
| AP-SEC-05 rotas admin abertas | Resolvido (`adminRequired`, 403 sem token) |
| AP-QUAL-02 CRITICAL (tipos derrubam o processo) | Resolvido (400, processo vivo) |
| AP-SEC-03 hash fraco/texto puro | Resolvido (scrypt + sal, seed `123` confere) |
| AP-ARCH-01 God Class | Resolvido (30 arquivos em camadas, `AppManager.js` e `utils.js` removidos) |
| AP-SEC-06 stack trace | Resolvido (`errorHandler`) |
| AP-SEC-07 sem autenticação de base | Parcial: rotas admin protegidas; checkout de e-mail existente sem conferir senha fica em "Not addressed" (RF-16 nível 2) |
| AP-ARCH-02/03/04, AP-PERF-01, AP-ARCH-05, AP-QUAL-01 | Resolvidos (as falhas de banco no curso/auditoria/DELETE mantêm a resposta original, agora logadas — "Not addressed") |
| AP-QUAL-02 MEDIUM | Parcial: (a)(b)(c) e DELETE resolvidos; matrícula duplicada e registros órfãos ficam em "Not addressed" |
| AP-QUAL-04/05/06/07 | Resolvidos |

## Limpeza
- Servidores encerrados: todos os iniciados pela validação (baseline, refatorado, 2 boots de tipos errados, concorrência), cada um com `trap` de encerramento; nenhum processo `node .../src/app.js` restante. Portas 5050, 5051 e 5052 livres: sim. A porta 3000 segue com o `ssh` do usuário (não tocado).
- Dados restaurados: sim (banco em memória, não há arquivo de dados).
- `reports/.tmp` removido: sim. `node_modules/` (criado por `npm ci`) foi mantido; não está no escopo da skill e pode ser apagado a qualquer momento.
- Desvio de protocolo: um `git status --short` (somente leitura, sem efeito) foi executado por engano durante a atualização do README. Nenhum comando de escrita do git foi executado.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── app.js
├── config/        (index.js, constants.js, logger.js)
├── db/            (connection.js, schema.js)
├── models/        (user, course, enrollment, payment, auditLog)
├── services/      (checkout, financialReport, user, passwordHasher, paymentGateway)
├── controllers/   (checkout, report, user)
├── routes/        (index, checkout, admin, user)
├── validators/    (checkout, user)
├── middlewares/   (adminAuth, validate, asyncHandler, errorHandler)
└── exceptions/    (AppError.js)

## Validation
  ✓ Application boots without errors (node src/app.js / npm start, PORT=5051)
  ✓ All endpoints respond (3/3 rotas, mais 27 chamadas de borda)
  ✓ No catalog anti-patterns remaining
  ✗ AP-SEC-07 parcial: checkout de e-mail existente sem conferir senha (RF-16 nível 2, exige mudança de contrato)
  ✗ Matrícula duplicada, registros órfãos após DELETE e respostas de falha de banco originais ficam em "Not addressed" (ver plano)

## Behavior changes
- [segurança] GET /api/admin/financial-report e DELETE /api/users/:id exigem X-Admin-Token (ADMIN_TOKEN); sem token/errado → 403 "Acesso negado"
- [segurança] JSON malformado → 400 "Bad Request" em texto (sem stack trace)
- [segurança] Log sem número completo do cartão nem chave do gateway; senhas com scrypt + sal (seed continua "123")
- [entrada inválida] Tipos errados no checkout (card/usr/eml/pwd não string; c_id não inteiro positivo) → 400 "Bad Request" (antes derrubava o servidor ou dava 404)
- [entrada inválida] eml sem formato texto@texto → 400; usuário novo sem pwd → 400
- [entrada inválida] Pagamento recusado não grava mais o usuário novo (escritas em transação)
- [entrada inválida] DELETE com id inexistente → 404 "Usuário não encontrado"; id não numérico → 400 "Bad Request"
- Ordem do relatório agora determinística (a do original variava entre execuções)
================================
```
