import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_chromium_options() -> Options:
    """
    Configura y retorna las opciones para Chromium / Google Chrome en Selenium.
    """
    options = Options()
    
    # Modo headless configurable por variable de entorno o por defecto en True
    headless = os.getenv("SELENIUM_HEADLESS", "False").lower() in ("true", "1", "yes")
    if bool(headless):
        options.add_argument("--headless=new")  # Sintaxis moderna para headless en Selenium 4
        
    # Configuraciones de rendimiento y compatibilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
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
    chromium_binary = os.getenv("CHROMIUM_BINARY_PATH")
    if chromium_binary:
        options.binary_location = chromium_binary
        
    return options

def get_chrome_driver() -> webdriver.Chrome:
    """
    Inicializa y retorna la instancia del webdriver de Chrome/Chromium
    con las configuraciones aplicadas.
    """
    options = get_chromium_options()


    
    # Ruta personalizada para el driver si está definida en el archivo .env
    # Nota: Desde Selenium 4.6+, Selenium Manager descarga e instala el driver
    # compatible de forma automática si no se proporciona un driver local.
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
        print("Error :c")
        return e
