import os
import time
import zipfile
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import datetime
from .BaseDownloader import BaseDownloader
from functools import wraps
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuração de logging melhorada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_portal_convenio_log.txt'),  # Grava no arquivo
        logging.StreamHandler()  # Exibe no console
    ]
)

logger = logging.getLogger()

# erros mais limpos no logging.
def log_error(message):
    logger.error(message)

def retry(max_attempts=3, delay=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        log_error(f'Todas as {max_attempts} tentativas falharam. Erro final: {str(e)}')
                        raise
                    logger.warning(f'Tentativa {attempts} falhou. Realizando outra tentativa em {delay} segundos..')
                    time.sleep(delay)
        return wrapper
    return decorator

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def find_most_recent_download_link(self, driver):
        wait = WebDriverWait(driver, 10)
        try:
            download_links = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'BD_Gestores_')]")))
        except TimeoutException:
            logger.info('Não foi possível encontrar links de download.')
            return None, None

        latest_date = datetime.date(1900, 1, 1)
        latest_link = None
        for link in download_links:
            href = link.get_attribute('href')
            date_str = href.split('BD_Gestores_')[1].split('.zip')[0]
            date = datetime.datetime.strptime(date_str, '%d_%m_%Y').date()
            if date > latest_date:
                latest_date = date
                latest_link = link

        return latest_link, latest_date

    @retry(max_attempts=3, delay=60)
    def download(self):
        self.setup_directories()
        logger.info('Iniciando o processo de download e busca - OGU..')

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)

        try:
            driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
            logger.info('Página de download acessada..')

            download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")))
            download_button.click()
            logger.info('Botão de download clicado...')

            latest_link, latest_date = self.find_most_recent_download_link(driver)
            if latest_link:
                zip_file_name = f"BD_Gestores_{latest_date.strftime('%d_%m_%Y')}.zip"
                zip_path = os.path.join(self.download_dir, zip_file_name)
                latest_link.click()
                logger.info(f'Iniciando download de {zip_file_name}...')
            else:
                log_error('Não foi possível encontrar um link de download válido.')
                return

            # Espera pelo download do arquivo
            download_wait = WebDriverWait(driver, 300)  # 5 minutos de timeout = espera no maximo 5 minutos para o download
            download_wait.until(lambda d: os.path.exists(zip_path) and 
                                not any(file.endswith('.part') or file.endswith('.crdownload') 
                                        for file in os.listdir(self.download_dir)))
            logger.info('Download concluído...')

        # tratamento de exceções
        except TimeoutException as e:
            log_error(f'Timeout ao esperar por um elemento: {str(e)}')
            raise
        except NoSuchElementException as e:
            log_error(f'Elemento não encontrado: {str(e)}')
            raise
        except Exception as e:
            log_error(f'Erro inesperado durante o download: {str(e)}')
            raise
        finally:
            driver.quit()
            logger.info('Navegador fechado...')

        if os.path.exists(zip_path):
            shutil.move(zip_path, self.final_dir)
            moved_file_path = os.path.join(self.final_dir, zip_file_name)
            logger.info(f'Arquivo zip movido para {moved_file_path}')
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.final_dir)
                logger.info('Arquivo zip extraído...')
                
            os.remove(moved_file_path)
            logger.info('Arquivo de Orçamento Geral da União extraído e removido com sucesso!')
        else:
            log_error(f'Arquivo zip não encontrado: {zip_path}')