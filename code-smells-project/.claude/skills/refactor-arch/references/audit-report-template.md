# Referência — Template de Saída (Fases 1, 2 e 3)

Use **exatamente** estes formatos. Todos os arquivos ficam em
`<PROJECT_ROOT>/reports/`:

| Arquivo | Conteúdo | Gerado em |
|---|---|---|
| `reports/audit-report.md` | Bloco da Fase 1 + relatório de auditoria | Fase 2 |
| `reports/refactoring-plan.md` | Plano de refatoração | Fase 2 |
| `reports/validation-report.md` | Evidências da validação + bloco da Fase 3 | Fase 3 |

Esses arquivos são artefatos da skill: gerá-los **não** conta como alteração do
projeto e é permitido antes da confirmação do usuário.

## Bloco da Fase 1 (resumo da análise)

Impresso na resposta ao fim da Fase 1 (obrigatório) e repetido no topo de
`audit-report.md`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework> <versão>
Dependencies:  <deps relevantes, separadas por vírgula>
Domain:        <o que a aplicação faz>
Architecture:  <classificação em uma frase>
Source files:  <N> files analyzed
DB tables:     <tabela1, tabela2, ...>
Entry point:   <arquivo> (boot: <comando>)
================================
```

Logo depois do bloco, liste o inventário de rotas (método + path), uma por linha.

## Relatório de auditoria (Fase 2)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<X> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <nome do anti-pattern>
File: <caminho:linha-inicio-linha-fim>
Description: <o que está errado, concreto>
Impact: <consequência prática>
Recommendation: <o que fazer — aponte o padrão do playbook>

### [HIGH] <...>
File: <...>
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================
```

### Regras de preenchimento

- **Ordem**: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, do mais
  impactante para o menos.
- **File**: sempre `caminho:linha` ou `caminho:inicio-fim`, com caminho relativo
  à PROJECT_ROOT. Quando o mesmo anti-pattern ocorre em muitos pontos, agrupe
  num finding e cite os arquivos, os métodos/endpoints e o número de
  ocorrências.
- **Summary**: a soma dos contadores = `Total`.
- **Recommendation**: aponte o padrão de refatoração correspondente
  (ex.: "RF-02 — queries parametrizadas").
- **APIs deprecated**: se não houver nenhuma, registre isso numa linha após o
  bloco.
- **Não invente** findings para inflar números; reporte o que existe.

## Plano de refatoração (Fase 2)

Impresso na resposta e salvo em `reports/refactoring-plan.md`.

```
## Refactoring Plan

Target structure:
<árvore de diretórios MVC>

Steps (CRITICAL → LOW):
1. [CRITICAL] <ação> — resolve <finding(s)> — padrão <RF-xx>
2. [HIGH]     <ação> — resolve <finding(s)> — padrão <RF-xx>
3. [MEDIUM]   <ação> — ...
4. [LOW]      <ação> — ...

Not addressed: <findings que ficam de fora e o motivo, ou "nenhum">

Contract to preserve:
- Rotas: <lista da Fase 1>
- Boot: <comando original>

Intentional behavior changes (segurança):
- <mudança> — <motivo>

Validation:
- App sobe sem erros com o comando de boot original
- Todos os endpoints da Fase 1 respondem
- Nenhum sinal do catálogo remanescente
```

## Bloco da Fase 3 (resumo da refatoração)

Impresso na resposta ao fim da Fase 3 e repetido no fim de
`reports/validation-report.md`, depois das evidências (comandos executados e
status de cada endpoint).

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios final>

## Validation
  ✓ Application boots without errors (<comando de boot>)
  ✓ All endpoints respond (<n>/<n>)
  ✓ No catalog anti-patterns remaining
  ✗ <item que falhou ou ficou pendente, com motivo>

## Behavior changes
- <mudança intencional>
================================
```
