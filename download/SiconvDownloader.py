import os
import time
import zipfile
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from .BaseDownloader import BaseDownloader
from functools import wraps

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_sinconv_log.txt'),
        logging.StreamHandler()
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
                    if attempts == max_attempts:
                        log_error(f'Todas as {max_attempts} tentativas falharam. Erro final: {str(e)}')
                        raise
                    logger.warning(f'Tentativa {attempts} falhou. Tentando novamente em {delay} segundos... Erro: {str(e)}')
                    time.sleep(delay)
        return wrapper
    return decorator

class SiconvDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    @retry(max_attempts=3, delay=60)
    def download(self):
        logger.info('Iniciando o processo de download Sinconv...')

        driver = None
        try:
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", self.download_dir)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.set_preference("pdfjs.disabled", True)

            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            wait = WebDriverWait(driver, 30)

            driver.get("https://repositorio.dados.gov.br/seges/detru/")
            logger.info('Página de download acessada...')

            try:
                download_link = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/pre/a[7]')))
                download_link.click()
                logger.info('Download iniciado...')
            except TimeoutException:
                raise Exception("Tempo limite excedido ao esperar pelo link de download.")
            except NoSuchElementException:
                raise Exception("O link de download não foi encontrado na página.")

            zip_path = os.path.join(self.download_dir, "siconv.zip")

            try:
                download_wait = WebDriverWait(driver, 600)  # 10 minutos de espera
                download_wait.until(lambda d: os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)))
                logger.info('Download concluído...')
            except TimeoutException:
                raise Exception("Tempo limite excedido ao aguardar o download do arquivo.")

        except WebDriverException as e:
            logger.error(f"Erro ao inicializar ou usar o WebDriver: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro durante o processo de download: {str(e)}")
            raise
        finally:
            if driver:
                driver.quit()
                logger.info('Navegador fechado...')

        logger.info('Iniciando processo de extração...')

        try:
            if os.path.exists(zip_path):
                destination_path = os.path.join(self.final_dir, "siconv.zip")
                
                if os.path.isfile(destination_path):
                    logger.info('O arquivo siconv.zip já existe no destino. Removendo arquivo existente...')
                    try:
                        os.remove(destination_path)
                    except PermissionError:
                        raise Exception("Não foi possível remover o arquivo existente. Verifique as permissões.")
                    except OSError as e:
                        raise Exception(f"Erro ao remover o arquivo existente: {str(e)}")

                try:
                    shutil.move(zip_path, self.final_dir)
                    logger.info(f'Arquivo movido para a pasta: {self.final_dir}')
                except shutil.Error as e:
                    raise Exception(f"Erro ao mover o arquivo: {str(e)}")
                
                moved_file_path = os.path.join(self.final_dir, "siconv.zip")
                
                try:
                    with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                        logger.info('Extraindo o zip...')
                        zip_ref.extractall(self.final_dir)
                except zipfile.BadZipFile:
                    raise Exception("O arquivo baixado não é um arquivo zip válido.")
                except PermissionError:
                    raise Exception("Não foi possível extrair o arquivo. Verifique as permissões da pasta de destino.")

                try:
                    logger.info('Deletando siconv.zip')
                    os.remove(moved_file_path)
                except PermissionError:
                    raise Exception("Não foi possível deletar o arquivo zip. Verifique as permissões.")
                except OSError as e:
                    raise Exception(f"Erro ao deletar o arquivo zip: {str(e)}")

                logger.info('Programa finalizado com sucesso!')
            else:
                raise FileNotFoundError(f"O arquivo zip não foi encontrado em {zip_path}")

        except Exception as e:
            logger.error(f"Erro durante o processo de extração e movimentação: {str(e)}")
            raise
