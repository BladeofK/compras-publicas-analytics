# Hallazgos y recomendaciones

**Alcance:** 232.377 órdenes de compra de 415 organismos del sector Municipalidades (Mercado Público / ChileCompra),
enviadas entre el 1 de enero y el 30 de junio de 2026. Monto total: unos **$1.715 mil millones** (monto neto en pesos,
sin impuestos). Las cifras salen de las vistas `dw.vw_*` y de las consultas al final de este documento.

> Estos son patrones en los datos, no juicios sobre personas ni instituciones. Una orden atípica puede tener una
> explicación legítima, o venir de un error de digitación en el origen: los datos solos no permiten distinguirlo.
> Por eso no se nombran proveedores ni municipios en los ejemplos.

## Hallazgo 1: el 1 % de las órdenes concentra casi el 60 % del gasto

- **Qué vimos:** el 1 % mayor de las órdenes (unas 2.300) suma el **59,2 %** del monto. Las licitaciones son el 74,3 % del
  monto, pero solo el 30 % de las órdenes. En la orden típica casi no hay diferencia entre modalidades: la mediana es de
  $0,6 M en Compra Ágil, $0,76 M en Trato Directo y $0,9 M en Licitación (el promedio de licitación, en cambio, es de $18,4 M).
- **Por qué importa para Paula:** revisar todas las órdenes con la misma intensidad no es viable ni eficiente. El riesgo
  y el monto están en una cola muy pequeña.
- **Recomendación:** definir una revisión reforzada para las órdenes sobre el percentil 99 de su rubro (la vista
  `vw_oc_atipicas`, 2.339 órdenes en el semestre): verificar monto, adjudicación y documentación antes del pago.
- **Cómo medir si funcionó:** % de las órdenes sobre el percentil 99 con revisión documentada (meta: 100 %).

## Hallazgo 2: una sola orden puede dominar el gasto de un municipio

- **Qué vimos:** en un municipio pequeño, una única orden de unos **$10.900 millones** explica el **89,6 %** de todo su
  gasto del semestre. Su índice de concentración (HHI) llega a 8.038 de 10.000, aunque compró a 148 proveedores.
  Entre las cinco órdenes más grandes de todo el semestre, todas superan los $14.000 millones y vienen en pesos en el archivo
  original, así que no se trata de un error de conversión de moneda.
- **Por qué importa para Paula:** un índice de concentración alto no siempre significa dependencia de un proveedor;
  puede deberse a un solo contrato. El indicador solo no basta para interpretarlo.
- **Recomendación:** mostrar el HHI junto con el nº de órdenes y el % que representa la orden más grande, y validar con
  la unidad compradora los montos que superan un múltiplo de la mediana de su rubro (posible error de digitación).
- **Cómo medir si funcionó:** nº de órdenes con monto corregido o confirmado tras la validación.
- **Pendiente:** solo se revisó en detalle un caso. Otros municipios con HHI alto (de 3.700 a 6.000) no se analizaron,
  y no se sabe si responden al mismo patrón.

## Hallazgo 3: el volumen de trabajo está en Compra Ágil, no el gasto

- **Qué vimos:** Compra Ágil es el **55 %** de las órdenes (128.161) pero solo el **9,2 %** del monto. Junto con Trato
  Directo suma el 63 % de las órdenes y el 18,5 % del monto. Además, entre enero y junio las órdenes mensuales subieron un
  54 % (de 29.051 a 44.806) mientras el monto mensual se movió entre $245 y $330 mil millones sin una tendencia clara.
- **Por qué importa para Paula:** su equipo dedica mucho esfuerzo administrativo a compras de bajo monto.
- **Recomendación (hipótesis a validar, no conclusión):** identificar qué rubros se repiten más en Compra Ágil y evaluar
  si alguno podría comprarse por convenio marco, donde la orden típica es mayor ($2,2 M de mediana). Este análisis aún no se hizo.
- **Cómo medir si funcionó:** nº de órdenes de Compra Ágil por rubro recurrente y % del monto movido a convenio marco.

## Limitaciones

- **Un solo semestre.** No se puede evaluar el cierre de año (la preocupación de Paula sobre diciembre), ni distinguir
  estacionalidad de tendencia.
- **Sin tiempos de aceptación.** Los archivos no traen la fecha de aceptación de la orden, por lo que ese KPI no se calcula.
- **Solo órdenes de compra.** No se analizaron licitaciones (bases, ofertas, adjudicación) ni sus plazos.
- **No se verificó la exactitud de los montos en el origen.** El pipeline reproduce lo que dice el archivo.
- **Monto = neto en pesos.** Excluye impuestos; las 20 órdenes sin monto (0,009 %) no suman.
- **Archivos con una fila por ítem.** El ETL conserva una fila por orden de compra.
- **415 organismos:** 46 no se llaman "municipalidad" (la fuente los clasifica en el sector municipal); no se revisó cada uno.

## Consultas usadas

```sql
-- Concentración del gasto en las órdenes mayores (excluye órdenes sin monto)
SELECT ROUND(100*SUM(monto_clp) FILTER (WHERE rn<=10)/SUM(monto_clp),1)         AS pct_top10,
       ROUND(100*SUM(monto_clp) FILTER (WHERE rn<=0.01*n)/SUM(monto_clp),1)     AS pct_top1_por_ciento
FROM (SELECT monto_clp,
             ROW_NUMBER() OVER (ORDER BY monto_clp DESC NULLS LAST) AS rn,
             COUNT(monto_clp) OVER () AS n
      FROM dw.fact_orden_compra) t;

-- Promedio y mediana por modalidad
SELECT m.nombre AS modalidad, COUNT(*) AS n_oc,
       ROUND(AVG(f.monto_clp)) AS promedio,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.monto_clp)::numeric) AS mediana
FROM dw.fact_orden_compra f JOIN dw.dim_modalidad m USING (modalidad_id)
GROUP BY m.nombre;

-- Reparto por modalidad y evolución mensual
SELECT * FROM dw.vw_gasto_por_modalidad;
SELECT mes, n_oc, monto_clp FROM dw.vw_estacionalidad ORDER BY mes;
```
