# Audit Report — ecommerce-api-legacy

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js v26, CommonJS)
Framework:     Express 4.22.1 (package.json: ^4.18.2)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6 (lock: 5.1.7)
Domain:        LMS (venda de cursos online) — checkout com criação de aluno, matrícula e pagamento por cartão; relatório financeiro administrativo; exclusão de usuário
Architecture:  Monólito sem camadas — uma God Class (src/AppManager.js) concentra conexão, schema, seed, rotas e regra de negócio; src/utils.js mistura config com segredos, cache global e "crypto"
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js — 180 linhas)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória, ':memory:')
Entry point:   src/app.js (boot: npm start → node src/app.js, porta 3000 fixa em src/utils.js:6 — hoje não há como trocá-la sem editar o código)
Setup:         npm install (node_modules/ ausente); schema + seed criados automaticamente no boot (initDb), banco zera a cada restart
================================
```

Inventário de rotas:

```
POST   /api/checkout
GET    /api/admin/financial-report
DELETE /api/users/:id
```

Fora da contagem: `package.json`, `package-lock.json`, `.env.example` (documenta `PORT`,
`PAYMENT_GATEWAY_KEY`, `ADMIN_TOKEN` via header `X-Admin-Token` e `LOG_LEVEL`, mas o código
atual não lê nenhuma dessas variáveis), `api.http`, `README.md`.

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] AP-SEC-01 — Credenciais e segredos hardcoded
File: src/utils.js:1-7
Description: O objeto `config` traz no código-fonte o usuário e a senha do banco (`dbUser: "admin_master"`, l.2; `dbPass: "senha_super_secreta_prod_123"`, l.3), a chave de PRODUÇÃO do gateway de pagamento (`paymentGatewayKey: "pk_live_1234567890abcdef"`, l.4), o remetente SMTP (l.5) e a porta fixa (l.6). Nada é lido do ambiente, embora o `.env.example` já documente `PORT` e `PAYMENT_GATEWAY_KEY`.
Impact: Quem tem acesso ao repositório tem a chave live do gateway e a senha do banco; não há como rotacionar segredos por ambiente; a porta não pode ser trocada sem editar o código.
Recommendation: RF-01 — `src/config/index.js` lendo `process.env` (`PAYMENT_GATEWAY_KEY` sem default; `PORT` com default 3000, valor não sensível); remover `dbUser`/`dbPass`/`smtpUser`, que nem são usados (ver AP-QUAL-07).

### [CRITICAL] AP-SEC-04 — Número do cartão e chave do gateway gravados em log
File: src/AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` escreve no stdout, a cada compra, o número completo do cartão recebido no checkout e a chave live do gateway.
Impact: Dados de cartão (escopo PCI) e o segredo do gateway vazam para qualquer arquivo/agregador de log.
Recommendation: RF-13 + RF-12 — logger que registra só os 4 últimos dígitos do cartão e nunca a chave.

### [CRITICAL] AP-SEC-05 — Endpoints administrativos e destrutivos sem autenticação
File: src/AppManager.js:80-129, src/AppManager.js:131-137
Description: `GET /api/admin/financial-report` devolve o faturamento por curso e o nome de cada aluno com o valor pago; `DELETE /api/users/:id` apaga usuários. Nenhuma das duas verifica credencial. O `.env.example` já prevê `ADMIN_TOKEN` + header `X-Admin-Token` para exatamente essas rotas, mas o código ignora.
Impact: Qualquer cliente anônimo lê dados financeiros e pessoais e apaga qualquer usuário (deixando matrículas e pagamentos órfãos).
Recommendation: RF-15 — middleware `adminRequired` (token de `ADMIN_TOKEN`, header `X-Admin-Token`, comparação em tempo constante); sem token configurado ou com token errado → 403.

### [CRITICAL] AP-QUAL-02 (severidade elevada) — Entrada com tipo errado derruba o processo e apaga o banco
File: src/AppManager.js:33, src/AppManager.js:35, src/AppManager.js:46, src/AppManager.js:68, src/utils.js:20
Description: O checkout só testa se os campos são "truthy" (l.35). Com `"card": 4111222233334444` (número), `cc.startsWith("4")` (l.46) lança `TypeError: cc.startsWith is not a function`; com `"pwd": 123` para e-mail novo, `Buffer.from(pwd)` (utils.js:20) lança `ERR_INVALID_ARG_TYPE`. As exceções ocorrem dentro de callbacks do sqlite3, fora do alcance do Express, e viram `uncaughtException`.
Impact: Uma única requisição anônima encerra o servidor (DoS). Como o banco é `:memory:`, todas as matrículas e pagamentos gravados desde o boot são perdidos. Severidade elevada de MEDIUM para CRITICAL por impedir o funcionamento e causar perda de dados.
Recommendation: RF-14 — validar tipo de `usr`, `eml`, `pwd`, `card` (string) e `c_id` (inteiro positivo) na rota, respondendo 400 `Bad Request` (formato atual da rota); RF-09 + RF-07 — async/await com erros encaminhados ao handler central.

