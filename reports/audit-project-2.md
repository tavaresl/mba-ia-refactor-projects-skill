# Audit Report — ecommerce-api-legacy

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js v26.5.0)
Framework:     Express 4.22.1 (manifest ^4.18.2)
Dependencies:  express, sqlite3 5.1.7 (^5.1.6)
Domain:        LMS (plataforma de cursos) com checkout: compra de curso com criação de aluno, matrícula, pagamento, relatório financeiro administrativo e remoção de usuário
Architecture:  Monólito sem camadas — uma classe "AppManager" concentra conexão, schema, seed, rotas e regra de negócio; utils.js mistura config, segredos, estado global e "crypto"
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js) — ~180 linhas
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória, ':memory:')
Entry point:   src/app.js (boot: npm start → node src/app.js, porta 3000 fixa em utils.js)
Setup:         none — schema e seed criados em memória no boot (AppManager.initDb); `npm install` já feito (node_modules presente)
================================
```

Rotas:

```
POST   /api/checkout
GET    /api/admin/financial-report
DELETE /api/users/:id
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] AP-SEC-01 — Credenciais / segredos hardcoded
File: src/utils.js:1-7
Description: O objeto `config` traz no código-fonte o usuário e a senha do banco (`dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`), a chave de produção do gateway de pagamento (`paymentGatewayKey: "pk_live_1234567890abcdef"`) e o usuário SMTP. A porta também é fixa (3000), sem leitura de ambiente.
Impact: Qualquer pessoa com acesso ao repositório tem a chave live do gateway e a senha do banco; não há como rotacionar segredos por ambiente.
Recommendation: RF-01 — `src/config/index.js` lendo `process.env` (`PAYMENT_GATEWAY_KEY`, `PORT`, `ADMIN_TOKEN`), default só para parâmetros não sensíveis (porta 3000), `.env.example` sem valores reais. `dbUser`/`dbPass`/`smtpUser` não são usados (ver AP-QUAL-07) e saem do código.

