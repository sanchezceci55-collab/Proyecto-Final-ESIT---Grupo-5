"""
Simulador IoT - Nube Verde
Genera lecturas de consumo energético simuladas para varios puntos
de monitoreo (labs, aulas, oficinas) y las envía a Firebase Realtime
Database usando su API REST (no requiere el SDK de Firebase).
Fase 2 Corregida con Autenticación Exitosa
"""

import sys
import subprocess

# --- AUTO-INSTALACIÓN (Asegura que 'requests' esté instalado) ---
try:
    import requests
except ModuleNotFoundError:
    print("[INFO] Falta la librería 'requests'. Instalándola automáticamente, espera un momento...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("[ÉXITO] Librería 'requests' instalada correctamente. Continuando...\n")
    import requests

# Importación de librerías del núcleo de Python
import random
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------
# CONFIGURACIÓN — URL de Firebase Realtime Database
# ---------------------------------------------------------------
FIREBASE_URL = "https://nube-verde-default-rtdb.firebaseio.com"

# Frecuencia estricta de simulación (60 segundos)
FRECUENCIA_SEGUNDOS = 60  

# ---------------------------------------------------------------
# INVENTARIO CORREGIDO Y VALIDADO POR SITIO (Semántica de Grupos)
# Se incorporan los bloques horarios operativos institucionales reales
# ---------------------------------------------------------------
INVENTARIO_DISPOSITIVOS = {
    "Laboratorio_A": [
        {"id": "lab_a_pc_grupo", "tipo": "Computadora de escritorio", "cantidad": 20, "potencia_nominal_w": 150, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "lab_a_clima_01", "tipo": "Aire acondicionado", "cantidad": 1, "potencia_nominal_w": 1500, "hora_apertura": 10, "hora_cierre": 14},
        {"id": "lab_a_ilum_grupo", "tipo": "Luces LED", "cantidad": 10, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 17},
        {"id": "lab_a_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 250, "hora_apertura": 8, "hora_cierre": 14}
    ],
    "Laboratorio_B": [
        {"id": "lab_b_pc_grupo", "tipo": "Computadora de escritorio", "cantidad": 16, "potencia_nominal_w": 150, "hora_apertura": 8, "hora_cierre": 15},
        {"id": "lab_b_clima_01", "tipo": "Aire acondicionado", "cantidad": 1, "potencia_nominal_w": 1200, "hora_apertura": 11, "hora_cierre": 15},
        {"id": "lab_b_ilum_grupo", "tipo": "Luces LED", "cantidad": 8, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 16},
        {"id": "lab_b_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 200, "hora_apertura": 9, "hora_cierre": 13}
    ],
    "Oficina_Administrativa": [
        {"id": "oficina_pc_grupo", "tipo": "Computadora de escritorio", "cantidad": 6, "potencia_nominal_w": 120, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "oficina_imp_01", "tipo": "Impresora", "cantidad": 1, "potencia_nominal_w": 300, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "oficina_ilum_grupo", "tipo": "Luces LED", "cantidad": 6, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 17},
        {"id": "oficina_clima_01", "tipo": "Aire acondicionado mini-split", "cantidad": 1, "potencia_nominal_w": 900, "hora_apertura": 11, "hora_cierre": 14}
    ],
    "Aula_101": [
        {"id": "aula_ilum_grupo", "tipo": "Luces LED", "cantidad": 8, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 13},
        {"id": "aula_proy_01", "tipo": "Proyector", "cantidad": 1, "potencia_nominal_w": 250, "hora_apertura": 8, "hora_cierre": 11},
        {"id": "aula_lap_docente", "tipo": "Laptop del docente", "cantidad": 1, "potencia_nominal_w": 65, "hora_apertura": 7, "hora_cierre": 12},
        {"id": "aula_vent_grupo", "tipo": "Ventiladores de techo", "cantidad": 2, "potencia_nominal_w": 75, "hora_apertura": 8, "hora_cierre": 12}
    ]
}


def generar_lectura_dispositivo(dispositivo: dict, zona: str, intervalo_segundos: int) -> dict:
    """
    Genera métricas por grupo de dispositivos aplicando lógica de horarios fijos,
    cero consumo absoluto en fallas/apagados y semántica de carga agregada documentada.
    """
    # Obtener hora local actual para evaluar el rango operativo
    hora_actual = datetime.now().hour
    
    # 1. EVALUACIÓN DE ESTADO BASADA EN HORARIOS DE INVENTARIO (Corrige control temporal aleatorio)
    if not (dispositivo["hora_apertura"] <= hora_actual < dispositivo["hora_cierre"]):
        estado = "apagado"
    else:
        # Si está en horario operativo, existe un 3% de probabilidad estocástica de falla técnica
        estado = "falla" if random.random() < 0.03 else "encendido"

    # 2. MODELADO OPERATIVO DE POTENCIA (Resolución de semántica agregada y base física)
    potencia_total_base = dispositivo["potencia_nominal_w"] * dispositivo["cantidad"]
    
    if estado == "encendido":
        # Fluctuación operativa normal controlada del +/- 5%
        variacion = random.uniform(-0.05, 0.05)
        potencia_estimada_w = round(potencia_total_base * (1 + variacion), 2)
    elif estado == "falla":
        # ¡CORRECCIÓN CRÍTICA!: En falla la potencia es estrictamente 0.0 W (Elimina el error del 15%)
        potencia_estimada_w = 0.0
    else:
        # En estado apagado el consumo es nulo
        potencia_estimada_w = 0.0

    # 3. INTEGRACIÓN MATEMÁTICA DE ENERGÍA (kWh) EN VENTANAS RÍGIDAS DE TRANSMISIÓN
    duracion_horas = intervalo_segundos / 3600.0
    consumo_kwh = round((potencia_estimada_w * duracion_horas) / 1000.0, 6)

    # Definición precisa de marcas de tiempo del intervalo
    ahora_utc = datetime.now(timezone.utc)
    timestamp_fin = ahora_utc.isoformat()
    timestamp_inicio = datetime.fromtimestamp(ahora_utc.timestamp() - intervalo_segundos, tz=timezone.utc).isoformat()

    # Estructura limpia del Payload JSON incluyendo metadato de cantidad para evitar duplicidad analítica
    return {
        "id_dispositivo": dispositivo["id"],
        "zona": zona,
        "tipo": dispositivo["tipo"],
        "cantidad_equipos": dispositivo["cantidad"],  # Define explícitamente que es una lectura agregada
        "estado": estado,
        "potencia_estimada_w": potencia_estimada_w,
        "consumo_kwh": consumo_kwh,
        "timestamp_inicio": timestamp_inicio,
        "timestamp_fin": timestamp_fin
    }


def enviar_a_firebase(lectura: dict) -> bool:
    """Envía el JSON del grupo de dispositivos a Firebase Realtime Database mediante POST."""
    # Token secreto integrado para solventar errores de acceso 401 Unauthorized
    TOKEN_FIREBASE = "6zW9PaqQ8q4nvoqdVGAtOsx8lrjhlzF0D1KcyPwt"
    url = f"{FIREBASE_URL}/lecturas.json?auth={TOKEN_FIREBASE}"
    try:
        response = requests.post(url, json=lectura, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR CLOUD] Fallo en la persistencia del dispositivo {lectura['id_dispositivo']}: {e}")
        return False


def main():
    print("====================================================")
    print("   Simulador IoT - Nube Verde (Fase 2 Corregida) ")
    print("====================================================")
    print(f"URL Nube: {FIREBASE_URL}")
    print(f"Frecuencia configurada: Ciclos estrictos cada {FRECUENCIA_SEGUNDOS} segundos.")
    print("Presiona Ctrl+C para detener el proceso de forma segura.\n")

    while True:
        # Registramos el inicio exacto del ciclo para compensar desfases de red
        tiempo_inicio_ciclo = time.time()
        
        for zona, lista_dispositivos in INVENTARIO_DISPOSITIVOS.items():
            print(f"📡 Procesando lecturas de la zona: {zona}...")
            for dispositivo in lista_dispositivos:
                payload = generar_lectura_dispositivo(dispositivo, zona, FRECUENCIA_SEGUNDOS)
                exito = enviar_a_firebase(payload)
                status_msg = "ENVIADO" if exito else "ERROR"
                
                print(f"   ↳ Grupo: [{payload['id_dispositivo']}] ({payload['cantidad_equipos']} uds) | Potencia: {payload['potencia_estimada_w']} W | Energía: {payload['consumo_kwh']} kWh | Estado: {payload['estado']} -> [{status_msg}]")
        
        # COMPENSACIÓN DINÁMICA DEL TIEMPO DE RED (Corrige desalineación temporal de sleep rígidos)
        tiempo_procesamiento = time.time() - tiempo_inicio_ciclo
        tiempo_espera_real = max(0.0, FRECUENCIA_SEGUNDOS - tiempo_procesamiento)
        
        print(f"\n[ESPERA] Envío completado en {round(tiempo_procesamiento, 2)}s.")
        print(f"Duración del sleep ajustada a {round(tiempo_espera_real, 2)}s para mantener sincronía exacta.\n")
        
        time.sleep(tiempo_espera_real)


if __name__ == "__main__":
    main()
