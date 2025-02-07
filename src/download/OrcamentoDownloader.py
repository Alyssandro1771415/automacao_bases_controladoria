# OrcamentoDownloader.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import datetime
from src.download.BaseDownloader import BaseDownloader

import os
import time
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.download.BaseDownloader import BaseDownloader

class OrcamentoDownloader(BaseDownloader):
    def __init__(self, geckoDriver, download_dir, final_dir):
        super().__init__(geckoDriver, download_dir, final_dir)

    def download(self):
        title = "Orçamento Geral da União"
        self.logger.info(f"\n\n\n{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\n\n\n")
        
        driver = self.get_driver()
        driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")

        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']"))
            )
            
            try:
                accept_all_cookies = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="adopt-accept-all-button"]'))
                )
                accept_all_cookies.click()
                self.logger.info("Botão de aceitar cookies clicado com sucesso.")
            except (TimeoutException, NoSuchElementException):
                self.logger.info("Botão de aceitar cookies não encontrado. Continuando...")
            
            initial_files = set(os.listdir(self.download_dir))

            try:
                download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
                download_button.click()
                time.sleep(3)

                zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"

                download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
                download_link.click()
                self.logger.info("Download iniciado...")
            except Exception:
                download_link = driver.find_element(By.XPATH, f"//*[@id='categoria_944']/div/div/ul/li[1]/a")
                download_link.click()
                self.logger.info("Download iniciado...")

            self.logger.info("Aguardando a conclusão do download...")
            downloaded_files = self._wait_for_download_to_complete(initial_files)

            if not downloaded_files:
                raise TimeoutException("Nenhum novo arquivo detectado após o download.")

            downloaded_file = list(downloaded_files)[0]
            self.logger.info(f"Arquivo detectado: {downloaded_file}")

            zip_path = os.path.join(self.download_dir, downloaded_file)

            self.extract_and_cleanup(zip_path)
            self.logger.info("Arquivo de Orçamento Geral da União extraído e removido com sucesso!")

        finally:
            driver.quit()
            self.logger.info("Driver encerrado.")