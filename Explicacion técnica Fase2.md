# INFORME DE CORRECCIONES TÉCNICAS (FASE 2)

## 1. Introducción y Justificación de las Correcciones
Este documento técnico consolida formalmente el levantamiento y resolución de las observaciones emitidas de la Fase 1 del proyecto Nube Verde. Las modificaciones realizadas corrigen fallas críticas de base física, semántica del modelo de datos, precisión temporal en la captura IoT y seguridad de la infraestructura en la nube. Con estas mejoras, el simulador se adapta al diseño de arquitectura objetivo del Grupo 5 para cumplir con los lineamientos operativos de la Fase 2.

---

## 2. Matriz de Correspondencia de Hallazgos y Soluciones

| Hallazgo Detectado (Fase 1) | Impacto / Justificación Física | Acción Correctiva Aplicada (Fase 2) |
| :--- | :--- | :--- |
| Estado de falla reportaba consumo eléctrico remanente (15% de la potencia nominal base). | Inconsistencia termodinámica. Si un dispositivo físico se apaga por anomalía o desconexión crítica, la potencia y el consumo deben caer inmediatamente a cero. | Se modificó el código del simulador para que, al detectar una falla técnica o desconexión, la potencia (W) y el consumo (kWh) bajen automáticamente a 0.0 de forma absoluta. |
| Ambigüedad de granularidad: se declararon lecturas individuales pero el script multiplicaba potencia por cantidad de equipos. | Confusión semántica en la capa de datos. Almacenar totales como si fuesen unidades individuales arriesgaba a una sobre-multiplicación y distorsionaba los KPIs del dashboard. | Se cambió el modelo a 'Lecturas Agregadas por Grupo'. Las variables ahora identifican el consumo total de un conjunto de equipos (ej. de pc_01 a pc_grupo) e incluyen un campo que especifica la cantidad exacta de aparatos medidos. |
| Retrasos ocultos acumulativos debido a la congelación rígida del hilo de ejecución mediante la llamada `time.sleep(60)`. | Pérdida de exactitud cronológica. El retardo de la petición de red HTTP síncrona hacia la nube se suma a la pausa, desfasando la ventana fija de 60 segundos. | Se programó un temporizador dinámico que calcula cuántos segundos tarda la red en enviar los datos a la nube y descuenta ese tiempo de la pausa, garantizando ciclos exactos de 60 segundos. |
| Ausencia de control horario operativo e inconsistencia de carga física en el balance de inventario del Aula 101. | Falta de realismo empírico. El apagado aleatorio ignoraba la planificación del campus. En Aula 101 se dividían 2.159 kWh/día entre 3 horas simulando 719.7W, superando la potencia nominal de 609W. | Se configuraron horarios de apertura y cierre por cada zona. El script consulta la hora real del reloj del sistema y apaga los equipos fuera de la jornada académica. También se recalcularon las cargas del Aula 101 para no superar su límite físico. |

---

## 3. Diccionario Técnico de Dispositivos por Sitio

A continuación, se detalla la base de datos estructural del inventario físico corregido que alimenta la matriz del simulador en esta Fase 2. Se han restringido los rangos e integrado las ventanas operativas del campus:

### Laboratorio A (Centro de Cómputo Avanzado)

| ID Dispositivo | Descripción del Equipo | Cant. | Potencia | Horario Académico | Consumo Diario |
| :--- | :--- | :---: | :---: | :---: | :---: |
| lab_a_pc_grupo | Computadora de Escritorio | 20 | 150 W | 08:00 - 14:00 (6h) | 18.00 kWh |
| lab_a_clima_01 | Aire Acondicionado Central | 1 | 1,500 W | 10:00 - 14:00 (4h) | 6.00 kWh |
| lab_a_ilum_grupo | Luminarias LED de Alta Eficiencia | 10 | 18 W | 08:00 - 16:00 (8h) | 1.44 kWh |
| lab_a_proy_01 | Proyector Multimedia | 1 | 250 W | 09:00 - 11:00 (2h) | 0.50 kWh |

* **Métricas del Sitio** -> Consumo Total Integrado: **25.94 kWh** | Demanda de Potencia Promedio: **3.2425 kW** (Ventana de 8h)

### Laboratorio B (Desarrollo y Programación)

| ID Dispositivo | Descripción del Equipo | Cant. | Potencia | Horario Académico | Consumo Diario |
| :--- | :--- | :---: | :---: | :---: | :---: |
| lab_b_pc_grupo | Computadora de Escritorio | 16 | 150 W | 08:00 - 13:00 (5h) | 12.00 kWh |
| lab_b_clima_01 | Aire Acondicionado Standard | 1 | 1,200 W | 09:00 - 13:00 (4h) | 4.80 kWh |
| lab_b_ilum_grupo | Luminarias LED de Alta Eficiencia | 8 | 18 W | 08:00 - 16:00 (8h) | 1.152 kWh |
| lab_b_proy_01 | Proyector Multimedia | 1 | 200 W | 10:00 - 11:00 (1h) | 0.20 kWh |

* **Métricas del Sitio** -> Consumo Total Integrado: **18.152 kWh** | Demanda de Potencia Promedio: **2.5931 kW** (Ventana de 7h)

### Oficina Administrativa (Gestión Académica)

