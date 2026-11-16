"""Lectura de archivos de ChileCompra (CSV o ZIP) en bloques, y descarga opcional por URL."""
import logging
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator

import pandas as pd

log = logging.getLogger(__name__)


def listar_archivos(raw_dir: Path) -> list[Path]:
    return sorted(p for p in raw_dir.glob("*") if p.suffix.lower() in {".csv", ".zip"})


def _muestra_bytes(path: Path, n: int = 200_000) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z, z.open(z.namelist()[0]) as f:
            return f.read(n)
    with open(path, "rb") as f:
        return f.read(n)


def detectar_encoding(path: Path) -> str:
    """UTF-8 si decodifica bien; si no, latin-1 (habitual en archivos del Estado)."""
    muestra = _muestra_bytes(path)
    try:
        muestra.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError as e:
        # un corte justo al final del buffer no cuenta como error real
        return "utf-8" if e.start >= len(muestra) - 4 else "latin-1"


def leer_bloques(path: Path, sep: str, chunk_rows: int) -> Iterator[pd.DataFrame]:
    """Entrega el archivo en bloques, todo como texto (la conversión de tipos va en transform)."""
    enc = detectar_encoding(path)
    log.info("Leyendo %s (encoding=%s, sep=%r)", path.name, enc, sep)
    yield from pd.read_csv(
        path, sep=sep, dtype=str, encoding=enc, chunksize=chunk_rows,
        on_bad_lines="skip", keep_default_na=False, na_values=[""],
    )


def descargar(url: str, destino_dir: Path, intentos: int = 3) -> Path:
    """Descarga un archivo de la sección Descargas de datos-abiertos.chilecompra.cl."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / Path(url.split("?")[0]).name
    for n in range(1, intentos + 1):
        try:
            log.info("Descargando %s (intento %d)", url, n)
            urllib.request.urlretrieve(url, destino)
            return destino
        except Exception as e:  # noqa: BLE001
            log.warning("Falló la descarga: %s", e)
            if n == intentos:
                raise
            time.sleep(2 ** n)
    return destino
