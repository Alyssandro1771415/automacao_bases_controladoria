import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader
import pandas as pd

class PainelObras(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def _get_latest_file(self):
        files = os.listdir(self.download_dir)
        if not files:
            return None
        files_with_paths = [os.path.join(self.download_dir, f) for f in files]
        return max(files_with_paths, key=os.path.getctime)

    def _wait_for_download_to_start(self, initial_files, start_time,timeout=30):

        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            if new_files:
                return new_files.pop()
            time.sleep(5)

        raise TimeoutError("Nenhum novo arquivo detectado no tempo limite.")

    def download(self):
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://clusterqap2.economia.gov.br/extensions/painel-obras/painel-obras.html")
        time.sleep(10)

        try:
            uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
            uf_element.click()
            
            download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
            
            initial_files = set(os.listdir(self.download_dir))
            start_time = time.time()
            download_button.click()
            print("Download iniciado...")

            downloaded_file = self._wait_for_download_to_start(initial_files=initial_files, start_time=start_time)
            print(f"Arquivo detectado: {downloaded_file}")

            file_path = os.path.join(self.download_dir, downloaded_file)
                    
            file_downloaded = pd.read_excel(file_path)
            self.clean_final_directory()
            csv_path = os.path.join(self.final_dir, "Obras.csv")
            file_downloaded.to_csv(csv_path, sep=";", index=False)
            print(f"Novo arquivo salvo em: {csv_path}")

            os.remove(file_path)

        finally:
            driver.quit()
            print("Driver encerrado.")
