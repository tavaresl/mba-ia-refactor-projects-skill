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
  inclui diretórios-pai, projetos irmãos, scripts e evidências de fora do
  projeto, diretórios temporários do sistema (ex.: `/tmp`) e o scratchpad ou
  diretório temporário que a própria ferramenta oferecer. Arquivos
  temporários ficam em `<PROJECT_ROOT>/reports/.tmp/` e são apagados no fim.
- **Exceções:** (1) os arquivos da própria skill, em `${CLAUDE_SKILL_DIR}`,
  somente para leitura; (2) o arquivo de plano que a própria ferramenta
  designar enquanto o plan mode estiver ativo.
- Ferramentas instaladas no sistema (`python`, `node`, `npm`, `curl`, `bash`
  etc.) podem ser **executadas**. Dependências do projeto devem ser instaladas
  **dentro** da PROJECT_ROOT (ex.: `.venv/`, `node_modules/`).
- **Não execute nenhum comando de controle de versão** (`git` ou equivalente):
  nem de leitura (`status`, `log`, `ls-files`, `diff`), nem de escrita (`add`,
  `rm`, `rm --cached`, `reset`, `checkout`, `commit`, `stash`). O repositório
  pode conter outros projetos e mudanças do usuário. Para apagar ou mover
  arquivos, use `rm` e `mv`. Versionar o resultado é decisão do usuário.

### Comandos de shell (todas as fases)

Em **todas** as fases (inclusive nas buscas da auditoria), sempre que um
comando tiver variáveis, laços ou mais de uma etapa, escreva-o num script em
`<PROJECT_ROOT>/reports/.tmp/` e execute com `bash <script>`. Não dependa do
shell interativo do usuário (no `zsh`, variáveis sem aspas não são separadas em
palavras e globs sem resultado abortam o comando). Detalhes em
`validation-protocol.md`.

## Conhecimento de referência

Leia os arquivos abaixo conforme a fase. Eles são a fonte de verdade — não
improvise critérios que os contradigam.

| Arquivo                                                   | Quando usar                                                                        |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/project-analysis.md`      | Fase 1 — detectar stack, banco, arquitetura e inventariar arquivos/rotas           |
| `${CLAUDE_SKILL_DIR}/references/anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns, sinais de detecção e severidade                |
| `${CLAUDE_SKILL_DIR}/references/audit-report-template.md` | Fases 1, 2 e 3 — formato exato dos blocos, do relatório, do plano e das evidências |
| `${CLAUDE_SKILL_DIR}/references/mvc-guidelines.md`        | Fase 2 (plano) e Fase 3 — camadas MVC alvo, responsabilidades e políticas          |
| `${CLAUDE_SKILL_DIR}/references/refactoring-playbook.md`  | Fase 2 (plano) e Fase 3 — transformações concretas antes/depois                    |
| `${CLAUDE_SKILL_DIR}/references/validation-protocol.md`   | Fase 3 — baseline, boot, chamadas, comparação e limpeza                            |

## Princípios inegociáveis

1. **Nenhum arquivo-fonte alterado antes da confirmação da Fase 3.** Até o
   usuário confirmar no gate da Fase 2, nenhum arquivo existente do projeto
   (código, configuração, manifestos de dependência, dados, documentação) pode
   ser criado, alterado, movido ou apagado.
2. **Artefatos de análise são permitidos e obrigatórios.** Resultados de
   análise, relatórios de auditoria, planos de refatoração e arquivos de
   evidência **podem e devem** ser gerados em `<PROJECT_ROOT>/reports/` sempre
   que o fluxo (ou o usuário) pedir — inclusive nas Fases 1 e 2. Eles não
   contam como alteração do projeto.
3. **Preservar o contrato externo.** Mesmos paths, métodos, campos de
   request/response, **mesmas mensagens** (de sucesso e de erro) e mesmo
   comando de boot. Toda diferença de comportamento precisa estar declarada no
   plano como mudança intencional (ver princípio 7); o resto é regressão e deve
   ser corrigido.
4. **Evidência sempre.** Todo finding aponta `arquivo:linha(s)`. Toda afirmação
   da validação vem acompanhada do comando executado e da saída real.
5. **Todas as severidades importam.** CRITICAL, HIGH, MEDIUM e LOW recebem a
   mesma atenção na varredura. A severidade define a **ordem** do relatório e
   do plano, não quais problemas merecem ser procurados.
