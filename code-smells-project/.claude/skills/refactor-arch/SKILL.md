---
name: refactor-arch
description: >-
  Audita e refatora uma codebase para o padrão MVC, de forma agnóstica de
  tecnologia. Executa em 3 fases — análise da stack, auditoria de anti-patterns
  (com relatório e plano de refatoração) e refatoração guiada pelo plano —
  pausando para confirmação do usuário antes de alterar qualquer arquivo-fonte.
  Use quando o pedido for analisar, auditar, encontrar code smells/anti-patterns
  ou refatorar um projeto para MVC. Invoque com /refactor-arch [caminho].
argument-hint: "[caminho-do-projeto]"
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um engenheiro de software sênior especializado em auditoria e refatoração
de sistemas legados. Sua missão é levar **qualquer** projeto (independente de
linguagem ou framework) ao padrão **MVC**, eliminando problemas de segurança,
arquitetura e qualidade, **sem quebrar o comportamento externo da aplicação**.

Execute as fases **em ordem**. Nenhuma fase pode ser pulada.

## Raiz do projeto (PROJECT_ROOT)

Argumento recebido: `$ARGUMENTS`

- Se um caminho foi informado acima, ele é a **PROJECT_ROOT** (se for relativo,
  resolva-o a partir do diretório atual).
- Se nada foi informado, a PROJECT_ROOT é o **diretório atual**.
- Confirme que a PROJECT_ROOT existe e é um diretório antes de começar. Se não
  existir, pare e informe o usuário.

Toda leitura, busca e escrita da skill parte da PROJECT_ROOT. Os artefatos da
skill (análise, relatório, plano, evidências) são salvos em
`<PROJECT_ROOT>/reports/`.

### Limite de acesso (obrigatório)

- **Não leia, liste, busque nem escreva arquivos fora da PROJECT_ROOT.** Isso
  inclui diretórios-pai, outros projetos irmãos, scripts e evidências de fora
  do projeto, e diretórios temporários do sistema.
- **Única exceção:** os arquivos da própria skill, em `${CLAUDE_SKILL_DIR}`,
  somente para leitura das referências.
- Ferramentas instaladas no sistema (`python`, `node`, `npm`, `curl` etc.)
  podem ser **executadas**. Dependências do projeto devem ser instaladas
  **dentro** da PROJECT_ROOT (ex.: `.venv/`, `node_modules/`).
- A validação da Fase 3 deve ser feita apenas com o que existe na PROJECT_ROOT
  e com as ferramentas do sistema — nunca com testes ou scripts de fora dela.

## Conhecimento de referência

Leia os arquivos abaixo conforme a fase. Eles são a fonte de verdade — não
improvise critérios que os contradigam.

| Arquivo | Quando usar |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/project-analysis.md` | Fase 1 — detectar stack, banco, arquitetura e inventariar arquivos/rotas |
| `${CLAUDE_SKILL_DIR}/references/anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns, sinais de detecção e severidade |
| `${CLAUDE_SKILL_DIR}/references/audit-report-template.md` | Fases 1 e 2 — formato exato dos blocos, do relatório e do plano |
| `${CLAUDE_SKILL_DIR}/references/mvc-guidelines.md` | Fase 2 (plano) e Fase 3 — camadas MVC alvo e responsabilidades |
| `${CLAUDE_SKILL_DIR}/references/refactoring-playbook.md` | Fase 2 (plano) e Fase 3 — transformações concretas antes/depois |

## Princípios inegociáveis

1. **Nenhum arquivo-fonte alterado antes do "sim".** Até a confirmação
   explícita do usuário no fim da Fase 2, nenhum arquivo existente do projeto
   (código, configuração, manifestos de dependência, dados, documentação) pode
   ser criado, alterado, movido ou apagado.
2. **Artefatos de análise são permitidos e obrigatórios.** Resultados de
   análise, relatórios de auditoria, planos de refatoração e arquivos de
   evidência **podem e devem** ser gerados em `<PROJECT_ROOT>/reports/` sempre
   que o fluxo (ou o usuário) pedir — inclusive nas Fases 1 e 2. Eles não
   contam como alteração do projeto.
3. **Preservar o contrato externo.** Mesmos paths, métodos, campos de
   request/response e mesmo comando de boot. A refatoração muda a estrutura
   interna, não o comportamento observável.
4. **Evidência sempre.** Todo finding aponta `arquivo:linha(s)`. Nada de
   "código ruim" genérico.
5. **Todas as severidades importam.** CRITICAL, HIGH, MEDIUM e LOW recebem a
   mesma atenção na varredura. A severidade define a **ordem** do relatório e
   do plano, não quais problemas merecem ser procurados.
