# MPRH – Interfaz Web (Beta)

Este repositorio contiene la **interfaz gráfica y el backend** del proyecto MPRH, junto con el código Arduino (`.ino`) usado en la placa para la adquisición de datos.  

La interfaz permite monitorear las variables de **dos riñones** (presiones, temperatura, flujo, burbujas) y controlar la bomba desde un navegador web.

---

💡 **Sugerencia para principiantes**  
Si en algún momento no entiendes un paso, puedes copiar y pegar este README en una herramienta de inteligencia artificial (como ChatGPT) y pedir que te explique cada comando y cada instrucción con más detalle.  
De esta manera tendrás una guía personalizada mientras aprendes a usar VSCode, Python y Git.

---

## 📦 Requisitos previos

Antes de empezar, asegúrate de tener:

- **Visual Studio Code (VSCode)** instalado:  
  👉 [Descargar VSCode](https://code.visualstudio.com/)

- **Python 3.12 o superior** instalado en tu computadora:  
  👉 [Descargar Python](https://www.python.org/downloads/)  
  Durante la instalación, marca la casilla **"Add Python to PATH"**.

- **Git** instalado para clonar el repositorio:  
  👉 [Descargar Git](https://git-scm.com/downloads)

- Un Arduino conectado en el puerto **COM15** (en Windows).  
  ⚠️ Si tu Arduino aparece en otro COM (p. ej. COM5), deberás ajustar `PREFERRED_PORT` en `backend/app.py`.

---

## 🔧 Configuración del entorno en VSCode

1. **Abrir la terminal en VSCode**  
   - En el menú superior, selecciona: `Ver` → `Terminal`  
   - O usa el atajo: <kbd>Ctrl</kbd> + <kbd>ñ</kbd>  
   - Asegúrate de que la terminal esté en la carpeta raíz del proyecto clonado.

2. **Clonar el repositorio**  
   En la terminal de VSCode:

   ```powershell
   git clone https://github.com/PabloAFV/MPRH_DEV.git
   cd MPRH_DEV
   ```

   Esto descarga el proyecto y entra en la carpeta.

---

3. **Crear un entorno virtual de Python**  
   Esto mantiene separadas las librerías del proyecto:

   ```powershell
   python -m venv venv
   ```

   Esto crea la carpeta `venv/` con un Python aislado.  
   👉 Si quieres más información, busca en internet *"cómo crear un entorno virtual en Python con venv"*.

---

4. **Activar el entorno virtual**  
   Cada vez que abras el proyecto deberías activarlo:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   Si funciona, verás `(venv)` al inicio de la terminal.  
   👉 Para más detalles, busca *"activar entorno virtual python windows venv"*.

   ⚠️ Si te da error de permisos, ejecuta primero:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

---

5. **Instalar dependencias del proyecto**  

   ```powershell
   pip install -r backend/requirements.txt
   ```

   Esto descarga e instala Flask, pyserial y demás librerías necesarias.

---

## ▶️ Ejecutar la aplicación

1. Desde la carpeta raíz del proyecto, corre:

   ```powershell
   python backend/app.py
   ```

2. Si todo está bien, deberías ver en la terminal algo como:

   ```
   [APP] arranca c:\Users\pablo\Programming\MPRH\backend\app.py
   [SERIAL] Abriendo COM15 @ 115200 ...
   [SERIAL] Abierto COM15.
    * Serving Flask app 'app'
    * Debug mode: on
   WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
    * Running on all addresses (0.0.0.0)
    * Running on http://127.0.0.1:5000
    * Running on http://192.168.0.217:5000
   Press CTRL+C to quit
   ```

3. Abre en tu navegador cualquiera de estos enlaces:
   - [http://127.0.0.1:5000](http://127.0.0.1:5000) (solo en tu PC)
   - [http://192.168.0.217:5000](http://192.168.0.217:5000) (desde otros dispositivos en tu red local)

4. Para **detener la aplicación**, vuelve a la terminal y presiona:
   ```
   CTRL + C
   ```

---

## 📂 Estructura importante del repositorio

- **`backend/`** → Código Python (Flask y comunicación serial con Arduino).
- **`templates/`** → Archivo `index.html` para la interfaz web.
- **`static/`** → Archivos de frontend (`main.js`, `style.css`).
- **`arduino_files/MPRHinoV2.ino`** → Código Arduino.  
  ⚠️ **Nota importante**:  
  - VSCode marcará este archivo con errores porque **no se compila aquí**.  
  - Para usarlo, **copia/pega en el IDE de Arduino** y cárgalo en la placa.  
  - Ignora cualquier advertencia de VSCode sobre este archivo.

---

## ⚠️ Posibles problemas y soluciones

- **El servidor no arranca / error de intérprete en VSCode**  
  - Abre la paleta de comandos (`Ctrl+Shift+P`) → `Python: Select Interpreter`.  
  - Elige el que diga algo como `.
env\Scripts\python.exe`.

- **Faltan paquetes (Flask, pyserial, etc.)**  
  - Ejecuta otra vez:  
    ```powershell
    pip install -r backend/requirements.txt
    ```

- **Arduino no detectado en COM15**  
  - Revisa en el **Administrador de Dispositivos → Puertos (COM & LPT)**.  
  - Si aparece en otro COM, edita `backend/app.py`:
    ```python
    PREFERRED_PORT = "COM5"
    ```

- **Permiso denegado al abrir COM**  
  - Cierra cualquier **Serial Monitor** del Arduino IDE.  
  - Solo un programa puede usar el puerto al mismo tiempo.

- **La interfaz abre pero los datos no cambian**  
  - Si solo quieres ver el diseño sin Arduino, activa el modo mock:  
    Edita `backend/app.py` y pon:
    ```python
    USE_MOCK = True
    ```

---

## 💡 Extensiones útiles en VSCode

- **Python** (de Microsoft): ayuda con resaltado de sintaxis y ejecución.  
- **Pylance**: para autocompletado.  
- **GitLens**: para ver cambios en Git de forma clara.

⚙️ En la carpeta `.vscode` del repo, dentro del archivo `settings.json`, puedes agregar el path de tu entorno virtual de Python.  
Así no necesitas activarlo manualmente cada vez.

Ejemplo de configuración:

```json
{
  "python.pythonPath": ".\\venv\\Scripts\\python.exe"
}
```

📍 Para encontrar el path exacto de tu entorno virtual en tu computadora:  
- En Windows, abre la terminal de VSCode con el entorno activado y corre:
  ```powershell
  where python
  ```
  La primera ruta que aparezca será la de tu intérprete activo.  
- En Mac/Linux, corre:
  ```bash
  which python
  ```

Con esa ruta puedes actualizar `settings.json` si quieres usar un path absoluto.

---

## 📌 Notas finales

- Este método de ejecución es **temporal** para desarrollo y pruebas.  
- En el futuro se generará un **ejecutable único**, que reducirá todo este proceso a un solo click.  
- Mientras tanto, pueden hacer cambios al proyecto sin miedo:  
  - Sus modificaciones **no afectan el repositorio original en GitHub**.  
  - Si algo deja de funcionar, siempre pueden borrar su copia local y volver a clonar el repo para regresar a una versión funcional.

