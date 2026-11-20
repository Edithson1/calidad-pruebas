"""Workloads and latency budgets for the two VisionText environments."""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
BACKEND = PROJECT / "VisionText-backend"
FRONTEND = PROJECT / "VisionText-frontend"
CSV_FILE = ROOT / "data" / "consultas.csv"
DATASET = BACKEND / "dataset_final"

RENDER_API = "https://visiontext-backend.onrender.com"
RENDER_WEB = "https://visiontext-sigma.vercel.app"


@dataclass(frozen=True)
class Group:
    flow: str
    users: int = 1
    loops: int = 1
    ramp: int = 1
    duration: int = 0
    pause_ms: int = 0


PROFILES = {
    "local": {
        "inicio": (Group("inicio"),),
        "rutas": (Group("rutas"),),
        "base": (Group("busquedas", loops=3, pause_ms=600),),
        "carga": (Group("texto", loops=4, ramp=2, pause_ms=900), Group("imagen", loops=4, ramp=2, pause_ms=900)),
        "incremental": (Group("texto", 4, 4, 12, pause_ms=650), Group("imagen", 2, 4, 12, pause_ms=650)),
        "pico": (Group("texto", 5, 2, 1, pause_ms=500), Group("imagen", 3, 2, 1, pause_ms=500)),
        "sostenida": (Group("texto", 2, -1, 4, 75, 750), Group("imagen", 1, -1, 4, 75, 750)),
        "admin": (Group("admin", 2, 3, 3, pause_ms=450),),
        "escritura": (Group("escritura", 2, 2, 3, pause_ms=550),),
        "web": (Group("web", 2, 3, 3, pause_ms=450),),
    },
    "render": {
        "inicio": (Group("inicio"),),
        "rutas": (Group("rutas"),),
        "base": (Group("busquedas", loops=3, pause_ms=600),),
        "carga": (Group("texto", loops=4, ramp=2, pause_ms=900), Group("imagen", loops=4, ramp=2, pause_ms=900)),
        "admin": (Group("admin", loops=1, pause_ms=900),),
        "web": (Group("web", 2, 3, 3, pause_ms=450),),
    },
}

# Each pair is (limit per request, p95 objective), in milliseconds. Established before running.
BUDGETS = {
    "local": {
        "first": (6000, 4000), "fast": (3500, 1500), "media": (5500, 2500),
        "text": (15000, 8500), "image": (20000, 11000),
        "admin": (4500, 2000), "write": (18000, 10000), "web": (3000, 1500),
    },
    "render": {
        "first": (155000, 155000), "fast": (18000, 10000), "media": (25000, 15000),
        "text": (40000, 28000), "image": (45000, 32000),
        "admin": (60000, 40000), "web": (18000, 11000),
    },
}

FLOWS = {
    "inicio": ("INI-01",),
    "rutas": ("API-01", "API-02", "API-03", "API-04", "ERR-01", "ERR-02", "ERR-03",
              "ERR-04", "ERR-05", "ERR-06", "APK-01"),
    "texto": ("BUS-01", "MED-01", "MED-02"),
    "imagen": ("BUS-02", "MED-03"),
    "busquedas": ("BUS-01", "MED-01", "MED-02", "BUS-02", "MED-03"),
    "admin": ("ADM-01", "ADM-02", "ADM-03", "ADM-04"),
    "escritura": ("ADM-01", "ESC-01", "ESC-02", "ESC-03", "ESC-04", "ESC-05"),
    "web": ("WEB-01", "WEB-02", "WEB-03"),
}

OPERATIONS = {
    "INI-01": ("first", "Primer acceso a la API"),
    "API-01": ("fast", "Raiz"),
    "API-02": ("fast", "Salud y conteo del indice"),
    "API-03": ("fast", "Contrato OpenAPI"),
    "API-04": ("fast", "Preflight CORS"),
    "ERR-01": ("fast", "Texto vacio (422)"),
    "ERR-02": ("fast", "Tipo de archivo incorrecto (400)"),
    "ERR-03": ("fast", "Original inexistente (404)"),
    "ERR-04": ("fast", "Miniatura inexistente (404)"),
    "ERR-05": ("fast", "Catalogo sin sesion (401)"),
    "ERR-06": ("fast", "Subida sin sesion (401)"),
    "APK-01": ("media", "Descarga de APK / respuesta local"),
    "BUS-01": ("text", "Busqueda por texto"),
    "BUS-02": ("image", "Busqueda por imagen"),
    "MED-01": ("media", "Miniatura de busqueda textual"),
    "MED-02": ("media", "Original de busqueda textual"),
    "MED-03": ("media", "Miniatura de busqueda visual"),
    "ADM-01": ("admin", "Login de administrador"),
    "ADM-02": ("admin", "Primera pagina de catalogo"),
    "ADM-03": ("admin", "Segunda pagina de catalogo"),
    "ADM-04": ("admin", "Estado de almacenamiento"),
    "ESC-01": ("write", "Subida multipart de imagen"),
    "ESC-02": ("media", "Original de prueba"),
    "ESC-03": ("media", "Miniatura de prueba"),
    "ESC-04": ("write", "Borrado de imagen de prueba"),
    "ESC-05": ("fast", "Original borrado (404)"),
    "WEB-01": ("web", "Documento HTML"),
    "WEB-02": ("web", "Bundle JavaScript"),
    "WEB-03": ("web", "Hoja CSS"),
}