6. **Não inventar achados.** Reporte só o que está de fato no código.
7. **Mudanças de comportamento aceitas** (sempre declaradas no plano e
   provadas na validação):
   - **segurança**: parar de expor dados sensíveis, fechar injeção, exigir
     token em endpoints perigosos e impedir que clientes anônimos definam
     campos de privilégio como `role` (`mvc-guidelines.md`, RF-16 nível 1);
   - **rejeição de entrada claramente inválida** que hoje é aceita ou vira erro
     500 (ex.: quantidade negativa, tipo errado, corpo ausente), respondendo
     4xx com a mensagem no formato original da rota.

   Qualquer outra mudança (novas regras de negócio, textos diferentes, efeitos
   colaterais novos) fica em "Not addressed" no plano, com a recomendação.
8. **Dados, credenciais e histórico preservados.**
   - Dados de seed/demonstração mantêm os valores documentados (inclusive
     credenciais de exemplo); só a forma de armazenar pode mudar (ex.: com hash).
   - Credenciais existentes continuam funcionando: ao trocar o algoritmo de
     hash, migre os hashes antigos (RF-08), nunca exija recriar o banco.
   - Nenhuma correção pode apagar ou alterar registros persistidos como efeito
     colateral (ex.: excluir pagamentos ou pedidos junto com um usuário). Se a
     correção exigiria isso, ela vai para "Not addressed".
   - Nenhum segredo vai para log ou resposta — nem um segredo gerado na hora
     (ex.: senha aleatória de admin).

## Exemplos de calibração de severidade

Exemplos genéricos e curtos, só para calibrar a classificação. Os sinais
completos estão no catálogo.

**CRITICAL**

```text
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")   → SQL injection
API_KEY = "sk_live_9f8a..."  (no código-fonte)                       → segredo hardcoded
return {"id": u.id, "email": u.email, "password": u.password}        → dado sensível exposto
um arquivo/classe com conexão, schema, rotas e regra de negócio      → God Class / God Module
POST /users aceita {"role": "admin"} de requisição sem credencial    → privilégio autoatribuível (AP-SEC-07)
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
quantity aceita <= 0 ou itens repetidos furam a checagem de estoque         → validação / invariante de negócio
datetime.utcnow()                                                            → API deprecated
```

**LOW**

```text
if status == 3:  (sem constante nomeada)                              → magic number
def f(d, x2, tmp):                                                     → nomes ruins
print("user created")  (no lugar de um logger)                         → print como log
```

## Perguntas ao usuário (clarificação)

Sempre que este documento mandar **perguntar ao usuário**, faça uma pergunta de
clarificação com a ferramenta de perguntas da ferramenta em uso (no Claude
Code, `AskUserQuestion`), usando **exatamente** as opções indicadas. Se não
houver ferramenta de perguntas, escreva a pergunta e as opções em texto e
**encerre o turno** aguardando a resposta.

Ao interpretar a resposta:

- Uma opção escolhida vale exatamente como descrito.
- Uma resposta livre que contenha uma instrução clara (ex.: "corrija só os
  CRITICAL") vale mais que o comportamento padrão: siga a instrução.
- Uma resposta que não deixe clara a intenção segue o **comportamento padrão**
  indicado em cada pergunta.

---

## Ajuste de modelo/effort — checkpoint inicial (antes da Fase 1)

Effort atual da sessão: `${CLAUDE_EFFORT}`. O modelo atual é o que a própria
sessão informa a você.

A auditoria (Fases 1–2) é uma tarefa de **análise e raciocínio**. Regra
objetiva:

- **Effort `low`** ou **modelo muito simples** (ex.: Haiku): **pare** antes da
  Fase 1, explique que a qualidade dos findings depende de mais raciocínio,
  proponha `/effort medium` (recomendado `/effort high`) e/ou `/model` com um
  modelo mais capaz, e encerre o turno aguardando o usuário.
- **Effort `medium`, `high`, `xhigh` ou `max`** com um modelo que não seja
  muito simples: diga em uma linha que vai seguir com a configuração atual e
  continue.
- Se o effort não puder ser determinado (o valor acima aparecer vazio ou como
  o texto literal do placeholder), diga isso em uma linha e siga.

Não troque nada por conta própria — apenas recomende; quem muda é o usuário.

---

## Fase 1 — Análise do projeto (OBRIGATÓRIA)

Objetivo: entender a stack e mapear a arquitetura atual. Siga
`${CLAUDE_SKILL_DIR}/references/project-analysis.md`.

**Regras desta fase:**

- A Fase 1 é executada **em toda invocação da skill**, mesmo que você já tenha
  lido o projeto antes nesta conversa. Refaça a análise a partir dos arquivos.
- A Fase 1 só termina quando o bloco `PHASE 1: PROJECT ANALYSIS` tiver sido
  **enviado ao usuário como mensagem de texto no chat**. Gravar o bloco em
  arquivo **não** conta como impressão.
- **Não abra `anti-patterns-catalog.md` nem comece a Fase 2 antes de enviar o
  bloco no chat.**
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
5. **Identifique o entry point, o comando de boot, a porta e a preparação**
   necessária antes do boot (seed, migrations), se houver.
6. **Infira o domínio** (o que a aplicação faz) e **classifique a arquitetura**
   (monólito sem camadas, camadas parciais, MVC etc.).
7. **Envie no chat o bloco `PHASE 1: PROJECT ANALYSIS`** exatamente no formato
   de `audit-report-template.md`, seguido do inventário de rotas. A contagem de
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
   injeção, senhas, exposição de dados, endpoints perigosos), arquitetura (God
   Class, estado global, lógica na camada errada, acoplamento), performance e
   padronização (N+1, tratamento de erro, validação e **invariantes de
   negócio**, duplicação) e legibilidade (magic numbers, nomes, logs, código
   morto).
