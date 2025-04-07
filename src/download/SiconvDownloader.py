import os
import requests
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from .BaseDownloader import BaseDownloader
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SiconvDownloader(BaseDownloader):

    def __init__(self, geckoDriver, download_dir, final_dir):
        super().__init__(geckoDriver, download_dir, final_dir)

    def _wait_for_download_to_complete(self, initial_files):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        previous_size = 0
        max_retries = 10
        retries = 0
        
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files

            temp_files = [
                file for file in new_files
                if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
            ]

            if temp_files:
                temp_file_path = os.path.join(self.download_dir, temp_files[0])
                try:
                    current_size = os.path.getsize(temp_file_path)
                    
                    # Exibir barra de loading
                    self._print_progress_bar(current_size)
                    
                    if current_size == previous_size:
                        retries += 1
                        if retries >= max_retries:
                            raise TimeoutError("Download parece estar pausado ou com erro.")
                    else:
                        retries = 0
                        previous_size = current_size
                except FileNotFoundError:
                    pass

            else:
                break

            time.sleep(5)

        return new_files

    def _print_progress_bar(self, current_size):
        # Converte tamanhos para MB
        current_size_mb = current_size / (1024 * 1024)
        
        # Obtém o tamanho total do arquivo via HTTP HEAD
        url = "https://repositorio.dados.gov.br/seges/detru/siconv.zip"
        response = requests.head(url, allow_redirects=True)
        total_size_mb = int(response.headers.get("Content-Length", 0)) / (1024 * 1024)

        # Calcula o progresso
        progress = current_size_mb / total_size_mb if total_size_mb > 0 else 0

        # Define tamanho da barra
        bar_length = 50
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        # Exibe a barra de progresso
        print(f'\rProgresso: |{bar}| {current_size_mb:.2f}/{total_size_mb:.2f} MB ({progress * 100:.2f}%)', end='', flush=True)
    
    def extract_and_cleanup(self, zip_path):
        
        for file in os.listdir(self.final_dir):
            os.remove(os.path.join(self.final_dir, file))
            
        shutil.move(zip_path, self.final_dir)
        print("Arquivo movido para a pasta: ", self.final_dir)
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            print("Dezipando")
            zip_ref.extractall(self.final_dir)
                        
        print("Deletando .zip")
        os.remove(moved_file_path)

    def download(self):
        title = "Repositório de Dados GOV - SICONV"
        print(f"\n\n\n\033[35;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("browser.download.manager.showAlertOnComplete", False)
        options.set_preference("browser.download.manager.focusWhenStarting", False)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.tabs.warnOnClose", False)
        options.set_preference("browser.tabs.warnOnCloseOtherTabs", False)
        options.set_preference("browser.tabs.warnOnOpen", False)
        options.set_preference("browser.download.manager.quitBehavior", 2)
        options.set_preference("browser.download.folderList", 2)
        options.add_argument("--headless") #

        driver = webdriver.Firefox(service=self.geckoDriver, options=options)
        driver.get("https://repositorio.dados.gov.br/seges/detru/")
        
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "body > pre"))
        )

        initial_files = set(os.listdir(self.download_dir))
        
        if not os.path.exists(self.final_dir):
            os.mkdir(self.final_dir)

        try:
            elemento_pai = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/pre"))
            )

            # Lista todos os <a> dentro do <pre>
            links = elemento_pai.find_elements(By.TAG_NAME, 'a')

            # Itera pelos links e clica no que contém o texto desejado
            for link in links:
                if "siconv.zip" == link.text:
                    link.click()
                    break
            else:
                print("Link com o texto desejado não foi encontrado.")
            print("Download iniciado...")

            downloaded_files = self._wait_for_download_to_complete(initial_files=initial_files)
            print(f"\nArquivos detectados: {downloaded_files}")

        except TimeoutError as e:
            print(f"Erro: {e}. Reiniciando o download...")
            driver.quit()
            self.download()
            return

        except Exception as e:
            print(f"Erro durante o download: {e}")
            driver.quit()
            return

        finally:
            if driver:
                driver.quit()

        zip_path = os.path.join(self.download_dir, str(next(iter(downloaded_files))))

        if os.path.exists(zip_path):
            file_path = os.path.join(self.download_dir, str(next(iter(downloaded_files))))

            self.extract_and_cleanup(file_path)            
