import threading
import time
import serial
import traceback
from serial.tools import list_ports

CANDIDATE_KEYWORDS = ("arduino", "ch340", "usb-serial", "usb serial", "wch", "silabs", "cp210", "ftdi")

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
    # 3) fallback: primero
    return ports[0].device if ports else None

class ArduinoSerial:
    """
    Protocolo esperado (una línea):
      T:<°C>,F:<ml/min>,P:<mmHg>,B:<0/1>,PUMP:<0/1>,COOL:<0/1>,MODE:<MAN/AUTO>
    Comandos:
      SET_PUMP:0|1
      SET_COOL:0|1
      SET_MODE:MAN|AUTO
    """
    def __init__(self, preferred_port: str | None, baudrate: int = 115200, timeout: float = 2.0):
        self.preferred_port = preferred_port
        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

        self.last_raw_line = ""
        self._last_state = {
            "temperature": 0.0,
            "flow": 0,
            "pressure": 0,
            "bubble": False,
            "pumpOn": False,
            "coolingOn": False,
            "mode": "Manual",
            "connected": False,
            "port": None,
        }
        self._lock = threading.Lock()
        self._stop = False
        self._t = threading.Thread(target=self._reader, daemon=True)
        self._t.start()

    def _try_open(self):
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
                candidate,
                self.baudrate,
                timeout=self.timeout,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
            )
            self.port = candidate
            time.sleep(2.0)  # reset del UNO
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
                # print(f"[SERIAL] <- {line}")  # descomenta si quieres flood de trazas

                parsed = {}
                for p in line.split(","):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        parsed[k.strip().upper()] = v.strip()

                with self._lock:
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
                    self._last_state["connected"] = True
                    self._last_state["port"] = self.port
            except Exception as e:
                print(f"[SERIAL] Error leyendo {self.port}: {e}")
                traceback.print_exc()
                with self._lock:
                    self._last_state["connected"] = False
                try:
                    if self.ser: self.ser.close()
                except: pass
                time.sleep(0.8)

    def read_status(self) -> dict:
        with self._lock:
            d = dict(self._last_state)
        d["_last_raw"] = self.last_raw_line
        return d

    def _send(self, s: str):
        if not self._try_open():
            print("[SERIAL] No abierto, no se envía:", s)
            return
        try:
            print(f"[SERIAL] -> {s}")
            self.ser.write((s + "\n").encode())
        except Exception as e:
            print(f"[SERIAL] Error enviando: {e}")
            try:
                if self.ser: self.ser.close()
            except: pass
            with self._lock:
                self._last_state["connected"] = False

    def set_pump(self, on: bool):
        self._send(f"SET_PUMP:{1 if on else 0}")

    def set_cooling(self, on: bool):
        self._send(f"SET_COOL:{1 if on else 0}")

    def set_mode(self, mode: str):
        self._send(f"SET_MODE:{'AUTO' if mode=='Automático' else 'MAN'}")

    def available_ports(self):
        return [{"device": p.device, "description": p.description, "manufacturer": p.manufacturer}
                for p in list_ports.comports()]

    def set_preferred_port(self, port: str | None):
        print(f"[SERIAL] Preferido cambiado a: {port}")
        self.preferred_port = port
        try:
            if self.ser: self.ser.close()
        except: pass
        with self._lock:
            self._last_state["connected"] = False
            self._last_state["port"] = None

    def close(self):
        self._stop = True
        try: self._t.join(timeout=1.0)
        except: pass
        try:
            if self.ser: self.ser.close()
        except: pass