3. Inclua a detecção de **APIs deprecated** quando aplicável, com o equivalente
   moderno (ver catálogo). Se não houver nenhuma, diga isso explicitamente.
4. **Ordene os findings por severidade** (CRITICAL → HIGH → MEDIUM → LOW).
5. **Imprima o relatório** no formato exato do template (bloco
   `ARCHITECTURE AUDIT REPORT`) e **salve-o** em
   `<PROJECT_ROOT>/reports/audit-report.md`, com o bloco da Fase 1 no topo.
   Crie a pasta `reports/` se não existir. Salve **antes** do passo 2.2, porque
   o plan mode pode impedir escritas.

### 2.2 Plano de refatoração

**Passo 1 — pergunta sobre o plan mode.** Se a sessão **já estiver** em plan
mode (a ferramenta informa isso), pule para o passo 2. Caso contrário,
**pergunte ao usuário**:

- Pergunta: "Como você quer gerar o plano de refatoração?"
- Opções (exatamente):
    - `A. Alterar para plan mode e gerar o plano`
    - `B. Seguir no modo atual e gerar o plano`
- **A** → você **DEVE** entrar em plan mode (no Claude Code, a ferramenta
  `EnterPlanMode`) antes de montar o plano. Se a ferramenta não existir ou
  falhar, avise o usuário em uma linha e siga no modo atual.
- **B** ou resposta não clara (comportamento padrão) → siga no modo atual.

**Passo 2 — monte o plano**, ainda **sem alterar nenhum arquivo-fonte**,
endereçando **todos** os findings e contendo obrigatoriamente:

- **Estrutura MVC alvo** (árvore de diretórios) segundo `mvc-guidelines.md`.
- **Passos ordenados por severidade** (CRITICAL → LOW), cada passo ligado
  ao(s) finding(s) que resolve e ao padrão correspondente em
  `refactoring-playbook.md`. Se algum finding ficar de fora, diga qual e por quê.
- **Contrato a preservar**: a lista de rotas da Fase 1, o formato das respostas
  (inclusive dos erros) e o comando de boot.
- **Mudanças de comportamento intencionais**, uma a uma, cada uma marcada como
  "segurança" ou "entrada inválida" (princípio 7), com a chamada que a prova.
  Qualquer diferença não listada aqui será tratada como regressão na Fase 3.
- **Preservação de dados** (princípio 8): o que acontece com seeds,
  credenciais existentes e registros persistidos.
- **Como validar** ao final, segundo `validation-protocol.md`.

**Passo 3 — apresente e salve o plano.**

- **Em plan mode:** apresente o plano pela saída do plan mode (no Claude Code,
  `ExitPlanMode`). Se o usuário pedir ajustes, revise e apresente de novo.
  Quando o plano for aprovado e o plan mode encerrado, salve-o em
  `<PROJECT_ROOT>/reports/refactoring-plan.md`.
  **A aprovação do plano não é a confirmação da Fase 3.** Mesmo que a
  ferramenta diga que você já pode implementar, **não altere nenhum
  arquivo-fonte**: vá para o gate 2.3.
- **No modo atual:** imprima o plano no chat e salve-o em
  `<PROJECT_ROOT>/reports/refactoring-plan.md`.

### 2.3 Gate de confirmação + ajuste de modelo/effort (OBRIGATÓRIO)

**Antes da pergunta**, envie no chat:

1. o bloco `PHASE 1: PROJECT ANALYSIS` de novo;
2. a linha `Summary` do relatório (contagem por severidade);
3. os caminhos de `audit-report.md` e `refactoring-plan.md`;
4. o modelo atual e o effort atual (`${CLAUDE_EFFORT}`).

**Classifique a configuração atual:**

- **Modelo:** de tarefas rotineiras (ex.: Sonnet e equivalentes), muito simples
  (ex.: Haiku e equivalentes), de tarefas complexas (ex.: Opus, Fable e
  equivalentes) ou desconhecido.
- **Effort:** `low`/`medium`, `high`/`xhigh`/`max` (ou equivalentes em outros
  agentes) ou desconhecido.

