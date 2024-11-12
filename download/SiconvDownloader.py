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

        while True:
            if os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                print("Download concluído!")
                break
            else:
                print("Aguardando o download do arquivo zip...")
                time.sleep(15)

        driver.quit()

        print("Chegou na zipagem")

        if os.path.exists(zip_path):
            file_path = os.path.join(self.download_dir, "siconv.zip")
            destination_path = os.path.join(self.final_dir, "siconv.zip")
            
            # Verifique se o arquivo já existe no destino e o exclua se necessário
            if os.path.isfile(destination_path):
                print("O arquivo siconv.zip já existe no destino. Removendo arquivo existente...")
                os.remove(destination_path)

            shutil.move(file_path, self.final_dir)
            print("Arquivo movido para a pasta: ", self.final_dir)
                
            moved_file_path = os.path.join(self.final_dir, "siconv.zip")
                
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                print("Dezipando")
                zip_ref.extractall(self.final_dir)

            print("Deletando siconv.zip")
            os.remove(moved_file_path)
            print("Programa finalizado!")
