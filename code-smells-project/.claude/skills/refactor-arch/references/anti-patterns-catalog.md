# Referência — Catálogo de Anti-Patterns (Fase 2)

Cada entrada tem: **ID**, **severidade padrão**, **sinais de detecção** (o que
procurar, de forma acionável), **por que importa** e o **padrão de refatoração**
correspondente em `refactoring-playbook.md`.

Regras de severidade (escala do desafio):

- **CRITICAL** — falha grave de arquitetura/segurança: expõe dados sensíveis,
  impede o funcionamento correto ou anula a separação de responsabilidades.
- **HIGH** — violação forte de MVC/SOLID que dificulta muito manutenção e testes.
- **MEDIUM** — padronização, duplicação ou performance moderada.
- **LOW** — legibilidade, nomenclatura, magic numbers.

Ajuste a severidade ao contexto quando houver motivo claro (ex.: um segredo de
teste em projeto de brinquedo pode cair para HIGH), mas **não rebaixe** riscos
reais de segurança sem justificativa.

---

## CRITICAL

### AP-SEC-01 — Credenciais / segredos hardcoded
- **Sinais**: `SECRET_KEY = "..."`, senha/chave de API/token literais no código,
  strings como `pk_live_`, `password = "..."`, URIs com usuário:senha.
- **Por que**: segredo versionado vaza; não há como rotacionar por ambiente.
- **Refatoração**: RF-01 (config via ambiente).

### AP-SEC-02 — SQL Injection (query montada por concatenação)
- **Sinais**: `execute("... " + var)`, f-strings/template strings com input em
  SQL, `"... %s" % var` em SQL, `WHERE x = '" + valor + "'`.
- **Por que**: permite ler/alterar/apagar o banco e burlar autenticação.
- **Refatoração**: RF-02 (queries parametrizadas).

### AP-SEC-03 — Senha em texto puro ou hash fraco
- **Sinais**: senha gravada/comparada sem hash; `md5`/`sha1`; hashing caseiro;
  ausência de `bcrypt`/`scrypt`/`argon2`/`werkzeug.security`.
- **Por que**: vazamento do banco expõe as senhas; MD5/SHA1 são quebráveis.
- **Refatoração**: RF-08 (hashing seguro).

### AP-SEC-04 — Exposição de dados sensíveis (resposta ou log)
- **Sinais**: serializer/`to_dict` que inclui `password`/`senha`/token; `print`/
  `console.log` de cartão, senha, segredo; endpoint de health que devolve a
  `SECRET_KEY`.
- **Por que**: vaza dado sensível para o cliente ou para os logs.
- **Refatoração**: RF-13 (remover campos sensíveis da serialização/logs).

### AP-SEC-05 — Execução arbitrária / endpoint admin sem autenticação
- **Sinais**: endpoint que executa SQL/comando recebido no corpo; rota
  `/admin/...` destrutiva sem auth; `eval`/`exec` com input.
- **Por que**: backdoor direto ao banco/servidor.
- **Refatoração**: RF-15 (política de endpoints perigosos em
  `mvc-guidelines.md`: desligado por padrão, token vindo do ambiente,
  consulta somente-leitura).

### AP-ARCH-01 — God Class / God Module
- **Sinais**: um arquivo/classe que concentra conexão de banco, schema, rotas,
  regra de negócio e serialização; arquivos muito longos com responsabilidades
  múltiplas.
- **Por que**: impossível testar/alterar em isolamento; qualquer mudança
  arrisca tudo.
- **Refatoração**: RF-03 (separar em camadas).

---

## HIGH

### AP-ARCH-02 — Lógica de negócio na camada errada
- **Sinais**: regra de domínio (cálculo, precificação, fluxo) dentro do
  controller/rota, ou dentro do módulo de acesso a dados.
- **Por que**: acopla HTTP/SQL à regra; não testável isoladamente.
- **Refatoração**: RF-04 (mover para controller/serviço).

### AP-ARCH-03 — Estado global mutável / conexão global compartilhada
- **Sinais**: variáveis globais mutáveis (`globalCache`, contadores), conexão
  única de banco compartilhada entre requisições/threads
  (`check_same_thread=False`).
- **Por que**: estado compartilhado gera acoplamento e condições de corrida.
- **Refatoração**: RF-05 (instância injetada / conexão por requisição).

### AP-ARCH-04 — Acoplamento forte sem injeção de dependência
- **Sinais**: módulos que instanciam/importam diretamente suas dependências
  concretas; impossível trocar implementação em teste.
- **Por que**: dificulta teste e evolução.
- **Refatoração**: RF-05/RF-03 (injeção de dependência, composição no entry point).

### AP-SEC-06 — Debug/stack traces habilitados por padrão
- **Sinais**: `debug=True`, `app.config["DEBUG"]=True`, `DEBUG` ligado no
  código, stack trace devolvido ao cliente.
