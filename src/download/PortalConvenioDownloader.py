import os
import time
import zipfile
import shutil
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

class PortalConvenioDownloader(BaseDownloader):

    def __init__(self, geckoDriver=None, retry_delay=5):
        super().__init__(geckoDriver=geckoDriver)
        self.retry_delay = retry_delay

    def download(self, browser="firefox"):
        retries = 0
        title = "Portal da Transparência - Convênio"

        while True:
            driver = None
            try:
                self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

                initial_files = set(os.listdir(self.download_dir))
                self.setup_directories()

                driver = self.get_driver(browser)
                driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='arquivo-unico']//a"))
                )

                try:
                    accept_cookies = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#accept-all-btn"))
                    )
                    accept_cookies.click()
                    self.log_info("Botão de aceitar cookies clicado com sucesso.")
                except (TimeoutException, NoSuchElementException):
                    self.log_info("Botão de aceitar cookies não encontrado. Continuando...")

                download_link = driver.find_element(By.XPATH, "//div[@id='arquivo-unico']//a")
                download_link.click()
                self.log_info("Download iniciado...")

                zip_file = self._wait_for_download_to_complete(initial_files)

                if zip_file:
                    zip_path = os.path.join(self.download_dir, str(next(iter(zip_file))))
                    self.extract_and_cleanup(zip_path, "Convenios.csv", r".*_Convenios_OrdensBancarias", r".*_Convenios.csv")
                    break
                else:
                    raise TimeoutException("Nenhum novo arquivo detectado após o download.")

            except Exception as e:
                retries += 1
                self.log_error(f"Erro durante a execução: {e}. Tentativa {retries}...")
                time.sleep(self.retry_delay)

            finally:
                if driver:
                    driver.quit()
                    self.log_info("Driver encerrado.")

    def _wait_for_download_to_complete(self, initial_files):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        retries = 0
        max_retries = 10
        previous_size = 0

        while retries < max_retries:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files

            temp_files = [
                file for file in new_files if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
            ]

            if temp_files:
                temp_file_path = os.path.join(self.download_dir, temp_files[0])
                try:
                    current_size = os.path.getsize(temp_file_path)
                    if current_size == previous_size:
                        retries += 1
                    else:
                        retries = 0
                        previous_size = current_size
                except FileNotFoundError:
                    pass
            else:
                return new_files if new_files else None

            time.sleep(5)

        raise TimeoutError("Download parece estar pausado ou com erro.")

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_pattern):
        self.clean_final_directory()

        shutil.move(zip_path, self.final_dir)
        self.log_info(f"Arquivo movido para a pasta: {self.final_dir}")
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))

        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.final_dir)

        os.remove(moved_file_path)
        self.log_info("Arquivo zip deletado após extração.")

        files = os.listdir(self.final_dir)
        file_to_delete = next((file for file in files if re.match(delete_pattern, file)), None)
        file_to_rename = next((file for file in files if re.match(rename_pattern, file)), None)

        if file_to_delete:
            os.remove(os.path.join(self.final_dir, file_to_delete))
            self.log_info(f"Arquivo '{file_to_delete}' deletado com sucesso!")

        if file_to_rename:
            os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
            self.log_info(f"Arquivo '{file_to_rename}' renomeado para '{rename_to}'!")