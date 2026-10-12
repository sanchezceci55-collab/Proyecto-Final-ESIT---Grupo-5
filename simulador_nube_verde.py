"""
Simulador IoT - Nube Verde (Fase 1)
Genera lecturas granulares por dispositivo individual, calcula el consumo incremental
en kWh según la fracción exacta de tiempo (60s) para evitar doble contabilidad,
e integra los estados semánticos validados por el tutor.
"""

import sys
import subprocess

# --- AUTO-INSTALACIÓN (Asegura que 'requests' esté instalado) ---
try:
    import requests
except ModuleNotFoundError:
    print("[INFO] Falta la librería 'requests'. Instalándola automáticamente, espera un momento...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("[ÉXITO] Librería 'requests' instalada correctamente. Continuando con la lectura...\n")
    import requests

# Importación de librerías del núcleo de Python
import random
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------
# CONFIGURACIÓN — URL de Firebase Realtime Database
# ---------------------------------------------------------------
FIREBASE_URL = "https://nube-verde-default-rtdb.firebaseio.com"

# Frecuencia inicial de simulación y registro recomendada por el tutor (60 segundos)
FRECUENCIA_SEGUNDOS = 60  

# Inventario granular por dispositivo individual para mitigar doble contabilidad de circuitos
INVENTARIO_DISPOSITIVOS = {
    "Laboratorio_A": [
        {"id": "lab_a_pc_01", "tipo": "Computadora de escritorio", "cantidad": 20, "potencia_nominal_w": 150},
        {"id": "lab_a_clima_01", "tipo": "Aire acondicionado", "cantidad": 1, "potencia_nominal_w": 1500},
        {"id": "lab_a_ilum_01", "tipo": "Luces LED", "cantidad": 10, "potencia_nominal_w": 18},
        {"id": "lab_a_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 250}
    ],
    "Laboratorio_B": [
        {"id": "lab_b_pc_01", "tipo": "Computadora de escritorio", "cantidad": 16, "potencia_nominal_w": 150},
        {"id": "lab_b_clima_01", "tipo": "Aire acondicionado", "cantidad": 1, "potencia_nominal_w": 1200},
        {"id": "lab_b_ilum_01", "tipo": "Luces LED", "cantidad": 8, "potencia_nominal_w": 18},
        {"id": "lab_b_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 200}
    ],
    "Oficina_Administrativa": [
        {"id": "oficina_pc_01", "tipo": "Computadora de escritorio", "cantidad": 6, "potencia_nominal_w": 120},
        {"id": "oficina_imp_01", "tipo": "Impresora", "cantidad": 1, "potencia_nominal_w": 300},
        {"id": "oficina_ilum_01", "tipo": "Luces LED", "cantidad": 6, "potencia_nominal_w": 18},
        {"id": "oficina_clima_01", "tipo": "Aire acondicionado mini-split", "cantidad": 1, "potencia_nominal_w": 900}
    ],
    "Aula_101": [
        {"id": "aula_ilum_01", "tipo": "Luces LED", "cantidad": 8, "potencia_nominal_w": 18},
        {"id": "aula_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 250},
        {"id": "aula_lap_docente", "tipo": "Laptop del docente", "cantidad": 1, "potencia_nominal_w": 65},
        {"id": "aula_vent_01", "tipo": "Ventiladores de techo", "cantidad": 2, "potencia_nominal_w": 75}
    ]
}


def generar_lectura_dispositivo(dispositivo: dict, zona: str, intervalo_segundos: int) -> dict:
    """
    Genera métricas por dispositivo aplicando variaciones aleatorias normales de carga,
    estados semánticos discretos y la ecuación física de integración de energía (kWh).
    """
    # 1. Simulación estocástica del estado (93% encendido, 5% apagado, 2% falla)
    probabilidad = random.random()
    if probabilidad < 0.02:
        estado = "falla"
    elif probabilidad < 0.07:
        estado = "apagado"
    else:
        estado = "encendido"

    # 2. Modelar la potencia estimada en Watts (W) basándose en la cantidad agregada del nodo
    potencia_total_base = dispositivo["potencia_nominal_w"] * dispositivo["cantidad"]
    
    if estado == "encendido":
        # Fluctuación aleatoria operativa normal del +/- 10%
        variacion = random.uniform(-0.10, 0.10)
        potencia_estimada_w = round(potencia_total_base * (1 + variacion), 2)
    elif estado == "falla":
        # Consumo parásito o cortocircuito de protección (15% de la carga base)
        potencia_estimada_w = round(potencia_total_base * 0.15, 2)
    else:
        potencia_estimada_w = 0.0

    # 3. Integración Matemática de Energía en kWh para la ventana temporal exacta
    # Fórmula: Energía (kWh) = Potencia (W) * Duración (Horas) / 1000
    duracion_horas = intervalo_segundos / 3600.0
    consumo_kwh = round((potencia_estimada_w * duracion_horas) / 1000.0, 6)

    # Definición de marcas de tiempo del intervalo simulado
    ahora_utc = datetime.now(timezone.utc)
    timestamp_fin = ahora_utc.isoformat()
    timestamp_inicio = datetime.fromtimestamp(ahora_utc.timestamp() - intervalo_segundos, tz=timezone.utc).isoformat()

    # Estructura limpia del Payload JSON alineada al Diccionario de la Fase 1
    return {
        "id_dispositivo": dispositivo["id"],
        "zona": zona,
        "tipo": dispositivo["tipo"],
        "estado": estado,
        "potencia_estimada_w": potencia_estimada_w,
        "consumo_kwh": consumo_kwh,
        "timestamp_inicio": timestamp_inicio,
        "timestamp_fin": timestamp_fin
    }


def enviar_a_firebase(lectura: dict) -> bool:
    """Envía el JSON de un dispositivo individual a Firebase Realtime Database mediante POST."""
    url = f"{FIREBASE_URL}/lecturas.json"
    try:
        response = requests.post(url, json=lectura, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR CLOUD] Fallo en la persistencia del dispositivo {lectura['id_dispositivo']}: {e}")
        return False


def main():
    print("====================================================")
    print("   Simulador IoT - Nube Verde ")
    print("====================================================")
    print(f"URL Nube: {FIREBASE_URL}")
    print(f"Frecuencia configurada: Transmisión cada {FRECUENCIA_SEGUNDOS} segundos.")
    print("Presiona Ctrl+C para detener de forma segura el envío.\n")

    while True:
        # Iteración por cada zona y por cada tipo de dispositivo físico independiente
        for zona, lista_dispositivos in INVENTARIO_DISPOSITIVOS.items():
            print(f"📡 Procesando lectura de la zona: {zona}...")
            for dispositivo in lista_dispositivos:
                # Generar lectura sin solapamientos ni duplicidades conceptuales
                payload = generar_lectura_dispositivo(dispositivo, zona, FRECUENCIA_SEGUNDOS)
                
                # Transmisión HTTP REST hacia la base de datos cloud
                exito = enviar_a_firebase(payload)
                status_msg = "ENVIADO" if exito else "ERROR"
                
                print(f"   ↳ Dispositivo: [{payload['id_dispositivo']}] | Potencia: {payload['potencia_estimada_w']} W | Energía: {payload['consumo_kwh']} kWh | Estado: {payload['estado']} -> [{status_msg}]")
        
        print(f"\n[ESPERA] Ciclo completado. Suspendiendo transmisión por {FRECUENCIA_SEGUNDOS} segundos...\n")
        time.sleep(FRECUENCIA_SEGUNDOS)


if __name__ == "__main__":
    main()
