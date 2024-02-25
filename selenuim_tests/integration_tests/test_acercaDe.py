import pytest
import time
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Obtener valores de variables de entorno
webdriver_host = os.getenv("WEBDRIVER_HOSTNAME")
webdriver_port = os.getenv("WEBDRIVER_PORT")
omnileads_host = os.getenv('OMNILEADS_HOSTNAME')
omnileads_secret = os.getenv('OMNILEADS_WEB_SECRET')
omnileads_user = os.getenv('OMNILEADS_WEB_USER')

class TestAcercaDe:
    def setup_method(self, method):
        # Configurar opciones de Chrome
        chromeOptions = Options()
        chromeOptions.add_argument('--ignore-certificate-errors') 
        chromeOptions.add_argument('--no-sandbox') 
        chromeOptions.add_argument('--headless') 
        
        # Iniciar el navegador remoto
        self.driver = webdriver.Remote(command_executor=f'http://{webdriver_host}:{webdriver_port}/wd/hub', options=chromeOptions)
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()
  
    def test_acerca_de(self):
        self.driver.get(f"https://{omnileads_host}/accounts/login/")
        self.driver.set_window_size(1440, 877)
        
        # Iniciar sesión
        self.driver.find_element(By.ID, "id_username").click()
        self.driver.find_element(By.ID, "id_username").send_keys(omnileads_user)
        self.driver.find_element(By.ID, "id_password").send_keys(omnileads_secret)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        
        # Navegar y hacer clic en elementos
        self.driver.find_element(By.XPATH, "//a[contains(@href, '#menuAyuda')]").click()
        self.driver.find_element(By.XPATH, "//ul[@id='menuAyuda']/li[2]/a").click()
        self.driver.find_element(By.CSS_SELECTOR, "h1").click()
        self.driver.find_element(By.CSS_SELECTOR, "h2:nth-child(2)").click()
        self.driver.find_element(By.CSS_SELECTOR, "h2:nth-child(4)").click()
        self.driver.find_element(By.CSS_SELECTOR, "h2:nth-child(6)").click()
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/accounts/logout/')]").click()

# Ejecutar las pruebas
if __name__ == '__main__':
    pytest.main(['-v', '-s', __file__])
