# Plano de Resolução — Desafio `refactor-arch`

Plano para resolver o desafio descrito em [`ENUNCIADO.md`](ENUNCIADO.md). São 8 etapas (0 a 7). Cada uma tem passos e uma lista de verificação objetiva para saber quando está pronta.

## Notas do ambiente

1. **A porta 5000 está ocupada.** O Receptor AirPlay do macOS (processo ControlCenter) usa a porta 5000, que é a porta dos projetos 1 e 3. Os apps originais vão falhar com "Address already in use". Desligue em Ajustes do Sistema › Geral › AirDrop e Handoff › Receptor AirPlay durante o desafio.
2. **O Python do sistema é o 3.9.6.** Ele roda os `requirements.txt`, mas tem dois efeitos:
   - O aviso de que `datetime.utcnow()` está obsoleto só aparece a partir do 3.12.
   - O código refatorado não pode usar recursos do 3.10 em diante (`str | None`, `match`, `datetime.UTC`).

   A Fase 1 da skill precisa detectar a versão do runtime, e a Fase 3 precisa respeitá-la. Use um venv por projeto.
3. **Node 26 + `sqlite3` (módulo nativo).** Confirme na Etapa 0 que o `npm install` funciona, antes que uma falha dele pareça culpa da skill.
4. **Git:** o `README.md` da raiz foi substituído pelo `ENUNCIADO.md`. O README novo é escrito na Etapa 7. O remote `tavaresl/mba-ia-refactor-projects-skill` precisa estar público na entrega.

---

## Etapa 0 — Baseline: como os apps respondem hoje

O enunciado exige que os endpoints originais continuem respondendo, e isso só se prova comparando com o comportamento atual. Sem essa referência, quem avalia a refatoração é o próprio agente que a fez.

**Passos**

- Criar um venv e instalar as dependências nos dois projetos Python. Rodar `npm install` no projeto Node.
- Subir cada app original. No P3, rodar `python seed.py` antes.
- Escrever um smoke test por projeto (ex.: `scripts/smoke-p1.sh`) que chama **todas** as rotas e grava o status e o corpo de cada resposta:
  - P1: 19 rotas (16 `add_url_rule` + `/`, `/admin/reset-db` e `/admin/query`)
  - P2: as 4 requisições do `api.http` (3 rotas)
  - P3: 22 rotas (tasks, users, login, reports, categories, `/health` e `/`)
- Colocar as rotas destrutivas (DELETE, reset-db) no fim do script.
- Exemplo de linha:

  ```bash
  curl -s -o /dev/null -w "%{http_code} GET /produtos\n" "$BASE/produtos"
  ```

**Como avaliar**

- [x] Os 3 apps sobem e o script roda até o fim.
- [x] Toda rota tem um status registrado. Um 4xx ou 5xx de hoje também faz parte do baseline.
- [x] Rodar duas vezes, recriando o banco entre elas, dá os mesmos status e as mesmas chaves no JSON. Compare com `jq 'keys'` e não pelo corpo inteiro, porque timestamps e ids mudam.

**Resultado (23/10/2026)**

- Smoke test: `scripts/smoke.py` (só biblioteca padrão, Python 3.9+) + uma spec por projeto em `scripts/specs/`. O script sobe o app, chama as rotas, derruba o app e grava em `evidencias/baseline/`:
  - `pN.txt`: resposta completa de cada requisição, com datas mascaradas
  - `pN.contract.txt`: status + formato do JSON, uma linha por requisição
  - `pN.server.log`: saída do servidor
- Cobertura: P1 com 31 requisições (19 rotas), P2 com 8 (3 rotas), P3 com 35 (22 rotas). Todas devolveram o status esperado, e uma segunda rodada saiu idêntica no `diff`.
- Como a porta 5000 está ocupada pelo AirPlay, o código original foi iniciado com `flask --app app run --port 5001` (P1) e `--port 5002` (P3), sem alterar o código. O P2 usa `npm start` na porta 3000.
- Para comparar depois da refatoração:

  ```bash
  python3 scripts/smoke.py scripts/specs/p1-code-smells.json --out evidencias/depois/p1 --start ".venv/bin/python app.py"
  diff -u evidencias/baseline/p1.txt evidencias/depois/p1.txt
  ```

  O script passa a porta na variável `PORT`, então o app refatorado deve lê-la da config.

---

## Etapa 1 — Análise manual (Requisito 1)

**Passos**

- Ler os 3 projetos inteiros: cerca de 2.100 linhas no total (P1 ≈ 780, P2 ≈ 180, P3 ≈ 1.150).
- Para cada achado, registrar severidade, nome, `arquivo:linha`, evidência e por que importa.
- Mirar em 8 a 12 achados por projeto, acima do mínimo de 5. Essa lista vira o gabarito da skill.

