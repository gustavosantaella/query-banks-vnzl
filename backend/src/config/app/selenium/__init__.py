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
    headless = os.getenv("SELENIUM_HEADLESS", "False").lower() in ("true", "1", "yes", "True")
    if bool(headless):
        options.add_argument("--headless=new")  # Sintaxis moderna para headless en Selenium 4
        
    # Configuraciones de rendimiento y compatibilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Dynamic window size and position from .env (defaults to tiny, off-screen window for stealth headed mode)
    width = os.getenv("SELENIUM_WINDOW_WIDTH", "10")
    height = os.getenv("SELENIUM_WINDOW_HEIGHT", "10")
    options.add_argument(f"--window-size={width},{height}")
    
    position = os.getenv("SELENIUM_WINDOW_POSITION", "3000,3000")
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
    return 149  # Fallback to the user's current version

def get_chrome_driver() -> webdriver.Chrome:
    """
    Inicializa y retorna la instancia del webdriver de Chrome/Chromium
    con las configuraciones aplicadas.
    """
    options = get_chromium_options()

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
        headless = os.getenv("SELENIUM_HEADLESS", "False").lower() in ("true", "1", "yes", "True")
        
        # Force user-agent to mock a standard Chrome instance
        uc_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        
        major_version = get_chrome_major_version()
        print(f"Detected Chrome major version: {major_version}")
        
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
            return e
