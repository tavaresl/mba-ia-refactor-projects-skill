# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC (skill `refactor-arch`).

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (`admin@loja.com`/`admin123`, `joao@email.com`/`123456`, `maria@email.com`/`senha123`; senhas gravadas com hash).

## Configuração (variáveis de ambiente, veja `.env.example`)

`SECRET_KEY`, `DEBUG` (padrão `false`), `HOST`, `PORT`, `DB_PATH`, `APP_ENV`, `ADMIN_TOKEN`.

## Endpoints administrativos

`POST /admin/reset-db` e `POST /admin/query` ficam **desligados** (403) até `ADMIN_TOKEN` ser definido. Com o token, envie o header `X-Admin-Token`. `/admin/query` aceita apenas consultas `SELECT`.

## Estrutura

```
app.py          composition root (create_app)
config/         settings (ambiente) e constants
db/             conexão por requisição, schema, seed e migração de senhas
models/         SQL parametrizado por entidade
services/       regras de negócio (pedido, relatório, auth, notificação)
controllers/    orquestração dos casos de uso
routes/         Blueprints (paths e métodos)
validators/     validação dos payloads
middlewares/    tratamento central de erros e autenticação admin
```
