import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import re
import glob
import logging
from functools import wraps
from .BaseDownloader import BaseDownloader

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_portal_convenio_log.txt'),  # Grava no arquivo
        logging.StreamHandler()  # Exibe no console
    ]
)

logger = logging.getLogger()

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
                    logger.warning(f'Tentativa {attempts} falhou. Erro: {type(e).__name__}: {str(e)}')
                    if attempts == max_attempts:
                        log_error(f'Todas as {max_attempts} tentativas falharam. Erro final: {type(e).__name__}: {str(e)}')
                        raise
                    logger.info(f'Tentando novamente em {delay} segundos...')
                    time.sleep(delay)
        return wrapper
    return decorator

class PortalConvenioDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)
        
    @retry(max_attempts=3, delay=60)
    def download(self):
        self.setup_directories()
        logger.info('Iniciando processo de download Portal Convênio...')

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        try:
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            wait = WebDriverWait(driver, 10)

            driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")
            logger.info('Página de download acessada...')

            try:
                botao_cookie = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "accept-all-btn"))
            )
                botao_cookie.click()
            except:
                log_error('O banner de cookies não foi encontrado ou já estava fechado...')

            download_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='arquivo-unico']//a")))
            download_link.click()
            logger.info('Download Iniciado...')

            zip_file_name = r".*_Convenios.zip"
            zip_path = self.wait_for_download(zip_file_name, driver)
            
            if zip_path:
                self.extract_and_cleanup(zip_path, "Convenios.csv", r".*_Convenios_OrdensBancarias", r".*_Convenios.csv")
            else:
                log_error("Falha no download do arquivo ZIP.")

        except TimeoutException as e:
            log_error(f"Timeout ao esperar por um elemento: {str(e)}")
        except NoSuchElementException as e:
            log_error(f"Elemento não encontrado: {str(e)}")
        except WebDriverException as e:
            log_error(f"Erro do WebDriver: {str(e)}")
        except Exception as e:
            log_error(f"Erro inesperado: {str(e)}")
        finally:
            if 'driver' in locals():
                driver.quit()
                logger.info('Navegador fechado.')
        
    def wait_for_download(self, zip_file_name, driver):
        max_wait_time = 300  # 5 minutos
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            zip_files = glob.glob(os.path.join(self.download_dir, "*.zip"))
            matching_files = [file for file in zip_files if re.match(zip_file_name, os.path.basename(file))]
            
            if matching_files:
                zip_path = matching_files[0]
                if not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    logger.info('Download concluído...')
                    return zip_path
            
            logger.info('Aguardando o download do arquivo zip...')
            time.sleep(15)

        log_error("Timeout: O download não foi concluído no tempo esperado.")
        return None

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_pattern):
        try:
            shutil.move(zip_path, self.final_dir)
            logger.info(f'Arquivo movido para a pasta: {self.final_dir}')
            moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                logger.info('Extraindo o zip...')
                zip_ref.extractall(self.final_dir)
                        
            logger.info('Deletando .zip')
            os.remove(moved_file_path)
        
            files = zip_ref.namelist()
            file_to_delete = next((file for file in files if re.match(delete_pattern, os.path.basename(file))), None)
            file_to_rename = next((file for file in files if re.match(rename_pattern, os.path.basename(file))), None)        

            logger.info(f"Arquivos encontrados - Para deletar: {file_to_delete}, Para renomear: {file_to_rename}")
        
            if file_to_delete:
                os.remove(os.path.join(self.final_dir, file_to_delete))
                logger.info(f'Arquivo "{file_to_delete}" deletado com sucesso!')
        
            if file_to_rename:
                os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
                logger.info(f'Arquivo "{file_to_rename}" renomeado com sucesso para "{rename_to}"!')

        except FileNotFoundError as e:
            log_error(f"Arquivo não encontrado: {str(e)}")
        except PermissionError as e:
            log_error(f"Erro de permissão ao manipular arquivos: {str(e)}")
        except zipfile.BadZipFile as e:
            log_error(f"Arquivo ZIP corrompido ou inválido: {str(e)}")
        except Exception as e:
            log_error(f"Erro inesperado durante a extração e limpeza: {str(e)}")