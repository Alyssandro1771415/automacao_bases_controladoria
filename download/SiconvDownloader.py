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
        
    def _wait_for_download_to_complete(self, initial_files):
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            if new_files:
                downloaded_file = new_files.pop()
                
                if not downloaded_file.endswith('.part') or downloaded_file.endswith('.crdownload'):
                    return downloaded_file
                else:
                    print(f"Aguardando conclusão do download: {downloaded_file}")
            
            time.sleep(5)

    def download(self):
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://repositorio.dados.gov.br/seges/detru/")
        time.sleep(10)
        
        initial_files = set(os.listdir(self.download_dir))

        download_link = driver.find_element(By.XPATH, '/html/body/pre/a[7]')
        download_link.click()
        print("Download iniciado...")

        zip_path = os.path.join(self.download_dir, "siconv.zip")

        time.sleep(5)
        downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
        print(f"Arquivo detectado: {downloaded_file}")

        driver.quit()

        print("Chegou na dezipagem")

        if os.path.exists(zip_path):
            file_path = os.path.join(self.download_dir, "siconv.zip")
            
            self.clean_final_directory()

            shutil.move(file_path, self.final_dir)
            print("Arquivo movido para a pasta: ", self.final_dir)
                
            moved_file_path = os.path.join(self.final_dir, "siconv.zip")
                
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                print("Dezipando")
                zip_ref.extractall(self.final_dir)

            print("Deletando siconv.zip")
            os.remove(moved_file_path)
            print("Programa finalizado!")
