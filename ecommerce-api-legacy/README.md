# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (ou na porta de `PORT`). O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

Veja `.env.example`.

| Variável              | Descrição                                                                 |
| --------------------- | ------------------------------------------------------------------------- |
| `PORT`                | Porta HTTP (padrão 3000)                                                  |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento (sem valor padrão; nunca é logada)          |
| `ADMIN_TOKEN`         | Token das rotas administrativas, enviado em `X-Admin-Token`. Vazio = 403  |
| `LOG_LEVEL`           | `debug`, `info`, `warn` ou `error` (padrão `info`)                        |

## Rotas

| Método   | Path                           | Observação                         |
| -------- | ------------------------------ | ---------------------------------- |
| `POST`   | `/api/checkout`                | Público                            |
| `GET`    | `/api/admin/financial-report`  | Exige `X-Admin-Token`              |
| `DELETE` | `/api/users/:id`               | Exige `X-Admin-Token`              |

## Estrutura

```
src/
├── app.js            # composition root
├── config/           # env, constantes, logger
├── db/               # conexão (Promises + transação) e schema/seed
├── models/           # acesso a dados por entidade
├── services/         # regra de negócio (checkout, relatório, usuário, hash, gateway)
├── controllers/      # orquestram cada caso de uso
├── routes/           # método + path -> controller
├── validators/       # validação de entrada
├── middlewares/      # auth admin, validação, erro central
└── exceptions/       # AppError
```
