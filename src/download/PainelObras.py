# PainelObras.py

import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .BaseDownloader import BaseDownloader

class PainelObras(BaseDownloader):
    
    def download(self):
        title = "Painel de Obras - Pernambuco"
        self.logger.info(f"\n\n\n{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\n\n\n")
        
        driver = self.get_driver()
        driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")
        
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
            )
            
            uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
            uf_element.click()
            
            download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
            initial_files = set(os.listdir(self.download_dir))
            download_button.click()
            self.logger.info("Download iniciado...")
            
            self.logger.info("Aguardando a conclusão do download...")
            downloaded_files = self._wait_for_download_to_complete(initial_files)

            if not downloaded_files:
                raise Exception("Nenhum arquivo foi baixado")
            
            file_path = os.path.join(self.download_dir, downloaded_file.pop())
            file_downloaded = pd.read_excel(file_path)
            
            csv_path = os.path.join(self.final_dir, "Obras.csv")
            file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
            self.logger.info(f"Novo arquivo salvo em: {csv_path}")
            
            os.remove(file_path)
            
        finally:
            driver.quit()
            self.logger.info("Driver encerrado.")

