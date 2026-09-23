"""
exportador_pdf.py
Convierte HTML a PDF con el navegador del sistema en modo headless.

Usa Microsoft Edge (viene con Windows 10/11) o, si no está, Google Chrome /
Chromium. Así no hace falta instalar librerías de PDF y el informe se ve
exactamente como la maqueta HTML (CSS moderno + gráficos SVG).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_S = 90

_CANDIDATOS_WINDOWS = [
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
]
_NOMBRES_PATH = ["msedge", "microsoft-edge", "google-chrome", "chrome", "chromium", "chromium-browser"]


class ErrorExportacion(RuntimeError):
    """No se pudo convertir el informe a PDF."""


def buscar_navegador():
    """Ruta a Edge/Chrome, o None si no hay ninguno instalado."""
    if sys.platform.startswith("win"):
        for ruta in _CANDIDATOS_WINDOWS:
            ruta = os.path.expandvars(ruta)
            if os.path.isfile(ruta):
                return ruta
    for nombre in _NOMBRES_PATH:
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    return None


def carpeta_descargas():
    """Carpeta Descargas real del usuario (respeta si la movió de lugar en Windows)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            import uuid

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                            ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

            u = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}")  # FOLDERID_Downloads
            guid = GUID(u.fields[0], u.fields[1], u.fields[2],
                        (ctypes.c_ubyte * 8).from_buffer_copy(u.bytes[8:]))
            ruta = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ruta)) == 0:
                try:
                    return Path(ruta.value)
                finally:
                    ctypes.windll.ole32.CoTaskMemFree(ruta)
        except Exception:  # noqa: BLE001
            pass
    for nombre in ("Downloads", "Descargas"):
        p = Path.home() / nombre
        if p.is_dir():
            return p
    return Path.home()


def ruta_disponible(carpeta, nombre):
    """`carpeta/nombre`, o `nombre (2).pdf`, `(3)`… si ya existe."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / nombre
    n = 2
    while destino.exists():
        destino = carpeta / f"{Path(nombre).stem} ({n}){Path(nombre).suffix}"
        n += 1
    return destino


def html_a_pdf(html, destino, navegador=None):
    """Escribe `html` a un archivo temporal y lo imprime a PDF en `destino`."""
    navegador = navegador or buscar_navegador()
    if not navegador:
        raise ErrorExportacion(
            "No se encontró Microsoft Edge ni Google Chrome, que se usan para crear el PDF.")
    destino = Path(destino)
    # ignore_cleanup_errors: el navegador puede tardar un instante en soltar su perfil temporal.
    with tempfile.TemporaryDirectory(prefix="vortrack_informe_", ignore_cleanup_errors=True) as tmp:
        archivo_html = Path(tmp) / "informe.html"
        archivo_html.write_text(html, encoding="utf-8")
        salida = Path(tmp) / "informe.pdf"
        cmd = [
            navegador, "--headless=new", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions",
            # Perfil propio: evita que se "cuelgue" de un Edge/Chrome ya abierto.
            f"--user-data-dir={Path(tmp) / 'perfil'}",
            "--no-pdf-header-footer", "--print-to-pdf-no-header",
            "--virtual-time-budget=5000",
            f"--print-to-pdf={salida}",
            archivo_html.as_uri(),
        ]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT_S, creationflags=flags)
        except subprocess.TimeoutExpired as exc:
            raise ErrorExportacion("El navegador tardó demasiado en generar el PDF.") from exc
        if not salida.exists() or salida.stat().st_size == 0:
            detalle = (proc.stderr or b"").decode("utf-8", "replace").strip()[-400:]
            raise ErrorExportacion(f"El navegador no generó el PDF.\n{detalle}")
        shutil.move(str(salida), str(destino))
    return destino
