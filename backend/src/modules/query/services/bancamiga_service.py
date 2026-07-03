
from typing import final
from time import sleep
from selenium import webdriver
from os import getenv
from src.config.app.selenium import get_chrome_driver
from nest.core import Injectable
from selenium.webdriver.common.by import By

@Injectable()
class BancamigaService:

    def login(self):
        try:
            print("--- BANCAMIGA LOGIN START ---")
            print("Initializing Chrome Driver...")
            driver = get_chrome_driver()
            
            url = getenv("BANCAMIGA_URL")
            print(f"Navigating to URL: {url}")
            driver.get(url)
            driver.implicitly_wait(10)

            DNI = getenv("DNI")
            print(f"Entering credentials (DNI: {DNI})...")
            d = driver.find_element(By.ID, "documento")
            u = driver.find_element(By.ID, "u")
            p = driver.find_element(By.ID, "p")

            d.send_keys(DNI)
            u.send_keys(getenv("BANCAMIGA_USER"))
            p.send_keys(getenv("BANCAMIGA_PASS"))

            print("Closing swal alert element...")
            self.swal_element(driver)

            print("Clicking initial Login submit button...")
            next_login_step_button = driver.find_element(By.XPATH, '//*[@id="cmdLogin"]')
            next_login_step_button.click()

            print("Awaiting Google Authenticator input...")
            google_auth_code = input("Code Of Google Authenticator: ")
            print(f"Entering Google Authenticator code: {google_auth_code}")
            google_auth_code_input = driver.find_element(By.ID, 'code')
            google_auth_code_input.send_keys(google_auth_code)

            print("Clicking final Login step button...")
            next_login_step_button = driver.find_element(By.ID, 'cmdLogin')
            next_login_step_button.click()

            print("Checking for PWA modal overlay...")
            dimiss_modal_alert = driver.find_elements(By.XPATH, "//*[@id='modalPWA']/div/div/div/div[1]/a")
            if len(dimiss_modal_alert) > 0:
                print("PWA modal found, dismissing it...")
                driver.execute_script("arguments[0].click()", dimiss_modal_alert[0])
            else:
                print("No PWA modal found.")
                
            sleep(1)

            print("Calling balance extraction...")
            result = self.balance(driver)
            print(f"Extraction result: {result}")
            return result
        except Exception as e:
            print(f"Error login method: {str(e)}")
            return []
        finally:
            print("Cleaning up / Logging out...")
            self.logout(driver)
            if driver:
                driver.quit()
            print("--- BANCAMIGA LOGIN END ---")
    
    def balance(self, driver: webdriver.Chrome):  
        try:
            print("--- STARTING BALANCE EXTRACTION ---")
            data = []
            driver.implicitly_wait(10)
            
            print("Searching for table containers (#posicion-global)...")
            tables = driver.find_elements(By.CSS_SELECTOR, "#posicion-global .table-responsive table")
            print(f"Found {len(tables)} tables to parse.")
            
            for index, table in enumerate(tables, start=1):
                headers = []
                th_elements = table.find_elements(By.TAG_NAME, "th")
                for th in th_elements:
                    headers.append(th.text.strip())
                
                print(f"Table {index} headers: {headers}")
                if not headers:
                    print(f"Table {index} has no headers, skipping.")
                    continue
                
                rows = table.find_elements(By.XPATH, ".//tbody/tr[position() > 1]")
                print(f"Table {index} has {len(rows)} data rows.")
                
                for row_idx, row in enumerate(rows, start=1):
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if not cols or len(cols) < len(headers):
                        print(f"Table {index} Row {row_idx}: cell count ({len(cols)}) mismatch with header count ({len(headers)}), skipping.")
                        continue
                    
                    col_texts = [col.text.strip() for col in cols]
                    print(f"Table {index} Row {row_idx} column texts: {col_texts}")
                    
                    # 1. Accounts Table (Cuentas / Cuentas Moneda Extranjera)
                    if "Instrumento Financiero" in headers and "Código Cuenta Cliente" in headers:
                        try:
                            instrument_idx = headers.index("Instrumento Financiero")
                            code_idx = headers.index("Código Cuenta Cliente")
                            currency_idx = headers.index("Moneda")
                            available_idx = headers.index("Saldo Disponible")
                            
                            instrument = col_texts[instrument_idx]
                            instrument_clean = " ".join([line.strip() for line in instrument.split("\n") if line.strip() and not line.strip().startswith("<")])
                            
                            code = col_texts[code_idx].split("\n")[0].strip()
                            currency = col_texts[currency_idx]
                            available = col_texts[available_idx].split("\n")[0].strip()
                            
                            label = f"{instrument_clean} ({code})"
                            value = f"{available} {currency}"
                            
                            print(f"Parsed Account: label='{label}', value='{value}'")
                            data.append({
                                "label": label,
                                "value": value
                            })
                        except Exception as inner_err:
                            print(f"Error parsing account row: {str(inner_err)}")
                            
                    # 2. Credits Table (Crédito)
                    elif "Producto" in headers and "Número de Crédito" in headers:
                        try:
                            prod_idx = headers.index("Producto")
                            num_idx = headers.index("Número de Crédito")
                            tasa_idx = headers.index("Tasa")
                            balance_idx = headers.index("Saldo Actual")
                            
                            prod = col_texts[prod_idx]
                            prod_clean = " ".join([line.strip() for line in prod.split("\n") if line.strip() and not line.strip().startswith("<")])
                            
                            num = col_texts[num_idx].split("\n")[0].strip()
                            tasa = col_texts[tasa_idx]
                            balance = col_texts[balance_idx].split("\n")[0].strip()
                            
                            label = f"{prod_clean} ({num}) - Tasa {tasa}"
                            value = balance
                            
                            print(f"Parsed Credit: label='{label}', value='{value}'")
                            data.append({
                                "label": label,
                                "value": value
                            })
                        except Exception as inner_err:
                            print(f"Error parsing credit row: {str(inner_err)}")
                            
                    # 3. Cards Table (Tarjeta en Divisas)
                    elif "Tipo" in headers and "Código Tarjeta" in headers:
                        try:
                            tipo_idx = headers.index("Tipo")
                            card_idx = headers.index("Código Tarjeta")
                            currency_idx = headers.index("Moneda")
                            
                            tipo = col_texts[tipo_idx]
                            tipo_clean = " ".join([line.strip() for line in tipo.split("\n") if line.strip() and not line.strip().startswith("<")])
                            
                            card = col_texts[card_idx].split("\n")[0].strip()
                            currency = col_texts[currency_idx]
                            
                            label = f"{tipo_clean} ({card})"
                            value = currency
                            
                            print(f"Parsed Card: label='{label}', value='{value}'")
                            data.append({
                                "label": label,
                                "value": value
                            })
                        except Exception as inner_err:
                            print(f"Error parsing card row: {str(inner_err)}")
            
            print(f"Total extracted elements: {len(data)}")
            print("--- EXTRACTION COMPLETED ---")
            return data
            
        except Exception as e:
            print(f"Error extracting balances from posicion-global: {str(e)}")
            return []
    
    def logout(self, driver: webdriver.Chrome):
        try:
            driver.execute_script("arguments[0].click()", driver.find_element(By.XPATH, '//*[@id="logout"]/span/a'))
            self.swal_confirm(driver)
            driver.close()
            print("Logout successfully")
        except Exception as e:
            print("Error to logout Bancamiga...")
            print(e)
            return e
        finally:
            driver.quit()

    
    def swal_element(self, driver):
        swal_element = driver.find_element(By.XPATH, "/html/body/div[6]/div/div[10]/button[1]")
        swal_element.click()

    def swal_confirm(self, driver):
        driver.execute_script("arguments[0].click()", driver.find_element(By.XPATH, '/html/body/div[7]/div/div[10]/button[1]'))
        sleep(3)

    
        
