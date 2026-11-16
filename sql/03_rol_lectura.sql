-- Usuario de solo lectura para el dashboard (credenciales de DEMO: cámbialas)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lector') THEN
        CREATE ROLE lector LOGIN PASSWORD 'lector';
    END IF;
END $$;

GRANT USAGE ON SCHEMA dw TO lector;
GRANT SELECT ON dw.vw_gasto_por_modalidad, dw.vw_top_proveedores_organismo,
                dw.vw_concentracion_organismo, dw.vw_tiempo_aceptacion,
                dw.vw_estacionalidad, dw.vw_oc_atipicas TO lector;
