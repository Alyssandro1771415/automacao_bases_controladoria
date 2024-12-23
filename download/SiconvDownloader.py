from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from .BaseDownloader import BaseDownloader
import os
import shutil

class SiconvDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def is_download_completed(self, zip_path):
        return os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(os.path.dirname(zip_path)))

    @BaseDownloader.retry(max_attempts=3, delay=60)
    def download(self):
        self.logger.info('Iniciando o processo de download Sinconv...')
        self.logger.info(f"Diretório de download: {self.download_dir}")
        self.logger.info(f"Diretório final: {self.final_dir}")

        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference('browser.download.folderList', 2)
        options.set_preference('browser.download.dir', self.download_dir)
        options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/zip')
        options.set_preference('pdfjs.disabled', True)

        driver = None
        try:
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            wait = WebDriverWait(driver, 60)

            self.logger.info('Acessando a página de download...')
            driver.get('https://repositorio.dados.gov.br/seges/detru/')
            self.logger.info('Página de download acessada com sucesso.')

            download_attempts = 0
            max_download_attempts = 3
            while download_attempts < max_download_attempts:
                try:
                    self.logger.info('Procurando o link de download...')
                    download_link = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/pre/a[7]')))
                    self.logger.info('Link de download encontrado. Iniciando o download...')
                    download_link.click()
                except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                    download_attempts += 1
                    if download_attempts == max_download_attempts:
                        raise Exception(f'Falha ao encontrar ou clicar no link de download após {max_download_attempts} tentativas: {str(e)}')
                    self.logger.warning(f'Falha ao encontrar ou clicar no link de download. Tentativa {download_attempts} de {max_download_attempts}. Erro: {str(e)}')
                    continue

                zip_path = os.path.join(self.download_dir, 'siconv.zip')
                normalized_path = os.path.normpath(zip_path)
                self.logger.info(f"Caminho normalizado do arquivo zip: {normalized_path}")

                try:
                    self.logger.info('Aguardando o download ser concluído...')
                    self.wait_for_download('siconv.zip', max_wait_time=600)
                    self.logger.info('Download concluído com sucesso.')
                    break
                except TimeoutError:
                    download_attempts += 1
                    if download_attempts == max_download_attempts:
                        raise Exception('Tempo limite excedido ao aguardar o download do arquivo após múltiplas tentativas.')
                    self.logger.warning(f'Tempo limite excedido ao aguardar o download. Tentativa {download_attempts} de {max_download_attempts}. Reiniciando o download...')
                    if os.path.exists(normalized_path):
                        os.remove(normalized_path)
                    continue

            if download_attempts == max_download_attempts:
                raise Exception('Falha ao completar o download após múltiplas tentativas.')

            self.logger.info('Iniciando processo de extração...')
            self.extract_and_cleanup(normalized_path, 'siconv.zip', None, None)
            self.logger.info('Programa finalizado com sucesso!')

        except Exception as e:
            error_message = f'Erro durante o processo de download: {str(e)}'
            self.log_error(error_message)
            raise

        finally:
            if driver:
                driver.quit()
                self.logger.info('Navegador fechado.')