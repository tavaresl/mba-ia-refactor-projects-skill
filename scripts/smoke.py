#!/usr/bin/env python3
"""Smoke test HTTP para os projetos do desafio refactor-arch.

Sobe a aplicação, chama todas as rotas descritas num arquivo de spec (JSON),
derruba a aplicação e grava a saída em arquivos comparáveis com `diff`
entre o baseline (código original) e o código refatorado.

Uso:
    python3 scripts/smoke.py scripts/specs/p1-code-smells.json --out evidencias/baseline/p1
    python3 scripts/smoke.py SPEC --out PREFIXO --start ".venv/bin/python app.py"

Arquivos gerados:
    PREFIXO.txt            resposta completa de cada requisição (timestamps mascarados)
    PREFIXO.contract.txt   uma linha por requisição: status + formato do JSON
    PREFIXO.server.log     saída da aplicação durante o teste

Usa só a biblioteca padrão e funciona com Python 3.9+.
Código de saída: 0 = tudo como esperado, 1 = falha de execução, 2 = status diferente do esperado.
"""
import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
READY_TIMEOUT_S = 30
REQUEST_TIMEOUT_S = 10
STOP_TIMEOUT_S = 5

# Valores que mudam a cada execução (datas e horas) são mascarados para o diff ficar estável.
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?")
HTTP_DATE_RE = re.compile(r"^[A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} GMT$")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


# ---------------------------------------------------------------- servidor

def port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def run_setup(commands, cwd, env, log):
    for cmd in commands:
        log.write(f"$ {cmd}\n")
        log.flush()
        result = subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                                stdout=log, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            raise RuntimeError(f"comando de setup falhou ({result.returncode}): {cmd}")


def start_server(cmd, cwd, env, log):
    log.write(f"$ {cmd}\n")
    log.flush()
    # Sessão própria: permite derrubar o processo e os filhos (reloader, npm -> node) de uma vez.
    return subprocess.Popen(cmd, shell=True, cwd=cwd, env=env, stdout=log,
                            stderr=subprocess.STDOUT, start_new_session=True)


def wait_until_ready(proc, url):
    deadline = time.monotonic() + READY_TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"a aplicação encerrou durante o boot (código {proc.returncode})")
        try:
            urllib.request.urlopen(url, timeout=1).close()
            return
        except urllib.error.HTTPError:
            return  # qualquer resposta HTTP (inclusive 404) indica que o servidor está no ar
        except (urllib.error.URLError, ConnectionError, socket.timeout):
            time.sleep(0.3)
    raise RuntimeError(f"a aplicação não respondeu em {READY_TIMEOUT_S}s")


