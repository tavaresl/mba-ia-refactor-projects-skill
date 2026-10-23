# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (porta configurável por `PORT`). O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Variáveis de ambiente (veja `.env.example`):

| Variável | Descrição |
| --- | --- |
| `PORT` | Porta HTTP (padrão `3000`) |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento |
| `ADMIN_TOKEN` | Token das rotas administrativas. Sem ele, `GET /api/admin/financial-report` e `DELETE /api/users/:id` respondem `403` |
| `LOG_LEVEL` | `debug`, `info` (padrão), `warn` ou `error` |

As rotas administrativas exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`:

```bash
ADMIN_TOKEN=meu-token npm start
curl -H "X-Admin-Token: meu-token" http://localhost:3000/api/admin/financial-report
```

## Estrutura

```
src/
├── app.js          # composition root
├── config/         # variáveis de ambiente e constantes
├── db/             # conexão SQLite (Promises, transações) e schema/seed
├── models/         # acesso a dados
├── services/       # regras de negócio (checkout, relatório, usuário, hash, gateway)
├── controllers/    # orquestração de cada caso de uso
├── routes/         # método + path -> controller
├── validators/     # validação de entrada
├── middlewares/    # auth admin, erros
└── utils/          # logger
```