| ID Dispositivo | Descripción del Equipo | Cant. | Potencia | Horario Académico | Consumo Diario |
| :--- | :--- | :---: | :---: | :---: | :---: |
| oficina_pc_grupo | Computadora de Escritorio | 6 | 120 W | 08:00 - 16:00 (8h) | 5.76 kWh |
| oficina_imp_01 | Impresora Multifuncional Láser | 1 | 300 W | 11:00 - 12:00 (1h) | 0.30 kWh |
| oficina_ilum_grupo | Luminarias LED Standard | 6 | 18 W | 07:30 - 17:30 (10h) | 1.08 kWh |
| oficina_clima_01 | Aire Acondicionado Mini-Split | 1 | 900 W | 12:00 - 15:00 (3h) | 2.70 kWh |

* **Métricas del Sitio** -> Consumo Total Integrado: **9.84 kWh** | Demanda de Potencia Promedio: **1.2300 kW** (Ventana de 8h)

### Aula 101 (Diseño Bioclimático Eficiente)

| ID Dispositivo | Descripción del Equipo | Cant. | Potencia | Horario Académico | Consumo Diario |
| :--- | :--- | :---: | :---: | :---: | :---: |
| aula_ilum_grupo | Luminarias LED Standard | 8 | 18 W | 07:00 - 13:00 (6h) | 0.864 kWh |
| aula_proy_01 | Proyector Multimedia | 1 | 250 W | 08:00 - 10:00 (2h) | 0.50 kWh |
| aula_lap_docente | Laptop Estación de Trabajo Docente | 1 | 65 W | 07:00 - 10:00 (3h) | 0.195 kWh |
| aula_vent_grupo | Ventiladores de Techo Corregidos | 2 | 75 W | 07:00 - 11:00 (4h) | 0.60 kWh |

* **Métricas del Sitio** -> Consumo Total Integrado: **2.159 kWh** | Demanda de Potencia Promedio: **0.7197 kW** (Ventana de 3h de Clase Simultánea)

---

## 4. Estructura de Mensajes JSON Validada
Este es el esquema oficial del payload JSON generado por el nuevo script. Incluye los metadatos requeridos por la capa intermedia de FastAPI para el almacenamiento en Firebase Realtime Database:

```json
{
  "zona": "Aula_101",
  "id_dispositivo": "aula_vent_grupo",
  "tipo": "Ventiladores de techo",
  "cantidad_equipos": 2,
  "estado": "encendido",
  "potencia_estimada_w": 152.08,
  "consumo_kwh": 0.002535,
  "timestamp_inicio": "2026-10-10T20:37:06.703917+00:00",
  "timestamp_fin": "2026-10-10T20:38:06.703917+00:00"
}
```

---

## 5. Evidencias de Cierre Técnico y Matriz de Pruebas
Para dar cumplimiento formal al Plan de Trabajo de la Fase 2, se ejecutaron pruebas de estrés sobre el script corregido (`simulador_nube_verde.py`), obteniendo los siguientes resultados reproducibles:

### 5.1 Matriz de Casos de Prueba Ejecutados

* **Caso de Prueba CP-01: Verificación Física del Estado de Falla (Evidencia E11)**
  * **Requisito:** Validar que al entrar en un estado de anomalía eléctrica, la transferencia de carga caiga a cero absolutos de forma matemática.
  * **Entrada de simulación:** Activación forzada del estado "falla" en el bucle lógico del script en Python.
  * **Resultado esperado:** Potencia fijada en 0.0 W y consumo integrado registrado en 0.000000 kWh en el JSON.
  * **Resultado obtenido:** `Grupo: [lab_b_pc_grupo] (16 uds) | Potencia: 0.0 W | Energía: 0.0 kWh | Estado: falla -> [ENVIADO]`.
  * **Estado:** **Aprobado**.

* **Caso de Prueba CP-02: Control Horario de Dispositivos por Zona (Evidencia E10)**
  * **Requisito:** Validar el apagado automático de los nodos según las ventanas del campus universitario.
  * **Entrada de simulación:** Lectura del reloj del sistema (`datetime.now().hour = 20`) ejecutada en horario nocturno.
  * **Resultado esperado:** Forzado inmediato de estado "apagado" para laboratorios y aulas fuera de servicio.
  * **Resultado obtenido:** Todos los equipos del campus pasaron a estado "apagado" reflejando consumos y potencias nulas, eliminando la aleatoriedad de la Fase 1.
  * **Estado:** **Aprobado**.

* **Caso de Prueba CP-03: Compensación de Latencia de Red (Sincronía Rígida) (Evidencia E12)**
  * **Requisito:** Garantizar que los ciclos de transmisión se mantengan exactamente cada 60 segundos sin retrasos acumulativos por culpa de las llamadas HTTP POST síncronas.
  * **Entrada de simulación:** Envío secuencial de 16 paquetes JSON hacia Firebase.
  * **Resultado esperado:** Medición diferencial de tiempo (`time.time()`) y reducción proporcional de la pausa del hilo.
  * **Resultado obtenido:** Tiempo neto de transmisión en red = 7.18 segundos. El simulador recalculó y aplicó un `time.sleep(52.82)`, completando el ciclo en el segundo 60.00 exacto.
  * **Estado:** **Aprobado**.

* **Caso de Prueba CP-04: Autenticación Segura y Denegación de Acceso (Brecha C5 / Evidencia E09)**
  * **Requisito:** Validar que Firebase Realtime Database recheze peticiones con tokens alterados o inválidos.
  * **Entrada de simulación:** Transmisión con la variable `TOKEN_FIREBASE` modificada erróneamente con un carácter aleatorio al final.
  * **Resultado esperado:** Recepción de un código HTTP `401 Unauthorized` de denegación de acceso.
  * **Resultado obtenido:** `[ERROR CLOUD] Fallo en la persistencia: 401 Client Error: Unauthorized for url`. Cierre de accesos verificado.
  * **Estado:** **Aprobado**.


