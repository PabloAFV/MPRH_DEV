from flask import Flask, jsonify, request, render_template
import os

print("[APP] arranca", __file__)  # para confirmar que corres el archivo correcto

USE_MOCK = False
PREFERRED_PORT = "COM15"
ARDUINO_BAUD = 115200

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR    = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

arduino = None
if not USE_MOCK:
    from arduino_serial import ArduinoSerial
    arduino = ArduinoSerial(PREFERRED_PORT, ARDUINO_BAUD)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    if not USE_MOCK:
        s = arduino.read_status()
        return jsonify({
            'temperature': s.get('temperature', 0.0),
            'flow': s.get('flow', 0),
            'pressure': s.get('pressure', 0),
            'bubble': s.get('bubble', False),
            'pumpOn': s.get('pumpOn', False),
            'coolingOn': s.get('coolingOn', False),
            'mode': s.get('mode', 'Manual'),
            'connected': s.get('connected', False),
            'port': s.get('port', None),
        })
    # fallback mock
    return jsonify({'temperature':0,'flow':0,'pressure':0,'bubble':False,'pumpOn':False,'coolingOn':False,'mode':'Manual','connected':True,'port':None})

@app.route('/api/pump', methods=['POST'])
def set_pump():
    data = request.get_json() or {}
    if not USE_MOCK:
        arduino.set_pump(bool(data.get('pumpOn', False)))
    return ('', 204)

@app.route('/api/cooling', methods=['POST'])
def set_cooling():
    data = request.get_json() or {}
    if not USE_MOCK:
        arduino.set_cooling(bool(data.get('coolingOn', False)))
    return ('', 204)

@app.route('/api/mode', methods=['POST'])
def set_mode():
    data = request.get_json() or {}
    m = data.get('mode', 'Manual')
    if not USE_MOCK:
        arduino.set_mode(m)
    return ('', 204)

# ---- Diagnóstico
@app.route('/api/debug')
def debug():
    s = arduino.read_status()
    return jsonify({
        "connected": s.get("connected", False),
        "port": s.get("port", None),
        "last_raw": s.get("_last_raw", "")
    })

@app.route('/api/ports')
def ports():
    return jsonify(arduino.available_ports())

@app.route('/api/select-port', methods=['POST'])
def select_port():
    port = (request.get_json() or {}).get("port")
    arduino.set_preferred_port(port)
    return ('', 204)

if __name__ == '__main__':
    # reloader desactivado => no arranca dos procesos
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

