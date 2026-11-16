"""Limpieza y estandarización de un bloque de filas (solo depende de pandas)."""
import re
import unicodedata
import warnings

import pandas as pd

from etl.config import COLUMN_ALIASES, STAGING_COLUMNS


def normalizar_nombre(nombre: str) -> str:
    """'Monto Total OC' -> 'montototaloc' (sin tildes, espacios ni símbolos)."""
    sin_tildes = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sin_tildes.lower())


def mapear_columnas(columnas) -> dict:
    """Devuelve {campo_logico: nombre_real_en_el_archivo} solo para los que se encuentran."""
    por_normalizado = {normalizar_nombre(c): c for c in columnas}
    encontrados = {}
    for campo, alias in COLUMN_ALIASES.items():
        for a in alias:
            if normalizar_nombre(a) in por_normalizado:
                encontrados[campo] = por_normalizado[normalizar_nombre(a)]
                break
    return encontrados


def parsear_monto(serie: pd.Series) -> pd.Series:
    """Acepta '1234.56', '1.234,56' y '1234' (CLP suele venir sin decimales)."""
    s = serie.astype("string").str.strip().str.replace(r"[^\d,.\-]", "", regex=True)
    con_coma = s.str.contains(",", na=False)
    s = s.where(~con_coma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    # En CLP un punto seguido de exactamente 3 dígitos es separador de miles ("1.234.567")
    miles = s.str.fullmatch(r"-?\d{1,3}(\.\d{3})+").fillna(False)
    s = s.where(~miles, s.str.replace(".", "", regex=False))
    return pd.to_numeric(s, errors="coerce")


def parsear_fecha(serie: pd.Series) -> pd.Series:
    """Primero formato ISO/estándar; lo que falle se reintenta como día/mes/año."""
    f = pd.to_datetime(serie, errors="coerce")
    pendientes = f.isna() & serie.notna()
    if pendientes.any():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            f[pendientes] = pd.to_datetime(serie[pendientes], errors="coerce", dayfirst=True)
    return f


def normalizar_rut(serie: pd.Series) -> pd.Series:
    return (serie.astype("string").str.upper().str.replace(r"[.\s]", "", regex=True)
            .replace({"": pd.NA}))


def limpiar(df: pd.DataFrame, fuente: str, modalidad_default: str | None = None) -> pd.DataFrame:
    """Renombra, convierte tipos y devuelve solo las columnas de staging."""
    mapa = mapear_columnas(df.columns)
    out = pd.DataFrame(index=df.index)
    for campo in STAGING_COLUMNS:
        if campo == "fuente_archivo":
            continue
        out[campo] = df[mapa[campo]] if campo in mapa else pd.NA

    out["fecha_envio"] = parsear_fecha(out["fecha_envio"])
    out["fecha_aceptacion"] = parsear_fecha(out["fecha_aceptacion"])
    out["monto_clp"] = parsear_monto(out["monto_clp"])
    out["organismo_rut"] = normalizar_rut(out["organismo_rut"])
    out["proveedor_rut"] = normalizar_rut(out["proveedor_rut"])

    for col in ["oc_codigo", "estado", "modalidad", "organismo_nombre", "proveedor_nombre", "rubro"]:
        out[col] = (out[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
                    .replace({"": pd.NA}))

    if modalidad_default:
        out["modalidad"] = out["modalidad"].fillna(modalidad_default)

    out["fuente_archivo"] = fuente
    out = out.dropna(subset=["oc_codigo"]).drop_duplicates(subset="oc_codigo", keep="last")
    return out[STAGING_COLUMNS].reset_index(drop=True)
