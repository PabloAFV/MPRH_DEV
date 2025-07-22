from flask import Flask, jsonify, request, render_template
import os
import random


# Cambia este flag a False cuando uses datos reales
USE_MOCK = True

# MOCK state: Estado inicial, todo apagado
current_state = {
    'temperature': 15.0,
    'coolingOn': False,
    'flow': 0,
    'pressure': 0,
    'bubble': False,
    'pumpOn': False,
    'mode': 'Automático'
}

TEMP_OPT_LOW, TEMP_OPT_HIGH = 4.0, 8.0

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    if USE_MOCK:
        # Simulación enfriamiento
        if current_state['mode'] == 'Manual' and current_state['coolingOn']:
            # Enfriamiento activo
            if current_state['temperature'] > TEMP_OPT_LOW:
                current_state['temperature'] -= 0.2 + random.uniform(0, 0.3)
            else:
                current_state['temperature'] += random.uniform(-0.05, 0.15)
        else:
            # Calentamiento pasivo
            if current_state['temperature'] < 18.0:
                current_state['temperature'] += 0.08 + random.uniform(0, 0.1)

        # Bomba simulada
        if current_state['pumpOn']:
            if TEMP_OPT_LOW <= current_state['temperature'] <= TEMP_OPT_HIGH:
                current_state['flow'] = random.randint(65, 80)
                current_state['pressure'] = random.randint(90, 120)
                current_state['bubble'] = (random.random() < 0.03)
            else:
                # Si está fuera de rango óptimo
                current_state['flow'] = random.randint(10, 20)
                current_state['pressure'] = random.randint(30, 55)
                current_state['bubble'] = False
        else:
            current_state['flow'] = 0
            current_state['pressure'] = 0
            current_state['bubble'] = False

        return jsonify(current_state)
    else:
        # 👇 Aquí conectas con Arduino (cuando toque)
        from arduino_serial import ArduinoSerial
        arduino = ArduinoSerial('/dev/ttyUSB0', 9600)
        return jsonify(arduino.read_status())

@app.route('/api/pump', methods=['POST'])
def set_pump():
    data = request.get_json() or {}
    if current_state['mode'] == 'Manual' and 'pumpOn' in data:
        current_state['pumpOn'] = bool(data['pumpOn'])
    return ('', 204)

@app.route('/api/cooling', methods=['POST'])
def set_cooling():
    data = request.get_json() or {}
    if current_state['mode'] == 'Manual' and 'coolingOn' in data:
        current_state['coolingOn'] = bool(data['coolingOn'])
    return ('', 204)

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    current_state['pumpOn'] = False
    # Opcional: también apaga la refrigeración
    # current_state['coolingOn'] = False
    return ('', 204)

@app.route('/api/mode', methods=['POST'])
def set_mode():
    data = request.get_json() or {}
    if 'mode' in data and data['mode'] in ['Automático', 'Manual']:
        current_state['mode'] = data['mode']
        # Seguridad: al cambiar modo apaga bomba y refrigeración
        current_state['pumpOn'] = False
        current_state['coolingOn'] = False
    return ('', 204)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
