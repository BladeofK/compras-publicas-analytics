-- Vistas que alimentan el dashboard

-- KPI 1: ¿cómo se reparte el gasto entre modalidades de compra?
CREATE OR REPLACE VIEW dw.vw_gasto_por_modalidad AS
SELECT t.anio,
       t.semestre,
       m.nombre                      AS modalidad,
       COUNT(*)                      AS n_oc,
       SUM(f.monto_clp)              AS monto_clp,
       ROUND(100.0 * SUM(f.monto_clp)
             / NULLIF(SUM(SUM(f.monto_clp)) OVER (PARTITION BY t.anio, t.semestre), 0), 1) AS pct_monto
FROM dw.fact_orden_compra f
JOIN dw.dim_modalidad m USING (modalidad_id)
LEFT JOIN dw.dim_tiempo t ON t.fecha_id = f.fecha_envio_id
GROUP BY t.anio, t.semestre, m.nombre;

-- KPI 2a: proveedores que concentran el gasto de cada organismo
CREATE OR REPLACE VIEW dw.vw_top_proveedores_organismo AS
WITH g AS (
    SELECT o.nombre AS organismo, p.nombre AS proveedor,
           COUNT(*) AS n_oc, SUM(f.monto_clp) AS monto_clp
    FROM dw.fact_orden_compra f
    JOIN dw.dim_organismo o USING (organismo_id)
    JOIN dw.dim_proveedor p USING (proveedor_id)
    GROUP BY o.nombre, p.nombre
)
SELECT organismo, proveedor, n_oc, monto_clp,
       ROUND(100.0 * monto_clp / NULLIF(SUM(monto_clp) OVER (PARTITION BY organismo), 0), 1) AS pct_organismo,
       RANK() OVER (PARTITION BY organismo ORDER BY monto_clp DESC) AS ranking
FROM g;

-- KPI 2b: índice de concentración (Herfindahl-Hirschman, 0 a 10.000) por organismo
CREATE OR REPLACE VIEW dw.vw_concentracion_organismo AS
SELECT organismo,
       COUNT(*)                                   AS n_proveedores,
       ROUND(SUM(POWER(pct_organismo, 2)), 0)     AS hhi
FROM dw.vw_top_proveedores_organismo
GROUP BY organismo;

-- KPI 3: días entre envío de la OC y aceptación del proveedor
CREATE OR REPLACE VIEW dw.vw_tiempo_aceptacion AS
SELECT m.nombre AS modalidad,
       COUNT(*) AS n_oc,
       ROUND(AVG(f.fecha_aceptacion - t.fecha)::numeric, 1)                          AS dias_promedio,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (f.fecha_aceptacion - t.fecha))   AS dias_mediana,
       PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY (f.fecha_aceptacion - t.fecha))   AS dias_p90
FROM dw.fact_orden_compra f
JOIN dw.dim_modalidad m USING (modalidad_id)
JOIN dw.dim_tiempo t ON t.fecha_id = f.fecha_envio_id
WHERE f.fecha_aceptacion IS NOT NULL AND f.fecha_aceptacion >= t.fecha
GROUP BY m.nombre;

-- KPI 4: estacionalidad del gasto
CREATE OR REPLACE VIEW dw.vw_estacionalidad AS
SELECT t.anio, t.mes, COUNT(*) AS n_oc, SUM(f.monto_clp) AS monto_clp
FROM dw.fact_orden_compra f
JOIN dw.dim_tiempo t ON t.fecha_id = f.fecha_envio_id
GROUP BY t.anio, t.mes;

-- KPI 6: órdenes atípicas (monto sobre el percentil 99 de su rubro)
CREATE OR REPLACE VIEW dw.vw_oc_atipicas AS
WITH p AS (
    SELECT rubro_id, PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY monto_clp) AS p99
    FROM dw.fact_orden_compra
    GROUP BY rubro_id
    HAVING COUNT(*) >= 30                  -- evita rubros con muy pocas órdenes
)
SELECT f.oc_codigo, o.nombre AS organismo, pr.nombre AS proveedor,
       r.nombre AS rubro, f.monto_clp, ROUND(p.p99::NUMERIC, 0) AS p99_rubro
FROM dw.fact_orden_compra f
JOIN p USING (rubro_id)
JOIN dw.dim_rubro r USING (rubro_id)
JOIN dw.dim_organismo o USING (organismo_id)
JOIN dw.dim_proveedor pr USING (proveedor_id)
WHERE f.monto_clp > p.p99;
