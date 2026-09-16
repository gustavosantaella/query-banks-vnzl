# 🏦 Query Bank VNZL

Query Bank VNZL es una solución premium de automatización financiera diseñada para consultar y consolidar saldos, cuentas y tarjetas de múltiples entidades bancarias venezolanas (como Bancamiga y Banco Nacional de Crédito) en un único panel de control unificado, moderno e interactivo.

Desarrollada con un enfoque híbrido, combina la potencia de un motor de scraping inteligente en el backend con una interfaz web progresiva (PWA) de diseño minimalista y alta fidelidad en el frontend.

---

## 🚀 Arquitectura y Características Clave

*   **Sincronización Concurrente (Multithreading)**: Ejecuta consultas de scraping en paralelo mediante hilos de ejecución para agilizar la recopilación de datos bancarios.
*   **Gestión Dinámica de 2FA (WebSockets)**: Si una entidad bancaria requiere validación de doble factor (OTP / Google Authenticator), el backend suspende temporalmente el scraping, notifica en tiempo real al portal web a través de un WebSocket, solicita el código al usuario mediante un modal premium, e introduce el token enviado de vuelta para continuar la automatización de forma ininterrumpida.
*   **Evasión de Bloqueos Anti-Bot (Stealth Mode)**: Integra `undetected-chromedriver` de forma nativa para enmascarar las firmas de Selenium, simulando un navegador regular.
*   **Navegador Headed Invisible**: Permite configurar un navegador visible pero posicionado fuera de los límites de la pantalla (ej. coordenada `3000,3000`) y con resolución ultra-reducida (`10x10` píxeles), permitiendo resolver desafíos de Cloudflare Turnstile sin interrumpir el trabajo de escritorio del usuario.
*   **Offline-First (Caché Local)**: Persiste de forma segura los saldos y balances extraídos en el `localStorage` del navegador, permitiendo al usuario revisar sus balances pasados al instante incluso si el servidor backend se encuentra offline.

---

## 📁 Estructura del Proyecto

El repositorio está dividido en dos grandes bloques:

```text
query-bank-vnzl/
├── backend/                  # Servidor API de Automatización (Python)
│   ├── src/
│   │   ├── app_module.py     # Inicializador y rutas FastAPI / WebSocket
│   │   ├── config/
│   │   │   └── app/
│   │   │       ├── constants/
│   │   │       │   └── banks.py     # Declaración de metadatos de bancos soportados
│   │   │       ├── selenium/
│   │   │       │   └── __init__.py  # Inicialización de Chrome/Undetected Driver
│   │   │       └── ws_state.py      # Estado compartido de WebSocket y sincronización
│   │   └── modules/
│   │       └── query/
│   │           ├── controllers/     # Controladores FastAPI (PyNest)
│   │           └── services/        # Lógica de scraping para cada banco (Selenium)
│   ├── .env                  # Variables de entorno críticas
│   ├── main.py               # Punto de entrada de la aplicación
│   └── requirements.txt      # Dependencias del backend
│
└── portal/                   # Aplicación Web Frontend (Angular)
    ├── src/
    │   ├── app/
    │   │   ├── components/   # Componentes modulares y reutilizables (UI/UX)
    │   │   ├── services/     # Clientes de servicios REST y WebSockets
    │   │   ├── app.html      # Plantilla principal del Dashboard
    │   │   └── app.ts        # Lógica de control y reactividad (Angular Signals)
    │   └── main.ts           # Inicialización de la aplicación standalone
    ├── tailwind.config.js    # Diseño del sistema de estilos Tailwind CSS
    └── package.json          # Dependencias y scripts NPM
```

---

## ⚙️ Configuración del Entorno (`.env`)

Crea un archivo `.env` en la raíz del directorio `backend/` con las siguientes variables:

| Variable | Descripción | Valor por Defecto / Ejemplo |
| :--- | :--- | :--- |
| `DB_NAME` | Nombre de la base de datos MySQL (opcional) | `query_bank_vnzl` |
| `SELENIUM_HEADLESS` | Ejecutar el navegador oculto (`True`) o visible (`False`) | `True` |
| `SELENIUM_WINDOW_WIDTH` | Ancho de la ventana del navegador stealth (en px) | `10` |
| `SELENIUM_WINDOW_HEIGHT` | Alto de la ventana del navegador stealth (en px) | `10` |
| `SELENIUM_WINDOW_POSITION` | Ubicación espacial (Coordenadas X, Y) del navegador | `3000,3000` |
| `DNI` | Documento de Identidad del usuario (Cédula de Identidad) | `V12345678` |
| `BNC_URL` | Portal oficial de login de Banco Nacional de Crédito | `https://personas.bncenlinea.com/` |
| `BNC_CARD_NUMBER` | Número de tarjeta de débito BNC | `12345678910XXXX` |
| `BNC_PASS` | Contraseña de acceso a BNC en línea | `Contrasena123$` |
| `BANCAMIGA_URL` | Portal oficial de login de Bancamiga | `https://online.bancamiga.com/?p=1` |
| `BANCAMIGA_USER` | Nombre de usuario de Bancamiga | `mi_usuario` |
| `BANCAMIGA_PASS` | Contraseña de acceso a Bancamiga | `Contrasena123$` |

---

## 🛠️ Instalación y Ejecución

