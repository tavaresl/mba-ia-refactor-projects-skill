# Validation Report

## Ambiente
- Porta usada: 3000 no baseline (fixa no código original; livre antes do boot: sim) e 5050 no app refatorado via PORT (livre antes do boot: sim); 5051 no teste de concorrência (livre: sim)
- Boot baseline: `node src/app.js` — log: `Frankenstein LMS rodando na porta 3000...`
- Boot refatorado: `npm start` (`node src/app.js`) com `PORT=5050 ADMIN_TOKEN=tok-teste` — log: `[INFO] Frankenstein LMS rodando na porta 5050...`
- Estado de dados: banco SQLite `:memory:` recriado a cada boot; o projeto não tem arquivo de dados (nada a restaurar)
- Cópia dos fontes originais: `reports/.tmp/original-src/` (removida na limpeza)

## Baseline × depois
Chamadas idênticas e na mesma ordem (`reports/baseline-responses.txt` × `reports/after-responses.txt`). O app original ignora o header `X-Admin-Token`; no depois o valor é `tok-teste`.

```
$ diff reports/baseline-responses.txt reports/after-responses.txt
15,16c15,16
< status: 200
< [{"course":"Docker","revenue":0,"students":[]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]
---
> status: 403
> Acesso negado
18c18
< ### GET /api/admin/financial-report  X-Admin-Token: qualquer
---
> ### GET /api/admin/financial-report  X-Admin-Token: tok-teste
52,59c52
< <!DOCTYPE html>
< <html lang="en">
< <head>
< <meta charset="utf-8">
< <title>Error</title>
< </head>
< <body>
< <pre>SyntaxError: Expected property name or &#39;}&#39; in JSON at position 1 (line 1 column 2)<br> &nbsp; &nbsp;at JSON.parse (&lt;anonymous&gt;)<br> &nbsp; &nbsp;at parse (/Users/lukaorocha/Dev/mba-ia-refactor-projects-skill/ecommerce-api-legacy/node_modules/body-parser/lib/types/json.js:92:19)<br>
---
> Bad Request
62,63c55,56
< status: 200
< {"msg":"Sucesso","enrollment_id":5}
---
> status: 400
> Bad Request
70,71c63,64
< status: 404
< Curso não encontrado
---
> status: 400
> Bad Request
75c68
< {"msg":"Sucesso","enrollment_id":6}
---
> {"msg":"Sucesso","enrollment_id":5}
78,79c71,72
< status: 200
< {"msg":"Sucesso","enrollment_id":7}
---
> status: 400
> Bad Request
82,83c75,76
< status: 200
< [{"course":"Docker","revenue":1491,"students":[{"student":"Guilherme","paid":497},{"student":"StrId","paid":497},{"student":"SemSenha","paid":497}]},{"course":"Clean Architecture","revenue":3988,"students":[{"student":"Leonan","paid":997},{"student":"Leonan","paid":997},{"student":"Sem Arroba","paid":997},{"student":"Maria","paid":997}]}]
---
> status: 403
> Acesso negado
85c78
< ### GET /api/admin/financial-report  X-Admin-Token: qualquer
---
> ### GET /api/admin/financial-report  X-Admin-Token: tok-teste
87c80
< [{"course":"Docker","revenue":1491,"students":[{"student":"Guilherme","paid":497},{"student":"SemSenha","paid":497},{"student":"StrId","paid":497}]},{"course":"Clean Architecture","revenue":3988,"students":[{"student":"Leonan","paid":997},{"student":"Maria","paid":997},{"student":"Leonan","paid":997},{"student":"Sem Arroba","paid":997}]}]
---
> [{"course":"Clean Architecture","revenue":2991,"students":[{"student":"Leonan","paid":997},{"student":"Leonan","paid":997},{"student":"Maria Nova","paid":997}]},{"course":"Docker","revenue":994,"students":[{"student":"Guilherme","paid":497},{"student":"StrId","paid":497}]}]
90,91c83,84
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 403
> Acesso negado
93,95c86,88
< ### DELETE /api/users/abc  X-Admin-Token: qualquer
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> ### DELETE /api/users/abc  X-Admin-Token: tok-teste
> status: 400
> Bad Request
97,99c90,92
< ### DELETE /api/users/9999  X-Admin-Token: qualquer
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> ### DELETE /api/users/9999  X-Admin-Token: tok-teste
> status: 404
> Usuário não encontrado
102,103c95,96
< status: 200
< Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
---
> status: 403
> Acesso negado
105c98
< ### DELETE /api/users/1  X-Admin-Token: qualquer
---
> ### DELETE /api/users/1  X-Admin-Token: tok-teste
109c102
< ### GET /api/admin/financial-report  X-Admin-Token: qualquer
---
> ### GET /api/admin/financial-report  X-Admin-Token: tok-teste
111c104
< [{"course":"Docker","revenue":1491,"students":[{"student":"StrId","paid":497},{"student":"SemSenha","paid":497},{"student":"Guilherme","paid":497}]},{"course":"Clean Architecture","revenue":3988,"students":[{"student":"Maria","paid":997},{"student":"Unknown","paid":997},{"student":"Unknown","paid":997},{"student":"Sem Arroba","paid":997}]}]
---
> [{"course":"Clean Architecture","revenue":2991,"students":[{"student":"Unknown","paid":997},{"student":"Unknown","paid":997},{"student":"Maria Nova","paid":997}]},{"course":"Docker","revenue":994,"students":[{"student":"Guilherme","paid":497},{"student":"StrId","paid":497}]}]
114,115c107,108
< status: 000
< [{"course":"Docker","revenue":1491,"students":[{"student":"StrId","paid":497},{"student":"SemSenha","paid":497},{"student":"Guilherme","paid":497}]},{"course":"Clean Architecture","revenue":3988,"students":[{"student":"Maria","paid":997},{"student":"Unknown","paid":997},{"student":"Unknown","paid":997},{"student":"Sem Arroba","paid":997}]}]
---
> status: 400
> Bad Request
117,119c110,112
< ### GET /api/admin/financial-report  X-Admin-Token: qualquer
< status: 000
< [{"course":"Docker","revenue":1491,"students":[{"student":"StrId","paid":497},{"student":"SemSenha","paid":497},{"student":"Guilherme","paid":497}]},{"course":"Clean Architecture","revenue":3988,"students":[{"student":"Maria","paid":997},{"student":"Unknown","paid":997},{"student":"Unknown","paid":997},{"student":"Sem Arroba","paid":997}]}]
---
> ### GET /api/admin/financial-report  X-Admin-Token: tok-teste
> status: 200
> [{"course":"Clean Architecture","revenue":2991,"students":[{"student":"Unknown","paid":997},{"student":"Unknown","paid":997},{"student":"Maria Nova","paid":997}]},{"course":"Docker","revenue":994,"students":[{"student":"Guilherme","paid":497},{"student":"StrId","paid":497}]}]
121c114
< processo morto no fim
---
> processo vivo no fim
```

