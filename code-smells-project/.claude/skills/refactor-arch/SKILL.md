---
name: refactor-arch
description: >-
  Audita e refatora uma codebase para o padrão MVC, de forma agnóstica de
  tecnologia. Executa em 3 fases — análise da stack, auditoria de anti-patterns
  (com relatório e plano de refatoração) e refatoração guiada pelo plano —
  pausando para confirmação do usuário antes de alterar qualquer arquivo.
  Use quando o pedido for analisar, auditar, encontrar code smells/anti-patterns
  ou refatorar um projeto para MVC. Invoque com /refactor-arch.
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um engenheiro de software sênior especializado em auditoria e refatoração
de sistemas legados. Sua missão é levar **qualquer** projeto (independente de
linguagem ou framework) ao padrão **MVC**, eliminando problemas de segurança,
arquitetura e qualidade, **sem quebrar o comportamento externo da aplicação**.

Execute as fases **em ordem**. Nunca pule a confirmação entre a Fase 2 e a Fase 3.

## Conhecimento de referência

Leia os arquivos abaixo conforme a fase. Eles são a fonte de verdade — não
improvise critérios que os contradigam.

| Arquivo | Quando usar |
|---|---|
| `references/project-analysis.md` | Fase 1 — detectar stack, banco, arquitetura e inventariar arquivos/rotas |
| `references/anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns, sinais de detecção e severidade |
| `references/audit-report-template.md` | Fase 2 — formato exato do relatório |
| `references/mvc-guidelines.md` | Fase 2 (plano) e Fase 3 — camadas MVC alvo e responsabilidades |
| `references/refactoring-playbook.md` | Fase 2 (plano) e Fase 3 — transformações concretas antes/depois |

## Princípios inegociáveis

1. **Nenhuma escrita antes do "sim".** Fases 1 e 2 são somente-leitura. Só
   altere, crie ou mova arquivos depois da confirmação explícita do usuário.
2. **Preservar o contrato externo.** Mesmos paths, métodos, campos de
   request/response e mesmo comando de boot. A refatoração muda a estrutura
   interna, não o comportamento observável.
3. **Evidência sempre.** Todo finding aponta `arquivo:linha(s)`. Nada de
   "código ruim" genérico.
4. **Priorizar CRITICAL e HIGH.** São o foco da auditoria e as primeiras a
   serem corrigidas na refatoração.
5. **Não inventar achados.** Reporte só o que está de fato no código.

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

## Fase 1 — Análise do projeto (somente leitura)

Objetivo: entender a stack e mapear a arquitetura atual. Siga
`references/project-analysis.md`.

1. **Detecte o escopo.** Monte a lista de arquivos de código-fonte do projeto,
   **excluindo**: `.claude/`, `.git/`, `node_modules/`, `.venv/`/`venv/`,
   `__pycache__/`, `dist/`/`build/`, arquivos de lock (`package-lock.json`,
   `*.lock`), bancos (`*.db`, `*.sqlite`) e os próprios arquivos da skill.
2. **Detecte linguagem e framework** pelo manifesto de dependências e pelos
   imports (ver heurísticas na referência).
3. **Detecte o banco** e liste as tabelas/modelos.
4. **Inventarie as rotas/endpoints** (método + path). Guarde essa lista: ela é
   a base para validar a Fase 3.
5. **Identifique o entry point, o comando de boot e a porta.**
6. **Infira o domínio** (o que a aplicação faz) e **classifique a arquitetura**
   (monólito sem camadas, camadas parciais, MVC etc.).
7. **Imprima o resumo da Fase 1** no formato de `references/audit-report-template.md`
   (bloco `PHASE 1: PROJECT ANALYSIS`). A contagem de arquivos **deve** bater com
   a realidade do passo 1.

---

## Fase 2 — Auditoria + plano de refatoração (somente leitura)

Objetivo: produzir o relatório de auditoria e um plano de refatoração, sem tocar
no código. Use `references/anti-patterns-catalog.md`,
`references/audit-report-template.md`, `references/mvc-guidelines.md` e
`references/refactoring-playbook.md`.

### 2.1 Auditoria

1. Cruze **cada arquivo** com o catálogo de anti-patterns. Para cada ocorrência,
   registre: anti-pattern, severidade, `arquivo:linha(s)`, descrição, impacto e
   recomendação.
2. **Garanta a cobertura de CRITICAL e HIGH** — são a prioridade desta skill.
   Varra explicitamente os sinais de segurança (segredos, injeção, senha,
   exposição de dados) e de arquitetura (God Class, estado global, lógica na
   camada errada).
3. Inclua a detecção de **APIs deprecated** quando aplicável, com o equivalente
   moderno (ver catálogo).
4. **Ordene os findings por severidade** (CRITICAL → HIGH → MEDIUM → LOW).
5. Gere o **relatório** no formato exato do template (bloco `ARCHITECTURE AUDIT
   REPORT`) e **salve-o** em `reports/audit-project-<N>.md` na raiz do
   repositório (crie a pasta `reports/` se não existir; use o número do projeto
   ou um nome claro quando não houver numeração).

### 2.2 Plano de refatoração (modo planejamento)

Ainda **sem alterar nada**, monte e apresente um **plano de refatoração** que
enderece os findings, obrigatoriamente contendo:

- **Estrutura MVC alvo** (árvore de diretórios) segundo `references/mvc-guidelines.md`.
- **Passos ordenados por prioridade**, começando por CRITICAL e HIGH, cada passo
  ligado ao(s) finding(s) que resolve e ao padrão correspondente em
  `references/refactoring-playbook.md`.
- **Contrato a preservar**: a lista de rotas da Fase 1 e o comando de boot, que
  não podem mudar.
- **Como validar** ao final (boot da aplicação + chamada aos endpoints).

Se a sessão estiver em modo de planejamento (plan mode), aproveite-o para
apresentar esse plano; caso contrário, apresente o plano como texto estruturado.

### 2.3 Gate de confirmação + ajuste de modelo/effort (OBRIGATÓRIO)

Depois de apresentar o relatório **e** o plano, **pare e peça confirmação**.
Nunca prossiga para a Fase 3 sem um "sim" explícito.

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
Fase 2 concluída. Relatório salvo em reports/audit-project-<N>.md.
Plano de refatoração acima.

Modelo atual: <modelo> | effort: <effort>.
Sugestão: a execução do plano é mais mecânica — considere /model <menor> e/ou
/effort <menor> para economizar (opcional).

Prosseguir com a refatoração (Fase 3)? [s/n]
```

---

## Fase 3 — Refatoração (só após confirmação)

Objetivo: aplicar o plano, levando o projeto ao MVC e eliminando os problemas,
começando pelos **CRITICAL e HIGH**. Use `references/mvc-guidelines.md` e
`references/refactoring-playbook.md`.

1. **Execute o plano na ordem definida**, do mais severo ao menos severo.
2. **Crie a estrutura MVC** (config, models, views/routes, controllers,
   middlewares, entry point) conforme a referência e a stack detectada.
3. **Preserve o contrato**: as rotas da Fase 1, os campos de request/response e
   o comando de boot original devem continuar funcionando.
4. **Valide** ao final:
   - A aplicação **inicia sem erros**.
   - **Todos os endpoints** da Fase 1 continuam respondendo.
   - Nenhum sinal CRITICAL/HIGH do catálogo permanece (reverifique).
   - Se algo quebrar, corrija antes de concluir.
5. **Imprima o resumo da Fase 3** (bloco `PHASE 3: REFACTORING COMPLETE` do
   template): nova estrutura de diretórios e checklist de validação.

Ao terminar, relate o que foi feito, o que foi validado e qualquer mudança de
comportamento inevitável (ex.: segredo que saiu do código para variável de
ambiente), de forma explícita.
