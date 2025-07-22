# MPRH_DEV

Aplicación web para monitoreo y control remoto de máquina de perfusión renal hipotérmica (MPRH).  
Permite simular o controlar el sistema real mediante una interfaz web sencilla y moderna.

---

## Características

- Monitoreo en tiempo real de temperatura, caudal, presión, burbuja y estado de la bomba.
- Simulación de variables en modo MOCK para pruebas de frontend sin hardware.
- Control de bomba y sistema de refrigeración en modo manual.
- Gráficas dinámicas usando Chart.js.
- Fácil de migrar a conexión real por serial con Arduino.

---

## Estructura de carpetas

MPRH_DEV/
│
├── backend/
│   ├── app.py               # Servidor Flask principal (API + lógica)
│   └── arduino_serial.py    # Clase para conexión serial con Arduino
│
├── static/
│   ├── main.js              # JS frontend (fetch API, gráficos)
│   └── style.css            # CSS principal
│
├── templates/
│   └── index.html           # Página principal (Jinja2/HTML)
│
├── requirements.txt         # Dependencias Python
├── .gitignore
└── README.md

---

## Instalación

1. **Clona el repositorio**

   git clone https://github.com/PabloAFV/MPRH_DEV.git
   cd MPRH_DEV

2. **Crea y activa un entorno virtual**

   Windows:
       python -m venv venv
       venv\Scripts\activate

   Linux/Mac:
       python3 -m venv venv
       source venv/bin/activate

3. **Instala los paquetes necesarios**

   pip install -r backend/requirements.txt

---

## Uso (modo simulación/mock)

   python backend/app.py

Abre tu navegador en http://127.0.0.1:5000

Por defecto, la app simula datos del sistema.  
Para cambiar a modo **real** (lecturas desde Arduino), edita la variable USE_MOCK = False en backend/app.py.

---

## Conexión con Arduino

- Implementa tu lectura real en backend/arduino_serial.py usando la clase ArduinoSerial.
- El archivo app.py está listo para integrar los datos reales cuando USE_MOCK=False.

---

## Personalización

- Modifica el diseño visual en static/style.css.
- Ajusta la lógica y flujos en backend/app.py y static/main.js.

---

## Notas

- **No uses este servidor en producción.** Es solo para desarrollo/test.
- Requiere Python 3.8+ y pip.
- Si tienes problemas con dependencias, revisa el archivo requirements.txt.

---

## Licencia

MIT (o la que decidas)

---

Proyecto para fines educativos/desarrollo por Pablo Adrián Fuentes Villarreal
