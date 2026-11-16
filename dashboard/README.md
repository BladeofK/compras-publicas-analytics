# Dashboard (Power BI)

Proyecto de Power BI guardado en formato `.pbip` en la raíz del repo (`DashboardsComprasPublicas.pbip` y sus carpetas
`.Report` y `.SemanticModel`). Se conecta a PostgreSQL (`localhost:5432`, base `compras`, usuario de solo lectura `lector`)
e importa las vistas `dw.vw_*`, excepto `vw_tiempo_aceptacion`, que queda vacía porque los archivos no traen fecha de aceptación.

## Páginas

| Página | Titular | Qué muestra | Vistas |
|---|---|---|---|
| 1. Resumen | El 1 % de las órdenes suma el 59 % del gasto | Tarjetas de monto total, n.º de órdenes y % del monto por Trato Directo; barras con el % del monto que suman las 10 órdenes más grandes y el 1 % más grande | `vw_gasto_por_modalidad`, `vw_concentracion_ordenes` |
| 2. Modalidades | Compra Ágil es más de la mitad de las órdenes, pero el 9 % del monto | % de las órdenes y % del monto por modalidad; mediana frente a promedio del monto por orden | `vw_gasto_por_modalidad`, `vw_estadisticas_modalidad` |
| 3. Concentración | Un solo contrato puede dominar el gasto de un municipio | Tabla de organismos por índice HHI (con 10 proveedores o más); % del gasto de los 10 mayores proveedores, filtrable por organismo | `vw_concentracion_organismo`, `vw_top_proveedores_organismo` |
| 4. Evolución | Las órdenes crecen 54 % de enero a junio; el monto, solo 6 % | Órdenes y monto por mes, con ejes desde cero | `vw_estacionalidad` |
| 5. Alertas | 2.339 órdenes para revisar primero | Órdenes sobre el percentil 99 de su rubro, filtrables por rubro y ordenadas por monto | `vw_oc_atipicas` |

Capturas en [`capturas/`](capturas/).

## Criterios de diseño

- Cada página abre con un **titular** que dice el hallazgo, no el nombre del gráfico, y debajo la fuente de los datos.
- Un mensaje por visual, con títulos en lenguaje simple (sin «Suma de…»).
- Notas «¿qué es esto?» donde hace falta: mediana (pág. 2), índice HHI (pág. 3), período disponible (pág. 4) y percentil 99 (pág. 5).
- Los montos se muestran con **mediana** además del promedio: el promedio lo distorsionan unas pocas órdenes muy grandes.
- Concentrado o atípico **no significa irregular**; las páginas 3 y 5 lo dicen explícitamente.
- La página de alertas **no muestra proveedores**: algunos son personas naturales. Muestra el código de la orden, el organismo y el rubro.

## Medidas y columnas agregadas en el modelo

- `Monto total (mil millones)`, `N° de órdenes`, `% monto Trato Directo`, `% de las órdenes`, `% del monto` (en `vw_gasto_por_modalidad`).
- `Órdenes atípicas` (en `vw_oc_atipicas`).
- `Monto mensual (mil millones)` y la columna `mes_nombre` (Ene–Jun, ordenada por `mes`) en `vw_estacionalidad`.
