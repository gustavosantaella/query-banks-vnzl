
from time import sleep

from src.config.app.selenium import get_chrome_driver

from os import getenv

from selenium.webdriver.common.by import By

from nest.core import Injectable
@Injectable()
class BncService:

    def balance(self):
        print("Starting driver...")
        driver = get_chrome_driver()
        print("driver has been started...")
        try:
            BNC_URL= getenv("BNC_URL")

            driver.get(BNC_URL)

            sleep(2)

            input_card_number = driver.find_element(By.ID, "CardNumber")

            input_dni = driver.find_element(By.ID, "UserID")

            BNC_CARD_NUMBER = getenv("BNC_CARD_NUMBER")
            DNI = getenv("DNI")

            input_card_number.send_keys(BNC_CARD_NUMBER)
            input_dni.send_keys(DNI)

            submit_button = driver.find_element(By.ID, "BtnSend").click()

            sleep(2)

            input_pwd = driver.find_element(By.ID, "UserPassword").send_keys(getenv("BNC_PASS"))

            submit_button = driver.find_element(By.ID, "BtnSend").click()

            sleep(3)

            amount = driver.find_element(By.XPATH, '//*[@id="FormContainer"]/div/div[2]/div/div/div/div[2]/div[1]/div/div').text
            

            return amount
        except Exception as e:
            print(f"Error to init Selenium: {str(e)}")
            return e
        
        finally:
            print("Quit selenium BNC")
            driver.quit()