"""Run native JMeter plans and index their evidence by environment."""

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import csv
from dataclasses import asdict
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit

from dotenv import dotenv_values
import requests

from perfiles import BACKEND, BUDGETS, CSV_FILE, DATASET, FLOWS, FRONTEND, OPERATIONS, PROFILES, RENDER_API, RENDER_WEB, ROOT


def date():
    return datetime.now().astimezone()


def save_json(path, result):
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def input_images():
    with CSV_FILE.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    names = [item["archivo"] for item in rows]
    if any(Path(name).name != name or Path(name).suffix.lower() not in (".jpg", ".jpeg") for name in names):
        raise ValueError("El CSV debe referenciar archivos JPEG por nombre dentro del dataset.")
    paths = [DATASET / name for name in names]
    if len(paths) < 6 or len(paths) != len(set(paths)) or any(not path.is_file() for path in paths):
        raise ValueError("Faltan imágenes del CSV o hay nombres duplicados en el dataset.")
    return paths


def credentials(env):
    if env == "local":
        return os.getenv("VT_KARATE_ADMIN_USER"), os.getenv("VT_KARATE_ADMIN_PASSWORD")
    given = os.getenv("VT_JMETER_ADMIN_USER"), os.getenv("VT_JMETER_ADMIN_PASSWORD")
    if all(given):
        return given
    values = dotenv_values(BACKEND / ".env.render", interpolate=False)
    return values.get("ADMIN_USERNAME"), values.get("ADMIN_PASSWORD")


def health(session, api):
    response = session.get(api + "/api/health", timeout=(10, 25), allow_redirects=False)
    response.raise_for_status()
    body = response.json()
    if body.get("status") != "healthy" or body.get("images_in_db") != body.get("vectors_in_index"):
        raise ValueError("La salud de la API o la correspondencia de sus registros y vectores es incorrecta.")
    return {key: body[key] for key in ("images_in_db", "vectors_in_index", "storage_provider", "inference_backend", "model")}


def seed_local(session, api, files, auth):
    started = time.monotonic()
    response = session.post(api + "/api/admin/login", data=dict(zip(("username", "password"), auth)),
                            timeout=(5, 15), allow_redirects=False)
    response.raise_for_status()
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    for path in files:
        with path.open("rb") as image:
            response = session.post(api + "/api/upload", headers=headers,
                                    files={"image": (path.name, image, "image/jpeg")},
                                    timeout=(5, 35), allow_redirects=False)
        if response.status_code != 200 or not response.json().get("success"):
            raise ValueError(f"No se pudo preparar la imagen {path.name} (HTTP {response.status_code}).")
    snapshot = health(session, api)
    if snapshot["storage_provider"] != "s3" or snapshot["images_in_db"] != len(files):
        raise ValueError("El catálogo local aislado no quedó completo.")
    return snapshot, headers, round(time.monotonic() - started, 3)


def storage_counts(session, api, headers):
    response = session.get(api + "/api/admin/storage", headers=headers, timeout=(5, 15), allow_redirects=False)
    response.raise_for_status()
    body = response.json()
    return {key: body[key] for key in ("images_bucket_count", "thumbnails_bucket_count")}


