# ============================================================================
#  Query Bank VNZL - Backend (PyNest / FastAPI + Selenium)
#  Imagen lista para desplegar en Railway (o cualquier runtime con Docker).
#
#  IMPORTANTE (contexto de build):
#    - Este archivo vive en la RAÍZ del repositorio.
#    - El código del backend vive en ./backend
#    - En Railway: Root Directory = "/" (raíz) y Dockerfile Path = "Dockerfile"
# ============================================================================
FROM python:3.12-slim-bookworm

# ---------------------------------------------------------------------------
# Variables de entorno
#   - PORT: Railway la inyecta automáticamente (uvicorn la usa como puerto).
#   - Selenium: en la nube no hay pantalla -> headless obligatorio.
#     Se puede sobreescribir desde Railway (Variables) sin recompilar la imagen.
# ---------------------------------------------------------------------------
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

WORKDIR /app

# ---------------------------------------------------------------------------
# Chromium + ChromeDriver (requeridos por Selenium para el scraping)
#   chromium-driver se compila desde el mismo código fuente que chromium,
#   por lo que ambos comparten versión (Selenium exige versiones compatibles).
#   Las fuentes evitan que el navegador renderice texto mal en el scraping.
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        ca-certificates \
        fonts-liberation \
        fonts-dejavu-core \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Dependencias de Python (capa cacheable: solo se reinstala si cambia el txt)
# ---------------------------------------------------------------------------
COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Código de la aplicación
#   Se copia explícitamente para NO incluir el .env (credenciales bancarias),
#   el entorno virtual, las plantillas HTML de referencia ni archivos de desarrollo.
# ---------------------------------------------------------------------------
COPY backend/src ./src
COPY backend/main.py ./main.py
COPY backend/README.md ./README.md

EXPOSE 8000

# ---------------------------------------------------------------------------
# Arranque
#   - ${PORT:-8000}: Railway define PORT; uvicorn escucha en 0.0.0.0.
#   - --proxy-headers / --forwarded-allow-ips: Railway termina TLS en su proxy.
#   - 1 solo worker: el flujo 2FA por WebSocket comparte estado EN MEMORIA
#     (src/config/app/ws_state.py), por lo que NO se deben usar múltiples
#     workers ni réplicas mientras se use la validación por WebSocket.
#   - "exec" para que uvicorn quede como PID 1 y reciba el SIGTERM al redesplegar.
# ---------------------------------------------------------------------------
CMD ["sh", "-c", "exec python -m uvicorn src.app_module:http_server --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
