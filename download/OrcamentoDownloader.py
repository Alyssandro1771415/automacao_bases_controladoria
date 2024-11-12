import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import datetime
from .BaseDownloader import BaseDownloader

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def download(self):
        self.setup_directories

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
        time.sleep(5)

        zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"
        zip_path = os.path.join(self.download_dir, zip_file_name)

        try:
            download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
            download_button.click()
            time.sleep(3)

            download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
            download_link.click()
            print("Download iniciado...")
            
            while True:
                if os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    print("Download concluído!")
                    break
                else:
                    
                    print("Aguardando o download do arquivo zip...")
                    time.sleep(15)
        
        finally:
            driver.quit()

        if os.path.exists(zip_path):
            shutil.move(zip_path, self.final_dir)
            moved_file_path = os.path.join(self.final_dir, zip_file_name)
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.final_dir)
                
            os.remove(moved_file_path)
            print("Arquivo de Orçamento Geral da União extraido e removido com sucesso!")