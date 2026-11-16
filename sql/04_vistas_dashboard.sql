-- Vistas extra para el dashboard (respaldan los titulares de docs/03_hallazgos.md).
-- Se ejecuta con el usuario compras (dueño de las tablas y vistas).

-- Promedio y mediana por modalidad: el promedio lo distorsionan pocas órdenes muy grandes.
CREATE OR REPLACE VIEW dw.vw_estadisticas_modalidad AS
SELECT m.nombre                                                              AS modalidad,
       COUNT(*)                                                              AS n_oc,
       ROUND(AVG(f.monto_clp))                                               AS promedio_clp,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.monto_clp)::NUMERIC) AS mediana_clp
FROM dw.fact_orden_compra f
JOIN dw.dim_modalidad m USING (modalidad_id)
GROUP BY m.nombre;

-- Qué parte del monto total aportan las órdenes más grandes (ignora órdenes sin monto).
CREATE OR REPLACE VIEW dw.vw_concentracion_ordenes AS
WITH r AS (
    SELECT monto_clp,
           ROW_NUMBER() OVER (ORDER BY monto_clp DESC) AS rn,
           COUNT(*)     OVER ()                        AS n
    FROM dw.fact_orden_compra
    WHERE monto_clp IS NOT NULL
)
SELECT 'Las 10 órdenes más grandes'::TEXT AS grupo,
       ROUND(100 * SUM(monto_clp) FILTER (WHERE rn <= 10) / SUM(monto_clp), 1) AS pct_monto
FROM r
UNION ALL
SELECT 'El 1 % de órdenes más grandes',
       ROUND(100 * SUM(monto_clp) FILTER (WHERE rn <= 0.01 * n) / SUM(monto_clp), 1)
FROM r;

GRANT SELECT ON dw.vw_estadisticas_modalidad, dw.vw_concentracion_ordenes TO lector;
