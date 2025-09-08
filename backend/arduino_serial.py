# backend/arduino_serial.py
import threading
import time
import serial
import traceback
from serial.tools import list_ports

CANDIDATE_KEYWORDS = (
    "arduino", "ch340", "usb-serial", "usb serial",
    "wch", "silabs", "cp210", "ftdi"
)

def find_serial_port(preferred: str | None = None) -> str | None:
    ports = list(list_ports.comports())
    # 1) preferido exacto
    if preferred:
        for p in ports:
            if p.device.lower() == preferred.lower():
                return p.device
    # 2) heurística por descripción
    for p in ports:
        desc = f"{p.device} {p.description} {p.manufacturer or ''}".lower()
        if any(k in desc for k in CANDIDATE_KEYWORDS):
            return p.device
    # 3) fallback
    return ports[0].device if ports else None


class ArduinoSerial:
    """
    Protocolo LEGACY (una línea por frame):
      T:<°C>,F:<ml/min>,P:<mmHg>,B:<0/1>,PUMP:<0/1>,COOL:<0/1>,MODE:<MAN/AUTO>

    Extensiones opcionales para 2 riñones (si el firmware las emite):
      P1:<mmHg>, P2:<mmHg>
      PAM1:<mmHg>, PAM2:<mmHg>
      SYS1:/DIA1:, SYS2:/DIA2:

    Comandos TX (LEGACY):
      SET_PUMP:0|1
      SET_COOL:0|1
      SET_MODE:MAN|AUTO
    """
    def __init__(self, preferred_port: str | None, baudrate: int = 115200, timeout: float = 2.0):
        self.preferred_port = preferred_port
        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None

        self.last_raw_line = ""
        self._last_state = {
            "temperature": 0.0,
            "flow": 0,
            "pressure": 0,       # compat principal (usa P1 si hay; si no, P)
            "pressure1": None,   # nuevo (si llega P1)
            "pressure2": None,   # nuevo (si llega P2)
            "bubble": False,
            "pumpOn": False,
            "coolingOn": False,
            "mode": "Manual",
            "connected": False,
            "port": None,
        }

        # Locks
        self._lock = threading.Lock()         # protege _last_state
        self._open_lock = threading.Lock()    # evita aperturas simultáneas
        self._send_lock = threading.Lock()    # evita colisiones write/close
        self._stop = False

        self._t = threading.Thread(target=self._reader, daemon=True)
        self._t.start()

    # -------------------- Conexión --------------------
    def _try_open(self) -> bool:
        # Un solo hilo a la vez puede intentar abrir/cerrar
        with self._open_lock:
            if self.ser and self.ser.is_open:
                return True

            candidate = find_serial_port(self.preferred_port)
            if not candidate:
                print("[SERIAL] No hay puertos disponibles.")
                with self._lock:
                    self._last_state["connected"] = False
                    self._last_state["port"] = None
                return False
            try:
                print(f"[SERIAL] Abriendo {candidate} @ {self.baudrate} ...")
                self.ser = serial.Serial(
                    candidate, self.baudrate, timeout=self.timeout,
                    rtscts=False, dsrdtr=False, xonxoff=False
                )
                self.port = candidate
                # reset típico al abrir el puerto (DTR)
                time.sleep(2.0)
                with self._lock:
                    self._last_state["connected"] = True
                    self._last_state["port"] = candidate
                print(f"[SERIAL] Abierto {candidate}.")
                return True
            except Exception as e:
                print(f"[SERIAL] Error abriendo {candidate}: {e}")
                traceback.print_exc()
                with self._lock:
                    self._last_state["connected"] = False
                    self._last_state["port"] = None
                return False

    # -------------------- Lectura --------------------
    def _reader(self):
        while not self._stop:
            if not self._try_open():
                time.sleep(0.8)
                continue
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                self.last_raw_line = line

                parsed = {}
                for p in line.split(","):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        parsed[k.strip().upper()] = v.strip()

                self._apply_legacy_packet(parsed)

                with self._lock:
                    self._last_state["connected"] = True
                    self._last_state["port"] = self.port

            except Exception as e:
                print(f"[SERIAL] Error leyendo {self.port}: {e}")
                traceback.print_exc()
                with self._lock:
                    self._last_state["connected"] = False
                try:
                    # Cerrar de forma segura con el lock de apertura
                    with self._open_lock:
                        if self.ser:
                            self.ser.close()
                except:
                    pass
                time.sleep(0.8)

    def _apply_legacy_packet(self, parsed: dict):
        with self._lock:
            # ---- básicos del protocolo viejo
            if "T" in parsed:
                try: self._last_state["temperature"] = float(parsed["T"])
                except: pass
            if "F" in parsed:
                try: self._last_state["flow"] = int(float(parsed["F"]))
                except: pass
            if "P" in parsed:
                try: self._last_state["pressure"] = int(float(parsed["P"]))
                except: pass
            if "B" in parsed:
                self._last_state["bubble"] = (parsed["B"] == "1")
            if "PUMP" in parsed:
                self._last_state["pumpOn"] = (parsed["PUMP"] == "1")
            if "COOL" in parsed:
                self._last_state["coolingOn"] = (parsed["COOL"] == "1")
            if "MODE" in parsed:
                self._last_state["mode"] = "Automático" if parsed["MODE"] == "AUTO" else "Manual"

            # ---- extensiones opcionales para 2 sensores
            if "P1" in parsed:
                try: self._last_state["pressure1"] = int(float(parsed["P1"]))
                except: pass
            if "P2" in parsed:
                try: self._last_state["pressure2"] = int(float(parsed["P2"]))
                except: pass

            # si tenemos P1, úsalo como pressure (compat con app.py actual)
            if self._last_state.get("pressure1") is not None:
                self._last_state["pressure"] = self._last_state["pressure1"]

    # -------------------- API pública --------------------
    def read_status(self) -> dict:
        with self._lock:
            d = dict(self._last_state)
        d["_last_raw"] = self.last_raw_line
        return d

    def _send(self, s: str):
        # Asegura apertura + exclusión mutua de escrituras
        with self._send_lock:
            if not self._try_open():
                print("[SERIAL] No abierto, no se envía:", s)
                return
            try:
                self.ser.write((s + "\n").encode())
            except Exception as e:
                print(f"[SERIAL] Error enviando: {e}")
                try:
                    with self._open_lock:
                        if self.ser:
                            self.ser.close()
                except:
                    pass
                with self._lock:
                    self._last_state["connected"] = False

    # ---- Comandos LEGACY ----
    def set_pump(self, on: bool):
        self._send(f"SET_PUMP:{1 if on else 0}")

    def set_cooling(self, on: bool):
        self._send(f"SET_COOL:{1 if on else 0}")

    def set_mode(self, mode: str):
        # acepta "Manual" o "Automático" desde la API
        val = "AUTO" if mode == "Automático" else "MAN"
        self._send(f"SET_MODE:{val}")

    def emergency_stop(self):
        # protocolo legacy: no hay comando dedicado en todos los firmwares,
        # así que forzamos bomba OFF
        self._send("SET_PUMP:0")

    def available_ports(self):
        return [
            {"device": p.device, "description": p.description, "manufacturer": p.manufacturer}
            for p in list_ports.comports()
        ]

    def set_preferred_port(self, port: str | None):
        print(f"[SERIAL] Preferido cambiado a: {port}")
        self.preferred_port = port
        # Reinicia conexión de forma segura
        with self._open_lock:
            try:
                if self.ser:
                    self.ser.close()
            except:
                pass
            with self._lock:
                self._last_state["connected"] = False
                self._last_state["port"] = None

    def close(self):
        self._stop = True
        try:
            self._t.join(timeout=1.0)
        except:
            pass
        with self._open_lock:
            try:
                if self.ser:
                    self.ser.close()
            except:
                pass
