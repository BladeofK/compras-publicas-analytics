"""Carga a PostgreSQL: staging por bloque -> dimensiones y hechos con upsert."""
import hashlib
import logging
import time
from functools import wraps
from pathlib import Path

import pandas as pd

from etl.config import DATABASE_URL

log = logging.getLogger(__name__)
SQL_CARGA = Path(__file__).parent / "sql" / "load_from_staging.sql"


def con_reintentos(intentos: int = 3, espera: float = 2.0):
    """Reintenta con espera creciente (cortes de red, base de datos aún levantando)."""
    def deco(fn):
        @wraps(fn)
        def interno(*a, **kw):
            for n in range(1, intentos + 1):
                try:
                    return fn(*a, **kw)
                except Exception as e:  # noqa: BLE001
                    if n == intentos:
                        raise
                    log.warning("%s falló (%s). Reintento %d/%d", fn.__name__, e, n, intentos - 1)
                    time.sleep(espera * n)
        return interno
    return deco


def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def crear_engine(url: str = DATABASE_URL):
    from sqlalchemy import create_engine
    return create_engine(url, pool_pre_ping=True)


def ya_cargado(engine, archivo: str, sha: str) -> bool:
    from sqlalchemy import text
    with engine.connect() as con:
        fila = con.execute(
            text("SELECT sha256 FROM dw.etl_archivos_cargados WHERE archivo = :a"), {"a": archivo}
        ).fetchone()
    return fila is not None and fila[0] == sha


@con_reintentos()
def cargar_bloque(engine, df: pd.DataFrame) -> None:
    from sqlalchemy import text
    limpio = df.astype(object).where(df.notna(), None)
    limpio.to_sql("stg_oc", engine, schema="dw", if_exists="replace",
                  index=False, chunksize=5000, method="multi")
    sentencias = [s.strip() for s in SQL_CARGA.read_text(encoding="utf-8").split(";") if s.strip()]
    with engine.begin() as con:          # una transacción: todo o nada por bloque
        for s in sentencias:
            con.execute(text(s))


@con_reintentos()
def registrar_archivo(engine, archivo: str, sha: str, filas: int) -> None:
    from sqlalchemy import text
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO dw.etl_archivos_cargados (archivo, sha256, filas)
            VALUES (:a, :s, :f)
            ON CONFLICT (archivo) DO UPDATE
               SET sha256 = EXCLUDED.sha256, filas = EXCLUDED.filas, cargado_en = now()
        """), {"a": archivo, "s": sha, "f": filas})