**Variante 1 — sem sugestão.** Use quando o modelo é de tarefas rotineiras
**ou** o effort é `low` ou `medium`. **Pergunte ao usuário**:

- Pergunta: "Fase 2 concluída. Prosseguir para a refatoração?"
- Opções (exatamente):
    - `A. Prosseguir para a fase 3`
    - `B. Não prosseguir, e direi ao agente o que fazer`
- **A** → vá para a Fase 3.
- **B** → não prossiga; aguarde as instruções do usuário sem alterar nenhum
  arquivo-fonte.
- Resposta não clara (comportamento padrão) → vá para a Fase 3 com a
  configuração atual.

**Variante 2 — com sugestão.** Use em **qualquer outro caso**: modelo muito
simples ou de tarefas complexas, **ou** effort `high`, `xhigh` ou `max`, **ou**
configuração desconhecida. Quando as regras se sobrepõem (ex.: Sonnet com
effort `high`, ou Opus com effort `medium`), vale esta variante.

A pergunta **DEVE** conter a sugestão de ajuste, explicando que executar um
plano já definido é mais mecânico que auditar:

- modelo de tarefas complexas e/ou effort alto → sugerir um modelo mais simples
  (ex.: `/model sonnet`) e/ou um effort menor (ex.: `/effort medium`);
- modelo muito simples → sugerir um modelo de tarefas rotineiras (ex.:
  `/model sonnet`), mais confiável para executar o plano.

**Pergunte ao usuário**:

- Pergunta: "Fase 2 concluída. <sugestão de ajuste>. Como prosseguir?"
- Opções (exatamente):
    - `A. Vou alterar o modelo/effort antes de prosseguirmos`
    - `B. Prossiga com modelo e effort atuais`
    - `C. Não prosseguir, e direi ao agente o que fazer`
- **A** → **interrompa a execução da skill**. Diga ao usuário que, depois de
  ajustar, basta pedir no chat para retomar (ex.: "retome") — sem invocar
  `/refactor-arch` de novo, o que recomeçaria da Fase 1. Não faça mais nada
  até lá. Quando o usuário pedir para retomar — **tendo alterado ou não** o
  modelo/effort — assuma que ele quer prosseguir com a configuração em vigor e
  vá para a Fase 3.
- **B** ou resposta não clara (comportamento padrão) → vá para a Fase 3 com o
  modelo e o effort atuais.
- **C** → não prossiga; aguarde as instruções do usuário sem alterar nenhum
  arquivo-fonte.

Em qualquer caso em que a Fase 3 não seja iniciada, o relatório e o plano
continuam salvos em `reports/`.

---

## Fase 3 — Refatoração (só após confirmação)

Objetivo: aplicar o plano, levando o projeto ao MVC e resolvendo os findings de
todas as severidades, sem regressões. Use `mvc-guidelines.md`,
`refactoring-playbook.md` e `validation-protocol.md`.

1. **Releia** `reports/audit-report.md` e `reports/refactoring-plan.md`
   (obrigatório ao retomar depois de uma pausa).
2. **Antes de mudar qualquer arquivo-fonte:**
   - copie os arquivos-fonte originais (escopo da Fase 1, mais manifestos e
     scripts de preparação) para `reports/.tmp/original-src/`, para poder
     rodar o app original de novo se o baseline precisar ser refeito;
   - suba o app original e grave a resposta de cada rota do inventário em
     `reports/baseline-responses.txt`, com a cobertura mínima de
     `validation-protocol.md`.
3. **Execute o plano na ordem definida** (CRITICAL → LOW), criando a estrutura
   MVC (config, models, views/routes, controllers, middlewares, entry point)
   conforme a referência e a stack detectada.
4. **Valide** seguindo `validation-protocol.md`, usando apenas a PROJECT_ROOT e
   ferramentas do sistema:
    - a aplicação **inicia sem erros** com o comando de boot original;
    - **todas as rotas** da Fase 1 respondem; grave as respostas em
      `reports/after-responses.txt`;
    - **compare** com o baseline: cada diferença precisa estar na lista de
      mudanças intencionais do plano; as demais são regressões e devem ser
      corrigidas antes de concluir;
    - reverifique os sinais do catálogo de **todas** as severidades, registrando
      os comandos e a saída real; o que ficar de propósito deve ser justificado.
5. **Limpe**: encerre todo servidor iniciado (confirme que a porta ficou
   livre), restaure os arquivos de dados ao estado anterior aos testes e apague
   `reports/.tmp/`.
6. **Salve as evidências** em `<PROJECT_ROOT>/reports/validation-report.md`
   (formato do template) e **envie no chat** o bloco
   `PHASE 3: REFACTORING COMPLETE`.

Ao terminar, relate o que foi feito, o que foi validado e cada mudança de
comportamento, de forma explícita.
