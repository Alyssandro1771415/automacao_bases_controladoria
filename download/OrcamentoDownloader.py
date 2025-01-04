import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import datetime
from .BaseDownloader import BaseDownloader

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)
        
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
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="adopt-accept-all-button"]'))
        )
        
        accept_all_cookies = driver.find_element(By.XPATH, '//*[@id="adopt-accept-all-button"]')
        accept_all_cookies.click()

        try:
            
            initial_files = set(os.listdir(self.download_dir))
            
            try: 
                download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
                download_button.click()
                time.sleep(3)

                zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"

                download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
                download_link.click()
                print("Download iniciado...")
            except Exception:
                download_link = driver.find_element(By.XPATH, f"//*[@id='categoria_944']/div/div/ul/li[1]/a")
                download_link.click()
                print("Download iniciado...")
            
            time.sleep(5)
            downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
            print(f"Arquivo detectado: {downloaded_file}")
        
            zip_path = os.path.join(self.download_dir, downloaded_file)

        
        finally:
            driver.quit()

        if os.path.exists(zip_path):
            self.clean_final_directory()

            shutil.move(zip_path, self.final_dir)
            moved_file_path = os.path.join(self.final_dir, downloaded_file)
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.final_dir)
                
            os.remove(moved_file_path)
            print("Arquivo de Orçamento Geral da União extraído e removido com sucesso!")