class QuietFiles(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass


@contextmanager
def local_web(enabled, directory, port, api):
    if not enabled:
        yield
        return
    node = shutil.which("node.exe") or shutil.which("node")
    vite = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
    if not node or not vite.is_file():
        raise ValueError("Instala las dependencias de VisionText-frontend con npm ci.")
    bundle = directory / "vite-dist"
    subprocess.run([node, str(vite), "build", "--outDir", str(bundle), "--emptyOutDir"],
                   cwd=FRONTEND, env=dict(os.environ, VITE_API_URL=api), check=True, timeout=120)
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(QuietFiles, directory=bundle))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def collect(folder, environment, profile, return_code):
    groups = PROFILES[environment][profile]
    expected = Counter()
    for group in groups:
        for key in FLOWS[group.flow]:
            expected[key] += group.users if key == "ADM-01" else (group.users * group.loops if group.loops > 0 else 0)
    jtl = folder / "muestras.jtl"
    rows = []
    if jtl.is_file():
        with jtl.open(encoding="utf-8-sig", newline="") as source:
            rows = list(csv.DictReader(source))
    dashboard = folder / "html"
    native_json = dashboard / "statistics.json"
    native = json.loads(native_json.read_text(encoding="utf-8")) if native_json.is_file() else {}
    issues = []
    if return_code:
        issues.append(f"Proceso JMeter terminó con código {return_code}.")
    if not rows:
        issues.append("El JTL no contiene muestras.")
    if not (dashboard / "index.html").is_file() or not native:
        issues.append("El dashboard nativo de JMeter está incompleto.")
    samples = defaultdict(list)
    for row in rows:
        samples[row["label"]].append(row)
    counts = Counter(row["label"].split(" ", 1)[0] for row in rows)
    for key, count in expected.items():
        if (count and counts[key] != count) or (not count and not counts[key]):
            issues.append(f"{key}: se esperaban {count or 'una o más'} muestras y se obtuvieron {counts[key]}.")
    failures = sum(row["success"].lower() != "true" for row in rows)
    if failures:
        issues.append(f"{failures} muestras fallaron por código, contenido, duración o conexión.")
    operations = {}
    for label, matching in sorted(samples.items()):
        key = label.split(" ", 1)[0]
        times = sorted(int(row["elapsed"]) for row in matching)
        duration_limit, p95_limit = BUDGETS[environment][OPERATIONS[key][0]]
        stats = native.get(label, {})
        p95 = stats.get("pct2ResTime", times[math.ceil(len(times) * 0.95) - 1])
        if p95 > p95_limit:
            issues.append(f"{key}: p95 de {p95:.1f} ms supera {p95_limit} ms.")
        operations[label] = {
            "muestras": len(matching), "fallos": sum(row["success"].lower() != "true" for row in matching),
            "codigos": dict(Counter(row["responseCode"] for row in matching)),
            "media_ms": round(sum(times) / len(times), 2), "p95_ms": round(p95, 2),
            "max_ms": max(times), "limite_muestra_ms": duration_limit, "objetivo_p95_ms": p95_limit,
            "motivos": dict(Counter(row.get("failureMessage") or "HTTP o transporte" for row in matching
                                    if row["success"].lower() != "true")),
        }
    seconds = ((max(int(row["timeStamp"]) + int(row["elapsed"]) for row in rows)
                - min(int(row["timeStamp"]) for row in rows)) / 1000) if rows else 0
    return {
        "perfil": profile, "grupos": [asdict(group) for group in groups], "estado": "REVISAR" if issues else "APROBADO",
        "muestras": len(rows), "fallos": failures, "error_pct": round(100 * failures / len(rows), 3) if rows else None,
        "ventana_con_muestras_s": round(seconds, 3), "muestras_por_segundo": round(len(rows) / seconds, 3) if seconds else None,
        "max_hilos_registrados": max((int(row["allThreads"]) for row in rows), default=0),
        "observaciones": issues, "operaciones": operations,
    }


