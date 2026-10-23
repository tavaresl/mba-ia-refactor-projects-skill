# Referência — Template do Relatório (Fase 2)

Use **exatamente** estes formatos. A Fase 1 imprime o primeiro bloco; a Fase 2
gera o relatório completo e o salva em `reports/audit-project-<N>.md`.

## Bloco da Fase 1 (resumo da análise)

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
================================
```

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

### [CRITICAL] <...>
File: <...>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================
```

## Regras de preenchimento

- **Ordem**: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, do mais
  impactante para o menos.
- **File**: sempre `caminho:linha` ou `caminho:inicio-fim`. Quando o mesmo
  anti-pattern ocorre em muitos pontos, agrupe num finding e cite o arquivo +
  o método/endpoint + o número de ocorrências (ex.:
  `models.py — login_usuario, criar_usuario (+22 queries)`).
- **Summary**: a soma dos contadores = `Total`.
- **Recommendation**: aponte o padrão de refatoração correspondente
  (ex.: "RF-02 — queries parametrizadas").
- **Não invente** findings para inflar números; reporte o que existe.

## Plano de refatoração (apresentado junto ao relatório)

Após o relatório, apresente o plano (ver SKILL.md, Fase 2.2). Formato sugerido:

```
## Refactoring Plan

Target structure:
<árvore de diretórios MVC>

Steps (prioridade CRITICAL → LOW):
1. [CRITICAL] <ação> — resolve <finding(s)> — padrão <RF-xx>
2. [CRITICAL] <ação> — ...
3. [HIGH]     <ação> — ...
...

Contract to preserve:
- Rotas: <lista da Fase 1>
- Boot: <comando original>

Validation:
- App sobe sem erros
- Todos os endpoints respondem
- Nenhum sinal CRITICAL/HIGH remanescente
```
