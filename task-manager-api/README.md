# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

A configuração vem de variáveis de ambiente (ou de um `.env` na raiz; veja `.env.example`): `SECRET_KEY`, `DATABASE_URL`, `DEBUG` (padrão `false`), `HOST`, `PORT` (padrão `5000`) e `SMTP_*`. Sem `SECRET_KEY`, a aplicação gera uma chave aleatória a cada execução.

## Estrutura

`config/` (settings), `models/` (dados), `routes/` (rotas finas), `validators/` (validação de entrada), `controllers/` (casos de uso), `services/` (regras de relatório, autenticação, notificação), `middlewares/` (tratamento central de erros) e `app.py` (`create_app`, ponto de composição).