### [CRITICAL] AP-SEC-03 — Senha em texto puro e hash caseiro reversível
File: src/utils.js:17-23, src/AppManager.js:18, src/AppManager.js:68
Description: `badCrypto` repete 10.000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10: o resultado depende só dos ~12 primeiros bits da senha, sem sal (medido: `"senhaforte"`, `"segredo"` e `"se"` → `c2c2c2c2c2`; `"123"` e `"123456"` → `MTMTMTMTMT`). O usuário de seed é gravado com a senha em texto puro (`'123'`, l.18).
Impact: Um vazamento do banco expõe as senhas (texto puro) ou permite recuperá-las na hora; colisões em massa; o laço síncrono de 10.000 iterações gasta CPU a cada cadastro.
Recommendation: RF-08 — `crypto.scrypt` com sal aleatório (formato `scrypt$<sal>$<hash>`), inclusive no seed (mesma senha documentada `123`).

### [CRITICAL] AP-ARCH-01 — God Class `AppManager`
File: src/AppManager.js:1-141
Description: Uma única classe cria a conexão (l.7), define schema e seed (l.10-23), registra as 3 rotas (l.25-137) e contém toda a regra de negócio (aprovação do pagamento, criação de usuário, matrícula, auditoria, agregação do relatório) e a montagem das respostas HTTP.
Impact: Nada pode ser testado nem alterado em isolamento; qualquer mudança arrisca o sistema inteiro.
Recommendation: RF-03 — separar em `config/`, `db/`, `models/`, `services/`, `controllers/`, `routes/`, `middlewares/`, com `src/app.js` como composition root.

### [HIGH] AP-SEC-07 — API sem autenticação de base: checkout ignora a senha de e-mail já cadastrado
File: src/AppManager.js:40-75
Description: Nenhuma rota verifica credencial (não há `Authorization`, sessão, token nem middleware de auth — a varredura só encontra `app.use(express.json())`). No checkout, se o e-mail já existe (l.66-75), a compra é feita em nome desse usuário sem conferir `pwd`. Não existem campos de privilégio (`role`, `is_admin`), logo não há escalada de privilégio — por isso HIGH e não CRITICAL.
Impact: Quem conhece um e-mail cadastrado cria matrículas e pagamentos em nome desse usuário.
Recommendation: RF-15 cobre as rotas administrativas (AP-SEC-05). RF-16 nível 1 não se aplica (não há campos de privilégio). Verificar identidade no checkout é RF-16 nível 2 (muda o contrato): propor, aplicar só se o usuário pedir.

### [HIGH] AP-SEC-06 — Stack trace devolvido ao cliente (sem error handler, Express em modo development)
File: src/app.js:5-6
Description: Não há middleware de erro nem `NODE_ENV`; o Express assume `env = development` e o handler padrão responde a um JSON malformado (`-d '{'`) com um HTML contendo o stack trace completo, com caminhos absolutos de `node_modules/body-parser`.
Impact: Expõe internals (caminhos do servidor, módulos, stack) a qualquer cliente anônimo.
Recommendation: RF-07 — error handler central `(err, req, res, next)` que loga o detalhe e responde texto fixo no formato da rota (`Bad Request` para corpo inválido).

### [HIGH] AP-ARCH-02 — Regra de negócio dentro das rotas
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: O handler de `POST /api/checkout` decide a aprovação do pagamento (`cc.startsWith("4")`), cria o usuário, matricula, registra pagamento e auditoria; o handler do relatório soma o faturamento dos pagamentos `PAID` e monta a lista de alunos — tudo misturado com SQL e `res.send`.
Impact: A regra fica acoplada a HTTP e SQL; não pode ser testada nem reutilizada.
Recommendation: RF-04 — `services/checkoutService.js`, `services/financialReportService.js`, `services/paymentGateway.js`; controllers e rotas finos.

### [HIGH] AP-ARCH-03 — Estado global mutável (`globalCache`, `totalRevenue`)
File: src/utils.js:9-15, src/utils.js:25, src/AppManager.js:59
Description: `globalCache` é um objeto de módulo exportado, alterado em todo checkout (`last_checkout_<userId>`), nunca lido nem limpo; `totalRevenue` é um contador global mutável exportado (por valor) e nunca atualizado.
Impact: Memória cresce sem limite (uma chave por comprador), estado compartilhado entre requisições, acoplamento oculto entre módulos.
Recommendation: RF-05 — remover cache e contador (nenhuma rota os lê); dependências passadas por injeção.