| Diferença | Esperada? | Mudança intencional do plano |
|---|---|---|
| GET relatório sem token: 200 → 403 `Acesso negado` (antes e depois dos checkouts) | sim | [segurança] relatório exige `X-Admin-Token` |
| GET relatório com token (seed): corpo idêntico ao baseline (só o texto do header muda na linha de cabeçalho) | sim | prova da rota protegida |
| POST `{`: página HTML com stack trace → 400 `Bad Request` | sim | [segurança + entrada inválida] |
| POST `eml: "sem-arroba"`: 200 → 400 `Bad Request` | sim | [entrada inválida] |
| POST `c_id: "abc"`: 404 `Curso não encontrado` → 400 `Bad Request` | sim | [entrada inválida] |
| POST `c_id: "2"`: continua 200; `enrollment_id` 6 → 5 | sim | consequência de "sem-arroba" não gerar mais matrícula (ID sequencial) |
| POST sem `pwd` (usuário novo): 200 → 400 `Bad Request` | sim | [entrada inválida] |
| DELETE sem token (`abc` e `1`): 200 → 403 `Acesso negado` | sim | [segurança] |
| DELETE `abc` com token: 200 → 400; DELETE `9999` com token: 200 → 404 `Usuário não encontrado` | sim | [entrada inválida] |
| DELETE `1` com token: 200 e mesma mensagem | sim | prova da rota protegida |
| POST `card: 4111` (número): processo morria (status 000) → 400 `Bad Request`; GET seguinte 000 → 200; "processo morto" → "processo vivo" | sim | [entrada inválida] |
| Relatório após os checkouts: faltam "Sem Arroba" e "SemSenha"; aparece "Maria Nova" em vez de "Maria"; totais menores | sim | consequência de rejeitar entradas inválidas e de a recusa de pagamento não criar mais o usuário ([entrada inválida]) |
| Relatório: ordem dos cursos e dos alunos | **não estava no plano** | No original a ordem dependia de corrida entre callbacks: dois GET idênticos seguidos devolveram os alunos em ordens diferentes (`Guilherme,StrId,SemSenha` e `Guilherme,SemSenha,StrId`). Agora é determinística (cursos sem matrículas primeiro, depois por id do curso; alunos por id da matrícula). Não altera campos nem valores, mas é diferença não prevista e fica registrada. |

