
from datetime import datetime
from html import unescape
from os import getenv
from re import findall, sub
from time import sleep
from urllib.parse import urljoin

from nest.core import Injectable
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.app.selenium import get_chrome_driver

# Rutas internas de BNCNET (personas.bncenlinea.com)
BNC_PATHS = {
    "welcome": "/Home/BNCNETHB/Welcome",
    "position": "/Home/ProductsSummary/List",
    "movements_online": "/Accounts/Transactions/Online",
    "movements_last25": "/Accounts/Transactions/Last25",
    "movements_previous_day": "/Accounts/Transactions/Previous_Day",
}

DEFAULT_BNC_URL = "https://personas.bncenlinea.com/"

# Ruta real de cierre de sesión (ver Scripts/Global.js: window.location = "/Auth/LogOut")
AUTH_LOGOUT_PATH = "/Auth/LogOut"

# Movimientos: tras presionar "Aceptar" el banco hace un POST y repinta #ContainerList
DEFAULT_MOVEMENTS_PAGE_SIZE = 100
MOVEMENTS_WAIT_TIMEOUT = 30
MAX_MOVEMENTS_PAGES = 20


def _clean_text(value) -> str:
    """Colapsa espacios/saltos de línea y recorta el texto."""
    return sub(r"\s+", " ", value or "").strip()


def _tooltip_values(raw: str) -> dict:
    """Extrae los pares 'label: valor' del data-original-title de los balances."""
    values = {}
    for label, value in findall(r">([^<>:]+):</div>\s*<div[^>]*><b>([^<]*)</b>", unescape(raw or "")):
        values[_clean_text(label)] = _clean_text(value)
    return values


