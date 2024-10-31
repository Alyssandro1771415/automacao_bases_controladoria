import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader

class SiconvDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    
    def download(self):

        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://repositorio.dados.gov.br/seges/detru/")
        time.sleep(5)

        download_link = driver.find_element(By.XPATH, '/html/body/pre/a[7]')
        download_link.click()
        print("Download iniciado...")

        zip_path = os.path.join(self.download_dir, "siconv.zip")

        # Voltar pra antiga versão da verificação
        while os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                            
            print("Aguardando o download do arquivo zip...")
            time.sleep(15)

        print("Download concluído!")
        driver.quit()

        if os.path.exists(zip_path):
            
            shutil.move(zip_path, self.final_dir)
            print("Arquivo movido para a pasta: ", self.final_dir)    
            moved_file_path = os.path.join(self.final_dir, "siconv.zip")
                
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                print("Dezipando")
                zip_ref.extractall(self.final_dir)

            os.remove(moved_file_path)
            print("Programa finalizado!")