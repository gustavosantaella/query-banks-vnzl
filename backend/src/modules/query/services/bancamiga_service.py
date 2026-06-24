
from os import getenv
from src.config.app.selenium import get_chrome_driver
from nest.core import Injectable
from selenium.webdriver.common.by import By

@Injectable()
class BancamigaService:

    def login(self):
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
        pass
    
    def balance(self):
        pass
    
    def logout(self, driver):
        pass

    
    def swal_element(self, driver):
        swal_element = driver.find_element(By.XPATH, "/html/body/div[6]/div/div[10]/button[1]")
        swal_element.click()
