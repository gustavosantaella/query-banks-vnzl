
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
            driver = get_chrome_driver()
            driver.get(getenv("BANCAMIGA_URL"))
            driver.implicitly_wait(10)

            DNI = getenv("DNI")
            d = driver.find_element(By.ID, "documento")
            u = driver.find_element(By.ID, "u")
            p = driver.find_element(By.ID, "p")

            d.send_keys(DNI)
            u.send_keys(getenv("BANCAMIGA_USER"))
            p.send_keys(getenv("BANCAMIGA_PASS"))

            self.swal_element(driver)

            next_login_step_button = driver.find_element(By.XPATH, '//*[@id="cmdLogin"]')
            next_login_step_button.click()

            google_auth_code = input("Code Of Google Authenticator: ")
            google_auth_code_input = driver.find_element(By.ID, 'code')
            google_auth_code_input.send_keys(google_auth_code)

            next_login_step_button = driver.find_element(By.ID, 'cmdLogin')
            next_login_step_button.click()

            sleep(3)
        except Exception as e:
            print(f"Error login method {str(e)}")
        finally:
            self.logout(driver)
            if driver:
                driver.quit()
    
    def balance(self):
        pass
    
    def logout(self, driver: webdriver.Chrome):
        try:
            driver.execute_script("arguments[0].click()", driver.find_element(By.XPATH, '//*[@id="logout"]/span/a'))
            self.swal_confirm(driver)
            driver.close()
            print("Logout successfully")
        except Exception as e:
            print("Error to logout Bancamiga...")
            return e
        finally:
            driver.quit()

    
    def swal_element(self, driver):
        swal_element = driver.find_element(By.XPATH, "/html/body/div[6]/div/div[10]/button[1]")
        swal_element.click()

    def swal_confirm(driver):
        driver.execute_script("arguments[0].click()", driver.find_element(By.XPATH, '//*[@id="Mdl-Confirm-Yes"]'))
        sleep(3)
        
