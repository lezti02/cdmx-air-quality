# Reporte: calidad del aire en la CDMX (2020–2025)

*Resumen en español. El análisis completo, con código y gráficas, está en los notebooks
de [`notebooks/`](../notebooks) (en inglés).*

## 1. Introducción

Este proyecto nació de un interés personal: saber qué tan contaminado está el aire de la Ciudad de
México y entender cómo cambian esos niveles en distintas zonas de la ciudad y a lo largo del
tiempo. Lo que empezó como un ejercicio exploratorio se volvió un problema con impacto real: la
calidad del aire afecta directamente la salud de las personas y es la base de muchas políticas
ambientales.

El trabajo avanza en dos etapas hacia un **sistema de alertas tempranas**:

1. **Entender** la atmósfera agrupando cada hora en escenarios de contaminación (clustering, 2025).
2. **Anticipar** el escenario de la siguiente hora con una red neuronal recurrente (LSTM, 2020–2025).

## 2. Datos

- **Fuente:** Red Automática de Monitoreo Atmosférico (RAMA), publicada por la Secretaría del Medio
  Ambiente de la CDMX (SEDEMA). Un archivo `.xls` por contaminante y año.
- **Contaminantes:** CO, NO, NO2, NOx, O3, PM10, PM2.5, PMCO y SO2, medidos cada hora.
- **Volumen:** 54 archivos que, unidos, dan 1,876,296 registros estación-hora (36 estaciones).
- **Estaciones usadas:** solo 7 miden todos los contaminantes con una cobertura aceptable:

| Clave | Estación | Zona |
|---|---|---|
| AJM | Ajusco Medio | Sur |
| PED | Pedregal | Suroeste |
| MER | Merced | Centro |
| TLA | Tlalnepantla | Norte (zona industrial) |
| CAM | Camarones | Norte |
| UIZ | UAM Iztapalapa | Oriente |
| NEZ | Nezahualcóyotl | Oriente |

## 3. Limpieza de datos

- Los valores `-99` son datos faltantes según la documentación de SEDEMA.
- Se elimina **PMCO** (es PM10 − PM2.5) y, para el modelado, **NOX** (es NO + NO2).
- **Outliers:** se conservan porque representan días reales de contingencia, pero se topan
  (*capping*) en Q3 + 1.5 × IQR para que no distorsionen el modelo.
- **Faltantes:** interpolación lineal para huecos de hasta 3 horas, dentro de la serie de cada
  estación, y MICE (`IterativeImputer`) para huecos más largos.

## 4. Escenarios atmosféricos (clustering, 2025)

Se compararon K-Means y GMM con el método del codo, BIC y el coeficiente de silueta. Las métricas
sugerían 2 grupos, pero eso solo separaría "limpio" de "contaminado", así que se eligió **K-Means
con 4 grupos** por ser más interpretable:

| Escenario | % de horas | Qué lo caracteriza | Cuándo ocurre |
|---|---|---|---|
| Aire limpio | 32% | Todos los contaminantes bajo el promedio | Madrugada, lluvias (jun–sep), domingos |
| Urbano moderado | 32% | Precursores vehiculares algo elevados, ozono bajo | Tardes-noche y noches |
| Pico de ozono | 20% | Ozono muy alto, por la radiación solar | 13–16 h, temporada seca-cálida (mar–may) |
| Contaminación alta | 15% | CO, NO, NO2 y partículas en su nivel más alto | 8–10 h, invierno (nov–dic) |

**Hallazgos principales**

- **Ciclo diario:** la contaminación alta se concentra en la hora pico de la mañana; el ozono, en
  las primeras horas de la tarde; el aire limpio, antes del amanecer.
- **Estacionalidad:** la temporada de lluvias es la más limpia. El invierno seco, frío y con poco
  viento favorece que los contaminantes se acumulen.
- **Fin de semana:** mejora muy poco. Solo el domingo tiene claramente más aire limpio (41%); el
  sábado se comporta como un día entre semana.
- **Zonas:** Ajusco Medio y Pedregal, rodeadas de áreas verdes, pasan la mitad del tiempo con aire
  limpio y solo 3–5% en contaminación alta. Merced (mucha movilidad) y Tlalnepantla (zona
  industrial) pasan cerca de una cuarta parte de sus horas en contaminación alta.
- **Persistencia:** de una hora a la siguiente, el escenario se mantiene igual entre 73% y 80% de
  las veces.

## 5. Pronóstico de la siguiente hora (LSTM, 2020–2025)

- **Etiquetas:** K-Means (4 grupos) asigna un escenario a cada hora.
- **Entrada:** las últimas 24 horas de los 7 contaminantes de cada estación. La autocorrelación del
  ozono muestra que el ciclo dominante es de 24 horas.
- **Modelo:** dos capas LSTM apiladas (128 y 64 neuronas) con BatchNormalization y Dropout de 0.3,
  una capa densa de 32 neuronas y salida softmax de 4 clases. Pesos de clase balanceados y parada
  temprana.
- **Evaluación por tiempo:** entrenamiento 2020–2023, validación 2024 y prueba 2025. Todos los pasos
  que aprenden de los datos (capping, imputación, escalado, K-Means y la red) se ajustan solo con
  el periodo de entrenamiento.

**Resultados en 2025 (año que el modelo nunca vio)**

| Modelo | Exactitud | F1 macro |
|---|---|---|
| Clase mayoritaria | 0.341 | 0.127 |
| Persistencia (mismo escenario que ahora) | 0.758 | 0.759 |
| Regresión logística, última hora | 0.768 | 0.771 |
| **LSTM, ventana de 24 horas** | **0.783** | **0.787** |
| Regresión logística, ventana de 24 horas | 0.791 | 0.795 |

- La LSTM supera a la persistencia y anticipa el 38% de las horas en las que el escenario cambia,
  algo que la persistencia nunca puede hacer.
- Una regresión logística con la misma ventana queda ligeramente arriba. Con estas variables, la
  capacidad extra de la LSTM no se traduce en mejor desempeño; en producción convendría el modelo
  más simple.
- El escenario más difícil es *Urbano moderado* (recall 0.63), porque queda "en medio" de los otros
  tres.

**Nota sobre la versión original.** La primera versión del proyecto reportaba 77% de exactitud,
pero el conjunto de prueba eran las últimas estaciones y no el último periodo de tiempo, la parada
temprana usaba el propio conjunto de prueba, y el escalado y K-Means se ajustaban con todos los
datos. Esta versión corrige esos tres puntos, así que las cifras de arriba son una estimación
honesta del desempeño en un año futuro.

## 6. Aplicaciones y siguientes pasos

**Cómo puede ayudar**

- **Alertas focalizadas:** saber qué zonas y horarios son más vulnerables permite a los servicios
  de salud y emergencia actuar de forma local, no a ciegas en toda la ciudad.
- **Políticas por zona:** conservar las áreas verdes del sur; medidas más estrictas de tráfico e
  industria en el centro y el norte.

**Siguientes pasos**

1. **Tiempo real:** conectar el pipeline al flujo horario de la RAMA y mostrar las alertas en un
   tablero por estación.
2. **Pronóstico a varias horas:** 6, 12 o 24 horas hacia adelante, que es lo que necesita un sistema
   de alertas tempranas.
3. **Más variables:** datos meteorológicos (temperatura, viento, radiación) y variables de
   calendario.
4. **Más estaciones:** cubrir toda la CDMX y la zona metropolitana.
5. **Monitoreo del modelo:** detectar cambios en los datos (*data drift*) y reentrenar de forma
   periódica.