def stop_server(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=STOP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    except ProcessLookupError:
        pass


# ------------------------------------------------------------- requisições

def substitute(value, saved):
    """Troca {variavel} por valores salvos de respostas anteriores."""
    if isinstance(value, str):
        whole = PLACEHOLDER_RE.fullmatch(value)
        if whole and whole.group(1) in saved:
            return saved[whole.group(1)]  # mantém o tipo original (ex.: int)
        return PLACEHOLDER_RE.sub(lambda m: str(saved.get(m.group(1), m.group(0))), value)
    if isinstance(value, list):
        return [substitute(item, saved) for item in value]
    if isinstance(value, dict):
        return {key: substitute(item, saved) for key, item in value.items()}
    return value


def lookup(data, dotted_path):
    for part in dotted_path.split("."):
        if isinstance(data, list) and part.isdigit():
            data = data[int(part)]
        elif isinstance(data, dict):
            data = data[part]
        else:
            raise KeyError(dotted_path)
    return data


def send(base_url, method, path, body, headers):
    data = None
    all_headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        all_headers["Content-Type"] = "application/json"
    all_headers.update(headers or {})
    req = urllib.request.Request(base_url + path, data=data, method=method, headers=all_headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def parse_json(text):
    try:
        return json.loads(text), True
    except ValueError:
        return text, False


# ------------------------------------------------------------ normalização

def mask_volatile(value):
    if isinstance(value, str) and (DATE_PREFIX_RE.match(value) or HTTP_DATE_RE.match(value)):
        return "<timestamp>"
    if isinstance(value, list):
        return [mask_volatile(item) for item in value]
    if isinstance(value, dict):
        return {key: mask_volatile(item) for key, item in value.items()}
    return value


def sort_lists(value):
    if isinstance(value, list):
        items = [sort_lists(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, dict):
        return {key: sort_lists(item) for key, item in value.items()}
    return value


def shape_of(value):
    """Formato do JSON: tipos e chaves, sem os valores. int e float viram 'number'."""
    if value is None:
        return {"null": True}
    if isinstance(value, bool):
        return {"bool": True}
    if isinstance(value, (int, float)):
        return {"number": True}
    if isinstance(value, str):
        return {"str": True}
    if isinstance(value, list):
        element = None
        for item in value:
            element = merge_shapes(element, shape_of(item))
        return {"array": element}
    return {"object": {key: shape_of(item) for key, item in value.items()}}


def merge_shapes(a, b):
    if a is None:
        return b
    if b is None:
        return a
    merged = dict(a)
    for kind, detail in b.items():
        if kind not in merged:
            merged[kind] = detail
        elif kind == "object":
            absent = {"absent": True}
            keys = set(merged[kind]) | set(detail)
            merged[kind] = {key: merge_shapes(merged[kind].get(key, absent), detail.get(key, absent))
                            for key in keys}
        elif kind == "array":
            merged[kind] = merge_shapes(merged[kind], detail)
    return merged


def render_shape(shape):
    if shape is None:
        return ""
    parts = []
    if "object" in shape:
        fields = []
        for key in sorted(shape["object"]):
            sub = dict(shape["object"][key])
            optional = sub.pop("absent", False)
            fields.append(f"{key}{'?' if optional else ''}: {render_shape(sub)}")
        parts.append("{" + ", ".join(fields) + "}")
    if "array" in shape:
        parts.append("[" + render_shape(shape["array"]) + "]")
    parts += [kind for kind in ("str", "number", "bool", "null") if kind in shape]
    return "|".join(parts)


# -------------------------------------------------------------------- main

def run_requests(spec, base_url, full_out, contract_out):
    saved = {}
    mismatches = 0
    for index, item in enumerate(spec["requests"], start=1):
        method = item.get("method", "GET").upper()
        path_template = item["path"]
        path = substitute(path_template, saved)
        body = substitute(item.get("body"), saved)
        expected = item.get("expect")

        try:
            status, text = send(base_url, method, path, body, item.get("headers"))
        except (urllib.error.URLError, ConnectionError, socket.timeout) as err:
            status, text = "ERR", str(err)

        parsed, is_json = parse_json(text)
        for name, dotted_path in item.get("save", {}).items():
            try:
                saved[name] = lookup(parsed, dotted_path)
            except (KeyError, IndexError, TypeError):
                pass

        ok = expected is None or status == expected
        mismatches += 0 if ok else 1
        flag = "" if ok else f"   !! esperado {expected}"
        print(f"  {index:02d} {method:6} {path:45} {status}{flag}")

        if is_json:
            normalized = mask_volatile(parsed)
            if item.get("sort_lists"):
                normalized = sort_lists(normalized)
            body_text = json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False)
            shape_text = render_shape(shape_of(parsed))
        else:
            body_text = text.strip() or "<vazio>"
            shape_text = "text" if text.strip() else "empty"

        full_out.write(f"### {index:02d}. {item.get('label', '')}\n")
        full_out.write(f"{method} {path_template}" + (f"  ->  {path}" if path != path_template else "") + "\n")
        if body is not None:
            full_out.write(f"request: {json.dumps(body, ensure_ascii=False, sort_keys=True)}\n")
        full_out.write(f"status: {status}{flag}\n{body_text}\n\n")
        contract_out.write(f"{index:02d} {method} {path_template} -> {status} {shape_text}\n")
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spec", help="arquivo JSON com as requisições")
    parser.add_argument("--out", required=True, help="prefixo dos arquivos de saída")
    parser.add_argument("--start", help="sobrescreve o comando de boot da spec ({port} é substituído)")
    parser.add_argument("--setup", action="append", help="sobrescreve os comandos de setup (pode repetir)")
    parser.add_argument("--port", type=int, help="sobrescreve a porta da spec")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    port = args.port or spec["port"]
    cwd = REPO_ROOT / spec["cwd"]
    setup = args.setup if args.setup is not None else spec.get("setup", [])
    start_cmd = (args.start or spec["start"]).replace("{port}", str(port))
    base_url = f"http://127.0.0.1:{port}"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PORT=str(port), PYTHONUNBUFFERED="1")

    if port_in_use(port):
        print(f"ERRO: a porta {port} já está em uso. Libere-a ou use --port.", file=sys.stderr)
        return 1

    print(f"[{spec['name']}] {base_url}  ({len(spec['requests'])} requisições)")
    with open(f"{out}.server.log", "w", encoding="utf-8") as log:
        proc = None
        try:
            run_setup(setup, cwd, env, log)
            proc = start_server(start_cmd, cwd, env, log)
            wait_until_ready(proc, base_url + spec.get("ready_path", "/"))
            with open(f"{out}.txt", "w", encoding="utf-8") as full_out, \
                    open(f"{out}.contract.txt", "w", encoding="utf-8") as contract_out:
                mismatches = run_requests(spec, base_url, full_out, contract_out)
        except RuntimeError as err:
            print(f"ERRO: {err}. Veja {out}.server.log", file=sys.stderr)
            return 1
        finally:
            if proc is not None:
                stop_server(proc)

    total = len(spec["requests"])
    print(f"[{spec['name']}] {total - mismatches}/{total} com o status esperado -> {out}.txt")
    return 2 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