def run_profile(args, run, profile, auth):
    folder = run / profile
    folder.mkdir()
    plan = ROOT / "plans" / args.entorno / f"{profile}.jmx"
    print(f"JMeter {args.entorno}/{profile}", flush=True)
    child_env = os.environ.copy()
    if profile in ("admin", "escritura"):
        if not all(auth):
            raise ValueError("Faltan las credenciales para medir el flujo de administración.")
        child_env["VT_JMETER_ADMIN_USER"], child_env["VT_JMETER_ADMIN_PASSWORD"] = auth
    api_port = urlsplit(args.api_url).port or 443
    cli = [
        args.java, "-Xms128m", "-Xmx512m", "-Dfile.encoding=UTF-8", "-jar", args.jmeter,
        "-n", "-t", str(plan), "-l", str(folder / "muestras.jtl"), "-j", str(folder / "jmeter.log"),
        "-i", str(ROOT / "config" / "log4j2.xml"), "-q", str(ROOT / "config" / "evidencia.properties"),
        "-e", "-o", str(folder / "html"), f"-JAPI_PORT={api_port}", f"-JWEB_PORT={args.web_port}",
        f"-JQUERY_CSV={CSV_FILE}", f"-JDATASET={DATASET}", f"-JINVALID_FILE={ROOT / 'data' / 'no-imagen.txt'}",
        f"-Jjmeter.reportgenerator.report_title=VisionText {args.entorno} {profile}",
    ]
    with (folder / "consola.log").open("w", encoding="utf-8") as output:
        code = subprocess.run(cli, cwd=ROOT, env=child_env, stdout=output, stderr=subprocess.STDOUT, timeout=420).returncode
    report = collect(folder, args.entorno, profile, code)
    save_json(folder / "metricas.json", report)
    print(f"{profile}: {report['estado']} | {report['muestras']} muestras | {report['fallos']} fallos", flush=True)
    return report