**Achados iniciais de uma passada rápida** (confira as linhas):

- **P1 — code-smells-project:**
  - SQL montado por concatenação em `models.py:28, 49, 58-60, 68, 92, 110, 128`
  - `SECRET_KEY` e `DEBUG=True` fixos no código em `app.py:7-8`
  - `/admin/query` executa SQL arbitrário sem autenticação (`app.py:59`)
  - Conexão global em `database.py:8`
  - Uso de `print` como log e como "notificação" em `controllers.py:208-210`
- **P2 — ecommerce-api-legacy:**
  - Credenciais e chave de pagamento em `utils.js:2-4`
  - Cartão e chave de pagamento aparecem no log em `AppManager.js:45`
  - Hash de senha feito à mão em `utils.js:17-23`
  - Estado global em `utils.js:9-10`
  - God class `AppManager`
  - Consultas N+1 em `AppManager.js:83-106`
  - Callbacks aninhados em vários níveis (callback hell)
  - Nomes como `usr`, `eml`, `c_id`
- **P3 — task-manager-api:**
  - Segredos em `app.py:13` e em `services/notification_service.py:10`
  - Senha com MD5 em `models/user.py:29`, devolvida pelo `to_dict` (`models/user.py:21`)
  - Regras de negócio dentro das rotas, em arquivos de 200 a 300 linhas
  - Consultas N+1 em `routes/task_routes.py:42, 51`
  - `except:` sem tipo
  - APIs obsoletas: `Model.query.get()` e `datetime.utcnow()`
  - Imports sem uso em `app.py:7`

**Como avaliar**

- [ ] Cada projeto tem ≥5 achados, com ≥1 CRITICAL/HIGH, ≥2 MEDIUM e ≥2 LOW.
- [ ] Cada `arquivo:linha` confere com `sed -n '<linha>p' <arquivo>`.
- [ ] Cada achado tem justificativa ligada à escala de severidade do enunciado.
- [ ] Existe uma matriz que liga cada achado a um anti-pattern. Ela é a entrada da Etapa 3.

---

## Etapa 2 — Estrutura da skill (Requisito 2)

```
code-smells-project/.claude/skills/refactor-arch/
├── SKILL.md                       # orquestra as 3 fases
└── references/
    ├── project-analysis.md        # área 1: heurísticas de detecção
    ├── anti-patterns-catalog.md   # área 2: catálogo + severidade
    ├── audit-report-template.md   # área 3: formato do relatório
    ├── mvc-guidelines.md          # área 4: camadas e responsabilidades
    └── refactoring-playbook.md    # área 5: transformações antes/depois
```

**Decisões para o SKILL.md**

- **Frontmatter:** `name: refactor-arch` e uma `description` clara. Considere `disable-model-invocation: true`, para que a skill só rode quando você chamar `/refactor-arch`, já que ela reescreve código. Confirme esse campo na documentação de Skills.
- **Fase 1:**
  - Detectar linguagem, framework, versão do runtime, banco, entry point, comando de boot e porta.
  - **Inventariar todas as rotas.** A Fase 3 usa essa lista para validar.
  - Inferir o domínio e classificar a arquitetura (monolito, camadas parciais, MVC).
- **Fase 2:**
  - Imprimir o relatório no template, ordenado de CRITICAL a LOW.
  - Terminar com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **encerrar o turno**, com uma regra explícita: nenhuma escrita em arquivo antes de um "y".
  - Para salvar o relatório, peça ao Claude na mesma sessão para gravá-lo em `../reports/`.
- **Fase 3:**
  - Aplicar o playbook achado por achado.
  - Manter o **contrato externo** (paths, métodos, campos do body, formato da resposta) e o **comando de boot original** (`python app.py`, `npm start`).
  - Depois validar em ciclo: instalar dependências, subir o app em background, chamar as rotas do inventário, conferir com grep que não sobrou nenhum sinal do catálogo, corrigir e repetir.
- **Excluir da análise** `.claude/`, `node_modules/`, `venv/`, `__pycache__/`, `*.db` e lockfiles. Sem isso, a skill audita os exemplos "antes" do próprio playbook, que contêm SQL injection e credenciais de propósito.
- **Projeto já organizado (P3):** melhorar o que existe em vez de reescrever do zero.

**Decisão pendente:** o que fazer com rotas perigosas como `/admin/query` (P1) e o `DELETE /api/users/:id` sem autenticação (P2). Recomendação: manter a rota respondendo, mas desligada por padrão via config ou protegida, e documentar a mudança. Remover a rota quebra o critério "endpoints originais respondendo".

**Como avaliar**

- [ ] Ao digitar `/` no `claude` dentro do P1, `refactor-arch` aparece.
- [ ] As 5 áreas têm um arquivo ou seção identificável.
- [ ] A skill não cita arquivos, tabelas ou rotas dos 3 projetos. Se citar, está acoplada a eles.

