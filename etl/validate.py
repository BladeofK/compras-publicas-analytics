"""Validaciones de calidad. Los errores críticos rechazan el archivo; los demás quedan en el log."""
from dataclasses import dataclass, field

import pandas as pd

from etl.config import MAX_DUPLICATE_RATIO, MIN_VALID_DATE_RATIO, REQUIRED_FIELDS
from etl.transform import mapear_columnas, parsear_fecha, parsear_monto


class ValidationError(Exception):
    """El archivo no cumple las condiciones mínimas para cargarse."""


@dataclass
class Reporte:
    errores: list = field(default_factory=list)
    avisos: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errores


def validar_esquema(columnas) -> Reporte:
    """Revisa que existan las columnas mínimas (antes de transformar)."""
    rep = Reporte()
    mapa = mapear_columnas(columnas)
    faltan = [c for c in REQUIRED_FIELDS if c not in mapa]
    if faltan:
        rep.errores.append(
            f"Faltan columnas obligatorias: {faltan}. Revisa COLUMN_ALIASES en etl/config.py "
            f"(columnas del archivo: {list(columnas)})."
        )
    for opcional in ("fecha_aceptacion", "modalidad", "rubro", "estado"):
        if opcional not in mapa:
            rep.avisos.append(f"Columna opcional no encontrada: {opcional}")
    return rep


def validar_bloque(df_crudo: pd.DataFrame) -> Reporte:
    """Revisa calidad de datos sobre las filas crudas de un bloque."""
    rep = validar_esquema(df_crudo.columns)
    if not rep.ok or df_crudo.empty:
        return rep
    mapa = mapear_columnas(df_crudo.columns)

    n = len(df_crudo)
    ratio_fechas = parsear_fecha(df_crudo[mapa["fecha_envio"]]).notna().mean()
    if ratio_fechas < MIN_VALID_DATE_RATIO:
        rep.errores.append(f"Solo {ratio_fechas:.1%} de fechas de envío son válidas (mínimo {MIN_VALID_DATE_RATIO:.0%}).")

    montos = parsear_monto(df_crudo[mapa["monto_clp"]])
    if montos.isna().mean() > 1 - MIN_VALID_DATE_RATIO:
        rep.errores.append(f"{montos.isna().mean():.1%} de los montos no son numéricos.")
    if (montos < 0).any():
        rep.avisos.append(f"{int((montos < 0).sum())} montos negativos.")

    codigos = df_crudo[mapa["oc_codigo"]]
    if codigos.isna().any():
        rep.avisos.append(f"{int(codigos.isna().sum())} filas sin código de OC (se descartan).")
    dup = codigos.dropna().duplicated().mean() if n else 0
    if dup > MAX_DUPLICATE_RATIO:
        # Normal en los archivos de ChileCompra: una fila por ítem. Se conserva una fila por OC.
        rep.avisos.append(
            f"{dup:.1%} de las filas repiten código de OC (una fila por ítem); se conserva una por OC."
        )
    return rep


def exigir(rep: Reporte, contexto: str) -> None:
    if not rep.ok:
        raise ValidationError(f"{contexto}: " + " | ".join(rep.errores))
