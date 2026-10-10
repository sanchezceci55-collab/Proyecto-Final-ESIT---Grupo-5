# Proyecto Nube Verde — Monitor de Consumo Energético  (Equipo 5)

Este repositorio contiene la arquitectura de software, el diccionario de datos y los scripts de simulación correspondientes al desarrollo del proyecto **Nube Verde** para la gestión y monitoreo eficiente del consumo eléctrico del campus.

## 👥 Integrantes del Equipo
* **Cecilia Elizabeth Sánchez Cortez** — Líder de Equipo
* ** Josué Magin Zepeda García ** — Ingeniero Cloud Jr.
* **Erick Ricardo Melara Ponce** — Ingeniero IoT Simulado Jr.

---

##  Componente Técnico: Simulador IoT (Fase 1)
*Responsable del Desarrollo: Erick Ricardo Melara Ponce*

El script de telemetría `Simulator_Nube_Verde.py` modela de forma granular el comportamiento de los sensores físicos embebidos en el campus, transmitiendo datos de manera síncrona hacia la nube.

### 1. Frecuencia y Almacenamiento Dinámico
Acatando las directrices de diseño de la Fase 1, el simulador se encuentra configurado con una **frecuencia de simulación y registro de 60 segundos por dispositivo**. Esto evita la saturación de los canales HTTP y se alinea con las pautas de acumulación temporal requeridas por la cátedra.

### 2. Diccionario de Datos  (Firebase Realtime Database)
Cada payload transmitido por la red IoT se estructura de forma independiente bajo las variables normalizadas del proyecto, garantizando consistencia semántica completa:

| Variable | Definición Técnica | Unidad / Valores |
| :--- | :--- | :--- |
| `id_dispositivo` | Identificador único del equipo sensorizado. | Alfanumérico (Ej: `lab_a_clima_01`) |
| `zona` | Espacio físico de ubicación del hardware. | Texto (`Laboratorio_A`, `Aula_101`, etc.) |
| `estado` | Condición operativa instantánea del equipo. | `encendido`, `apagado`, `falla` |
| `potencia_estimada_w` | Demanda de potencia instantánea en el intervalo. | Watts (W); Valor numérico ≥ 0 |
| `consumo_kwh` | Energía incremental neta del intervalo. | Kilovatios-hora (kWh); Valor numérico ≥ 0 |
| `timestamp_inicio` | Registro de inicio del intervalo de medición. | Formato ISO 8601 (YYYY-MM-DDTHH:MM:SS) |
| `timestamp_fin` | Registro de finalización del intervalo de medición. | Formato ISO 8601 (YYYY-MM-DDTHH:MM:SS) |

### 3. Sustentación Matemática de Consumo (kWh)
Para mitigar de forma absoluta la duplicación o solapamiento de consumos eléctricos en los circuitos, el simulador ejecuta la integración discreta de energía sobre la fracción temporal exacta de envío (t = 60 segundos = 0.016667 horas):

\[\text{Energía (consumo\_kwh)} = \frac{\text{potencia\_estimada\_w} \times t\text{ (horas)}}{1000}\]

*Ejemplo de Operación:* Un extractor o unidad de aire acondicionado operando a una potencia constante de 1500 W durante el intervalo de un minuto, genera un registro incremental neto de:
\[\text{consumo\_kwh} = \frac{1500\text{ W} \times 0.016667\text{ h}}{1000} \approx 0.025\text{ kWh}\]

---

##  Inventario Teórico Base de Monitoreo
Estos umbrales representan la capacidad de carga instalada por espacio físico y sirven como parámetros maestros de calibración para las fluctuaciones estocásticas del software:

* **Laboratorio A:** 20 Computadoras (150W), 1 Aire Acondicionado (1500W), 10 Luces LED (18W c/u), 1 Proyector (250W). *Consumo base teórico: 3.25 kWh*.
* **Laboratorio B:** 16 Computadoras (150W), 1 Aire Acondicionado (1200W), 8 Luces LED (18W c/u), 1 Proyector (200W). *Consumo base teórico: 2.59 kWh*.
* **Oficina Administrativa:** 6 Computadoras (120W), 1 Impresora (300W), 6 Luces LED (18W c/u), 1 Aire Acondicionado Mini-Split (900W). *Consumo base teórico: 1.23 kWh*.
* **Aula 101:** 8 Luces LED (18W c/u), 1 Proyector (250W), 1 Laptop Docente (65W), 2 Ventiladores de Techo (75W c/u). *Consumo base teórico: 0.72 kWh*.

> **Nota de Diseño Arquitectónico (Aula 101):** Se seleccionó un sistema de climatización pasiva mediante ventiladores de techo en lugar de aire acondicionado debido al perfil de carga disipada bajo, aforos variables intermitentes y con el fin de enriquecer los análisis comparativos de los tableros de control en Grafana.
