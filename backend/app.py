# backend/app.py
from flask import Flask, jsonify, request, render_template
import os

print("[APP] arranca", __file__)  # para confirmar que corres el archivo correcto

# ==== Config ====
USE_MOCK = False
PREFERRED_PORT = "COM15"   # en RPi será /dev/ttyUSB0 o similar
ARDUINO_BAUD = 115200

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR    = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

# ==== Serial ====
arduino = None
if not USE_MOCK:
    from arduino_serial import ArduinoSerial
    arduino = ArduinoSerial(PREFERRED_PORT, ARDUINO_BAUD)
    # Forzar estado seguro/esperado al arrancar
    try:
        arduino.set_mode('Manual')   # iniciar en Manual
        arduino.set_pump(False)      # bomba OFF por seguridad
    except Exception as e:
        print("[APP] No pude forzar estado inicial:", e)

# ==== Rutas UI ====
@app.route('/')
def index():
    return render_template('index.html')

# ==== API ====
@app.route('/api/status')
def status():
    """
    Devuelve el estado actual.
    Compatibilidad: 'pressure' se mantiene (usa P1 si está disponible).
    Extensiones: 'pressure1' y 'pressure2' para dos riñones.
    """
    if not USE_MOCK:
        s = arduino.read_status()
        return jsonify({
            'temperature': s.get('temperature', 0.0),
            'flow':        s.get('flow', 0),
            'pressure':    s.get('pressure', 0),       # compat principal
            'pressure1':   s.get('pressure1', None),   # nuevo opcional
            'pressure2':   s.get('pressure2', None),   # nuevo opcional
            'bubble':      s.get('bubble', False),
            'pumpOn':      s.get('pumpOn', False),
            'coolingOn':   s.get('coolingOn', False),
            'mode':        s.get('mode', 'Manual'),
            'connected':   s.get('connected', False),
            'port':        s.get('port', None),
        })
    # Mock de respaldo
    return jsonify({
        'temperature': 5.0, 'flow': 0, 'pressure': 0,
        'pressure1': None, 'pressure2': None,
        'bubble': False, 'pumpOn': False, 'coolingOn': False,
        'mode': 'Manual', 'connected': True, 'port': None
    })

@app.route('/api/pump', methods=['POST'])
def set_pump():
    """
    Cambia la bomba SOLO si el modo actual es Manual.
    En Automático, se ignora la petición (la UI también debería deshabilitar).
    """
    data = request.get_json() or {}
    if not USE_MOCK:
        s = arduino.read_status()
        if (s.get('mode') or 'Manual') == 'Manual':
            arduino.set_pump(bool(data.get('pumpOn', False)))
        else:
            # Ignorar en Automático
            pass
    return ('', 204)

@app.route('/api/cooling', methods=['POST'])
def set_cooling():
    data = request.get_json() or {}
    if not USE_MOCK:
        arduino.set_cooling(bool(data.get('coolingOn', False)))
    return ('', 204)

@app.route('/api/mode', methods=['POST'])
def set_mode():
    """
    Cambia el modo. Si se pasa 'Automático', la bomba no cambia aquí;
    la lógica de bomba queda en /api/pump (y seguirá bloqueada en Automático).
    """
    data = request.get_json() or {}
    m = data.get('mode', 'Manual')
    if not USE_MOCK:
        arduino.set_mode(m)
        # seguridad opcional: si cambiamos a Automático, podríamos forzar bomba OFF
        # if m == 'Automático':
        #     arduino.set_pump(False)
    return ('', 204)

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """
    Parada de emergencia: siempre detiene la bomba (en cualquier modo).
    """
    if not USE_MOCK:
        arduino.emergency_stop()
    return ('', 204)

# ---- Diagnóstico
@app.route('/api/debug')
def debug():
    s = arduino.read_status() if arduino else {}
    return jsonify({
        "connected": s.get("connected", False),
        "port": s.get("port", None),
        "last_raw": s.get("_last_raw", "")
    })

@app.route('/api/ports')
def ports():
    return jsonify(arduino.available_ports() if arduino else [])

@app.route('/api/select-port', methods=['POST'])
def select_port():
    port = (request.get_json() or {}).get("port")
    if arduino:
        arduino.set_preferred_port(port)
    return ('', 204)

# ==== Run ====
if __name__ == '__main__':
    # reloader desactivado => no arranca dos procesos
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