### [HIGH] AP-ARCH-04 — Acoplamento forte sem injeção de dependência
File: src/AppManager.js:1-8, src/app.js:2-10
Description: `AppManager` instancia o próprio banco (`new sqlite3.Database(':memory:')`, l.7) e importa `config` e funções concretas de `utils`; os handlers usam `this.db` direto; `app.js` só consegue montar essa composição fixa.
Impact: Impossível trocar banco ou gateway em teste; tudo depende de tudo.
Recommendation: RF-05/RF-03 — `db` e `paymentGateway` criados no entry point e injetados em models, services e controllers.

### [MEDIUM] AP-PERF-01 — Queries N+1 no relatório financeiro
File: src/AppManager.js:83-128
Description: 1 query de cursos + 1 query de matrículas por curso (l.92) + 2 queries por matrícula (usuário l.104, pagamento l.106): 1 + C + 2E queries por chamada.
Impact: O custo do relatório cresce linearmente com o número de matrículas.
Recommendation: RF-06 — número fixo de queries (cursos + uma query com `LEFT JOIN` matrículas × usuários × pagamento), agrupadas em memória, mantendo campos e ordem da resposta.

### [MEDIUM] AP-ARCH-05 — Callback hell e controle de fluxo manual com contadores
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Description: Checkout com 6 níveis de callbacks aninhados e sem transação (se o pagamento falhar, a matrícula já ficou gravada — l.50-55); relatório com contadores manuais `coursesPending`/`enrPending` e o bloco "push + decrementa + responde" duplicado (l.95-99 e l.117-122). A ordem dos cursos no relatório depende da ordem em que os callbacks terminam.
Impact: Ilegível, sem atomicidade (dados parciais), exceções escapam do Express.
Recommendation: RF-09 — wrapper de Promises sobre o sqlite3, `async/await`, transação (`BEGIN`/`COMMIT`/`ROLLBACK`) serializada para as escritas do checkout.

### [MEDIUM] AP-QUAL-01 — Erros ignorados e tratados à mão em cada callback
File: src/AppManager.js:38, src/AppManager.js:57-60, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135, src/app.js:5-14
Description: Erro de banco na busca do curso vira 404 "Curso não encontrado" (l.38); o `err` da auditoria é ignorado e a resposta é 200 (l.57); `err` ignorado nas queries do relatório (l.92, 104, 106 — com erro, `enrollments.length` lança TypeError e derruba o processo); `err` do DELETE ignorado, e a rota responde sucesso (l.133-135). Não existe handler central.
Impact: Falhas silenciosas, respostas enganosas, queda do processo.
Recommendation: RF-07 — erros propagados (`next(err)`) a um middleware central que reproduz as mensagens originais de cada rota (`Erro DB`, `Erro Matrícula`...) e loga o detalhe.

### [MEDIUM] AP-QUAL-02 — Validação fraca e invariantes de negócio
File: src/AppManager.js:35, src/AppManager.js:48, src/AppManager.js:50, src/AppManager.js:66-72, src/AppManager.js:131-137
Description: (a) `pwd` não é obrigatório e, ausente, vira a senha fixa `"123456"` (l.68); (b) `eml` não tem formato checado e `c_id` não tem tipo checado (`true`, `"abc"`, `-1`, `1.5` chegam ao SQL) (l.35); (c) o usuário novo é gravado antes da decisão do pagamento, então um checkout recusado deixa um usuário gravado sem matrícula (l.66-72 → l.48); (d) nada impede matricular o mesmo usuário duas vezes no mesmo curso, pagando de novo (l.50); (e) `DELETE /api/users/:id` com id inexistente ou não numérico responde a mensagem de sucesso, e a exclusão deixa matrículas/pagamentos apontando para usuário inexistente (l.131-137).
Impact: Contas com senha previsível, dados inconsistentes, cobrança duplicada, falsa confirmação de exclusão.
Recommendation: RF-14 + RF-04 — validação na rota (400 `Bad Request`), `pwd` obrigatório para usuário novo, decisão do pagamento antes de qualquer escrita e escritas em transação; DELETE com id inválido → 400, inexistente → 404. (d) e os órfãos de (e) exigem regra nova ou apagar dados → "Not addressed".

