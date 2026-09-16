# ============================================================================
#  Query Bank VNZL - Backend (PyNest / FastAPI + Selenium)
#
#  Diseño en 2 etapas:
#
#    [browser]  IMAGEN BASE: solo el entorno del navegador
#               (Python 3.12 + Chromium + ChromeDriver + fuentes). NO contiene
#               nada de la aplicación, por lo que se puede construir y publicar
#               aparte para reutilizarla en otros proyectos:
#
#                   docker build --target browser -t tuusuario/querybank-browser:1 .
#                   # y en otro Dockerfile:  FROM tuusuario/querybank-browser:1
#
#    [app]      (etapa final) capa delgada sobre la base: dependencias de Python
#               + código + arranque. Es la imagen que se despliega.
#
#  En Railway: Root Directory = "/" (raíz) y Dockerfile Path = "Dockerfile"
#  (Railway construye la etapa final; si solo cambia el código, las capas del
#   navegador quedan en caché y el rebuild es de segundos).
# ============================================================================


# ----------------------------------------------------------------------------
# ETAPA 1 (imagen base): entorno del navegador, sin la aplicación
# ----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS browser

# Variables de entorno del entorno de ejecución
#   - PORT: Railway la inyecta automáticamente (uvicorn la usa como puerto).
#   - Selenium: en la nube no hay pantalla -> headless.
#   - CHROMIUM_BINARY_PATH / CHROME_DRIVER_PATH: al apuntar a los binarios del
#     sistema, Selenium NO descarga drivers y se evita el error
#     "Status code was: 127" de ~/.cache/selenium.
#   - SELENIUM_REMOTE_URL (opcional): si se define, se usa un navegador remoto
#     (contenedor selenium/standalone-chromium) en lugar del Chromium local.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Caracas \
    HOME=/app \
    PORT=8000 \
    SELENIUM_HEADLESS=True \
    SELENIUM_WINDOW_WIDTH=1920 \
    SELENIUM_WINDOW_HEIGHT=1080 \
    CHROMIUM_BINARY_PATH=/usr/bin/chromium \
    CHROME_DRIVER_PATH=/usr/bin/chromedriver

# /app debe existir antes de ejecutar el navegador (HOME=/app)
WORKDIR /app

# Chromium + ChromeDriver + librerías y fuentes que Selenium necesita.
#   chromium-driver se compila desde el mismo código fuente que chromium, por lo
#   que ambos comparten versión (Selenium exige versiones compatibles).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        ca-certificates \
        fonts-liberation \
        fonts-dejavu-core \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# Verificación de la base: si el navegador o el driver no pueden ejecutarse
# (p. ej. faltan librerías del sistema), el build falla aquí y no en producción.
RUN chromium --version \
    && chromedriver --version


# ----------------------------------------------------------------------------
# ETAPA 2 (imagen final): la aplicación, usando la base anterior
#   Solo agrega dependencias de Python y el código del backend.
# ----------------------------------------------------------------------------
FROM browser AS app

# Dependencias de Python (capa cacheable: solo se reinstala si cambia el txt)
COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Código de la aplicación
#   Se copia explícitamente para NO incluir el .env (credenciales bancarias),
#   el entorno virtual ni archivos de desarrollo.
COPY backend/src ./src
COPY backend/main.py ./main.py
COPY backend/README.md ./README.md

EXPOSE 8000

# ----------------------------------------------------------------------------
# Arranque
#   - ${PORT:-8000}: Railway define PORT; uvicorn escucha en 0.0.0.0.
#   - --proxy-headers / --forwarded-allow-ips: Railway termina TLS en su proxy.
#   - 1 solo worker: el flujo 2FA por WebSocket comparte estado EN MEMORIA
#     (src/config/app/ws_state.py), por lo que NO se deben usar múltiples
#     workers ni réplicas mientras se use la validación por WebSocket.
#   - "exec" para que uvicorn quede como PID 1 y reciba el SIGTERM al redesplegar.
# ----------------------------------------------------------------------------
CMD ["sh", "-c", "exec python -m uvicorn src.app_module:http_server --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
