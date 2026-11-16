"""Punto de entrada del ETL.

  python -m etl.run inspect data/raw/archivo.csv     # ver columnas y cómo se mapean
  python -m etl.run load [--modalidad "Trato Directo"] [archivos...]
  python -m etl.run descargar <URL>                  # baja un archivo a data/raw
"""
import argparse
import json
import logging
import os
import sys
import urllib.request
from pathlib import Path

from etl import extract, transform, validate
from etl.config import CHUNK_ROWS, COLUMN_ALIASES, CSV_SEP, RAW_DIR
from etl.logging_config import setup_logging

log = logging.getLogger("etl")


def notificar_error(mensaje: str) -> None:
    """Aviso opcional a Slack (SLACK_WEBHOOK_URL). Nunca debe romper el ETL."""
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return
    try:
        req = urllib.request.Request(
            url, data=json.dumps({"text": f":warning: ETL compras públicas: {mensaje}"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:  # noqa: BLE001
        log.warning("No se pudo notificar a Slack: %s", e)


def cmd_inspect(archivo: Path) -> int:
    primer = next(extract.leer_bloques(archivo, CSV_SEP, 5))
    mapa = transform.mapear_columnas(primer.columns)
    print(f"\nColumnas del archivo ({len(primer.columns)}):")
    for c in primer.columns:
        print(f"  - {c}")
    print("\nMapeo a campos del modelo:")
    for campo in COLUMN_ALIASES:
        print(f"  {campo:18s} <- {mapa.get(campo, '*** NO ENCONTRADA ***')}")
    rep = validate.validar_esquema(primer.columns)
    print("\nResultado:", "OK" if rep.ok else "FALTAN COLUMNAS OBLIGATORIAS")
    for m in rep.errores + rep.avisos:
        print("  *", m)
    return 0 if rep.ok else 1


def cmd_load(archivos: list[Path], modalidad: str | None) -> int:
    from etl import load
    engine = load.crear_engine()
    fallidos = 0
    for archivo in archivos or extract.listar_archivos(RAW_DIR):
        try:
            sha = load.sha256_archivo(archivo)
            if load.ya_cargado(engine, archivo.name, sha):
                log.info("%s ya estaba cargado (mismo hash). Se omite.", archivo.name)
                continue
            total = 0
            for bloque in extract.leer_bloques(archivo, CSV_SEP, CHUNK_ROWS):
                rep = validate.validar_bloque(bloque)
                for aviso in rep.avisos:
                    log.warning("%s: %s", archivo.name, aviso)
                validate.exigir(rep, archivo.name)
                limpio = transform.limpiar(bloque, archivo.name, modalidad)
                load.cargar_bloque(engine, limpio)
                total += len(limpio)
                log.info("%s: %d filas acumuladas", archivo.name, total)
            load.registrar_archivo(engine, archivo.name, sha, total)
            log.info("%s cargado: %d filas", archivo.name, total)
        except Exception as e:  # noqa: BLE001
            fallidos += 1
            log.exception("Falló la carga de %s", archivo.name)
            notificar_error(f"falló {archivo.name}: {e}")
    return 1 if fallidos else 0


def main(argv=None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(prog="etl.run")
    sub = p.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("inspect"); s1.add_argument("archivo", type=Path)
    s2 = sub.add_parser("load"); s2.add_argument("archivos", nargs="*", type=Path)
    s2.add_argument("--modalidad", help="Si el archivo no trae la columna, se asigna esta modalidad")
    s3 = sub.add_parser("descargar"); s3.add_argument("url")
    a = p.parse_args(argv)
    if a.cmd == "inspect":
        return cmd_inspect(a.archivo)
    if a.cmd == "load":
        return cmd_load(a.archivos, a.modalidad)
    extract.descargar(a.url, RAW_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
