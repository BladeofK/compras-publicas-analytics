"""Configuración central del ETL.

IMPORTANTE: los nombres de columna de los archivos de ChileCompra pueden variar según el
archivo y el año. Antes de cargar, corre `python -m etl.run inspect data/raw/<archivo>` y
ajusta COLUMN_ALIASES con los nombres reales que veas.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:  # lee el archivo .env de la raíz del repo (si python-dotenv está instalado)
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

RAW_DIR = Path(os.getenv("RAW_DIR", ROOT / "data" / "raw"))
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://compras:compras@localhost:5432/compras"
)
CSV_SEP = os.getenv("CSV_SEP", ";")
CHUNK_ROWS = int(os.getenv("CHUNK_ROWS", "200000"))
MIN_VALID_DATE_RATIO = 0.95      # bajo este % de fechas válidas, el archivo se rechaza
MAX_DUPLICATE_RATIO = 0.05       # (ya no rechaza: los archivos reales traen una fila por ítem)

# Campo lógico -> nombres posibles de la columna (se compara sin tildes, mayúsculas ni símbolos).
# El primer alias que exista en el archivo es el que se usa.
#
# Archivos reales de ChileCompra (órdenes de compra): una fila por ítem de la OC.
#  - monto_clp usa MontoNetoOC_CLP (monto neto de la OC en pesos, sin impuestos).
#  - organismo = Institucion (nombre). No se usa UnidadCompraRUT como clave porque identifica
#    a la unidad de compra, no a la institución.
COLUMN_ALIASES = {
    "oc_codigo":        ["codigooc", "codigo", "numerooc", "codigo_oc"],
    "estado":           ["estadooc", "estado"],
    "fecha_envio":      ["fechaenviooc", "fechaenvio", "fechacreacion", "fechaoc"],
    "fecha_aceptacion": ["fechaaceptacion"],
    "modalidad":        ["modalidad", "tipocompra", "modalidadcompra", "tipo"],
    "organismo_rut":    ["rutorganismo", "rutcomprador"],
    "organismo_nombre": ["institucion", "nombreorganismo", "organismo",
                         "organismocomprador", "nombrecomprador"],
    "proveedor_rut":    ["proveedorrut", "rutproveedor", "rutsucursal"],
    "proveedor_nombre": ["proveedor", "nombreproveedor", "razonsocialproveedor"],
    "rubro":            ["rubron1", "rubro", "categoria"],
    "monto_clp":        ["montonetoocclp", "montototal", "montototaloc", "totalneto", "total", "monto"],
}

# Sin estos campos el archivo no sirve para el modelo
REQUIRED_FIELDS = ["oc_codigo", "fecha_envio", "monto_clp", "organismo_nombre", "proveedor_nombre"]

STAGING_COLUMNS = [
    "oc_codigo", "estado", "fecha_envio", "fecha_aceptacion", "modalidad",
    "organismo_rut", "organismo_nombre", "proveedor_rut", "proveedor_nombre",
    "rubro", "monto_clp", "fuente_archivo",
]
