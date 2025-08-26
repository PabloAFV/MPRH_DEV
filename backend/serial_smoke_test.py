# backend/serial_smoke_test.py
import time, sys
import serial
from serial.tools import list_ports

PORT = "COM15"   # cambia si ves otro en list_ports -v
BAUD = 115200

print("Puertos disponibles:")
for p in list_ports.comports():
    print("  ", p.device, "-", p.description)

print(f"\nAbriendo {PORT} @ {BAUD}...")
ser = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2.0)  # UNO se resetea al abrir; espera al bootloader

print("Leyendo 10 líneas...")
for i in range(10):
    line = ser.readline().decode(errors="ignore").strip()
    print(f"[{i}] {line!r}")
    time.sleep(0.2)

ser.close()
print("Cerrado.")
