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

## Módulos de apoio

Validação de entrada e exceções da aplicação ficam **dentro** da estrutura,
nunca soltos na raiz:

- validação: `validators/` (ou junto das rotas, ex.: `routes/validators.py`);
- exceções da aplicação e tradução para HTTP: `middlewares/` (ex.:
  `middlewares/errors.py`) ou um pacote `exceptions/`.

A raiz fica só com o entry point e os arquivos de projeto (manifesto,
`.env.example`, README).

## Política de endpoints perigosos (obrigatória)

Vale para rotas que executam SQL/comando arbitrário, apagam ou reiniciam dados,
ou expõem operações administrativas sem autenticação:

1. **A rota continua existindo** (contrato), mas fica **desligada por padrão**.
2. Só funciona quando um token for configurado no ambiente (ex.:
   `ADMIN_TOKEN`) e enviado num header (ex.: `X-Admin-Token`), comparado em
   tempo constante. Sem token configurado, ou com token errado: **403**.
3. Consulta arbitrária (ex.: "executar SQL"): conexão **somente-leitura**;
   escrita é recusada com 400. Nunca devolva a mensagem do banco na resposta.
4. Operações destrutivas (reset, limpeza): permitidas só com o token, com SQL
   fixo e log do evento.
5. **Remoção** da rota só se o usuário pedir explicitamente.
6. Sempre: listar no plano como mudança intencional, documentar a variável no
   `.env.example` e validar **sem** token (403) e **com** token.

## Respostas de erro

- O handler central reproduz o formato de erro **original** de cada rota (mesmos
  campos, mesmas mensagens). Não acrescente nem remova campos.
- Nunca inclua a mensagem da exceção, stack trace ou detalhe do banco na
  resposta — nem para administradores. O detalhe vai para o log.

## Preservação do contrato (regra de ouro da Fase 3)

A refatoração **reorganiza**, não **reescreve o comportamento**:

- Mesmos paths e métodos das rotas (lista da Fase 1).
- Mesmos campos de request e de response (inclusive nomes "feios" do contrato
  externo, como `usr`/`eml`, que podem ser renomeados **internamente** mas
  continuam aceitos na entrada/saída).
- Mesmo comando de boot. A porta passa a vir de config/ambiente (`PORT`),
  mantendo como padrão o valor original.
- Mesmos valores padrão de configuração que aparecem nas respostas (ex.: um
  campo `ambiente` que valia `"producao"` continua `"producao"` por padrão).
- Mesmas mensagens de sucesso e de erro, palavra por palavra — inclusive
  mensagens estranhas do original (ex.: um texto de confirmação que admite um
  bug). Corrigir o texto é recomendação para o relatório, não para o código.

### Preservação de dados

- **Seeds e dados de demonstração** mantêm os valores documentados, inclusive
  credenciais de exemplo (ex.: o login do admin de teste continua funcionando
  com a mesma senha). Pode mudar só a forma de armazenar (ex.: com hash).
- **Credenciais existentes continuam válidas** quando o algoritmo de hash muda:
  migre os hashes antigos (RF-08). Nunca exija recriar o banco ou rodar o seed
  de novo para o login voltar a funcionar.
- **Registros persistidos não são apagados nem alterados como efeito
  colateral** de uma correção (ex.: excluir pagamentos, matrículas ou pedidos
  junto com um usuário apaga histórico financeiro). Registros órfãos são um
  finding de integridade; a correção que exigiria apagar dados vai para
  "Not addressed", com a recomendação (ex.: exclusão lógica).
- **Segredos nunca vão para log ou resposta**, inclusive os gerados na hora
  (ex.: uma senha aleatória de admin). Se for preciso gerar um segredo, exija-o
  por variável de ambiente ou mantenha o valor documentado do seed.

### Mudanças de comportamento aceitas

Só duas categorias, sempre **listadas no plano** antes da execução e
**confirmadas** pela comparação com o baseline (`validation-protocol.md`):

1. **Segurança**: parar de expor dados sensíveis, fechar injeção, proteger
   endpoints perigosos (política acima).
2. **Rejeição de entrada claramente inválida** que hoje é aceita ou vira erro
   500 (quantidade negativa, tipo errado, corpo ausente ou malformado),
   respondendo 4xx com o formato de erro original da rota.

Qualquer outra mudança — nova regra de negócio, texto diferente, efeito
colateral novo, ordem diferente de resultados — é regressão, ou fica em
"Not addressed" com a recomendação.
