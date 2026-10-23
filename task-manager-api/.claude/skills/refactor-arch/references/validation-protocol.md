# Referência — Protocolo de Validação (Fase 3)

Como provar que a refatoração não quebrou a aplicação, usando **apenas** a
PROJECT_ROOT e ferramentas do sistema. O protocolo roda duas vezes: antes de
qualquer alteração (baseline) e depois da refatoração (comparação).

## Regras gerais

1. **Execute com `bash` explícito — em todas as fases.** Escreva os passos num
   script em `<PROJECT_ROOT>/reports/.tmp/` (ex.: `scan.sh` nas buscas da
   auditoria, `validate.sh` na Fase 3) e rode com `bash <script>`. Não dependa
   do shell interativo do usuário (no `zsh`, variáveis sem aspas não são
   separadas em palavras e globs sem resultado abortam o comando).
2. **Arquivos temporários só em `reports/.tmp/`.** Nunca em `/tmp`, no
   scratchpad da ferramenta ou fora da PROJECT_ROOT. Apague `reports/.tmp/` no
   fim.
3. **Sem comandos de controle de versão** (`git` etc.), nem para consultar o
   código original: ele está na cópia de `reports/.tmp/original-src/` (abaixo).
4. **Porta livre, confirmada antes do boot.** Não confie na porta padrão do
   projeto: outro processo pode estar nela (no macOS, o AirPlay ocupa a 5000 e
   responde 403). Escolha uma porta livre e passe por variável de ambiente
   (`PORT`). Se a porta estava livre antes do boot e o processo iniciado está
   vivo, quem responde é a aplicação.
5. **PID guardado e servidor sempre encerrado**, inclusive se algo falhar no
   meio (use `trap ... EXIT`). Ao final, confirme que a porta ficou livre.
6. **Mesmo estado inicial nas duas execuções.** Antes do baseline, copie os
   arquivos de dados do projeto (ex.: `*.db`, `*.sqlite`) para
   `reports/.tmp/data-backup/`. Restaure-os antes de cada execução e no fim.
   Se um arquivo de dados não existia, garanta que ele não exista antes de cada
   execução. Rode a preparação do projeto (seed, migrations) identificada na
   Fase 1 antes de cada execução.
7. **Rotas destrutivas por último** (DELETE, reset, limpeza).

## Cópia dos fontes originais (antes de qualquer alteração)

Logo após a confirmação da Fase 3, antes de capturar o baseline:

```bash
mkdir -p reports/.tmp/original-src
# copie o escopo da Fase 1 + manifestos + scripts de preparação (seed, migrations)
rsync -a --exclude '.claude' --exclude 'reports' --exclude '.venv' --exclude 'venv' \
  --exclude 'node_modules' --exclude '__pycache__' --exclude '*.db' --exclude 'instance' \
  ./ reports/.tmp/original-src/
```

Se o baseline precisar ser refeito depois que o código já mudou, rode o app a
partir dessa cópia (com as dependências da PROJECT_ROOT, ex.: o mesmo `.venv`
ou `node_modules` via caminho relativo). **Nunca** reconstrua o código original
de memória.

## Cobertura mínima das chamadas

O baseline e a comparação usam as mesmas chamadas. No mínimo:

- **cada rota** do inventário da Fase 1, no caso de sucesso;
- **cada rota com parâmetro de caminho**: um ID inexistente;
- **cada POST/PUT/PATCH**: um corpo válido, um corpo sem campo obrigatório e
  um JSON malformado (ex.: `-d '{'`);
- **cada mudança intencional do plano**: pelo menos uma chamada que a prove;
- **cada rota protegida pela política de endpoints perigosos**: sem token e com
  token;
- **dados de seed**: um login (ou leitura) com as credenciais/valores
  documentados, para provar que continuam valendo;
- rotas destrutivas por último.

## IDs dinâmicos

Não fixe IDs de recursos criados durante o teste: capture-os da resposta e
reutilize nas chamadas seguintes, para que o mesmo script funcione no app
original e no refatorado.

```bash
# depois de um POST que devolve o recurso criado
NEW_ID=$(grep -oE '"id" *: *[0-9]+' "$TMP/body" | head -1 | grep -oE '[0-9]+')
call PUT "/recursos/$NEW_ID" '{"campo": "novo"}'
```