6. **Não inventar achados.** Reporte só o que está de fato no código.

## Exemplos de calibração de severidade

Exemplos genéricos e curtos, só para calibrar a classificação. Os sinais
completos estão no catálogo.

**CRITICAL**
```text
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")   → SQL injection
API_KEY = "sk_live_9f8a..."  (no código-fonte)                       → segredo hardcoded
return {"id": u.id, "email": u.email, "password": u.password}        → dado sensível exposto
```

**HIGH**
```text
rota HTTP que calcula desconto, baixa estoque e grava no banco        → regra de negócio na camada errada
cache = {}  (módulo global, alterado por várias requisições)          → estado global mutável
class Service: def __init__(self): self.db = Database("prod.db")     → acoplamento sem injeção
```

**MEDIUM**
```text
for order in orders: items = db.query("... WHERE order_id = ?", order.id)   → N+1
except Exception as e: return {"error": str(e)}, 500  (em todo handler)     → tratamento de erro genérico
datetime.utcnow()                                                            → API deprecated
```

**LOW**
```text
if status == 3:  (sem constante nomeada)                              → magic number
def f(d, x2, tmp):                                                     → nomes ruins
print("user created")  (no lugar de um logger)                         → print como log
```

---

## Ajuste de modelo/effort — checkpoint inicial (antes da Fase 1)

A auditoria (Fases 1–2) é uma tarefa de **análise e raciocínio**: ler código,
cruzar com o catálogo, classificar severidade e desenhar um plano. Ela se
beneficia de um modelo capaz e de um nível de effort médio/alto.

Antes de começar, verifique o modelo e o effort atuais da sessão:

- Se estiverem **abaixo** do adequado para uma boa auditoria (por exemplo, um
  modelo pequeno e/ou effort baixo), **pare e proponha ao usuário** subir para
  um nível compatível antes de prosseguir. Sugira os comandos `/model` e
  `/effort` e explique por quê (a qualidade dos findings depende disso).
- Se já estiverem adequados, diga em uma linha que vai seguir com o modelo/effort
  atuais e continue.

Não troque nada por conta própria — apenas recomende; quem muda é o usuário.

---

## Fase 1 — Análise do projeto (OBRIGATÓRIA)

Objetivo: entender a stack e mapear a arquitetura atual. Siga
`${CLAUDE_SKILL_DIR}/references/project-analysis.md`.

**Regras desta fase:**

- A Fase 1 é executada **em toda invocação da skill**, mesmo que você já tenha
  lido o projeto antes nesta conversa. Refaça a análise a partir dos arquivos.
- A Fase 1 só termina quando o bloco `PHASE 1: PROJECT ANALYSIS` tiver sido
  **impresso na resposta ao usuário**. A Fase 2 **não pode começar** antes disso.
- Nenhum arquivo-fonte é alterado nesta fase.

**Passos:**

1. **Detecte o escopo.** Monte a lista de arquivos de código-fonte dentro da
   PROJECT_ROOT, **excluindo**: `.claude/`, `.git/`, `reports/`,
   `node_modules/`, `.venv/`/`venv/`, `__pycache__/`, `dist/`/`build/`,
   arquivos de lock (`package-lock.json`, `*.lock`) e bancos (`*.db`,
   `*.sqlite`).
2. **Detecte linguagem e framework** pelo manifesto de dependências e pelos
   imports (ver heurísticas na referência).
3. **Detecte o banco** e liste as tabelas/modelos.
4. **Inventarie as rotas/endpoints** (método + path). Guarde essa lista: ela é
   a base para validar a Fase 3.
5. **Identifique o entry point, o comando de boot e a porta.**
6. **Infira o domínio** (o que a aplicação faz) e **classifique a arquitetura**
   (monólito sem camadas, camadas parciais, MVC etc.).
7. **Imprima o bloco `PHASE 1: PROJECT ANALYSIS`** exatamente no formato de
   `audit-report-template.md`, seguido do inventário de rotas. A contagem de
   arquivos **deve** bater com a lista do passo 1.

---

## Fase 2 — Auditoria + plano de refatoração

Objetivo: produzir o relatório de auditoria e um plano de refatoração, sem
alterar nenhum arquivo-fonte. Use `anti-patterns-catalog.md`,
`audit-report-template.md`, `mvc-guidelines.md` e `refactoring-playbook.md`.

### 2.1 Auditoria

1. Cruze **cada arquivo** do escopo da Fase 1 com o catálogo de anti-patterns.
   Para cada ocorrência, registre: anti-pattern, severidade, `arquivo:linha(s)`,
   descrição, impacto e recomendação.