### 1. Inicialización del Backend
Accede a la carpeta de backend, inicializa tu entorno virtual e instala los requerimientos:

```powershell
cd backend
python -m venv .venv
# Activar entorno (Windows)
.venv\Scripts\activate
# Instalar dependencias
pip install -r requirements.txt
pip install undetected-chromedriver
# Ejecutar servidor FastAPI
python main.py
```
El servidor backend se levantará en `http://localhost:8000`.

### 2. Inicialización del Portal Frontend
Abre una terminal paralela en la raíz del proyecto, accede a la carpeta de portal e inicializa:

```powershell
cd portal
npm install
npm start
```
La aplicación web se compilará y se desplegará localmente en `http://localhost:4200`.

---

## 🚢 Despliegue del Backend en Railway

El backend se despliega como contenedor Docker. En la raíz del repositorio están:

```text
query-bank-vnzl/
├── Dockerfile        # Imagen del backend (Python 3.12 + Chromium + ChromeDriver)
├── railway.json      # Configuración de build/deploy para Railway
└── .dockerignore     # Excluye .venv, .env, html_templates y el portal del contexto
```

### 1. Crear el servicio

1. En Railway: **New Project → Deploy from GitHub repo** y selecciona este repositorio.
2. Railway detecta `railway.json` y construye con el `Dockerfile`.
3. Asegúrate de que:
   * **Root Directory**: vacío / `/` (el `Dockerfile` está en la raíz).
   * **Dockerfile Path**: `Dockerfile`.
   * **Healthcheck Path**: `/api/query/banks` (ya viene en `railway.json`).

> El prefijo `/api` funciona tanto en `/api/query/...` como en `/query/...`
> (`app_module.py` define `root_path = "/api"`), igual que el WebSocket en
> `/api/ws/query`.

### 2. Variables de entorno (Railway → Variables)

El contenedor no tiene terminal interactiva, por lo que **no** se puede usar el
respaldo por consola: todas las credenciales deben estar definidas como variables.

| Variable | Valor sugerido | Notas |
| :--- | :--- | :--- |
| `SELENIUM_HEADLESS` | `True` | Ya viene `True` en la imagen (no hay pantalla en la nube) |
| `SELENIUM_WINDOW_WIDTH` | `1920` | El DOM de los bancos es responsive |
| `SELENIUM_WINDOW_HEIGHT` | `1080` | |
| `DNI` | `V12345678` | |
| `BNC_URL` | `https://personas.bncenlinea.com/` | |
| `BNC_CARD_NUMBER` | `0000000000000000` | |
| `BNC_PASS` | `********` | |
| `BANCAMIGA_URL` | `https://online.bancamiga.com/?p=1` | |
| `BANCAMIGA_USER` | `usuario` | |
| `BANCAMIGA_PASS` | `********` | |

`PORT` lo inyecta Railway automáticamente; la imagen ya lo usa en el arranque
(`uvicorn ... --port ${PORT:-8000}`).

### 3. Recomendaciones de recursos

* **Memoria**: reserva al menos **1 GB**. Cada consulta abre una instancia de Chromium
  (~300–500 MB) y las consultas de los distintos bancos corren en paralelo.
* **Réplicas**: mantener **1 réplica** mientras se use la validación 2FA por WebSocket:
  el estado del OTP vive en memoria del proceso (`src/config/app/ws_state.py`), así que
  varias instancias no podrían intercambiar el código.
* **Cloudflare Turnstile / anti-bot**: en headless es más probable recibir retos. Si
  esto ocurre, se puede alternar `SELENIUM_HEADLESS=False` (la imagen soporta ambos
  modos) o aumentar la memoria de la instancia.
* **`.env`**: nunca se copia a la imagen (ver `.dockerignore` y `Dockerfile`); los
  secretos deben vivir únicamente en las variables de Railway.

### 4. Conectar el Portal Angular

El frontend tiene la URL del backend fija en dos lugares; cámbialos por el dominio
que Railway asigne a tu servicio:

| Archivo | Constante |
| :--- | :--- |
| `portal/src/app/services/bank.service.ts` | `API_BASE = 'https://<tu-servicio>.up.railway.app/api/query'` |
| `portal/src/app/app.ts` | `const wsUrl = 'wss://<tu-servicio>.up.railway.app/api/ws/query'` |

---

## ⚠️ Descargo de Responsabilidad (Disclaimer)

> [!WARNING]
> **ÚNICAMENTE PARA DESARROLLADORES Y USO EDUCATIVO**
>
> Este proyecto ha sido desarrollado exclusivamente con fines educativos y de demostración técnica de capacidades de automatización web. 
>
> *   **Responsabilidad**: El autor no se hace responsable por bloqueos de cuentas, accesos restringidos, suspensión de servicios de banca en línea o violaciones a los términos y condiciones de uso de las respectivas plataformas bancarias.
> *   **Seguridad**: Asegúrese de **NUNCA** comprometer o subir su archivo `.env` que contenga contraseñas reales a repositorios públicos de Git. Use siempre credenciales en entornos seguros y controlados.
> *   **Uso Ético**: Utilice esta herramienta con consciencia, precaución y responsabilidad. No realice llamadas reiteradas o masivas que puedan ser interpretadas como ataques de denegación de servicio (DoS) por los servidores de las instituciones financieras.