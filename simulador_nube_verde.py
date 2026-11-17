"""
Simulador IoT - Nube Verde
Fase 2 - Versión Final Auditada
Incluye zona horaria explícita (UTC-6 El Salvador), tope físico Aula 101 y lectura .env.
"""

import os
import sys
import subprocess

# --- AUTO-INSTALACIÓN DE LIBRERÍAS ---
try:
    import requests
except ModuleNotFoundError:
    print("[INFO] Instalando dependencia 'requests'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

import random
import time
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------
# CONFIGURACIÓN SEGURA DE INFRAESTRUCTURA
# ---------------------------------------------------------------
FIREBASE_URL = "https://nube-verde-default-rtdb.firebaseio.com"
FRECUENCIA_SEGUNDOS = 60  

# Zona horaria explícita de El Salvador (UTC-6) sin depender de paquetes externos
ZONA_HORARIA_CAMPUS = timezone(timedelta(hours=-6), name="America/El_Salvador")


INVENTARIO_DISPOSITIVOS = {
    "Laboratorio_A": [
        {"id": "lab_a_pc_grupo", "tipo": "Computadora de Escritorio", "cantidad": 20, "potencia_nominal_w": 150, "hora_apertura": 8, "hora_cierre": 14},
        {"id": "lab_a_clima_01", "tipo": "Aire Acondicionado Central", "cantidad": 1, "potencia_nominal_w": 1500, "hora_apertura": 10, "hora_cierre": 14},
        {"id": "lab_a_ilum_grupo", "tipo": "Luminarias LED de Alta Eficiencia", "cantidad": 10, "potencia_nominal_w": 18, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "lab_a_proy_01", "tipo": "Proyector Multimedia", "cantidad": 1, "potencia_nominal_w": 250, "hora_apertura": 9, "hora_cierre": 11}
    ],
    "Laboratorio_B": [
        {"id": "lab_b_pc_grupo", "tipo": "Computadora de Escritorio", "cantidad": 16, "potencia_nominal_w": 150, "hora_apertura": 8, "hora_cierre": 13},
        {"id": "lab_b_clima_01", "tipo": "Aire Acondicionado Standard", "cantidad": 1, "potencia_nominal_w": 1200, "hora_apertura": 9, "hora_cierre": 13},
        {"id": "lab_b_ilum_grupo", "tipo": "Luminarias LED de Alta Eficiencia", "cantidad": 8, "potencia_nominal_w": 18, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "lab_b_proy_01", "tipo": "Proyector Multimedia", "cantidad": 1, "potencia_nominal_w": 200, "hora_apertura": 10, "hora_cierre": 11}
    ],
    "Oficina_Administrativa": [
        {"id": "oficina_pc_grupo", "tipo": "Computadora de Escritorio", "cantidad": 6, "potencia_nominal_w": 120, "hora_apertura": 8, "hora_cierre": 16},
        {"id": "oficina_imp_01", "tipo": "Impresora Multifuncional Láser", "cantidad": 1, "potencia_nominal_w": 300, "hora_apertura": 11, "hora_cierre": 12},
        {"id": "oficina_ilum_grupo", "tipo": "Luminarias LED Standard", "cantidad": 6, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 17, "minuto_apertura": 30, "minuto_cierre": 30},
        {"id": "oficina_clima_01", "tipo": "Aire Acondicionado Mini-Split", "cantidad": 1, "potencia_nominal_w": 900, "hora_apertura": 12, "hora_cierre": 15}
    ],
    "Aula_101": [
        {"id": "aula_ilum_grupo", "tipo": "Luminarias LED Standard", "cantidad": 8, "potencia_nominal_w": 18, "hora_apertura": 7, "hora_cierre": 13},
        {"id": "aula_proy_01", "tipo": "Proyector Multimedia", "cantidad": 1, "potencia_nominal_w": 250, "hora_apertura": 8, "hora_cierre": 10},
        {"id": "aula_lap_docente", "tipo": "Laptop Estación de Trabajo Docente", "cantidad": 1, "potencia_nominal_w": 65, "hora_apertura": 7, "hora_cierre": 10},
        {"id": "aula_vent_grupo", "tipo": "Ventiladores de Techo Corregidos", "cantidad": 2, "potencia_nominal_w": 75, "hora_apertura": 7, "hora_cierre": 11}
    ]
}

def generar_lectura_dispositivo(dispositivo: dict, zona: str, intervalo_segundos: int, id_ciclo: str) -> dict:
    """Genera lecturas usando estrictamente la zona horaria oficial de El Salvador."""
    ahora_campus = datetime.now(ZONA_HORARIA_CAMPUS)
    minutos_actuales = ahora_campus.hour * 60 + ahora_campus.minute
    
    min_apertura = dispositivo["hora_apertura"] * 60 + dispositivo.get("minuto_apertura", 0)
    min_cierre = dispositivo["hora_cierre"] * 60 + dispositivo.get("minuto_cierre", 0)

    if not (min_apertura <= minutos_actuales < min_cierre):
        estado = "apagado"
    else:
        estado = "falla" if random.random() < 0.03 else "encendido"

    potencia_total_base = dispositivo["potencia_nominal_w"] * dispositivo["cantidad"]
    
    if estado == "encendido":
        variacion = random.uniform(-0.05, 0.05)
        potencia_estimada_w = round(potencia_total_base * (1 + variacion), 2)
        # Control físico: Evita que la fluctuación supere el límite nominal en Aula 101
        if zona == "Aula_101" and potencia_estimada_w > potencia_total_base:
            potencia_estimada_w = float(potencia_total_base)
    else:
        potencia_estimada_w = 0.0

    duracion_horas = intervalo_segundos / 3600.0
    consumo_kwh = round((potencia_estimada_w * duracion_horas) / 1000.0, 6)

    ahora_utc = datetime.now(timezone.utc)
    timestamp_fin = ahora_utc.isoformat()
    timestamp_inicio = datetime.fromtimestamp(ahora_utc.timestamp() - intervalo_segundos, tz=timezone.utc).isoformat()

    return {
        "id_ciclo": id_ciclo,
        "id_dispositivo": dispositivo["id"],
        "zona": zona,
        "tipo": dispositivo["tipo"],
        "cantidad_equipos": dispositivo["cantidad"],
        "estado": estado,
        "potencia_estimada_w": potencia_estimada_w,
        "consumo_kwh": consumo_kwh,
        "timestamp_inicio": timestamp_inicio,
        "timestamp_fin": timestamp_fin
    }

def enviar_a_firebase(lectura: dict) -> bool:
    """Envía la métrica cargando el token desde un archivo local .env o variable de entorno."""
    token_firebase = os.environ.get("FIREBASE_TOKEN", "")
    
    if not token_firebase and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("FIREBASE_TOKEN="):
                        token_firebase = line.strip().split("=")[1].strip('"').strip("'")
                        break
        except Exception:
            pass

    url = f"{FIREBASE_URL}/lecturas.json"
    params = {"auth": token_firebase} if token_firebase else {}
    
    try:
        response = requests.post(url, json=lectura, params=params, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        print(f"  [ERROR CLOUD] Fallo de persistencia en dispositivo: {lectura['id_dispositivo']}")
        return False

def main():
    print("====================================================")
    print("   Simulador IoT - Nube Verde (Fase 2 Auditado)     ")
    print("====================================================")
    print(f"Zona Horaria Activa: {ZONA_HORARIA_CAMPUS}")
    print(f"Frecuencia de Ingesta: Cada {FRECUENCIA_SEGUNDOS}s.\n")

    while True:
        tiempo_inicio_ciclo = time.time()
        id_ciclo = f"ciclo_{int(tiempo_inicio_ciclo)}"
        
        for zona, lista_dispositivos in INVENTARIO_DISPOSITIVOS.items():
            print(f"📡 Procesando zona: {zona}...")
            for dispositivo in lista_dispositivos:
                payload = generar_lectura_dispositivo(dispositivo, zona, FRECUENCIA_SEGUNDOS, id_ciclo)
                exito = enviar_a_firebase(payload)
                status_msg = "ENVIADO" if exito else "ERROR"
                print(f"   ↳ [{payload['id_dispositivo']}] ({payload['cantidad_equipos']} uds) | {payload['potencia_estimada_w']} W | {payload['estado']} -> [{status_msg}]")
        
        tiempo_procesamiento = time.time() - tiempo_inicio_ciclo
        tiempo_espera_real = max(0.0, FRECUENCIA_SEGUNDOS - tiempo_procesamiento)
        
        if tiempo_procesamiento > FRECUENCIA_SEGUNDOS:
            print(f"⚠️ [TOLERANCIA EXCEDIDA] El ciclo tardó {round(tiempo_procesamiento, 2)}s (>60s). Iniciando siguiente ciclo sin pausa.")
            
        print(f"\n[SINCRO] Ciclo completado en {round(tiempo_procesamiento, 2)}s. Pausa: {round(tiempo_espera_real, 2)}s.\n")
        time.sleep(tiempo_espera_real)

if __name__ == "__main__":
    main()
    