@Injectable()
class BncService:
    """Scraping de la banca en línea del Banco Nacional de Crédito (código 0191)."""

    def __init__(self, config: dict = None):
        # Valores opcionales que sobreescriben el .env (por ejemplo, enviados por la API)
        self._config = config or {}
        # URL base usada en el último login (necesaria para el logout de emergencia)
        self._base_url = None

    # ------------------------------------------------------------------ #
    # Helpers de entorno / consola
    # ------------------------------------------------------------------ #
    def _env(self, key: str, label: str, default: str = None, secret: bool = False) -> str:
        """Obtiene una credencial desde config, el .env o, si no existe, la pide por consola."""
        override = _clean_text(self._config.get(key))
        if override:
            print(f"[BNC] '{key}' recibido por parámetro.")
            return override

        value = (getenv(key) or "").strip()
        if value:
            print(f"[BNC] '{key}' obtenido desde el entorno.")
            return value

        print(f"[BNC] La variable de entorno '{key}' no está definida; se solicitará por consola.")
        suffix = f" [Enter para usar: {default}]" if default else ""
        while True:
            value = input(f"[BNC] Ingrese {label}{suffix}: ").strip()
            if not value and default:
                value = default
            if value:
                print(f"[BNC] {label} capturado." if secret else f"[BNC] {label}: {value}")
                return value
            print("[BNC] El valor es obligatorio, intente nuevamente.")

    # ------------------------------------------------------------------ #
    # Helpers de Selenium
    # ------------------------------------------------------------------ #
    def _wait(self, driver: WebDriver, by, selector: str, timeout: int = 30):
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except Exception:
            return None

    def _wait_required(self, driver: WebDriver, by, selector: str, description: str, timeout: int = 30):
        element = self._wait(driver, by, selector, timeout)
        if element is None:
            raise Exception(f"No se pudo localizar {description} (selector: {selector}).")
        return element

    def _click(self, driver: WebDriver, by, selector: str, timeout: int = 30):
        element = self._wait_required(
            driver, by, selector, f"el elemento clickeable {selector}", timeout=timeout
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except Exception:
            pass
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception:
            element.click()
        return element

    def _go(self, driver: WebDriver, base_url: str, path: str, wait_for: tuple):
        target = urljoin(base_url, path)
        print(f"[BNC] Navegando a {target}")
        driver.get(target)
        self._wait_required(driver, wait_for[0], wait_for[1], f"el contenido de {path}")
        sleep(1)
        return driver

    def _text(self, element) -> str:
        if element is None:
            return ""
        value = (element.text or "").strip()
        if not value:
            value = element.get_attribute("textContent") or ""
        return _clean_text(value)

    def _child_text(self, parent, by, selector: str) -> str:
        try:
            return self._text(parent.find_element(by, selector))
        except Exception:
            return ""

    def _driver_text(self, driver: WebDriver, by, selector: str) -> str:
        try:
            return self._text(driver.find_element(by, selector))
        except Exception:
            return ""

    def _parent(self, element):
        try:
            return element.find_element(By.XPATH, "..")
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # Login: tarjeta + cédula -> clave
    # ------------------------------------------------------------------ #
    def _login(self, driver: WebDriver) -> str:
        """Inicia sesión en BNCNET y retorna la URL base utilizada."""
        base_url = self._env(
            "BNC_URL",
            "URL de BNCNET (ej: https://personas.bncenlinea.com/)",
            default=DEFAULT_BNC_URL,
        )
        card_number = self._env("BNC_CARD_NUMBER", "Número de Tarjeta")
        dni = self._env("DNI", "Cédula de Identidad")
        password = self._env("BNC_PASS", "Clave de BNCNET", secret=True)

        # Se guarda de inmediato: si el login falla, el logout de emergencia la necesita
        self._base_url = base_url

        print(f"[BNC] Abriendo {base_url}")
        driver.get(base_url)
        driver.implicitly_wait(5)

        # Paso 1: Número de tarjeta + Cédula de identidad (#CardNumber / #UserID)
        card_input = self._wait_required(driver, By.ID, "CardNumber", "el campo 'Número de Tarjeta'")
        card_input.clear()
        card_input.send_keys(card_number)

        dni_input = self._wait_required(driver, By.ID, "UserID", "el campo 'Cédula de Identidad'")
        dni_input.clear()
        dni_input.send_keys(dni)

        print("[BNC] Enviando tarjeta + cédula...")
        self._click(driver, By.ID, "BtnSend")

        # Paso 2: la pantalla cambia y queda disponible el campo de clave (#UserPassword)
        print("[BNC] Esperando la pantalla de clave...")
        password_input = self._wait_required(driver, By.ID, "UserPassword", "la pantalla de clave de BNCNET")
        password_input.clear()
        password_input.send_keys(password)

        print("[BNC] Enviando clave...")
        self._click(driver, By.ID, "BtnSend")

        print("[BNC] Esperando el ingreso al home bancario...")
        self._wait_required(
            driver,
            By.ID,
            "btn-logout",
            "el home de BNCNET (verifique tarjeta, cédula y clave)",
            timeout=45,
        )
        sleep(1)
        print("[BNC] Sesión iniciada correctamente.")
        return base_url

    # ------------------------------------------------------------------ #
    # Dashboard (home)
    # ------------------------------------------------------------------ #
    def _extract_dashboard(self, driver: WebDriver, base_url: str) -> dict:
        self._go(driver, base_url, BNC_PATHS["welcome"], (By.ID, "FormContainer"))

        data = {
            "title": self._driver_text(driver, By.CSS_SELECTOR, "#SubNavbar h1"),
            "user": self._driver_text(driver, By.CSS_SELECTOR, ".info-session .list-inline-item strong"),
            "greeting": self._driver_text(driver, By.CSS_SELECTOR, "#rac .h2-custom"),
            "last_login": self._driver_text(driver, By.CSS_SELECTOR, ".info-session .text-lg-right strong"),
            "balances": [],
            "notifications": [],
        }

        # Bloques de balance (ej: "Depósitos a la Vista (Bs.)")
        for block in driver.find_elements(By.CSS_SELECTOR, "#FormContainer div.tbs"):
            # El data-original-title (Total Bloqueado / Total Diferido) vive en el contenedor padre
            tooltip_raw = ""
            for candidate in (block, self._parent(block)):
                if candidate is None:
                    continue
                tooltip_raw = candidate.get_attribute("data-original-title") or candidate.get_attribute("title") or ""
                if tooltip_raw:
                    break
            tooltip = _tooltip_values(tooltip_raw)
            data["balances"].append({
                "product": self._child_text(block, By.CSS_SELECTOR, ".font-size-product"),
                "amount": self._child_text(block, By.CSS_SELECTOR, ".font-size-money"),
                "label": self._child_text(block, By.CSS_SELECTOR, ".small.font-weight-bold"),
                "blocked": tooltip.get("Total Bloqueado", ""),
                "deferred": tooltip.get("Total Diferido", ""),
            })

        # Notificaciones del carrusel del home
        for item in driver.find_elements(By.CSS_SELECTOR, "#slick-carousel .Notification"):
            data["notifications"].append({
                "title": self._child_text(item, By.CSS_SELECTOR, ".bg-bnc-n"),
                "message": self._child_text(item, By.CSS_SELECTOR, "h6"),
                "data_args": item.get_attribute("data-args") or "",
            })

        return data

    # ------------------------------------------------------------------ #
    # Posición consolidada
    # ------------------------------------------------------------------ #
    def _extract_position(self, driver: WebDriver, base_url: str) -> list:
        self._go(driver, base_url, BNC_PATHS["position"], (By.ID, "ProductsSummary"))

        groups = []
        for accordion in driver.find_elements(By.CSS_SELECTOR, "#ProductsSummary"):
            group = {
                "group": self._child_text(accordion, By.CSS_SELECTOR, ".card.bg-bnc-n .text-header"),
                "products": [],
            }
            for card in accordion.find_elements(By.CSS_SELECTOR, ".card:not(.bg-bnc-n)"):
                holder = self._child_text(card, By.CSS_SELECTOR, ".card-header .custom-small")
                if not holder:
                    holder = self._child_text(card, By.CSS_SELECTOR, ".card-body h4")
                group["products"].append({
                    "product": self._child_text(card, By.CSS_SELECTOR, ".card-header .font-size-1"),
                    "holder": holder,
                    "amount": self._child_text(card, By.CSS_SELECTOR, ".card-header .text-Amount"),
                    "amount_label": self._child_text(card, By.CSS_SELECTOR, ".card-header .col-5 .font-size-1"),
                    "details": self._extract_detail_pairs(card),
                })
            groups.append(group)

        return groups

    def _extract_detail_pairs(self, card) -> list:
        """Los detalles de cada producto vienen en pares de <h5> label/valor."""
        details = []
        pending = None
        for element in card.find_elements(By.CSS_SELECTOR, ".card-body h5"):
            text = self._text(element)
            if not text:
                continue
            if text.endswith(":"):
                pending = text[:-1].strip()
            elif pending:
                details.append({"label": pending, "value": text})
                pending = None
        return details

    # ------------------------------------------------------------------ #
    # Movimientos
    # ------------------------------------------------------------------ #
    def _extract_movements(self, driver: WebDriver, base_url: str, path: str, page_size: int = DEFAULT_MOVEMENTS_PAGE_SIZE) -> dict:
        """
        Carga los movimientos de una cuenta.

        El banco no lista nada al abrir la página: hay un formulario (#Frm_Accounts) con el
        selector de cuenta y el botón 'Aceptar'; recién al enviarlo, el JS del banco hace
        POST a /Accounts/Transactions/{...}_List y reemplaza #ContainerList con la tabla.
        """
        self._go(driver, base_url, path, (By.ID, "ContainerList"))
        self._set_page_filters(driver, page_size)

        before_html = self._container_html(driver)
        if not self._apply_account_filter(driver):
            print("[BNC] No se pudo enviar el filtro de cuenta; se devuelve el estado actual de la página.")
            return {"path": path, **self._parse_transactions_table(driver)}

        self._wait_container_update(driver, before_html)
        result = self._parse_transactions_table(driver)

        items = list(result.get("items", []))
        seen = {self._movement_key(item) for item in items}
        pages = 1

        while pages < MAX_MOVEMENTS_PAGES:
            next_page = self._next_page_value(driver, pages)
            if not next_page:
                break
            before_html = self._container_html(driver)
            if not self._click_page_link(driver, next_page):
                break
            if not self._wait_container_update(driver, before_html):
                break
            page_result = self._parse_transactions_table(driver)
            new_items = [item for item in page_result.get("items", []) if self._movement_key(item) not in seen]
            if not new_items:
                break
            items.extend(new_items)
            seen.update(self._movement_key(item) for item in new_items)
            result["total"] = page_result.get("total") or result.get("total")
            result["message"] = page_result.get("message")
            pages += 1

        result["items"] = items
        result["pages"] = pages
        return {"path": path, **result}

    def _apply_account_filter(self, driver: WebDriver) -> bool:
        """Selecciona la primera cuenta disponible y presiona 'Aceptar' (#Frm_Accounts)."""
        try:
            account = self._select_first_account(driver)
        except Exception as exc:
            print(f"[BNC] No se pudo preparar el filtro de cuenta: {exc}")
            return False

        if not account:
            print("[BNC] No hay cuentas disponibles para consultar movimientos.")
            return False

        print("[BNC] Presionando 'Aceptar' para que el banco liste los movimientos...")
        try:
            self._click(driver, By.CSS_SELECTOR, "#Frm_Accounts button[type='submit']", timeout=15)
            return True
        except Exception as exc:
            print(f"[BNC] No se pudo presionar 'Aceptar': {exc}")
            return False

    def _select_first_account(self, driver: WebDriver):
        """Deja seleccionada la primera cuenta real del <select id='Account'> (value != '0')."""
        select_el = driver.find_element(By.ID, "Account")
        current = select_el.get_attribute("value") or "0"
        if current != "0":
            print(f"[BNC] Cuenta ya preseleccionada por el banco: ...{current[-12:]}")
            return current

        account = None
        for option in select_el.find_elements(By.TAG_NAME, "option"):
            value = option.get_attribute("value") or "0"
            if value != "0":
                account = value
                break

        if account:
            print(f"[BNC] Seleccionando cuenta: ...{account[-12:]}")
            driver.execute_script(
                "var s=arguments[0],v=arguments[1];s.value=v;"
                "if(window.jQuery){jQuery(s).val(v).trigger('change');}"
                "else{s.dispatchEvent(new Event('change'));}",
                select_el, account,
            )
        return account

    def _set_page_filters(self, driver: WebDriver, page_size: int):
        """Fija PageSize/Page antes de enviar el filtro (así una sola consulta trae más filas)."""
        try:
            driver.execute_script(
                "var i, ids = ['PageSize', 'prv_PageSize'];"
                "for (i = 0; i < ids.length; i++) {"
                "  var e = document.getElementById(ids[i]); if (e) { e.value = arguments[0]; } }"
                "var names = document.querySelectorAll(\"input[name$='PageSize']\");"
                "for (i = 0; i < names.length; i++) { names[i].value = arguments[0]; }"
                "var pages = document.querySelectorAll(\"input[name$='Page']:not([name*='Old'])\");"
                "for (i = 0; i < pages.length; i++) { pages[i].value = '1'; }"
                "var olds = document.querySelectorAll(\"input[name$='prv_OldPage']\");"
                "for (i = 0; i < olds.length; i++) { olds[i].value = '1'; }",
                str(page_size),
            )
        except Exception as exc:
            print(f"[BNC] No se pudo ajustar el tamaño de página: {exc}")

    def _container_html(self, driver: WebDriver) -> str:
        try:
            return driver.execute_script(
                "var c=document.getElementById('ContainerList');return c?c.innerHTML:'';"
            ) or ""
        except Exception:
            return ""

    def _wait_container_update(self, driver: WebDriver, previous_html: str, timeout: int = MOVEMENTS_WAIT_TIMEOUT) -> bool:
        """Espera a que termine el POST disparado por 'Aceptar' (o por el paginador).

        Se compara el HTML de #ContainerList con el snapshot previo: así funciona tanto en la
        primera carga (contenedor vacío) como al cambiar de página (la tabla anterior ya existía).
        """
        def finished(target_driver):
            try:
                progress = target_driver.find_elements(By.ID, "Mdl-Progress")
                if progress and "show" in (progress[0].get_attribute("class") or ""):
                    return False
                return self._container_html(target_driver) != previous_html
            except Exception:
                return False

        try:
            WebDriverWait(driver, timeout).until(finished)
            return True
        except Exception:
            print("[BNC] Timeout esperando la lista de movimientos.")
            return False

    def _next_page_value(self, driver: WebDriver, current_page: int):
        """Devuelve el valor de la página siguiente en #Tbl-Pagination (None si no hay)."""
        target = str(current_page + 1)
        try:
            for link in driver.find_elements(By.CSS_SELECTOR, "#Tbl-Pagination a.page-link"):
                classes = link.get_attribute("class") or ""
                if "disabled" in classes or "custom-page-link" in classes:
                    continue
                if (link.get_attribute("data-action") or "") == target:
                    return target
        except Exception:
            pass
        return None

    def _click_page_link(self, driver: WebDriver, page_value: str) -> bool:
        try:
            link = driver.find_element(
                By.CSS_SELECTOR, f"#Tbl-Pagination a.page-link[data-action='{page_value}']"
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", link)
            return True
        except Exception as exc:
            print(f"[BNC] No se pudo ir a la página {page_value}: {exc}")
            return False

    def _movement_key(self, item: dict) -> tuple:
        return (
            item.get("date"), item.get("time"), item.get("description"),
            item.get("reference"), item.get("amount"), item.get("balance"),
        )

    def _parse_transactions_table(self, driver: WebDriver) -> dict:
        """Parsea #Tbl_Transactions (Fecha/Hora, Descripción, Ref., Monto, Saldo)."""
        result = {
            "total": self._input_value(driver, "TotalRows") or self._input_value(driver, "prv_TotalRows"),
            "message": None,
            "items": [],
        }

        tables = driver.find_elements(By.ID, "Tbl_Transactions")
        if not tables:
            result["message"] = self._driver_text(driver, By.CSS_SELECTOR, "#ContainerList .alert-custom") or None
            print(f"[BNC] Sin tabla de movimientos. {result['message'] or ''}")
            return result

        group = None
        for row in tables[0].find_elements(By.CSS_SELECTOR, "tbody tr"):
            classes = row.get_attribute("class") or ""
            cells = row.find_elements(By.TAG_NAME, "td")

            if "dtrg-group" in classes:
                if cells:
                    group = self._text(cells[0])
                continue

            if len(cells) < 5:
                continue

            lines = [line.strip() for line in (cells[0].text or "").splitlines() if line.strip()]
            result["items"].append({
                "date": lines[0] if lines else "",
                "time": lines[1] if len(lines) > 1 else "",
                "group": group,
                "description": self._text(cells[1]),
                "reference": self._text(cells[2]),
                "amount": self._text(cells[3]),
                "balance": self._text(cells[4]),
                "type": "credit" if "PositiveTransaction" in (cells[0].get_attribute("class") or "") else "debit",
            })

        print(f"[BNC] Movimientos encontrados: {len(result['items'])}")
        return result

    def _input_value(self, driver: WebDriver, element_id: str):
        values = driver.find_elements(By.ID, element_id)
        return values[0].get_attribute("value") if values else None

    # ------------------------------------------------------------------ #
    # Orquestación
    # ------------------------------------------------------------------ #
    def _safe_step(self, description: str, func, *args, default=None):
        """Ejecuta un paso de extracción sin romper la consulta completa."""
        try:
            return func(*args)
        except Exception as exc:
            print(f"[BNC] Error extrayendo {description}: {exc}")
            return default

    def balance(self, config: dict = None):
        """Consulta completa de BNC (0191): dashboard, posición consolidada y movimientos."""
        if config:
            self._config = config

        print("[BNC] ===== INICIO CONSULTA BNC (0191) =====")
        driver = get_chrome_driver()
        if not hasattr(driver, "get"):
            print(f"[BNC] No se pudo iniciar el navegador: {driver}")
            return {
                "bank": "Banco Nacional de Crédito",
                "code": "0191",
                "error": f"Could not start the browser: {driver}",
            }
        try:
            base_url = self._login(driver)

            data = {
                "bank": "Banco Nacional de Crédito",
                "code": "0191",
                "queried_at": datetime.now().isoformat(timespec="seconds"),
                "dashboard": self._safe_step(
                    "el dashboard", self._extract_dashboard, driver, base_url, default={}
                ),
                "position": self._safe_step(
                    "la posición consolidada", self._extract_position, driver, base_url, default=[]
                ),
                "movements": {
                    "last_25": self._safe_step(
                        "los movimientos (25 últimos)",
                        self._extract_movements, driver, base_url, BNC_PATHS["movements_last25"],
                        default={"path": BNC_PATHS["movements_last25"], "items": []},
                    ),
                    "previous_day": self._safe_step(
                        "los movimientos del día anterior",
                        self._extract_movements, driver, base_url, BNC_PATHS["movements_previous_day"],
                        default={"path": BNC_PATHS["movements_previous_day"], "items": []},
                    ),
                    "online": self._safe_step(
                        "los movimientos en línea",
                        self._extract_movements, driver, base_url, BNC_PATHS["movements_online"],
                        default={"path": BNC_PATHS["movements_online"], "items": []},
                    ),
                },
            }

            print("[BNC] ===== FIN CONSULTA BNC (0191) =====")
            return data
        except Exception as e:
            print(f"[BNC] Error en la consulta: {str(e)}")
            try:
                import os
                screenshot_path = "bnc_login_error.png"
                driver.save_screenshot(screenshot_path)
                print(f"[BNC] Captura de depuración guardada en {os.path.abspath(screenshot_path)}")
            except Exception as se:
                print(f"[BNC] No se pudo guardar la captura: {str(se)}")
            return {
                "bank": "Banco Nacional de Crédito",
                "code": "0191",
                "error": str(e),
            }
        finally:
            # El cierre de sesión es obligatorio al terminar, sin importar el resultado
            print("[BNC] Cerrando sesión (obligatorio al finalizar)...")
            try:
                self.logout(driver, self._base_url)
            except Exception as exc:
                print(f"[BNC] No se pudo cerrar sesión: {exc}")
            try:
                # Garantía extra: no dejar ninguna cookie de sesión en el navegador
                if hasattr(driver, "delete_all_cookies"):
                    driver.delete_all_cookies()
            except Exception as exc:
                print(f"[BNC] No se pudieron limpiar las cookies: {exc}")
            try:
                if hasattr(driver, "quit"):
                    driver.quit()
            except Exception as exc:
                print(f"[BNC] No se pudo cerrar el navegador: {exc}")

    def logout(self, driver: WebDriver, base_url: str = None) -> bool:
        """Cierra la sesión SIEMPRE al terminar: botón + confirmación y, si falla, /Auth/LogOut."""
        logged_out = False

        try:
            if driver.find_elements(By.ID, "btn-logout"):
                print("[BNC] Cerrando sesión (botón #btn-logout)...")
                self._click(driver, By.ID, "btn-logout", timeout=15)
                # Dialogs.Confirm crea dinámicamente #Mdl-Confirm con el botón #Mdl-Confirm-Yes
                self._click(driver, By.ID, "Mdl-Confirm-Yes", timeout=15)
                logged_out = self._wait_logout_page(driver, timeout=25)
                if not logged_out:
                    print("[BNC] La confirmación no completó el cierre; se reintentará por /Auth/LogOut.")
            else:
                print("[BNC] No se encontró el botón de salir en la página actual.")
        except Exception as e:
            print(f"[BNC] Logout por interfaz no disponible: {str(e)}")

        if not logged_out:
            fallback_base = base_url or self._base_url or DEFAULT_BNC_URL
            target = urljoin(fallback_base, AUTH_LOGOUT_PATH)
            print(f"[BNC] Forzando cierre de sesión en {target} ...")
            try:
                driver.get(target)
                logged_out = self._wait_logout_page(driver, timeout=25)
            except Exception as e:
                print(f"[BNC] No se pudo forzar el cierre de sesión: {str(e)}")

        if logged_out:
            print("[BNC] Sesión cerrada correctamente :D")
        else:
            print("[BNC] Advertencia: no se pudo confirmar el cierre de sesión.")
        return logged_out

    def _wait_logout_page(self, driver: WebDriver, timeout: int = 25) -> bool:
        """La sesión está cerrada cuando volvemos al login (#CardNumber) o a /Auth/..."""
        def is_closed(target_driver):
            try:
                current_url = (target_driver.current_url or "").lower()
                if "auth/logout" in current_url or "auth/login" in current_url:
                    return True
                return bool(target_driver.find_elements(By.ID, "CardNumber"))
            except Exception:
                return False

        try:
            WebDriverWait(driver, timeout).until(is_closed)
            return True
        except Exception:
            return False
