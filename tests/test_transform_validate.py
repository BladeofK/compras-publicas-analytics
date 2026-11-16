from pathlib import Path

import pandas as pd

from etl import extract, transform, validate
from etl.config import STAGING_COLUMNS

MUESTRA = Path(__file__).resolve().parents[1] / "data" / "sample" / "ordenes_muestra.csv"


def _crudo() -> pd.DataFrame:
    return next(extract.leer_bloques(MUESTRA, ";", 10_000))


def test_normalizar_nombre():
    assert transform.normalizar_nombre("Monto Total OC") == "montototaloc"
    assert transform.normalizar_nombre("Código_Órgano") == "codigoorgano"


def test_mapear_columnas_muestra():
    mapa = transform.mapear_columnas(_crudo().columns)
    assert mapa["oc_codigo"] == "Codigo"
    assert mapa["monto_clp"] == "MontoTotal"
    assert mapa["modalidad"] == "Tipo"


def test_parsear_monto():
    s = pd.Series(["1234", "1.234.567", "1.234,56", "$ 2500", "abc", None])
    r = transform.parsear_monto(s)
    assert r.iloc[0] == 1234
    assert r.iloc[1] == 1234567
    assert abs(r.iloc[2] - 1234.56) < 1e-9
    assert r.iloc[3] == 2500
    assert pd.isna(r.iloc[4]) and pd.isna(r.iloc[5])


def test_parsear_fecha_iso_y_dmy():
    r = transform.parsear_fecha(pd.Series(["2025-03-12", "25-03-2025", "sin dato"]))
    assert r.iloc[0] == pd.Timestamp("2025-03-12")
    assert r.iloc[1] == pd.Timestamp("2025-03-25")
    assert pd.isna(r.iloc[2])


def test_limpiar_muestra():
    out = transform.limpiar(_crudo(), "ordenes_muestra.csv")
    assert list(out.columns) == STAGING_COLUMNS
    assert out["oc_codigo"].is_unique                  # el duplicado se elimina
    assert len(out) == 300
    assert out["monto_clp"].notna().all()
    assert out["fecha_envio"].isna().sum() == 2        # las 2 fechas inválidas quedan nulas
    assert (out["fuente_archivo"] == "ordenes_muestra.csv").all()
    assert out["organismo_rut"].str.contains(r"\.").sum() == 0   # RUT sin puntos


def test_modalidad_por_defecto():
    crudo = _crudo().drop(columns=["Tipo"])
    out = transform.limpiar(crudo, "x.csv", modalidad_default="Trato Directo")
    assert (out["modalidad"] == "Trato Directo").all()


def test_validar_esquema_detecta_faltantes():
    rep = validate.validar_esquema(["Codigo", "FechaEnvio"])
    assert not rep.ok
    assert "Faltan columnas obligatorias" in rep.errores[0]


def test_validar_bloque_muestra_ok():
    rep = validate.validar_bloque(_crudo())
    assert rep.ok, rep.errores


def test_validar_bloque_rechaza_fechas_malas():
    crudo = _crudo()
    crudo["FechaEnvio"] = "sin dato"
    rep = validate.validar_bloque(crudo)
    assert not rep.ok
