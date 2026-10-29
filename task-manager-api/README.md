# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Estrutura

```
app.py            # create_app() (composition root) e entry point
seed.py           # dados de exemplo
config/           # settings (ambiente) e constantes
models/           # User, Task, Category e db
validators/       # validação de entrada
controllers/      # orquestração dos casos de uso
services/         # relatórios/estatísticas e notificações
routes/           # blueprints (método + path)
middlewares/      # erros e credencial de administrador
utils/            # datas
```

## Configuração

Copie `.env.example` para `.env` (ou exporte as variáveis). Principais:

- `SECRET_KEY`, `SMTP_USER`, `SMTP_PASSWORD`: segredos, sem valor padrão.
- `DEBUG` (padrão `false`), `HOST` (`0.0.0.0`), `PORT` (`5000`), `DATABASE_URL` (`sqlite:///tasks.db`).
- `ADMIN_TOKEN`: habilita definir/alterar o campo `role` em `POST/PUT /users` com o header `X-Admin-Token`. Sem ele, o `role` só pode ser o padrão (`user`) ou o valor atual; qualquer outro retorna 403.

Senhas passam a ser gravadas com scrypt; hashes MD5 antigos continuam válidos e são regravados no primeiro login.
