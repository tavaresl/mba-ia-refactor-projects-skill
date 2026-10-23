# Referência — Playbook de Refatoração (Fase 2 plano e Fase 3)

Padrões concretos de transformação, um por anti-pattern do catálogo. Cada um tem
**antes → depois**. Aplique na ordem de prioridade do plano (CRITICAL → LOW),
sempre preservando o contrato externo (ver `mvc-guidelines.md`).

---

## RF-01 — Config via ambiente (resolve AP-SEC-01, AP-SEC-06)

**Antes (Python)**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois (`config/settings.py`)**
```python
import os
class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]            # obrigatório, sem default inseguro
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "app.db")
```
**Antes (Node)**
```js
const config = { paymentGatewayKey: "pk_live_123...", dbPass: "senha..." };
```
**Depois (`config/index.js`)**
```js
module.exports = {
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  dbPass: process.env.DB_PASS,
  port: process.env.PORT || 3000,
};
```
Forneça um `.env.example` com as chaves (sem valores reais). Mantenha o default
igual ao valor antigo **só** para parâmetros não-sensíveis (ex.: porta).

---

## RF-02 — Queries parametrizadas (resolve AP-SEC-02)

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```
**Node (antes → depois)**
```js
db.get("SELECT * FROM users WHERE id = " + id, cb);      // antes
db.get("SELECT * FROM users WHERE id = ?", [id], cb);    // depois
```
Nunca concatene input em SQL. Use sempre placeholders do driver/ORM.

**Mesmo com valores fixos, não concatene.** Nomes de tabela ou trechos
constantes também devem virar instruções SQL completas e fixas, para o código
não disparar o próprio sinal do catálogo e não abrir brecha se a lista mudar:

```python
# antes
for tabela in ("itens_pedido", "pedidos"):
    db.execute("DELETE FROM " + tabela)
# depois
RESET_STATEMENTS = ("DELETE FROM itens_pedido", "DELETE FROM pedidos")
for stmt in RESET_STATEMENTS:
    db.execute(stmt)
```

---

## RF-03 — Quebrar a God Class em camadas (resolve AP-ARCH-01)

**Antes**: `AppManager` com conexão + schema + rotas + regra de negócio.
**Depois**: separe em arquivos por responsabilidade:
```
config/        # credenciais e parâmetros
db/            # conexão + inicialização do schema
models/        # acesso a dados por entidade (user, course, ...)
services/      # regra de negócio (checkout, relatório)
controllers/   # orquestra cada caso de uso
routes/        # métodos + paths -> controllers
middlewares/   # erro, auth
app.js         # compõe tudo (composition root)
```
Mova cada responsabilidade para o seu arquivo; o entry point passa a apenas
montar as peças.

---

## RF-04 — Mover regra de negócio para controller/serviço (resolve AP-ARCH-02, AP-QUAL-03)

**Antes (regra dentro da rota/model)**
```python
# na rota: calcula total, baixa estoque, monta resposta, tudo inline
```
**Depois**
```python
# routes/pedido_routes.py
@bp.post("/pedidos")
def criar_pedido():
    dados = PedidoSchema().load(request.get_json())   # validação
    return jsonify(pedido_controller.criar(dados)), 201

# controllers/pedido_controller.py
def criar(dados):
    return pedido_service.criar_pedido(dados["usuario_id"], dados["itens"])

# services/pedido_service.py  (regra de negócio, sem HTTP/SQL direto)
def criar_pedido(usuario_id, itens):
    ...  # usa models para persistir
```
Rotas finas, controllers orquestram, serviços contêm a regra.

---

## RF-05 — Estado global → instância injetada / conexão por requisição (resolve AP-ARCH-03, AP-ARCH-04)

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
**Depois (Flask)**
```python
from flask import g
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```
**Node**: nada de `let globalCache = {}` compartilhado — passe dependências via
construtor/parâmetro (injeção), e use o cache/estado dentro da instância.

---

## RF-06 — N+1 → JOIN / eager loading (resolve AP-PERF-01)

**Antes**
```python
for pedido in pedidos:
    itens = query("SELECT * FROM itens WHERE pedido_id = ?", pedido.id)
    for item in itens:
        nome = query("SELECT nome FROM produtos WHERE id = ?", item.produto_id)
```
**Depois**
```python
rows = query("""
  SELECT p.id, i.produto_id, pr.nome, i.quantidade
  FROM pedidos p
  JOIN itens_pedido i ON i.pedido_id = p.id
  JOIN produtos pr ON pr.id = i.produto_id
""")  # uma query; agrupe em memória
```
Com ORM: use `joinedload`/`selectinload` (SQLAlchemy) em vez de acessar o
relacionamento dentro do laço.

---

## RF-07 — Error handler central (resolve AP-QUAL-01, AP-SEC-05)

**Antes**
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500   # repetido em todo handler, vaza interno
```
**Depois (Flask)**
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle(e):
    app.logger.exception(e)
    code = getattr(e, "code", 500)
    return jsonify({"error": e.description if hasattr(e, "description") else "Erro interno"}), code
```
**Express**
```js
app.use((err, req, res, next) => {
  logger.error(err);
  res.status(err.status || 500).json({ error: "Erro interno" });
});
```
Handlers deixam de capturar `Exception`/`except:` e passam a deixar o erro subir.

**Nunca devolva a mensagem da exceção na resposta** — nem em rotas de admin.
Registre o detalhe no log e responda com uma mensagem fixa:

```python
# antes
except sqlite3.Error as err:
    raise ApiError(str(err), 500)