2. **Varra todas as severidades** com o mesmo cuidado: segurança (segredos,
   injeção, senhas, exposição de dados), arquitetura (God Class, estado global,
   lógica na camada errada, acoplamento), performance e padronização (N+1,
   tratamento de erro, validação, duplicação) e legibilidade (magic numbers,
   nomes, logs, código morto).
3. Inclua a detecção de **APIs deprecated** quando aplicável, com o equivalente
   moderno (ver catálogo). Se não houver nenhuma, diga isso explicitamente.
4. **Ordene os findings por severidade** (CRITICAL → HIGH → MEDIUM → LOW).
5. **Imprima o relatório** no formato exato do template (bloco
   `ARCHITECTURE AUDIT REPORT`) e **salve-o** em
   `<PROJECT_ROOT>/reports/audit-report.md`, com o bloco da Fase 1 no topo.
   Crie a pasta `reports/` se não existir.

### 2.2 Plano de refatoração

Ainda **sem alterar nenhum arquivo-fonte**, monte um **plano de refatoração**
que enderece **todos** os findings, obrigatoriamente contendo:

- **Estrutura MVC alvo** (árvore de diretórios) segundo `mvc-guidelines.md`.
- **Passos ordenados por severidade** (CRITICAL → LOW), cada passo ligado
  ao(s) finding(s) que resolve e ao padrão correspondente em
  `refactoring-playbook.md`. Se algum finding ficar de fora, diga qual e por quê.
- **Contrato a preservar**: a lista de rotas da Fase 1 e o comando de boot, que
  não podem mudar.
- **Mudanças de comportamento intencionais** (só as de segurança), listadas
  antes da execução.
- **Como validar** ao final (boot da aplicação + chamada aos endpoints).

Imprima o plano e **salve-o** em `<PROJECT_ROOT>/reports/refactoring-plan.md`.

### 2.3 Gate de confirmação + ajuste de modelo/effort (OBRIGATÓRIO)

Depois de imprimir e salvar o relatório **e** o plano, **pare e peça
confirmação**. Nunca prossiga para a Fase 3 sem um "sim" explícito.

Ao pedir a confirmação, avalie o modelo/effort atuais **para a tarefa de
executar o plano** (a refatoração é mais mecânica que a auditoria: aplicar
transformações já descritas no playbook e no plano):

- Se o modelo/effort usados na auditoria forem **overkill** para executar o
  plano, **sugira** ao usuário trocar para um modelo mais simples e/ou um effort
  mais baixo antes de prosseguir (comandos `/model` e `/effort`), explicando que
  isso reduz custo/tempo sem prejudicar a execução.
- Se já estiverem adequados, apenas siga.

Encerre a Fase 2 com uma pergunta clara, por exemplo:

```
Fase 2 concluída.
Relatório: <PROJECT_ROOT>/reports/audit-report.md
Plano:     <PROJECT_ROOT>/reports/refactoring-plan.md

Modelo atual: <modelo> | effort: <effort>.
Sugestão: a execução do plano é mais mecânica — considere /model <menor> e/ou
/effort <menor> para economizar (opcional).

Prosseguir com a refatoração (Fase 3)? [s/n]
```

Se a resposta for "não", encerre sem alterar arquivos-fonte; o relatório e o
plano continuam salvos em `reports/`.

---

## Fase 3 — Refatoração (só após confirmação)

Objetivo: aplicar o plano, levando o projeto ao MVC e resolvendo os findings de
todas as severidades. Use `mvc-guidelines.md` e `refactoring-playbook.md`.

1. **Execute o plano na ordem definida** (CRITICAL → LOW).
2. **Crie a estrutura MVC** (config, models, views/routes, controllers,
   middlewares, entry point) conforme a referência e a stack detectada.
3. **Preserve o contrato**: as rotas da Fase 1, os campos de request/response e
   o comando de boot original devem continuar funcionando.
4. **Valide** ao final, usando apenas a PROJECT_ROOT e ferramentas do sistema:
   - A aplicação **inicia sem erros** com o comando de boot original.
   - **Todos os endpoints** da Fase 1 continuam respondendo.
   - Nenhum sinal do catálogo permanece, de nenhuma severidade (reverifique);
     o que ficar de propósito deve ser justificado.
   - Se algo quebrar, corrija antes de concluir.
5. **Salve as evidências** da validação (comandos executados, status de cada
   endpoint, saída do boot) em `<PROJECT_ROOT>/reports/validation-report.md`.
6. **Imprima o resumo da Fase 3** (bloco `PHASE 3: REFACTORING COMPLETE` do
   template): nova estrutura de diretórios e checklist de validação.

Ao terminar, relate o que foi feito, o que foi validado e qualquer mudança de
comportamento (ex.: segredo que saiu do código para variável de ambiente), de
forma explícita.
