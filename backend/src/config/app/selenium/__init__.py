import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Valores aceptados como "verdadero" en las variables de entorno
TRUTHY_VALUES = ("true", "1", "yes", "y", "on", "si", "sí", "t")

DEFAULT_WINDOW_WIDTH = 1920
DEFAULT_WINDOW_HEIGHT = 1080

# Ayuda para el error más común en Linux/contenedores:
# Selenium ("Selenium Manager") descarga su propio chromedriver en ~/.cache/selenium,
# pero ese binario necesita las librerías del sistema. Si el proceso termina con
# "Status code was: 127" significa que el binario no pudo ejecutarse (librerías
# ausentes o distribución incompatible, p. ej. Alpine/musl).
TROUBLESHOOTING_HINT = (
    "El navegador no pudo iniciarse. En Linux/contenedores instale el navegador y su "
    "driver desde la distribución ('apt-get install -y chromium chromium-driver') y "
    "defina CHROMIUM_BINARY_PATH=/usr/bin/chromium y CHROME_DRIVER_PATH=/usr/bin/chromedriver. "
    "El código de salida 127 significa que el binario de ChromeDriver no puede ejecutarse "
    "(faltan librerías del sistema o la distribución no es compatible, p. ej. Alpine/musl)."
)


def env_flag(name: str, default: bool = False) -> bool:
    """Lee un flag booleano desde el entorno/.env (ej: SELENIUM_HEADLESS=True)."""
    value = os.getenv(name)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in TRUTHY_VALUES


def env_int(name: str, default: int) -> int:
    """Lee un entero desde el entorno/.env; si no existe o no es válido, devuelve el default."""
    value = str(os.getenv(name, "") or "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        print(f"Valor inválido para {name} ('{value}'); se usará {default}.")
        return default


def is_headless() -> bool:
    """Indica si el navegador debe ejecutarse sin interfaz visible (SELENIUM_HEADLESS)."""
    return env_flag("SELENIUM_HEADLESS", default=False)


def get_remote_url() -> str:
    """
    URL de un navegador remoto (Selenium Grid / contenedor 'selenium/standalone-chromium').
    Si está definida, la app NO necesita Chromium ni ChromeDriver instalados localmente.
    Ej: SELENIUM_REMOTE_URL=http://localhost:4444
    """
    return (os.getenv("SELENIUM_REMOTE_URL") or "").strip()


def get_window_size() -> tuple:
    """Tamaño de la ventana configurable (SELENIUM_WINDOW_WIDTH x SELENIUM_WINDOW_HEIGHT)."""
    return (
        env_int("SELENIUM_WINDOW_WIDTH", DEFAULT_WINDOW_WIDTH),
        env_int("SELENIUM_WINDOW_HEIGHT", DEFAULT_WINDOW_HEIGHT),
    )


def validate_binaries() -> list:
    """
    Revisa los binarios configurados (CHROMIUM_BINARY_PATH / CHROME_DRIVER_PATH)
    y avisa por consola si no existen o no son ejecutables. Devuelve la lista de avisos.
    """
    warnings = []
    for env_name, description in (
        ("CHROMIUM_BINARY_PATH", "el binario de Chrome/Chromium"),
        ("CHROME_DRIVER_PATH", "el binario de ChromeDriver"),
    ):
        path = os.getenv(env_name)
        if not path:
            continue
        if not os.path.exists(path):
            warnings.append(f"{env_name} apunta a una ruta inexistente: {path}")
        elif not os.access(path, os.X_OK):
            warnings.append(f"{description} en {path} no tiene permisos de ejecución (chmod +x)")

    for warning in warnings:
        print(f"ADVERTENCIA (Selenium): {warning}")
    return warnings


def get_chromium_options(remote: bool = False) -> Options:
    """
    Configura y retorna las opciones para Chromium / Google Chrome en Selenium.

    Parámetro:
      - remote=True: las opciones se enviarán a un navegador remoto (Selenium Grid /
        contenedor), por lo que NO se fija binary_location (el binario vive allá).

    Variables de entorno soportadas:
      - SELENIUM_REMOTE_URL: URL de un navegador remoto (ej: http://localhost:4444).
                             Si está definida, se ignora el Chrome/ChromeDriver local.
      - SELENIUM_HEADLESS: "True" ejecuta el navegador en segundo plano (sin verse).
                           Por defecto "False" (ventana visible).
      - SELENIUM_WINDOW_WIDTH / SELENIUM_WINDOW_HEIGHT: tamaño de la ventana
                           (por defecto 1920x1080). Importante en headless, porque el DOM
                           del banco es responsive y con ventanas pequeñas se ocultan campos.
      - SELENIUM_WINDOW_POSITION: posición "x,y" de la ventana (solo en modo visible).
      - CHROMIUM_BINARY_PATH: ruta personalizada al binario de Chrome/Chromium.
    """
    options = Options()

    headless = is_headless()
    if headless:
        options.add_argument("--headless=new")  # Sintaxis moderna para headless en Selenium 4
        print("Selenium: modo headless activado (SELENIUM_HEADLESS).")

    # Configuraciones de rendimiento y compatibilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Tamaño de ventana configurable (en headless define el viewport real de la página)
    width, height = get_window_size()
    options.add_argument(f"--window-size={width},{height}")

    # Posición de la ventana (solo tiene sentido en modo visible)
    if not headless:
        position = os.getenv("SELENIUM_WINDOW_POSITION")
        if position:
            options.add_argument(f"--window-position={position}")

    options.add_argument("--disable-extensions")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    # Desactivar logs innecesarios de la terminal
    options.add_argument("--log-level=3")
    options.add_argument("--silent")

    # Evitar la detección de automatización básica (evita bloqueos de algunos sitios)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Ruta personalizada para el binario de Chromium si está definida en el archivo .env
    # (se omite en modo remoto: el binario vive en el contenedor del navegador)
    if not remote:
        chromium_binary = os.getenv("CHROMIUM_BINARY_PATH")
        if chromium_binary:
            options.binary_location = chromium_binary

    return options


def get_chrome_major_version() -> int:
    try:
        import winreg
        reg_path = r"Software\Google\Chrome\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        value, _ = winreg.QueryValueEx(key, "version")
        return int(value.split(".")[0])
    except Exception:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
            value, _ = winreg.QueryValueEx(key, "DisplayVersion")
            return int(value.split(".")[0])
        except Exception:
            pass

    # Linux (contenedor Docker) / macOS: se deduce del propio binario del navegador
    try:
        import re
        import subprocess

        candidates = [
            os.getenv("CHROMIUM_BINARY_PATH"),
            "chromium",
            "chromium-browser",
            "google-chrome",
            "google-chrome-stable",
            "chrome",
        ]
        for candidate in candidates:
            if not candidate:
                continue
            try:
                completed = subprocess.run(
                    [candidate, "--version"], capture_output=True, text=True, timeout=5
                )
            except Exception:
                continue
            match = re.search(r"(\d+)\.", completed.stdout or "")
            if match:
                return int(match.group(1))
    except Exception:
        pass

    return 149  # Fallback to the user's current version


def _get_remote_driver(remote_url: str) -> webdriver.Remote:
    """
    Se conecta a un navegador que corre en otro contenedor/servidor.

    Uso típico: 'docker compose up -d' levanta 'selenium/standalone-chromium'
    (solo el navegador) y la app se conecta con:
        SELENIUM_REMOTE_URL=http://localhost:4444
    Con esto el contenedor de la app NO necesita Chromium ni ChromeDriver.
    """
    print(f"Selenium: usando navegador remoto en {remote_url} (no se usa Chrome local).")
    options = get_chromium_options(remote=True)

    try:
        driver = webdriver.Remote(command_executor=remote_url, options=options)
    except Exception as exc:
        message = (
            f"No se pudo conectar al navegador remoto en {remote_url}: {exc} "
            "(verifique que el contenedor del navegador esté en ejecución y que la URL sea accesible)."
        )
        print(message)
        return Exception(message)

    try:
        # Remueve el flag navigator.webdriver (evita detección básica)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "const newProto = navigator.__proto__; delete newProto.webdriver; navigator.__proto__ = newProto;"
            }
        )
    except Exception as exc:
        print(f"Aviso: no se pudo aplicar el ajuste stealth en el navegador remoto: {exc}")

    return driver