---

## Etapa 3 — Conteúdo das referências

- **project-analysis.md:**
  - Manifesto → linguagem (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`…) e dependência → framework
  - Sinais de banco (`sqlite3`, `SQLAlchemy`, `sequelize`, `:memory:`)
  - Onde encontrar rotas (`@app.route`, `add_url_rule`, `Blueprint`, `app.get`, `router.post`)
  - Regra para contar arquivos e linhas
  - Como classificar a arquitetura
- **anti-patterns-catalog.md:** 12 a 15 entradas (mínimo 8). Cada uma tem ID, severidade padrão, sinais concretos (regex mais um exemplo em Python e outro em JS), critérios para subir ou baixar a severidade e o padrão correspondente no playbook.
  - **CRITICAL:** credenciais no código · SQL injection · God class · senha em texto puro ou hash fraco · dados sensíveis em resposta ou log · rota de admin sem autenticação
  - **HIGH:** regra de negócio na rota · estado global mutável · acoplamento sem injeção de dependência · SQL fora do model · debug ligado no código
  - **MEDIUM:** N+1 · falta de validação · `except` genérico · callback hell · duplicação · **APIs obsoletas**
  - **LOW:** magic numbers · nomes ruins · `print`/`console.log` como log · imports e dependências sem uso
  - **APIs obsoletas:** a entrada precisa de uma tabela "obsoleto → moderno", por exemplo:
    - `datetime.utcnow()` → `datetime.now(timezone.utc)`
    - `Model.query.get(id)` → `db.session.get(Model, id)`
    - `new Buffer()` → `Buffer.from()`
    - `body-parser` → `express.json()`
- **audit-report-template.md:** o formato exato do enunciado (cabeçalho, Summary, blocos `### [SEV] Nome` com File/Description/Impact/Recommendation, Total e a pergunta final). Inclui as regras `File: caminho:inicio-fim`, "ordenar por severidade" e "agrupar ocorrências iguais num bloco".
- **mvc-guidelines.md:**
  - Pastas `config/`, `models/`, `views|routes/`, `controllers/` e `middlewares/`, mais o composition root
  - O que cada camada pode e não pode fazer, e a direção das dependências
  - Onde `services/` entra
  - Como cada stack implementa isso: Flask com Blueprints e `create_app()`; Express com `Router` e middleware de erro `(err, req, res, next)`
  - Config via variável de ambiente, com default igual ao valor original, mais um `.env.example`
- **refactoring-playbook.md:** 10 a 14 padrões (mínimo 8), cada um ligado a um anti-pattern e com código antes/depois:
  - config para env
  - query parametrizada
  - quebrar a God class
  - regra de negócio da rota para o controller
  - estado global para instância injetada
  - N+1 para JOIN ou eager loading
  - error handler central
  - hash de senha com biblioteca padrão (`werkzeug.security`, `crypto.scrypt`)
  - callbacks para async/await
  - API obsoleta para a moderna
  - constantes no lugar de magic numbers
  - `print` para logging
  - validação de entrada

**Como avaliar**

- [ ] O catálogo tem ≥8 entradas, cobre as 4 severidades e inclui APIs obsoletas.
- [ ] O playbook tem ≥8 padrões, todos com antes e depois.
- [ ] Todo achado da Etapa 1 cai numa entrada do catálogo, e toda entrada aponta para um padrão do playbook.
- [ ] Os exemplos "depois" rodam sem erro.
- [ ] **A skill foi commitada antes de rodar.** Assim, se uma refatoração sair ruim, `git restore <proj> && git clean -fd <proj>` volta o código ao original sem apagar a skill.

---

## Etapa 4 — Projeto 1 (code-smells-project)

**Passos**

1. Rodar `cd code-smells-project && claude "/refactor-arch"` no modo interativo. O `claude -p` não pausa para a confirmação.
2. Na primeira rodada, responder **n** e conferir com `git status` que nenhum arquivo mudou.
3. Fase 1 esperada: Python, Flask 3.1.1, flask-cors, e-commerce, 4 arquivos, tabelas `produtos`, `usuarios`, `pedidos` e `itens_pedido`, monolito.
4. Na Fase 2, pelo menos 5 dos seus achados precisam aparecer, com as linhas certas. Salvar em `reports/audit-project-1.md`.
5. Rodar de novo e responder **y**.
6. Validar por fora: apagar o `loja.db`, subir o app com o comando original e comparar o smoke test com o baseline.
7. Commitar o código refatorado junto com o relatório.

**Como avaliar**

- [ ] Checklist de validação do enunciado, item por item.
- [ ] O smoke test bate com o baseline em status e chaves JSON. Só podem diferir as mudanças de segurança documentadas.
- [ ] O grep pelos sinais do catálogo (`minha-chave`, SQL montado com `+`) não encontra nada.
- [ ] Log do boot e saída do smoke test guardados para o README.

**Se falhar:** ajuste as referências, não o código à mão. Depois restaure o projeto e rode de novo. De 2 a 4 rodadas é normal.

---

## Etapa 5 — Projeto 2 (ecommerce-api-legacy)

**Passos**

- Copiar a skill e rodar como na Etapa 4:

  ```bash
  rsync -a --delete code-smells-project/.claude/skills/refactor-arch/ ecommerce-api-legacy/.claude/skills/refactor-arch/
  ```

- Fase 1 esperada: JavaScript/Node, Express 4.x, sqlite3 em memória, LMS com checkout, 3 arquivos, tabelas `users`, `courses`, `enrollments`, `payments` e `audit_logs`.
- **Riscos:**
  - A troca de callbacks por async/await não pode mudar a ordem dos passos do checkout.
  - Os campos `usr`, `eml`, `pwd`, `c_id` e `card` fazem parte do contrato e precisam continuar aceitos.

**Como avaliar**

- [ ] Checklist de validação do enunciado, item por item.
- [ ] As 4 requisições do `api.http` dão o mesmo resultado do baseline: checkout aprovado, checkout recusado, relatório e delete.
- [ ] O JSON do relatório financeiro é idêntico ao do baseline (compare com `jq -S`). Isso prova que a correção do N+1 não mudou o resultado.
- [ ] `grep -rn "pk_live\|senha_super" src` não encontra nada, e o número do cartão não aparece em nenhum log.
- [ ] `reports/audit-project-2.md` salvo e commitado.

---

## Etapa 6 — Projeto 3 (task-manager-api)

**Passos**

- Copiar a skill com o mesmo `rsync`, rodar o `seed.py` e depois a skill.
- Fase 1 esperada: Python, Flask 3.0.0 + Flask-SQLAlchemy, SQLite, Task Manager, arquitetura em camadas parciais.
- A Fase 2 precisa encontrar problemas mesmo com essa organização: MD5, senha no `to_dict`, segredos no código, regra de negócio nas rotas, N+1, `except:` e APIs obsoletas.
- A Fase 3 deve ser incremental: aproveitar `models/`, deixar as rotas finas, criar `controllers/`, manter `services/` e adicionar config e error handler.
- **Atenção:** se o hash de senha mudar, o `seed.py` precisa mudar junto. Apague o `tasks.db` e rode o seed de novo antes de validar.

**Como avaliar**

- [ ] Checklist de validação do enunciado, item por item.
- [ ] As 22 rotas batem com o baseline, e `POST /login` funciona com um usuário do seed.
- [ ] `grep -rnE "query\.get\(|utcnow|md5" --include=*.py .` não encontra nada.
- [ ] `git diff --stat` mostra uma melhoria incremental, sem reescrita total.
- [ ] `reports/audit-project-3.md` salvo e commitado.

---

## Etapa 7 — Consolidação e README

**Passos**

- **Cópias da skill:** as 3 precisam ser idênticas (`diff -r` entre elas sem saída). Edite sempre num lugar só e propague com `rsync`.
- **Se a skill mudou muito depois do P1 ou do P2:** rode a versão final a partir do código original, por exemplo num `git worktree` do commit `6d1ce62`.
- **README:**
  - **A) Análise Manual:** tabelas da Etapa 1.
  - **B) Construção da Skill:** decisões das Etapas 2 e 3, o catálogo com o motivo de cada item, como garantiu que a skill não depende da stack e os problemas das iterações.
  - **C) Resultados:** contagem por severidade, árvore antes/depois (o antes sai de `git ls-tree -r --name-only 6d1ce62 <proj>`), os 3 checklists, os logs e uma comparação entre as stacks.
  - **D) Como Executar:** pré-requisitos, comandos e como validar (scripts de smoke test).
- **Arquivos do repositório:**
  - `.env` fica fora do git e o `.env.example` entra.
  - `*.db`, `node_modules/` e `venv/` não podem ser commitados.
  - Decidir se o `ENUNCIADO.md` e este `PLANO.md` ficam no repositório.
- Fazer o push e conferir a visibilidade com `gh repo view --json visibility`.

**Como avaliar**

- [ ] A estrutura bate com a árvore do enunciado.
- [ ] A tabela dos critérios de aceite fecha 3/3 em todas as linhas:

  | Critério | P1 | P2 | P3 |
  |---|---|---|---|
  | Fase 1 detecta a stack | | | |
  | ≥5 findings | | | |
  | ≥1 CRITICAL/HIGH | | | |
  | App funciona após a refatoração | | | |

- [ ] **Teste final:** clonar o repositório numa pasta temporária e seguir só o README. Se tudo funcionar a partir do zero, a entrega está pronta.
