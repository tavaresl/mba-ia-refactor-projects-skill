# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

Usuários de demonstração (senhas gravadas com hash): `admin@loja.com` / `admin123`, `joao@email.com` / `123456`, `maria@email.com` / `senha123`.

## Estrutura (MVC)

```
app.py            # composition root (create_app) e boot
config/           # settings (variáveis de ambiente) e constantes
db/               # conexão por requisição e schema/seed
models/           # acesso a dados (SQL parametrizado)
services/         # regras de negócio (pedido, relatório, auth, notificação)
validators/       # validação dos payloads
controllers/      # orquestração dos casos de uso
routes/           # métodos + paths (Blueprints)
middlewares/      # erro central e autenticação admin
```

## Configuração (variáveis de ambiente — ver `.env.example`)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por boot | chave da aplicação |
| `DEBUG` | `false` | debug do Flask |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | endereço do servidor |
| `DB_PATH` | `loja.db` | arquivo SQLite |
| `APP_ENV` | `producao` | valor exibido em `/health` |
| `ADMIN_TOKEN` | vazio | habilita `/admin/*` (header `X-Admin-Token`); vazio = 403 |

`POST /admin/query` aceita apenas consultas de leitura; `POST /admin/reset-db` apaga os dados (só com token).
