import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import re
import glob
from .BaseDownloader import BaseDownloader

class PortalConvenioDownloader(BaseDownloader):
    
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
        driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")
        time.sleep(5)

        download_link = driver.find_element(By.XPATH, "//div[@id='arquivo-unico']//a")
        download_link.click()
        print("Download iniciado...")

        zip_file_name = r".*_Convenios.zip"
        zip_path = self.wait_for_download(zip_file_name, driver)
        
        if zip_path:
            self.extract_and_cleanup(zip_path, "Convenios.csv", r"_Convenios_OrdensBancarias")
        driver.quit()
        
    def wait_for_download(self, zip_file_name, driver):

        while True:
            zip_files = glob.glob(os.path.join(self.download_dir, "*.zip"))
            if any(re.match(zip_file_name, os.path.basename(file)) for file in zip_files):
                zip_path = next(file for file in zip_files if re.match(zip_file_name, os.path.basename(file)))
                if not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    print("Download concluído!")
                    break
            else:
                print("Aguardando o download do arquivo zip...")
                time.sleep(15)

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern):
            
        shutil.move(zip_path, self.final_dir)
        print("Arquivo movido para a pasta: ", self.final_dir)
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            print("Dezipando")
            zip_ref.extractall(self.final_dir)
            
        print("Deletando .zip")
        os.remove(moved_file_path)

        files = glob.glob(os.path.join(self.final_dir, f"{delete_pattern}*"))
            
        for file in files:
            os.remove(file)
            
        file_to_rename = glob.glob(os.path.join(self.final_dir, f"{rename_to}.csv"))[0]
        os.rename(file_to_rename, os.path.join(self.final_dir, "Convenio.csv"))
        print(f"Arquivo renomeado para '{rename_to}.csv' com sucesso! ")
            
            