# depois
except sqlite3.Error:
    logger.exception("Falha ao executar consulta administrativa")
    raise ApiError("Consulta inválida ou não permitida", 400)
```

**Preserve o formato das respostas de erro.** Se a API original devolvia
`{"erro": "..."}` num caso e `{"erro": "...", "sucesso": false}` em outro, o
handler central deve reproduzir cada formato — não acrescente nem remova
campos.

---

## RF-08 — Hashing de senha seguro (resolve AP-SEC-03)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
**Depois (Python)**
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)          # pbkdf2/scrypt + sal
# verificação:
check_password_hash(self.password, pwd)
```
**Node**
```js
const crypto = require("crypto");
const hash = crypto.scryptSync(pwd, salt, 64).toString("hex");  // com sal
```
> Se houver seed/dados existentes com o hash antigo, atualize o seed para gerar
> o novo formato (e re-rode o seed na validação).

---

## RF-09 — Callbacks aninhados → async/await (resolve AP-ARCH-05)

**Antes**
```js
db.get(q1, (e, a) => { db.run(q2, (e) => { db.run(q3, (e) => { res.json(...) }) }) });
```
**Depois**
```js
const { promisify } = require("util");
const get = promisify(db.get.bind(db)), run = promisify(db.run.bind(db));
async function checkout(req, res, next) {
  try {
    const a = await get(q1, [..]);
    await run(q2, [..]);
    await run(q3, [..]);
    res.json(...);
  } catch (e) { next(e); }   // vai para o error handler central
}
```

---

## RF-10 — API deprecated → equivalente moderno (resolve AP-DEPR-01)

```python
datetime.utcnow()              # antes
datetime.now(timezone.utc)     # depois

User.query.get(id)             # antes (SQLAlchemy 2.x)
db.session.get(User, id)       # depois
```
```js
new Buffer(x)                  // antes
Buffer.from(x)                 // depois
```
Consulte a tabela de substituição em `anti-patterns-catalog.md` (AP-DEPR-01).

---

## RF-11 — Magic numbers → constantes nomeadas (resolve AP-QUAL-05)

**Antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
```
**Depois**
```python
# config ou módulo de constantes
FAIXA_DESCONTO_ALTO = 10_000
TAXA_DESCONTO_ALTO = 0.10
if faturamento > FAIXA_DESCONTO_ALTO:
    desconto = faturamento * TAXA_DESCONTO_ALTO
```

---

## RF-12 — `print`/`console.log` → logger (resolve AP-QUAL-04)

**Antes**
```python
print("Login bem-sucedido: " + email)
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Login bem-sucedido", extra={"email": email})
```
**Node**: use um logger (`console` configurado, `pino`, `winston`) em vez de
`console.log` espalhado.

---

## RF-13 — Remover campos sensíveis da serialização/logs (resolve AP-SEC-04, AP-QUAL-03)

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, ...}
```
**Depois**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role, ...}  # sem password
```
Centralize a serialização no model (um `to_dict` só, reutilizado) e nunca logue
cartão/senha/segredo.

---

## RF-14 — Camada de validação de entrada (resolve AP-QUAL-02, AP-SEC-05)

**Antes**
```python
nome = dados.get("nome", "")   # sem checar; default silencioso
```
**Depois (Python, marshmallow)**
```python
class UsuarioSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    email = fields.Email(required=True)
    senha = fields.Str(required=True, validate=validate.Length(min=6))

dados = UsuarioSchema().load(request.get_json())   # erro -> handler central
```
**Express**: valide o corpo (ex.: schema) antes do controller; rejeite
campos obrigatórios ausentes em vez de aplicar default silencioso.

**Invariantes de negócio**: valide no serviço, antes de gravar, as regras que
o payload sozinho não garante:

```python
# antes: checa cada item contra o estoque atual; itens repetidos furam o limite
for item in itens:
    if produto(item.id).estoque < item.quantidade: erro()
# depois: quantidades positivas e soma por produto antes de checar
for item in itens:
    if not isinstance(item.quantidade, int) or item.quantidade <= 0: erro(400)
pedido = Counter()
for item in itens:
    pedido[item.produto_id] += item.quantidade
for produto_id, qtd in pedido.items():
    if produto(produto_id).estoque < qtd: erro(400)
```

---

## RF-15 — Endpoints perigosos: desligados por padrão, token do ambiente, somente-leitura (resolve AP-SEC-05)

Aplica a política de `mvc-guidelines.md`. A rota continua existindo (contrato),
mas só funciona quando um token de admin é configurado no ambiente.

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])   # qualquer SQL, sem auth, com commit
    db.commit()
```
**Depois (Flask)**
```python
# middlewares/admin_auth.py
def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(esperado, recebido):
            raise ApiError("Acesso negado", 403)          # desligado sem token configurado
        return view(*args, **kwargs)
    return wrapper

# models/admin_model.py — conexão somente-leitura para consultas arbitrárias
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```
**Depois (Express)**
```js
function adminRequired(req, res, next) {
  const expected = process.env.ADMIN_TOKEN || "";
  const received = req.get("X-Admin-Token") || "";
  const ok = expected && received.length === expected.length &&
             crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected));
  return ok ? next() : res.status(403).json({ error: "Acesso negado" });
}
```
Remova o endpoint só se o usuário pedir. Em qualquer caso, liste a mudança no
plano como intencional e documente `ADMIN_TOKEN` no `.env.example`.
