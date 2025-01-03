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
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
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

def check_directory_permissions(directory):
    if not os.access(directory, os.W_OK):
        logger.error(f"Sem permissão de escrita no diretório: {directory}")
        raise PermissionError(f"Sem permissão de escrita no diretório: {directory}")

class SiconvDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)
        self.ensure_directories_exist()

    def ensure_directories_exist(self):
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        logger.info(f"Diretórios criados/verificados: {self.download_dir}, {self.final_dir}")

    def is_download_completed(self, zip_path):
        return os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(os.path.dirname(zip_path)))

    @retry(max_attempts=3, delay=60)
    def download(self):
        logger.info('Iniciando o processo de download Sinconv...')
        logger.info(f"Diretório de download: {self.download_dir}")
        logger.info(f"Diretório final: {self.final_dir}")

        self.ensure_directories_exist()
        check_directory_permissions(self.download_dir)
        check_directory_permissions(self.final_dir)

        options = webdriver.FirefoxOptions()
        options.set_preference('browser.download.folderList', 2)
        options.set_preference('browser.download.dir', self.download_dir)
        options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/zip')
        options.set_preference('pdfjs.disabled', True)

        try:
            with webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options) as driver:
                wait = WebDriverWait(driver, 60)

                logger.info('Acessando a página de download...')
                driver.get('https://repositorio.dados.gov.br/seges/detru/')
                logger.info('Página de download acessada com sucesso.')

                download_attempts = 0
                max_download_attempts = 3
                while download_attempts < max_download_attempts:
                    try:
                        logger.info('Procurando o link de download...')
                        download_link = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/pre/a[7]')))
                        logger.info('Link de download encontrado. Iniciando o download...')
                        download_link.click()
                    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                        download_attempts += 1
                        if download_attempts == max_download_attempts:
                            raise Exception(f'Falha ao encontrar ou clicar no link de download após {max_download_attempts} tentativas: {str(e)}')
                        logger.warning(f'Falha ao encontrar ou clicar no link de download. Tentativa {download_attempts} de {max_download_attempts}. Erro: {str(e)}')
                        continue

                    zip_path = os.path.join(self.download_dir, 'siconv.zip')
                    normalized_path = os.path.normpath(zip_path)
                    logger.info(f"Caminho normalizado do arquivo zip: {normalized_path}")

                    try:
                        logger.info('Aguardando o download ser concluído...')
                        download_wait = WebDriverWait(driver, 600)  # 10 minutos de espera
                        download_wait.until(lambda d: self.is_download_completed(normalized_path))
                        logger.info('Download concluído com sucesso.')
                        break
                    except TimeoutException:
                        download_attempts += 1
                        if download_attempts == max_download_attempts:
                            raise Exception('Tempo limite excedido ao aguardar o download do arquivo após múltiplas tentativas.')
                        logger.warning(f'Tempo limite excedido ao aguardar o download. Tentativa {download_attempts} de {max_download_attempts}. Reiniciando o download...')
                        if os.path.exists(normalized_path):
                            os.remove(normalized_path)
                        continue

                if download_attempts == max_download_attempts:
                    raise Exception('Falha ao completar o download após múltiplas tentativas.')

        except WebDriverException as e:
            logger.error(f'Erro ao inicializar ou usar o WebDriver: {str(e)}')
            raise
        except Exception as e:
            logger.error(f'Erro durante o processo de download: {str(e)}')
            raise

        logger.info('Iniciando processo de extração...')

        try:
            if os.path.exists(normalized_path):
                destination_path = os.path.join(self.final_dir, 'siconv.zip')
                
                if os.path.isfile(destination_path):
                    logger.info('O arquivo siconv.zip já existe no destino. Removendo arquivo existente...')
                    try:
                        os.remove(destination_path)
                        logger.info('Arquivo existente removido com sucesso.')
                    except PermissionError:
                        raise Exception('Não foi possível remover o arquivo existente. Verifique as permissões.')
                    except OSError as e:
                        raise Exception(f'Erro ao remover o arquivo existente: {str(e)}')

                try:
                    logger.info(f'Movendo o arquivo para a pasta: {self.final_dir}')
                    shutil.move(normalized_path, self.final_dir)
                    logger.info('Arquivo movido com sucesso.')
                except shutil.Error as e:
                    raise Exception(f'Erro ao mover o arquivo: {str(e)}')
                
                moved_file_path = os.path.join(self.final_dir, 'siconv.zip')
                
                try:
                    logger.info('Iniciando a extração do arquivo zip...')
                    with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                        zip_ref.extractall(self.final_dir)
                    logger.info('Extração concluída com sucesso.')
                except zipfile.BadZipFile:
                    raise Exception('O arquivo baixado não é um arquivo zip válido.')
                except PermissionError:
                    raise Exception('Não foi possível extrair o arquivo. Verifique as permissões da pasta de destino.')

                try:
                    logger.info('Deletando o arquivo siconv.zip...')
                    os.remove(moved_file_path)
                    logger.info('Arquivo zip deletado com sucesso.')
                except PermissionError:
                    raise Exception('Não foi possível deletar o arquivo zip. Verifique as permissões.')
                except OSError as e:
                    raise Exception(f'Erro ao deletar o arquivo zip: {str(e)}')

                logger.info('Programa finalizado com sucesso!')
            else:
                raise FileNotFoundError(f'O arquivo zip não foi encontrado em {normalized_path}')

        except Exception as e:
            logger.error(f'Erro durante o processo de extração e movimentação: {str(e)}')
            raise