### [CRITICAL] AP-SEC-04 — Número do cartão e chave do gateway gravados em log
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` escreve o número completo do cartão e a chave live do gateway na saída padrão a cada checkout (confirmado em execução: `Processando cartão 4111 na chave pk_live_1234567890abcdef`).
Impact: Dado de cartão (PCI) e segredo de produção vazam para qualquer sistema de logs.
Recommendation: RF-13 + RF-12 — logar só o cartão mascarado (últimos 4 dígitos) via logger; nunca logar a chave.

### [CRITICAL] AP-SEC-03 — Senha em texto puro e hash caseiro fraco
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres: o "hash" depende só dos ~2 primeiros caracteres da senha, não tem sal e é praticamente reversível (senhas com o mesmo prefixo colidem). O usuário de seed é gravado com a senha em texto puro (`'123'`).
Impact: Um vazamento do banco expõe as senhas; colisões triviais.
Recommendation: RF-08 — `crypto.scryptSync` com sal aleatório (formato `scrypt$<sal>$<hash>`), seed com a mesma senha documentada (`123`) gravada já com hash, e verificação que reconhece o formato legado (texto puro / `badCrypto`) e regrava no formato novo.

### [CRITICAL] AP-SEC-05 — Endpoints administrativos/destrutivos sem autenticação
File: src/AppManager.js:80-129 (GET /api/admin/financial-report); src/AppManager.js:131-137 (DELETE /api/users/:id)
Description: O relatório financeiro (nomes de alunos, valores pagos, faturamento por curso) e a exclusão de usuários são acessíveis por qualquer cliente, sem nenhum token ou sessão.
Impact: Exposição de dados financeiros e pessoais; qualquer um apaga usuários.
Recommendation: RF-15 — middleware `adminAuth`: rota mantida, desligada por padrão; só funciona com `ADMIN_TOKEN` configurado no ambiente e enviado em `X-Admin-Token` (comparação em tempo constante); caso contrário 403.

### [CRITICAL] AP-ARCH-01 — God Class (`AppManager`) / God Module (`utils.js`)
File: src/AppManager.js:1-141; src/utils.js:1-25
Description: `AppManager` cria a conexão (l.7), define o schema e o seed (l.10-23), registra as rotas no Express (l.25-138) e contém toda a regra de negócio (aprovação de pagamento, criação de usuário, matrícula, auditoria, agregação do relatório). `utils.js` mistura configuração, segredos, estado global, log e criptografia.
Impact: Nada pode ser testado nem alterado isoladamente; qualquer mudança mexe em HTTP, SQL e regra ao mesmo tempo.
Recommendation: RF-03 — separar em config / db / models / services / controllers / routes / middlewares, com `src/app.js` como composition root.

### [HIGH] AP-QUAL-02 + AP-QUAL-01 — Entrada inválida derruba o processo inteiro (exceção não tratada em callback)
File: src/AppManager.js:46; src/AppManager.js:92-93
Description: `cc.startsWith("4")` é chamado sem checar o tipo de `card`. Com `"card": 4111` (número), o `TypeError` é lançado dentro do callback do sqlite3, fora do ciclo do Express, e o processo Node encerra (confirmado em execução: a requisição fica sem resposta, `status: 000`, e o processo morre). Da mesma forma, no relatório, um erro em `db.all` (l.92) deixa `enrollments` indefinido e `enrollments.length` lança fora do Express. Severidade elevada de MEDIUM para HIGH porque uma única requisição tira a API do ar (impede o funcionamento correto).
Impact: Negação de serviço trivial com um corpo JSON comum.
Recommendation: RF-14 (validar tipos antes do serviço) + RF-09 (async/await, erros propagados ao handler central) + RF-07.

### [HIGH] AP-SEC-06 — Stack trace devolvido ao cliente
File: src/app.js:5-10 (nenhum error middleware; `NODE_ENV` não definido)
Description: Sem handler de erro próprio, os erros caem no handler padrão do Express, que fora de `NODE_ENV=production` responde uma página HTML com o stack trace. Confirmado: `POST /api/checkout` com corpo `{` devolve `400` com `<!DOCTYPE html>...<title>Error</title>` contendo `SyntaxError ... at JSON.parse ... node_modules/body-parser/lib/types/json.js:92:19` e caminhos absolutos do servidor.
Impact: Expõe internals (caminhos, versões, bibliotecas) a qualquer cliente.
Recommendation: RF-07 — middleware de erro central `(err, req, res, next)` que responde no formato original da rota (texto) sem stack; detalhe só no log.

### [HIGH] AP-ARCH-02 — Regra de negócio dentro do handler HTTP
File: src/AppManager.js:28-78 (checkout); src/AppManager.js:80-129 (relatório)
Description: O handler do checkout decide a aprovação do pagamento (`cc.startsWith("4")`), cria o usuário com hash, cria matrícula, pagamento e log de auditoria, tudo misturado com `req`/`res` e SQL. O handler do relatório calcula faturamento e monta a lista de alunos inline.
Impact: Regra acoplada a HTTP e SQL; impossível testar ou reutilizar.
Recommendation: RF-04 — `CheckoutService`, `PaymentGateway` e `ReportService` sem HTTP; controllers só orquestram; rotas só ligam path → controller.

### [HIGH] AP-ARCH-03 — Estado global mutável
File: src/utils.js:9-15, 25; src/AppManager.js:59
Description: `globalCache` (objeto de módulo) é alterado a cada checkout por `logAndCache` (`last_checkout_<userId>`), sem limite de tamanho; `totalRevenue` é um contador global (exportado por valor, nunca atualizado).
Impact: Estado compartilhado entre requisições, crescimento sem limite, acoplamento escondido.
Recommendation: RF-05 — cache como instância (`Map`) criada no composition root e injetada no serviço; remover `totalRevenue`.

### [HIGH] AP-ARCH-04 — Acoplamento forte sem injeção de dependência
File: src/AppManager.js:2, 7; src/app.js:8-10
Description: `AppManager` instancia o banco concreto no construtor (`new sqlite3.Database(':memory:')`) e importa `config`/funções de `utils` diretamente; o entry point delega à própria classe o registro das rotas (`manager.setupRoutes(app)`).
Impact: Não dá para trocar o banco, o gateway ou o cache em teste.
Recommendation: RF-05/RF-03 — conexão criada no composition root e injetada nos models; services recebem models, gateway, cache e logger por construtor.

### [MEDIUM] AP-QUAL-02 — Validação ausente e invariantes de negócio quebradas
File: src/AppManager.js:29-35, 46-48, 50-55, 66-72, 131-136
Description:
- l.35: só checa presença (`!u || !e || !cid || !cc`); tipo e formato não são validados (`eml` sem `@`, `c_id` qualquer valor, `card` não string — ver finding HIGH).
- l.68: senha ausente vira silenciosamente `"123456"` para o usuário novo.
- l.66-72 × l.46-48: o usuário novo é gravado **antes** da aprovação do pagamento; com cartão recusado o usuário fica criado mesmo com `400 Pagamento recusado`.
- l.50-55: matrícula gravada antes do pagamento, sem transação; se o insert do pagamento falha, fica matrícula sem pagamento.
- l.131-136: `DELETE /api/users/:id` responde sucesso para id inexistente ou não numérico.
- l.40, 74: e-mail já existente reaproveita a conta ignorando `usr` e `pwd` (qualquer um compra em nome de outra conta); compras repetidas do mesmo curso geram matrículas e cobranças duplicadas.
Impact: Dados inválidos entram no banco; senha previsível; registros parciais.
Recommendation: RF-14 (validator do checkout e do id) + RF-04 com transação no `CheckoutService` (pagamento decidido antes de qualquer escrita; usuário, matrícula, pagamento e auditoria na mesma transação). As duas regras novas da última linha (autenticar comprador existente, bloquear compra duplicada) mudariam o negócio e vão para "Not addressed".

### [MEDIUM] AP-QUAL-01 — Tratamento de erro manual, inconsistente e erros ignorados
File: src/AppManager.js:38, 57, 92, 104, 106, 133
Description: Cada callback trata erro à mão; `err` é ignorado no insert de auditoria (l.57), na busca de matrículas (l.92), de usuário (l.104), de pagamento (l.106) e no DELETE (l.133, sempre responde sucesso). Na l.38 erro de banco vira `404 Curso não encontrado`. Não há handler central.
Impact: Falhas silenciosas, respostas inconsistentes, crash (ver HIGH).
Recommendation: RF-07 — `AppError(status, message)` + middleware central; services propagam erros.

### [MEDIUM] AP-PERF-01 — Queries N+1 no relatório financeiro
File: src/AppManager.js:83-125
Description: 1 query de cursos + 1 query de matrículas por curso + 2 queries (usuário e pagamento) por matrícula: `1 + C + 2E` queries por chamada.
Impact: Custo cresce linearmente com matrículas; relatório lento com dados reais.
Recommendation: RF-06 — 1 query de cursos + 1 query de matrículas com `LEFT JOIN users` e `LEFT JOIN payments`, agrupadas em memória, preservando a ordem atual da resposta.

### [MEDIUM] AP-ARCH-05 — Callback hell e controle de fluxo por contadores
File: src/AppManager.js:37-77; src/AppManager.js:86-122
Description: O checkout tem 5 níveis de callback (curso → usuário → [insert usuário] → matrícula → pagamento → auditoria), mistura `this`/`self`/`function` para ler `lastID`. O relatório controla o fim com contadores manuais (`coursesPending`, `enrPending`), e o bloco de finalização está duplicado (l.95-99 e l.118-122, AP-QUAL-03). A ordem dos cursos na resposta depende da ordem de término dos callbacks (cursos sem matrícula saem primeiro: `[Docker, Clean Architecture]`).
Impact: Ilegível, sem transação, erro no meio deixa dados parciais.
Recommendation: RF-09 — wrapper de Promises sobre o sqlite3 e `async/await`; ordem atual da resposta reproduzida de forma determinística.

### [MEDIUM] AP-QUAL-02 — Integridade referencial: exclusão de usuário deixa matrículas e pagamentos órfãos
File: src/AppManager.js:12-15 (sem FOREIGN KEY), src/AppManager.js:131-136
Description: `DELETE FROM users` não trata `enrollments`/`payments` do usuário; a própria mensagem admite ("as matrículas e pagamentos ficaram sujos no banco"). O relatório passa a listar `student: "Unknown"` para esses registros.
Impact: Dados inconsistentes no relatório financeiro.
Recommendation: Não corrigir apagando dados (preservação de histórico financeiro). Recomendação para o futuro: exclusão lógica (`deleted_at`) ou `FOREIGN KEY ... ON DELETE RESTRICT`. Fica em "Not addressed".

### [LOW] AP-QUAL-04 — `console.log` como logging
File: src/app.js:13; src/utils.js:13; src/AppManager.js:45
Description: Eventos registrados com `console.log` espalhado, sem nível nem padrão.
Impact: Sem controle de nível/destino; facilita vazar dados (ver AP-SEC-04).
Recommendation: RF-12 — `src/utils/logger.js` com níveis (`LOG_LEVEL`), mantendo a mensagem de boot.

### [LOW] AP-QUAL-05 — Magic numbers e strings de negócio
File: src/AppManager.js:21, 37, 46, 48, 68, 108; src/utils.js:6, 19-22
Description: Prefixo de aprovação `"4"`, status `'PAID'`/`'DENIED'` repetidos, `active = 1`, senha padrão `"123456"`, `10000`/`2`/`10` no "hash", porta `3000`.
Impact: Regra escondida e repetida; difícil de mudar com segurança.
Recommendation: RF-11 — `src/config/constants.js` (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `COURSE_ACTIVE`).

### [LOW] AP-QUAL-06 — Nomes ruins
File: src/AppManager.js:26, 29-33, 52, 89; src/utils.js:12, 17
Description: `u`, `e`, `p`, `cid`, `cc`, `enrId`, `c`, `self`; funções `badCrypto`, `logAndCache`; classe `AppManager` sem significado de domínio.
Impact: Leitura difícil.
Recommendation: Renomear internamente (`name`, `email`, `password`, `courseId`, `cardNumber`), mantendo os campos externos `usr`, `eml`, `pwd`, `c_id`, `card`.

### [LOW] AP-QUAL-07 — Código morto
File: src/utils.js:2-3, 5, 10, 25; src/AppManager.js:2, 104
Description: `config.dbUser`, `config.dbPass` e `config.smtpUser` nunca são usados (banco em memória, sem SMTP); `totalRevenue` é exportado e importado em `AppManager.js:2`, mas nunca usado; `globalCache` é exportado e nunca lido; a query da l.104 busca `email` sem usá-lo.
Impact: Ruído e segredos sem propósito no código.
Recommendation: Remover.

================================
Total: 19 findings
================================
```

**APIs deprecated:** nenhuma encontrada no código (`Buffer.from` e `express.json()` já são as formas modernas; sem `new Buffer`, `body-parser`, `url.parse`, `crypto.createCipher`).

**SQL injection (AP-SEC-02):** não encontrada — todas as queries com entrada usam placeholders `?`. O único resultado da busca (`src/AppManager.js:57`) é um template string passado como **valor** parametrizado.

## Evidência das verificações em execução (app original, porta 3000)

```
--- JSON malformado
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Error</title>
--- relatório (ordem)
[{"course":"Docker","revenue":0,"students":[]},{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}]
status: 200
--- card numérico

status: 000
processo MORREU
--- log do processo
Processando cartão 4111 na chave pk_live_1234567890abcdef
/Users/.../ecommerce-api-legacy/src/AppManager.js:46
                        let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