## Porta do app original

- Se o app original lê a porta de ambiente, use `PORT`.
- Se o app original **fixa** a porta no código: use essa porta se estiver
  livre; se não estiver, use o mecanismo do framework para trocar a porta sem
  editar código (Flask: `flask --app <módulo> run --port <porta>`); se não
  houver mecanismo, registre que o baseline não pôde ser capturado e valide só
  o app refatorado.
- O app refatorado **deve** ler a porta de config/ambiente, mantendo o padrão
  original quando a variável não existir.

## Script-modelo (adapte ao projeto)

```bash
#!/usr/bin/env bash
# Uso: bash reports/.tmp/validate.sh <saida.txt> <comando de boot>
set -u
set -m                                  # cada job em background ganha seu próprio grupo de processos
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$1"; shift
BOOT_CMD="$*"
TMP="$ROOT/reports/.tmp"
mkdir -p "$TMP"
cd "$ROOT"

# 1. porta livre
PORT=""
for p in $(seq 5050 5099); do
  if ! (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then PORT="$p"; break; fi
done
[ -n "$PORT" ] || { echo "nenhuma porta livre" >&2; exit 1; }
export PORT

# 2. boot em background, com encerramento garantido
PORT="$PORT" bash -c "$BOOT_CMD" > "$TMP/boot.log" 2>&1 &
PID=$!
cleanup() { kill -- -"$PID" 2>/dev/null; wait "$PID" 2>/dev/null; }
trap cleanup EXIT

# 3. espera ficar pronto (ou falha se o processo morrer)
for _ in $(seq 1 60); do
  kill -0 "$PID" 2>/dev/null || { echo "app morreu no boot"; cat "$TMP/boot.log"; exit 1; }
  curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break
  sleep 0.5
done

# 4. chamadas (uma linha por rota do inventário da Fase 1)
call() {  # call METODO PATH [JSON] [HEADER]
  local method="$1" path="$2" body="${3:-}" header="${4:-}"
  local args=(-s -o "$TMP/body" -w "%{http_code}" -X "$method")
  [ -n "$body" ] && args+=(-H "Content-Type: application/json" -d "$body")
  [ -n "$header" ] && args+=(-H "$header")
  local code; code=$(curl "${args[@]}" "http://127.0.0.1:$PORT$path")
  printf '### %s %s\nstatus: %s\n%s\n\n' "$method" "$path" "$code" "$(cat "$TMP/body")" >> "$OUT"
}
: > "$OUT"
call GET  /
call POST /exemplo '{"campo": "valor"}'
# ... todas as rotas, destrutivas por último ...
```

## Comparação baseline × depois

1. Gere `reports/baseline-responses.txt` (app original) e
   `reports/after-responses.txt` (app refatorado) com **as mesmas chamadas, na
   mesma ordem e a partir do mesmo estado de dados**.
2. Mascare valores voláteis antes de comparar (datas/horas geradas na hora,
   tokens aleatórios):

   ```bash
   mask() { sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9:.]+/<ts>/g' "$1"; }
   diff <(mask reports/baseline-responses.txt) <(mask reports/after-responses.txt)
   ```

3. Para **cada** diferença: se estiver na lista de mudanças intencionais do
   plano, registre-a como esperada; se não estiver, é **regressão** — corrija o
   código e rode de novo. Isso inclui campos novos ou removidos nas respostas
   de erro (ex.: um `"sucesso": false` que não existia), **textos de mensagem
   diferentes** e mudanças em dados persistidos (ex.: um relatório que passou a
   somar menos porque registros foram apagados).
4. Rotas protegidas pela política de endpoints perigosos
   (`mvc-guidelines.md`): chame **sem** token (espera-se 403) e **com** token
   (espera-se o comportamento original permitido pela política).

## Reverificação do catálogo

Rode os `grep` dos sinais do catálogo sobre o escopo da Fase 1 e **copie a
saída real** para o relatório de validação. Não resuma ("2 ocorrências") sem
mostrar as linhas. Para cada linha que permanecer, explique por que ela é
aceitável.

## Limpeza (sempre)

- Servidores encerrados e porta livre (confirme).
- Arquivos de dados restaurados ao estado anterior aos testes.
- `reports/.tmp/` apagado.