## Rotas protegidas
| Rota | Sem token | Com token |
|---|---|---|
| GET /api/admin/financial-report | 403 `Acesso negado` | 200, corpo igual ao baseline (seed) |
| DELETE /api/users/abc | 403 `Acesso negado` | 400 `Bad Request` |
| DELETE /api/users/9999 | (mesma proteção, 403) | 404 `Usuário não encontrado` |
| DELETE /api/users/1 | 403 `Acesso negado` | 200 `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` |

Sem `ADMIN_TOKEN` configurado as rotas respondem 403 mesmo com header (`src/middlewares/adminAuth.js` exige `adminToken !== ''`).

## Log do app refatorado (7 cobranças)
```
[INFO] Frankenstein LMS rodando na porta 5050...
[INFO] Processando cartão final 4444 (gateway sem chave)
[INFO] Processando cartão final 4444 (gateway sem chave)
[INFO] Processando cartão final 4444 (gateway sem chave)
[INFO] Processando cartão final 4444 (gateway sem chave)
[INFO] Processando cartão final 4444 (gateway sem chave)
[INFO] Processando cartão final 4111 (gateway sem chave)
[INFO] Processando cartão final 4111 (gateway sem chave)
```
Só os 4 últimos dígitos do cartão aparecem; a chave do gateway e o ADMIN_TOKEN nunca são escritos.

## Hash de senha (RF-08)
```
$ node proofs.js  (script de verificação, comparando com a badCrypto original de original-src)
seed armazenado: scrypt$bbea5013d7ce2...
seed verify("123"): {"valid":true,"needsRehash":false}
seed verify("errada"): {"valid":false,"needsRehash":false}
legado texto puro verify("123","123"): {"valid":true,"needsRehash":true}
legado badCrypto("senhaforte")="c2c2c2c2c2" -> {"valid":true,"needsRehash":true}
legado badCrypto("abc")="YWYWYWYWYW" -> {"valid":true,"needsRehash":true}
legado badCrypto("x")="eAeAeAeAeA" -> {"valid":true,"needsRehash":true}
legado badCrypto("123456")="MTMTMTMTMT" -> {"valid":true,"needsRehash":true}
legado badCrypto("")="" -> {"valid":true,"needsRehash":true}
legado com senha errada: {"valid":false,"needsRehash":false}
sal distinto por hash: true
```

## Concorrência e transação
```
$ bash concurrency.sh  (20 POST /api/checkout simultâneos com usuários novos)
  20 200      (20 respostas 200)
      20      (20 enrollment_id distintos)
      21      (21 alunos no relatório: seed + 20)
```
A rejeição por falta de pwd acontece dentro da transação (rollback): "SemSenha" não aparece no relatório, e o checkout recusado não deixa usuário ("Maria" ausente, "Maria Nova" presente).

## Reverificação do catálogo
```
Arquivos: 29
     654 total
$ grep -nE (pk_live|senha_super|dbPass|dbUser|smtpUser|password\s*[:=]\s*["'][^"']+["'])  (escopo: src/**/*.js)
src/db/schema.js:3:const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

$ grep -nE (run|get|all|exec)\(\s*[`"].*(\$\{|"\s*\+)  (escopo: src/**/*.js)
(nenhuma ocorrência)

$ grep -nE console\.(log|error|warn)  (escopo: src/**/*.js)
(nenhuma ocorrência)

$ grep -nE globalCache|totalRevenue|badCrypto|logAndCache  (escopo: src/**/*.js)
src/services/passwordHasher.js:7:// Formato legado do projeto original ("badCrypto"): os 2 primeiros caracteres do
src/services/passwordHasher.js:25:    // (texto puro e badCrypto); quem chamar deve regravar com hash() quando needsRehash.

