import os
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

class PainelObras(BaseDownloader):
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5, max_retries=5):
        super().__init__(geckoDriver, download_dir, final_dir, retry_delay, max_retries)
    
    def download(self, driver):
        try:
            self.logger.info("Iniciando download do Painel de Obras - Pernambuco")
            driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")
            
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
            )
            
            uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
            uf_element.click()
            
            download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
            initial_files = set(os.listdir(self.download_dir))
            download_button.click()
            self.logger.info("Download iniciado...")
            
            downloaded_files = self._wait_for_download_to_complete(initial_files)
            if not downloaded_files:
                raise Exception("Nenhum arquivo foi detectado após o download.")
            
            downloaded_file = os.path.join(self.download_dir, downloaded_files.pop())
            self.logger.info(f"Arquivo detectado: {downloaded_file}")
            
            file_downloaded = pd.read_excel(downloaded_file, dtype=str, engine="openpyxl")
            campos_porcentagem = ["Execução Física", "Execução Financeira"]
            
            for campo in campos_porcentagem:
                file_downloaded[campo] = file_downloaded[campo].apply(lambda x: f"{round(float(x) * 100, 2)}%" if x != "-" else x)
            
            self.clean_final_directory()
            csv_path = os.path.join(self.final_dir, "Obras.csv")
            file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
            self.logger.info(f"Novo arquivo salvo em: {csv_path}")
            
            os.remove(downloaded_file)
            return csv_path
        
        except Exception as e:
            self.logger.error(f"Erro durante o download: {e}")
            return None
