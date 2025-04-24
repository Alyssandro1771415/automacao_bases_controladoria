import os
import requests
import time
import zipfile
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .BaseDownloader import BaseDownloader

class SiconvDownloader(BaseDownloader):

    def __init__(self, geckoDriver=None, retry_delay=5):
        super().__init__(geckoDriver=geckoDriver)
        self.retry_delay = retry_delay

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
                    self._log_progress_bar(current_size)
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

    def _log_progress_bar(self, current_size):
        # Converte tamanhos para MB
        current_size_mb = current_size / (1024 * 1024)

        # Obtém o tamanho total do arquivo via HTTP HEAD
        url = "https://repositorio.dados.gov.br/seges/detru/siconv.zip"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            total_size_mb = int(response.headers.get("Content-Length", 0)) / (1024 * 1024)
        except Exception:
            total_size_mb = 0

        # Calcula o progresso
        progress = current_size_mb / total_size_mb if total_size_mb > 0 else 0

        # Define tamanho da barra
        bar_length = 50
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        # Loga a barra de progresso
        self.log_info(
            f'Progresso: |{bar}| {current_size_mb:.2f}/{total_size_mb:.2f} MB ({progress * 100:.2f}%)'
        )

    def extract_and_cleanup(self, zip_path):
        self.clean_final_directory()
        shutil.move(zip_path, self.final_dir)
        self.log_info(f"Arquivo movido para a pasta: {self.final_dir}")
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))

        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            self.log_info("Dezipando")
            zip_ref.extractall(self.final_dir)

        self.log_info("Deletando .zip")
        os.remove(moved_file_path)

    @staticmethod
    def wait_for_element(driver, locator_value, timeout=100, poll_frequency=0.5):
        try:
            # Pode ser adaptado para logging se desejar
            print(f"Aguardando elemento: {locator_value} com timeout de {timeout}s...")
            element = WebDriverWait(driver, timeout, poll_frequency).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locator_value))
            )
            print(f"Elemento encontrado: {locator_value}")
            return element
        except TimeoutException:
            print(f"Elemento {locator_value} não encontrado após {timeout} segundos.")
            raise

    def download(self, browser="firefox"):
        title = "Repositório de Dados GOV - SICONV"
        self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

        driver = None
        try:
            self.setup_directories()
            driver = self.get_driver(browser)
            driver.get("https://repositorio.dados.gov.br/seges/detru/")

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "body > pre"))
            )

            initial_files = set(os.listdir(self.download_dir))

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
                self.log_info("Link com o texto desejado não foi encontrado.")
                return

            self.log_info("Download iniciado...")

            downloaded_files = self._wait_for_download_to_complete(initial_files=initial_files)
            self.log_info(f"Arquivos detectados: {downloaded_files}")

            zip_path = os.path.join(self.download_dir, str(next(iter(downloaded_files))))

            if os.path.exists(zip_path):
                self.extract_and_cleanup(zip_path)

        except TimeoutError as e:
            self.log_error(f"Erro: {e}. Reiniciando o download...")
            if driver:
                driver.quit()
            self.download()
            return

        except Exception as e:
            self.log_error(f"Erro durante o download: {e}")
            return

        finally:
            if driver:
                driver.quit()
                self.log_info("Driver encerrado.")