$ grep -nE new sqlite3|new Buffer|body-parser|url\.parse|createCipher\(  (escopo: src/**/*.js)
src/db/connection.js:6:    const driver = new sqlite3.Database(filename);

$ grep -nE \|\| "|\|\| '1  (escopo: src/**/*.js)
(nenhuma ocorrência)

$ grep -nE "PAID"|'PAID'|"DENIED"|'DENIED'|startsWith\(  (escopo: src/**/*.js)
src/config/constants.js:2:    PAID: 'PAID',
src/config/constants.js:3:    DENIED: 'DENIED',
src/services/passwordHasher.js:27:        if (typeof stored === 'string' && stored.startsWith(`${SCHEME}$`)) {
src/services/paymentGateway.js:14:        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;

$ grep -nE forEach\(.*(await|db\.)  (escopo: src/**/*.js)
(nenhuma ocorrência)

$ grep -nE let (u|e|p|cid|cc) =  (escopo: src/**/*.js)
(nenhuma ocorrência)

$ grep -nE catch \(e\)|catch\(e\)  (escopo: src/**/*.js)
(nenhuma ocorrência)

```
Linhas remanescentes e justificativa:
- `src/db/schema.js:3` — `password: '123'` é a senha de demonstração documentada do usuário seed (preservada por regra); gravada com scrypt.
- `src/services/passwordHasher.js:7,25` — "badCrypto" só em comentários; o formato legado precisa ser reconhecido para migrar hashes antigos (RF-08).
- `src/db/connection.js:6` — única criação de conexão, na camada `db`, chamada uma vez no composition root (`src/app.js`) e injetada; conexão única é necessária para `:memory:`.
- `src/config/constants.js:2-3`, `src/services/paymentGateway.js:14` — `'PAID'`/`'DENIED'` só como definição da constante; `startsWith` usa `APPROVED_CARD_PREFIX`.
- `src/services/passwordHasher.js:27` — `startsWith` do prefixo `scrypt$` (formato do hash), não é regra de negócio.
- AP-DEPR-01: nenhuma API deprecated no código novo.
- Not addressed (plano): órfãos ao excluir usuário, e-mail existente reaproveitando a conta, compra duplicada.

## Limpeza
- Servidores encerrados (trap EXIT em cada script); portas 3000, 5050 e 5051 livres: sim
- Dados restaurados: não aplicável (banco em memória, nenhum arquivo de dados)
- reports/.tmp removido: sim

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── app.js                  # composition root
├── config/                 # index.js (env), constants.js
├── db/                     # connection.js (Promises + transações), schema.js (schema + seed)
├── models/                 # user, course, enrollment, payment, auditLog
├── services/               # checkout, report, user, passwordHasher, paymentGateway
├── controllers/            # checkout, report, user
├── routes/                 # index, checkoutRoutes, adminRoutes, userRoutes
├── validators/             # checkoutValidator, idValidator
├── middlewares/            # adminAuth, appError, asyncHandler, errorHandler
└── utils/                  # logger
.env.example

## Validation
  ✓ Application boots without errors (npm start)
  ✓ All endpoints respond (3/3)
  ✓ No catalog anti-patterns remaining
  ✗ Pendente de propósito (Not addressed): órfãos ao excluir usuário, e-mail existente reaproveitando a conta, compra duplicada
  ✗ Ordem do relatório não é idêntica ao original (o original era não determinístico); agora é determinística

## Behavior changes
- [segurança] GET /api/admin/financial-report e DELETE /api/users/:id exigem X-Admin-Token = ADMIN_TOKEN (sem token configurado: 403)
- [segurança] cartão completo e chave do gateway não vão mais para o log; senhas com scrypt + sal
- [segurança + entrada inválida] JSON malformado → 400 "Bad Request" (sem stack trace)
- [entrada inválida] card não string, eml sem @, c_id inválido, usuário novo sem pwd → 400 "Bad Request"
- [entrada inválida] pagamento recusado não cria mais o usuário
- [entrada inválida] DELETE com id não numérico → 400; id inexistente → 404 "Usuário não encontrado"
- Ordem do relatório agora determinística (diferença não prevista no plano)
================================