### [LOW] AP-QUAL-04 — `console.log` como logging
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: 3 `console.log` soltos, sem nível nem padrão.
Impact: Sem controle de nível por ambiente; facilita vazar dado sensível (ver AP-SEC-04).
Recommendation: RF-12 — `src/config/logger.js` com nível vindo de `LOG_LEVEL` (já documentado no `.env.example`).

### [LOW] AP-QUAL-05 — Magic numbers e strings de negócio
File: src/AppManager.js:21, src/AppManager.js:37, src/AppManager.js:46-48, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:6, src/utils.js:19-22
Description: Regra de aprovação `startsWith("4")`, status `'PAID'`/`'DENIED'` repetidos, `active = 1`, senha padrão `"123456"`, porta `3000` e os `10000`/`2`/`10` do hash caseiro, sem nome.
Impact: Regra de negócio escondida e fácil de divergir entre pontos do código.
Recommendation: RF-11 — `src/config/constants.js` (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `COURSE_ACTIVE`, `DEFAULT_PORT`).

### [LOW] AP-QUAL-06 — Nomes ruins
File: src/AppManager.js:26, src/AppManager.js:29-33, src/AppManager.js:89, src/AppManager.js:102, src/utils.js:12, src/utils.js:17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`, `c`, `enr`, `self`; funções `logAndCache`, `badCrypto`; classe `AppManager` e módulo `utils` sem significado de domínio.
Impact: Código difícil de ler e revisar.
Recommendation: Nomes descritivos internamente (`name`, `email`, `password`, `courseId`, `cardNumber`); os campos externos `usr`/`eml`/`pwd`/`c_id`/`card` continuam aceitos.

### [LOW] AP-QUAL-07 — Código e configuração mortos
File: src/AppManager.js:2, src/utils.js:2-3, src/utils.js:5, src/utils.js:9-10, src/utils.js:25
Description: `totalRevenue` importado e nunca usado (AppManager.js:2); `globalCache` exportado e nunca lido; `config.dbUser`, `config.dbPass` e `config.smtpUser` nunca usados (o banco é `:memory:` e não há envio de e-mail).
Impact: Ruído e segredos mantidos sem motivo.
Recommendation: Remover.

================================
Total: 19 findings
================================
```

APIs deprecated (AP-DEPR-01): nenhuma encontrada — o código já usa `Buffer.from` e
`express.json()`; não há `new Buffer`, `body-parser`, `url.parse` nem `crypto.createCipher`.

SQL Injection (AP-SEC-02): nenhuma — todas as queries usam placeholders `?`; a template
string em `src/AppManager.js:57` é um valor de parâmetro, não SQL.

## Evidência da varredura

Comando: `bash reports/.tmp/scan.sh` (sinais do catálogo sobre `src/app.js`,
`src/AppManager.js`, `src/utils.js`). Trechos relevantes da saída real:

```
== AP-SEC-01 segredos/literais de config ==
src/utils.js:3:    dbPass: "senha_super_secreta_prod_123",
src/utils.js:4:    paymentGatewayKey: "pk_live_1234567890abcdef",
src/utils.js:5:    smtpUser: "no-reply@fullcycle.com.br",
src/utils.js:6:    port: 3000

== AP-SEC-02 SQL montado com concatenação/template ==
src/AppManager.js:57:  self.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${cid} por ${userId}`], (err) => {
(nenhum com +)

== AP-SEC-03 hashing / senha ==
src/AppManager.js:18:  this.db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
src/AppManager.js:68:  let hash = badCrypto(p || "123456");
src/utils.js:20:        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
(nenhum hash seguro)

== AP-SEC-04 log de dado sensível ==
src/app.js:13:    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
src/AppManager.js:45:  console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
src/utils.js:13:    console.log(`[LOG] Salvando no cache: ${key}`);

== AP-SEC-05/07 auth/middleware ==
src/app.js:6:app.use(express.json());

== AP-SEC-06 error handler / env ==
(nenhum error handler nem NODE_ENV)

== AP-ARCH-03 estado global mutável ==
src/utils.js:9:let globalCache = {};
src/utils.js:10:let totalRevenue = 0;

== AP-DEPR-01 ==
(nenhuma API deprecated)
```

Comando: `node reports/.tmp/probe.js` (cópia literal de `badCrypto` + chamadas com tipos
errados, sem tocar no projeto):

```
"senhaforte" -> c2c2c2c2c2
"segredo" -> c2c2c2c2c2
"se" -> c2c2c2c2c2
"123" -> MTMTMTMTMT
"123456" -> MTMTMTMTMT
"1zzzzzz" -> MXMXMXMXMX
card numérico: TypeError cc.startsWith is not a function
pwd numérico: TypeError ERR_INVALID_ARG_TYPE
```