- **Por que**: expõe internals e, no Flask, habilita console com execução remota.
- **Refatoração**: RF-01 (vir de ambiente, default seguro).

---

## MEDIUM

### AP-PERF-01 — Queries N+1
- **Sinais**: query dentro de laço; para cada registro de uma lista, nova query
  de relacionamento; `len(obj.relacionamento)` em laço.
- **Por que**: número de queries cresce com os dados.
- **Refatoração**: RF-06 (JOIN / eager loading).

### AP-QUAL-01 — Tratamento de erro genérico / ausência de handler central
- **Sinais**: `except Exception` ou `except:` repetidos, retornando `str(e)` ao
  cliente; cada handler trata erro à mão; `err` ignorado em callbacks;
  mensagem de exceção devolvida na resposta (inclusive em rotas de admin).
- **Por que**: esconde causa real, vaza mensagem interna, comportamento
  inconsistente.
- **Refatoração**: RF-07 (handler/middleware central).

### AP-QUAL-02 — Validação de entrada ausente ou fraca / invariantes de negócio
- **Sinais de validação**: payload usado sem validar tipo/obrigatoriedade;
  default silencioso para campo ausente (ex.: senha vira valor fixo); formato
  não checado; corpo ausente ou JSON inválido virando erro 500; regras
  diferentes entre criar e atualizar o mesmo recurso.
- **Sinais de invariantes de negócio** (procure ativamente, com exemplos
  concretos do fluxo):
  - quantidades, preços ou valores aceitos como `<= 0` ou negativos;
  - estoque/saldo/limite checado **item a item** sem somar itens repetidos do
    mesmo recurso no mesmo pedido;
  - operação que pode deixar estoque, saldo ou total negativo;
  - campo numérico aceito como string (e usado em conta ou em SQL);
  - atualização/exclusão de recurso inexistente respondendo sucesso;
  - registro criado antes de uma etapa que pode falhar (ex.: usuário criado
    mesmo com pagamento recusado), sem transação.
- **Por que**: dados inválidos entram no sistema; regras de negócio são
  burladas; comportamento inseguro.
- **Refatoração**: RF-14 (camada de validação) + RF-04 (regra no serviço, com
  transação).

### AP-QUAL-03 — Duplicação de código
- **Sinais**: mesmo bloco de mapeamento/validação/serialização copiado em vários
  pontos; métodos do model reimplementados inline.
- **Por que**: mudança precisa ser feita em N lugares; divergência.
- **Refatoração**: RF-04/RF-13 (extrair para função/serviço/serializer).

### AP-DEPR-01 — APIs deprecated
- **Sinais**: uso de APIs obsoletas. Tabela de substituição:

  | Deprecated | Equivalente moderno |
  |---|---|
  | `datetime.utcnow()` (Python) | `datetime.now(timezone.utc)` |
  | `Model.query.get(id)` (SQLAlchemy 2.x) | `db.session.get(Model, id)` |
  | `Query.<legacy>` do SQLAlchemy 1.x | API 2.0 (`select(...)`, `session.execute`) |
  | `new Buffer(x)` (Node) | `Buffer.from(x)` |
  | `body-parser` (Express) | `express.json()` / `express.urlencoded()` |
  | `url.parse()` (Node) | `new URL()` |
  | `crypto.createCipher` (Node) | `crypto.createCipheriv` |

- **Por que**: quebra em versões futuras; muitas vezes emite warning.
- **Refatoração**: RF-10 (trocar pelo equivalente moderno).

### AP-ARCH-05 — Callback hell / fluxo assíncrono aninhado
- **Sinais**: callbacks aninhados em vários níveis (sqlite3, fs); controle de
  fluxo manual com contadores; erro tratado em cada nível.
- **Por que**: ilegível, não testável, sem transação; erro no meio deixa dados
  parciais.
- **Refatoração**: RF-09 (async/await + Promises).

---

## LOW

### AP-QUAL-04 — `print` / `console.log` como logging
- **Sinais**: `print(...)`/`console.log(...)` para registrar eventos no lugar de
  um logger.
- **Refatoração**: RF-12 (logger).

### AP-QUAL-05 — Magic numbers e enumerações soltas
- **Sinais**: números/strings de negócio no meio da lógica (faixas, taxas,
  listas de status válidas) sem constante nomeada.
- **Refatoração**: RF-11 (constantes nomeadas / config).

### AP-QUAL-06 — Nomes ruins
- **Sinais**: variáveis de uma letra sem contexto (`u`, `e`, `p`), campos
  abreviados sem padrão (`usr`, `eml`).
- **Refatoração**: renomear para nomes descritivos (sem mudar o contrato
  externo de request/response).

### AP-QUAL-07 — Imports / código morto
- **Sinais**: imports não usados, funções/módulos nunca chamados, dependências
  declaradas e não utilizadas.
- **Refatoração**: remover (limpeza).
