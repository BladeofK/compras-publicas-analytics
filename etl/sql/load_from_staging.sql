-- Se ejecuta por cada bloque de filas cargado en dw.stg_oc. Es idempotente (ON CONFLICT).

INSERT INTO dw.dim_tiempo (fecha_id, fecha, anio, semestre, trimestre, mes, dia_semana)
SELECT TO_CHAR(d, 'YYYYMMDD')::INT, d::DATE,
       EXTRACT(YEAR FROM d)::INT,
       CASE WHEN EXTRACT(MONTH FROM d) <= 6 THEN 1 ELSE 2 END,
       EXTRACT(QUARTER FROM d)::INT,
       EXTRACT(MONTH FROM d)::INT,
       EXTRACT(ISODOW FROM d)::INT
FROM GENERATE_SERIES((SELECT MIN(fecha_envio)::DATE FROM dw.stg_oc),
                     (SELECT MAX(fecha_envio)::DATE FROM dw.stg_oc),
                     INTERVAL '1 day') AS d
ON CONFLICT (fecha_id) DO NOTHING;

INSERT INTO dw.dim_organismo (clave, rut, nombre)
SELECT DISTINCT ON (COALESCE(organismo_rut, organismo_nombre))
       COALESCE(organismo_rut, organismo_nombre), organismo_rut, organismo_nombre
FROM dw.stg_oc
WHERE organismo_nombre IS NOT NULL
ON CONFLICT (clave) DO UPDATE SET nombre = EXCLUDED.nombre;

INSERT INTO dw.dim_proveedor (clave, rut, nombre)
SELECT DISTINCT ON (COALESCE(proveedor_rut, proveedor_nombre))
       COALESCE(proveedor_rut, proveedor_nombre), proveedor_rut, proveedor_nombre
FROM dw.stg_oc
WHERE proveedor_nombre IS NOT NULL
ON CONFLICT (clave) DO UPDATE SET nombre = EXCLUDED.nombre;

INSERT INTO dw.dim_modalidad (nombre)
SELECT DISTINCT COALESCE(modalidad, 'Sin modalidad') FROM dw.stg_oc
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO dw.dim_rubro (nombre)
SELECT DISTINCT COALESCE(rubro, 'Sin rubro') FROM dw.stg_oc
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO dw.fact_orden_compra
       (oc_codigo, fecha_envio_id, fecha_aceptacion, organismo_id, proveedor_id,
        modalidad_id, rubro_id, estado, monto_clp, fuente_archivo)
SELECT s.oc_codigo,
       TO_CHAR(s.fecha_envio, 'YYYYMMDD')::INT,
       s.fecha_aceptacion::DATE,
       o.organismo_id, p.proveedor_id, m.modalidad_id, r.rubro_id,
       s.estado, s.monto_clp, s.fuente_archivo
FROM dw.stg_oc s
LEFT JOIN dw.dim_organismo o ON o.clave = COALESCE(s.organismo_rut, s.organismo_nombre)
LEFT JOIN dw.dim_proveedor p ON p.clave = COALESCE(s.proveedor_rut, s.proveedor_nombre)
LEFT JOIN dw.dim_modalidad m ON m.nombre = COALESCE(s.modalidad, 'Sin modalidad')
LEFT JOIN dw.dim_rubro     r ON r.nombre = COALESCE(s.rubro, 'Sin rubro')
ON CONFLICT (oc_codigo) DO UPDATE SET
       fecha_envio_id   = EXCLUDED.fecha_envio_id,
       fecha_aceptacion = EXCLUDED.fecha_aceptacion,
       organismo_id     = EXCLUDED.organismo_id,
       proveedor_id     = EXCLUDED.proveedor_id,
       modalidad_id     = EXCLUDED.modalidad_id,
       rubro_id         = EXCLUDED.rubro_id,
       estado           = EXCLUDED.estado,
       monto_clp        = EXCLUDED.monto_clp,
       fuente_archivo   = EXCLUDED.fuente_archivo,
       cargado_en       = now();
