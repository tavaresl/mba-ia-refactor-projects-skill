# Referência — Guidelines de Arquitetura MVC (Fase 2 plano e Fase 3)

O alvo é o padrão **MVC** com separação clara de responsabilidades e um
**composition root** (entry point) que monta tudo. As regras são agnósticas de
linguagem; a seção final mostra como mapear em Flask e Express.

## Camadas e responsabilidades

```
src/ (ou raiz)
├── config/          # configuração e segredos (via ambiente)
├── models/          # dados e persistência (uma entidade por arquivo)
├── views/ ou routes/# definição de rotas e (de)serialização de entrada/saída
├── controllers/     # orquestra o fluxo de cada caso de uso
├── services/        # regra de negócio reutilizável (opcional, quando há domínio)
├── middlewares/     # transversais: erro, auth, logging
└── app.(py|js)      # entry point / composition root
```

### Config (`config/`)
- Lê segredos e parâmetros de **variáveis de ambiente**, com default seguro.
- Nenhum segredo hardcoded. Fornece um `.env.example`.

### Models (`models/`)
- Representam dados e falam com o banco (queries, ORM).
- **Podem** conter regras muito ligadas ao dado (validação de invariantes do
  próprio modelo).
- **Não** conhecem HTTP (request/response) nem orquestram casos de uso.
- Serialização (`to_dict`) **não** expõe campos sensíveis (senha/hash/token).

### Views / Routes (`routes/`)
- Declaram `método + path` e ligam ao controller.
- Fazem (de)serialização e validação de forma da entrada.
- **Não** contêm regra de negócio nem SQL.

### Controllers (`controllers/`)
- Orquestram o caso de uso: recebem dados já validados, chamam models/services,
  montam a resposta.
- **Não** montam SQL direto nem conhecem detalhes de transporte além do
  necessário.

### Services (`services/`) — quando fizer sentido
- Regra de negócio reutilizável e independente de HTTP (ex.: criar pedido,
  calcular relatório, enviar notificação).
- Útil quando a lógica é usada por mais de um controller ou é complexa.

### Middlewares (`middlewares/`)
- **Error handler central**: captura exceções e devolve resposta padronizada,
  sem vazar stack trace/mensagem interna.
- Auth, logging e CORS quando aplicável.

### Entry point / composition root
- Cria a app, carrega config, registra rotas e middlewares, injeta
  dependências. É o único lugar que "conhece" todas as peças.
- Mantém o **mesmo comando de boot** de antes.

## Direção das dependências

```
routes  ->  controllers  ->  services  ->  models  ->  (banco)
                     \-------------------->/
config e middlewares são transversais; o entry point compõe tudo.
```

Nunca na direção contrária: model não importa controller; controller não importa
rota.

## Mapeamento por stack

### Flask (Python)
- `create_app()` factory no entry point; `Blueprint` por domínio nas rotas.
- Config via `os.environ` / `python-dotenv`, `app.config.from_...`.
- Error handler com `@app.errorhandler`.
- Conexão: por requisição (`g`/teardown) ou `Flask-SQLAlchemy`, nunca global
  compartilhada com `check_same_thread=False`.

### Express (Node.js)
- `Router` por domínio nas rotas; controllers como funções/módulos.
- Config via `process.env` (+ `.env`).
- Error handler como middleware de 4 args `(err, req, res, next)`.
- Acesso a dados em um módulo/repositório; usar `async/await` com uma camada
  de Promise sobre o driver (evitar callbacks aninhados).

## Preservação do contrato (regra de ouro da Fase 3)

A refatoração **reorganiza**, não **reescreve o comportamento**:

- Mesmos paths e métodos das rotas (lista da Fase 1).
- Mesmos campos de request e de response (inclusive nomes "feios" do contrato
  externo, como `usr`/`eml`, que podem ser renomeados **internamente** mas
  continuam aceitos na entrada/saída).
- Mesmo comando de boot.

Mudanças de comportamento só são aceitáveis quando corrigem um problema de
segurança (ex.: parar de devolver a senha na resposta) e **devem ser
documentadas** explicitamente no fim da Fase 3.