def write_index(run, result):
    save_json(run / "ejecucion.json", result)
    lines = [
        f"# VisionText en JMeter · {result['entorno']}", "",
        f"Inicio de la ejecución `{result['inicio']}`.",
        f"API `{result['api']}`. Web `{result['web']}`.", "",
    ]
    if result.get("catalogo"):
        catalog = result["catalogo"]
        lines += [f"Catálogo al medir `{catalog['images_in_db']}` imágenes y `{catalog['vectors_in_index']}` vectores. "
                  f"Almacenamiento `{catalog['storage_provider']}`. Inferencia `{catalog['inference_backend']}`.", ""]
    if result.get("arranque_api_local_ms") is not None:
        lines += [f"El proceso local tardó **{result['arranque_api_local_ms']} ms** en quedar listo. "
                  "El perfil `inicio` mide la petición HTTP posterior a la comprobación de salud.", ""]
    if result.get("hilos_inferencia"):
        lines += [f"El número de hilos de inferencia del backend local fue **{result['hilos_inferencia']}**.", ""]
    if result.get("observaciones"):
        lines += [f"- {note}" for note in result["observaciones"]] + [""]
    lines += ["| Perfil | Estado | Muestras | Fallos | Hilos máximos | Muestras/s | Archivos |",
              "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for profile in result["perfiles"]:
        name = profile["perfil"]
        links = f"[HTML]({name}/html/index.html) · [JTL]({name}/muestras.jtl) · [Métricas]({name}/metricas.json)"
        if profile["muestras"] == 0:
            links = f"[Registro]({name}/metricas.json)"
        lines.append(f"| {name} | {profile['estado']} | {profile['muestras']} | {profile['fallos']} | "
                     f"{profile['max_hilos_registrados']} | {profile['muestras_por_segundo'] or '—'} | {links} |")
    for profile in result["perfiles"]:
        if profile["observaciones"]:
            lines += ["", f"**{profile['perfil']}**", ""] + [f"- {issue}" for issue in profile["observaciones"]]
    (run / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entorno", choices=PROFILES, required=True)
    parser.add_argument("--perfil", action="append", default=[])
    parser.add_argument("--java", required=True)
    parser.add_argument("--jmeter", required=True)
    parser.add_argument("--api-url")
    parser.add_argument("--web-port", type=int, default=4173)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--arranque-ms", type=int)
    parser.add_argument("--solo-publico", action="store_true")
    args = parser.parse_args()
    env = args.entorno
    requested = args.perfil or PROFILES[env]
    if any(name not in PROFILES[env] for name in requested):
        parser.error(f"Perfiles de {env}: {', '.join(PROFILES[env])}")
    profiles = [name for name in PROFILES[env] if name in requested and (not args.solo_publico or name != "admin")]
    if not profiles:
        parser.error("Selecciona al menos un perfil para medir.")
    if env == "local":
        api = urlsplit(args.api_url or "")
        if (not args.trabajo or api.scheme != "http" or api.hostname != "127.0.0.1" or
                api.username or api.password or api.path or api.query or api.fragment or not api.port):
            parser.error("Usa el lanzador de PowerShell para iniciar el entorno local aislado.")
        web = f"http://127.0.0.1:{args.web_port}"
    else:
        args.api_url, web = RENDER_API, RENDER_WEB
    start = date()
    run = ROOT / "reports" / env / start.strftime("%Y%m%d-%H%M%S-%f")
    run.mkdir(parents=True)
    plan_deps = input_images()
    auth = credentials(env) if env == "local" or "admin" in profiles else (None, None)
    report = {
        "entorno": env, "inicio": start.isoformat(timespec="seconds"), "api": args.api_url, "web": web,
        "sistema_generador": platform.platform(), "procesadores_logicos": os.cpu_count(),
        "arranque_api_local_ms": args.arranque_ms, "catalogo": None, "perfiles": [], "observaciones": [],
    }
    if env == "local":
        report["hilos_inferencia"] = int(os.environ.get("INFERENCE_THREADS", "1"))
    print(f"Resultados: {run}", flush=True)

    def run_one(name):
        try:
            result = run_profile(args, run, name, auth)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            issue = f"No se completó {name}: {type(error).__name__}: {error}"
            result = dict(perfil=name, estado="REVISAR", muestras=0, fallos=0,
                          max_hilos_registrados=0, muestras_por_segundo=None, observaciones=[issue])
            folder = run / name
            folder.mkdir(exist_ok=True)
            save_json(folder / "metricas.json", result)
        report["perfiles"].append(result)
        write_index(run, report)

    with requests.Session() as session:
        session.trust_env = False
        if "inicio" in profiles:
            run_one("inicio")
        if env == "render":
            try:
                snapshot = health(session, args.api_url)
                if snapshot["storage_provider"] != "google_drive":
                    raise ValueError("Render no reportó el proveedor Drive esperado.")
                report["catalogo"] = snapshot
            except (requests.RequestException, ValueError) as error:
                report["observaciones"].append(f"No se pudo capturar el catálogo de Render ({type(error).__name__}).")
        elif any(name != "inicio" for name in profiles):
            if not all(auth):
                parser.error("Faltan las credenciales temporales del entorno local.")
            print(f"Preparando {len(plan_deps)} imágenes locales del CSV fuera de la medición.", flush=True)
            report["catalogo"], headers, report["preparacion_catalogo_s"] = seed_local(session, args.api_url, plan_deps, auth)
            stored_before = storage_counts(session, args.api_url, headers)

        for name in profiles:
            if name in ("inicio", "web"):
                continue
            if env == "render" and name == "admin" and not report["catalogo"]:
                report["observaciones"].append("Admin de Render quedó pendiente porque la comprobación de salud no se completó.")
                continue
            run_one(name)

        if "web" in profiles:
            try:
                with local_web(env == "local", args.trabajo, args.web_port, args.api_url):
                    run_one("web")
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                report["observaciones"].append(f"Web quedó pendiente al preparar el servidor: {error}")
        if env == "local" and "escritura" in profiles:
            report["catalogo_final"] = health(session, args.api_url)
            report["s3_antes"] = stored_before
            report["s3_despues"] = storage_counts(session, args.api_url, headers)
            if report["catalogo_final"] != report["catalogo"] or report["s3_antes"] != report["s3_despues"]:
                report["observaciones"].append("Los conteos posteriores al ciclo de escritura cambiaron.")
    report["fin"] = date().isoformat(timespec="seconds")
    write_index(run, report)
    return int(bool(report["observaciones"]) or any(item["estado"] != "APROBADO" for item in report["perfiles"]))


if __name__ == "__main__":
    raise SystemExit(main())
