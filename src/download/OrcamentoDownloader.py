import os
import time
import zipfile
import shutil
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, geckoDriver=None, retry_delay=5):
        # Não precisa mais passar download_dir e final_dir, pois já são lidos do .env na classe pai
        super().__init__(geckoDriver=geckoDriver)
        self.retry_delay = retry_delay

    def _wait_for_download_to_complete(self, initial_files):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            if new_files:
                temp_files = [file for file in new_files if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)]
                if not temp_files:
                    return new_files
            time.sleep(5)

    def download(self, browser="firefox"):
        retries = 0
        title = "Orçamento Geral da União"

        while True:
            try:
                self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

                self.setup_directories()

                driver = self.get_driver(browser)
                driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")

                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']"))
                )

                try:
                    try:
                        accept_all_cookies = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="adopt-accept-all-button"]'))
                        )
                        accept_all_cookies.click()
                        self.log_info("Botão de aceitar cookies clicado com sucesso.")
                    except TimeoutException:
                        self.log_info("Botão de aceitar cookies não encontrado. Continuando...")
                    except NoSuchElementException:
                        self.log_info("Botão de aceitar cookies não existe. Continuando...")

                    initial_files = set(os.listdir(self.download_dir))

                    try:
                        download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
                        download_button.click()
                        time.sleep(3)

                        zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"

                        download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
                        download_link.click()
                        self.log_info("Download iniciado...")
                    except Exception:
                        download_link = driver.find_element(By.XPATH, f"//*[@id='categoria_944']/div/div/ul/li[1]/a")
                        download_link.click()
                        self.log_info("Download iniciado...")

                    self.log_info("Aguardando a conclusão do download...")
                    downloaded_files = self._wait_for_download_to_complete(initial_files)

                    if not downloaded_files:
                        raise TimeoutException("Nenhum novo arquivo detectado após o download.")

                    downloaded_file = list(downloaded_files)[0]
                    self.log_info(f"Arquivo detectado: {downloaded_file}")

                    zip_path = os.path.join(self.download_dir, downloaded_file)

                finally:
                    driver.quit()
                    self.log_info("Driver encerrado.")

                if os.path.exists(zip_path):
                    self.clean_final_directory()
                    shutil.move(zip_path, self.final_dir)
                    moved_file_path = os.path.join(self.final_dir, downloaded_file)

                    with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                        zip_ref.extractall(self.final_dir)

                    os.remove(moved_file_path)
                    self.log_info("Arquivo de Orçamento Geral da União extraído e removido com sucesso!")

                break

            except Exception as e:
                retries += 1
                self.log_error(f"Erro durante a execução. Tentativa {retries}...", e)
                time.sleep(self.retry_delay)