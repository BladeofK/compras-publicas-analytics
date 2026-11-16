# Levantamiento de requerimientos

> Entrevista **simulada** con un usuario ficticio, construida para este proyecto de portafolio.

## Usuaria: Paula, jefa de abastecimiento de una municipalidad mediana

**Contexto.** Su equipo emite cientos de órdenes de compra al mes. Hoy arma reportes a mano en Excel
cuando alguien se los pide, y no tiene una vista que le diga si el municipio compra bien.

**Dolores (en sus palabras).**
1. «No sé cuánto de lo que compramos va por trato directo y si eso es normal comparado con otros.»
2. «Siento que siempre compramos a los mismos proveedores, pero no tengo cómo medirlo.»
3. «Cuando auditoría pregunta por compras raras, me toma días encontrarlas.»
4. «A fin de año se nos acumula todo y no sé cuánto es realmente.»

## Del dolor al requerimiento de datos

| Dolor | Pregunta de negocio | KPI | Vista SQL |
|---|---|---|---|
| 1 | ¿Qué % del gasto va por cada modalidad de compra? | % del monto por modalidad | `vw_gasto_por_modalidad` |
| 2 | ¿Qué tan concentrado está el gasto en pocos proveedores? | % por proveedor, índice HHI | `vw_top_proveedores_organismo`, `vw_concentracion_organismo` |
| 3 | ¿Qué órdenes se salen de lo habitual para su rubro? | Órdenes sobre el percentil 99 | `vw_oc_atipicas` |
| 4 | ¿Cómo se distribuye el gasto en el año? | Monto y n.º de OC por mes | `vw_estacionalidad` |

**Nota sobre el dolor 4:** con un solo semestre de datos solo se ve la evolución mensual de enero a junio.
Evaluar el cierre de año exige cargar también el segundo semestre.

## Criterios de aceptación
- Paula entiende cada gráfico sin leer una definición técnica.
- Cada KPI tiene una frase de «qué significa» y una de «qué haría con esto».
- Los datos se pueden actualizar sin que nadie toque el código.

## Fuera de alcance (versión 1)
- **Tiempo entre el envío de una orden y su aceptación por el proveedor.** Se había considerado como KPI extra,
  pero los archivos de Datos Abiertos no incluyen la fecha de aceptación. La vista `vw_tiempo_aceptacion` existe
  en el modelo y quedaría vacía.
- Licitaciones y sus tiempos de adjudicación (se necesita otro archivo y otro modelo).
- Comparación entre organismos de distinto tamaño sin normalizar.
- Cualquier juicio de valor sobre proveedores u organismos: los datos muestran patrones, no irregularidades.
