-- Modelo en estrella para órdenes de compra de Mercado Público
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_tiempo (
    fecha_id   INT PRIMARY KEY,          -- AAAAMMDD
    fecha      DATE NOT NULL,
    anio       INT  NOT NULL,
    semestre   INT  NOT NULL,
    trimestre  INT  NOT NULL,
    mes        INT  NOT NULL,
    dia_semana INT  NOT NULL             -- 1 = lunes ... 7 = domingo
);

CREATE TABLE IF NOT EXISTS dw.dim_organismo (
    organismo_id SERIAL PRIMARY KEY,
    clave        TEXT UNIQUE NOT NULL,   -- RUT si existe; si no, el nombre
    rut          TEXT,
    nombre       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_proveedor (
    proveedor_id SERIAL PRIMARY KEY,
    clave        TEXT UNIQUE NOT NULL,
    rut          TEXT,
    nombre       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_modalidad (
    modalidad_id SERIAL PRIMARY KEY,
    nombre       TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_rubro (
    rubro_id SERIAL PRIMARY KEY,
    nombre   TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.fact_orden_compra (
    oc_codigo        TEXT PRIMARY KEY,
    fecha_envio_id   INT REFERENCES dw.dim_tiempo (fecha_id),
    fecha_aceptacion DATE,
    organismo_id     INT REFERENCES dw.dim_organismo (organismo_id),
    proveedor_id     INT REFERENCES dw.dim_proveedor (proveedor_id),
    modalidad_id     INT REFERENCES dw.dim_modalidad (modalidad_id),
    rubro_id         INT REFERENCES dw.dim_rubro (rubro_id),
    estado           TEXT,
    monto_clp        NUMERIC(18, 2),
    fuente_archivo   TEXT,
    cargado_en       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fact_fecha     ON dw.fact_orden_compra (fecha_envio_id);
CREATE INDEX IF NOT EXISTS ix_fact_organismo ON dw.fact_orden_compra (organismo_id);
CREATE INDEX IF NOT EXISTS ix_fact_proveedor ON dw.fact_orden_compra (proveedor_id);
CREATE INDEX IF NOT EXISTS ix_fact_modalidad ON dw.fact_orden_compra (modalidad_id);

-- Control de carga incremental: un archivo ya cargado (mismo hash) no se vuelve a procesar
CREATE TABLE IF NOT EXISTS dw.etl_archivos_cargados (
    archivo    TEXT PRIMARY KEY,
    sha256     TEXT NOT NULL,
    filas      BIGINT NOT NULL,
    cargado_en TIMESTAMPTZ DEFAULT now()
);
