"""Run VisionText browser tests with reports independent of the application."""

import argparse
from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

from dotenv import dotenv_values
import requests

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
BACKEND = PROJECT / "VisionText-backend"
FRONTEND = PROJECT / "VisionText-frontend"
RENDER_API = "https://visiontext-backend.onrender.com"
VERCEL = "https://visiontext-sigma.vercel.app"


def login_credentials(environment):
    if environment == "local":
        return os.environ["VT_KARATE_ADMIN_USER"], os.environ["VT_KARATE_ADMIN_PASSWORD"]
    explicit = os.getenv("VT_WEB_USER"), os.getenv("VT_WEB_PASSWORD")
    if all(explicit):
        return explicit
    config = dotenv_values(BACKEND / ".env.render", interpolate=False)
    return config.get("ADMIN_USERNAME"), config.get("ADMIN_PASSWORD")


def health(session, api, timeout=20):
    response = session.get(api + "/api/health", timeout=(10, timeout), allow_redirects=False)
    response.raise_for_status()
    state = response.json()
    if state["status"] != "healthy" or state["images_in_db"] != state["vectors_in_index"]:
        raise RuntimeError("La API no informó un catálogo saludable y sincronizado.")
    return {name: state[name] for name in ("images_in_db", "vectors_in_index", "storage_provider")}


def seed_catalog(session, api, credentials):
    username, password = credentials
    response = session.post(api + "/api/admin/login", data={"username": username, "password": password},
                            timeout=15, allow_redirects=False)
    response.raise_for_status()
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    dataset = BACKEND / "dataset_final"
    paths = []
    for prefix, size in (("african_elephant_", 11), ("alpaca_", 11), ("zebra_", 10)):
        selected = sorted(dataset.glob(prefix + "*.jpg"))[:size]
        if len(selected) != size:
            raise RuntimeError(f"No hay suficientes imágenes de prueba para {prefix}.")
        paths.extend(selected)
    print(f"Preparando {len(paths)} imágenes en el catálogo temporal.", flush=True)
    for photo in paths:
        with photo.open("rb") as content:
            response = session.post(api + "/api/upload", headers=headers,
                                    files={"image": (photo.name, content, "image/jpeg")},
                                    timeout=40, allow_redirects=False)
        if response.status_code != 200 or not response.json().get("success"):
            raise RuntimeError(f"La carga de preparación falló para {photo.name} (HTTP {response.status_code}).")
    if health(session, api)["images_in_db"] != len(paths):
        raise RuntimeError("El catálogo inicial no tiene la cantidad esperada de imágenes.")
    return headers


def local_snapshot(session, api, headers):
    result = health(session, api)
    response = session.get(api + "/api/admin/storage", headers=headers, timeout=15, allow_redirects=False)
    response.raise_for_status()
    storage = response.json()
    return result | {name: storage[name] for name in ("images_bucket_count", "thumbnails_bucket_count")}


@contextmanager
def preview(session, api, work, port):
    node = shutil.which("node.exe") or shutil.which("node")
    vite = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
    if not node or not vite.is_file():
        raise RuntimeError("Instala las dependencias del frontend con npm ci.")
    dist = work / "selenium-dist"
    env = dict(os.environ, VITE_API_URL=api)
    subprocess.run([node, str(vite), "build", "--outDir", str(dist), "--emptyOutDir"],
                   cwd=FRONTEND, env=env, check=True, timeout=150)
    url = f"http://127.0.0.1:{port}"
    with (work / "vite-selenium.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([node, str(vite), "preview", "--host", "127.0.0.1", "--port", str(port),
                                   "--strictPort", "--outDir", str(dist)], cwd=FRONTEND, env=env,
                                  stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("Vite terminó antes de abrir VisionText. Consulta vite-selenium.log.")
                try:
                    response = session.get(url, timeout=1)
                    if response.status_code == 200 and "VisionText AI" in response.text:
                        break
                except requests.ConnectionError:
                    pass
                time.sleep(0.3)
            else:
                raise RuntimeError("Vite no estuvo disponible a tiempo.")
            yield url
        finally:
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=10)


def execute(args, url, directory, scratch, credentials):
    print(f"Selenium {args.entorno} en {url}. Reportes: {directory}", flush=True)
    env = dict(os.environ, VT_WEB_ENV=args.entorno, VT_WEB_URL=url,
               VT_WEB_VISIBLE="1" if args.visible else "0", VT_WEB_REPORT_DIR=str(directory),
               VT_WEB_USER=credentials[0], VT_WEB_PASSWORD=credentials[1])
    command = [
        sys.executable, "-m", "pytest", "-v", "--tb=short", "--html", str(directory / "index.html"),
        "--self-contained-html", "--junitxml", str(directory / "junit.xml"),
        "--basetemp", str(scratch / "pytest"),
    ]
    if args.caso:
        command += ["-k", args.caso]
    return subprocess.run(command, env=env, cwd=ROOT, timeout=1050).returncode


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--entorno", choices=("local", "render"), required=True)
    cli.add_argument("--api-url")
    cli.add_argument("--trabajo", type=Path)
    cli.add_argument("--puerto", type=int, default=4174)
    cli.add_argument("--caso", default="")
    cli.add_argument("--visible", action="store_true")
    args = cli.parse_args()
    local = args.entorno == "local"
    api = args.api_url if local else RENDER_API
    if local:
        origin = urlsplit(api or "")
        if (os.getenv("VT_KARATE_LOCAL_ISOLATED") != "1" or not args.trabajo or
                origin.scheme != "http" or origin.hostname != "127.0.0.1" or origin.username or
                origin.path or origin.query or origin.fragment or not origin.port):
            cli.error("Las escrituras requieren el backend local aislado del lanzador de PowerShell.")
    credentials = login_credentials(args.entorno)
    if not all(credentials):
        cli.error("Faltan credenciales del entorno. Para Render usa las variables VT_WEB_USER y VT_WEB_PASSWORD.")
    now = datetime.now().astimezone()
    run = now.strftime("%Y%m%d-%H%M%S-%f")
    report = ROOT / "reports" / args.entorno / run
    scratch = ROOT / "target" / run
    report.mkdir(parents=True)
    scratch.mkdir(parents=True)
    info = {"entorno": args.entorno, "fecha": now.isoformat(timespec="seconds"), "api": api,
            "brave": os.environ.get("BRAVE_BINARY"), "filtro": args.caso or None}
    status = 1
    try:
        with requests.Session() as session:
            session.trust_env = False
            info["salud_inicial"] = health(session, api, timeout=170 if not local else 20)
            if local:
                if info["salud_inicial"]["images_in_db"] != 0 or info["salud_inicial"]["storage_provider"] != "s3":
                    raise RuntimeError("Se esperaba una instancia aislada con S3 y un catálogo vacío.")
                token = seed_catalog(session, api, credentials)
                info["catalogo_antes"] = local_snapshot(session, api, token)
                with preview(session, api, args.trabajo, args.puerto) as url:
                    info["web"] = url
                    status = execute(args, url, report, scratch, credentials)
                info["catalogo_despues"] = local_snapshot(session, api, token)
                if info["catalogo_antes"] != info["catalogo_despues"]:
                    print("Los conteos del catálogo temporal cambiaron tras las pruebas.", flush=True)
                    status = 1
            else:
                info["web"] = VERCEL
                status = execute(args, VERCEL, report, scratch, credentials)
    finally:
        info["codigo_salida"] = status
        (report / "entorno.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