def get_chrome_driver() -> webdriver.Chrome:
    """
    Inicializa y retorna la instancia del webdriver de Chrome/Chromium.

    Modos de funcionamiento:
      1. SELENIUM_REMOTE_URL definido  -> se conecta a un navegador remoto
         (Selenium Grid / contenedor 'selenium/standalone-chromium'). No requiere
         Chromium ni ChromeDriver instalados en esta máquina.
      2. undetected_chromedriver disponible -> navegador local stealth.
      3. Fallback -> webdriver.Chrome local (CHROMIUM_BINARY_PATH / CHROME_DRIVER_PATH).

    El navegador se ejecuta oculto o visible según SELENIUM_HEADLESS.
    """
    remote_url = get_remote_url()
    if remote_url:
        return _get_remote_driver(remote_url)

    options = get_chromium_options()
    headless = is_headless()
    validate_binaries()

    try:
        import undetected_chromedriver as uc
        print("Using undetected_chromedriver for stealth browsing...")

        uc_options = uc.ChromeOptions()
        # Copy standard arguments
        for arg in options.arguments:
            uc_options.add_argument(arg)
        if options.binary_location:
            uc_options.binary_location = options.binary_location

        driver_path = os.getenv("CHROME_DRIVER_PATH")

        # Force user-agent to mock a standard Chrome instance
        uc_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

        major_version = get_chrome_major_version()
        print(f"Detected Chrome major version: {major_version}")
        print(f"Browser headless: {headless}")

        if driver_path:
            driver = uc.Chrome(
                driver_executable_path=driver_path,
                options=uc_options,
                headless=headless,
                version_main=major_version
            )
        else:
            driver = uc.Chrome(
                options=uc_options,
                headless=headless,
                version_main=major_version
            )

        return driver
    except Exception as uc_err:
        print(f"undetected_chromedriver failed to initialize: {uc_err}. Falling back to standard webdriver...")

        try:
            driver_path = os.getenv("CHROME_DRIVER_PATH")
            if driver_path:
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)

            # Remueve el flag navigator.webdriver (evita detección básica)
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "const newProto = navigator.__proto__; delete newProto.webdriver; navigator.__proto__ = newProto;"
                }
            )
            return driver
        except Exception as e:
            print(f"Standard ChromeDriver initialization failed: {e}")
            print(TROUBLESHOOTING_HINT)
            return Exception(f"{e} | {TROUBLESHOOTING_HINT}")
