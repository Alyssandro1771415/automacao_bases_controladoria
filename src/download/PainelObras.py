import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, SessionNotCreatedException
import pandas as pd
from .BaseDownloader import BaseDownloader

class PainelObras(BaseDownloader):
    
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = retry_delay
    
    def _wait_for_download_to_complete(self, initial_files):
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            if new_files:
                downloaded_file = new_files.pop()
                
                if not downloaded_file.endswith('.part'):
                    return downloaded_file
                else:
                    print(f"Aguardando conclusão do download: {downloaded_file}")
            
            time.sleep(5)

    def download(self):
        retries = 0
        
        while True:
            driver = None
            try:
                title = "Painel de Obras - Pernambuco"
                print(f"\n\n\n\033[36;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")
                
                self.setup_directories()
                
                options = webdriver.FirefoxOptions()
                options.set_preference("browser.download.folderList", 2)
                options.set_preference("browser.download.dir", self.download_dir)
                options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
                options.set_preference("pdfjs.disabled", True)
                options.add_argument("--headless")
                
                driver = webdriver.Firefox(service=self.geckoDriver, options=options)
                driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")
                
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
                )
                
                try:
                    
                    uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
                    uf_element.click()
                    
                    download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
                    initial_files = set(os.listdir(self.download_dir))
                    download_button.click()
                    print("Download iniciado...")
                    
                    downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
                    print(f"Arquivo detectado: {downloaded_file}")
                    
                    file_path = os.path.join(self.download_dir, downloaded_file)
                    file_downloaded = pd.read_excel(file_path)
                    
                    self.clean_final_directory()
                    csv_path = os.path.join(self.final_dir, "Obras.csv")
                    file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
                    print(f"Novo arquivo salvo em: {csv_path}")
                    
                    os.remove(file_path)
                    break
                
                finally:
                    if driver:
                        driver.quit()
                    print("Driver encerrado.")
                    
            except Exception as e:
                print(f"Erro durante a execução: {e}. Tentativa {retries + 1}...")
                if driver:
                    driver.quit()
                retries += 1
                time.sleep(self.retry_delay)
