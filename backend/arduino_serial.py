import time

class ArduinoSerial:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def read_status(self):
        time.sleep(0.1)
        # Aquí parsearías los datos reales del Arduino
        return {
            'temperature': None,
            'flow': None,
            'pressure': None,
            'bubble': None,
            'pumpOn': None,
            'mode': None
        }