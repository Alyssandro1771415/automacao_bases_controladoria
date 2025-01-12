from abc import ABC, abstractmethod
import os
import logging
from functools import wraps
import time
import glob
import re
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager

class BaseDownloader(ABC):
    
    def __init__(self, download_dir, final_dir) -> None:
        self.download_dir = download_dir
        self.final_dir = final_dir
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('downloader_log.txt'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger()

    def log_error(self, message):
        self.logger.error(message)

    @staticmethod
    def retry(max_attempts=3, delay=60):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, browser="firefox", **kwargs):
                browsers = ["firefox", "edge", "chrome"]
                for current_browser in browsers:
                    attempts = 0
                    while attempts < max_attempts:
                        try:
                            return func(self, *args, browser=current_browser, **kwargs)
                        except Exception as e:
                            attempts += 1
                            error_message = f'Tentativa {attempts} com {current_browser} falhou. Erro: {type(e).__name__}: {str(e)}'
                            self.log_error(error_message)
                            if attempts == max_attempts:
                                if current_browser != browsers[-1]:
                                    self.logger.info(f"Todas as tentativas com {current_browser} falharam. Tentando com o próximo navegador...")
                                    break
                                else:
                                    final_error = f'Todas as tentativas com todos os navegadores falharam.'
                                    self.log_error(final_error)
                                    raise
                            self.logger.info(f'Tentando novamente com {current_browser} em {delay} segundos...')
                            time.sleep(delay)
            return wrapper
        return decorator
    
    def get_driver(self, browser):
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", self.download_dir)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.set_preference("pdfjs.disabled", True)
            return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        elif browser == "edge":
            options = webdriver.EdgeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
        elif browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        else:
            raise ValueError("Navegador não suportado")

    @abstractmethod
    def download(self, browser="firefox"):
        pass
        
    def setup_directories(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)

    def wait_for_download(self, zip_file_name, max_wait_time=600):
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            zip_files = glob.glob(os.path.join(self.download_dir, "*.zip"))
            matching_files = [file for file in zip_files if re.match(zip_file_name, os.path.basename(file))]
            
            if matching_files:
                zip_path = matching_files[0]
                if not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    self.logger.info('Download concluído...')
                    return zip_path
            
            self.logger.info('Aguardando o download do arquivo zip...')
            time.sleep(15)

        error_message = "Timeout: O download não foi concluído no tempo esperado."
        self.log_error(error_message)
        raise TimeoutError(error_message)

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_pattern):
        try:
            shutil.move(zip_path, self.final_dir)
            self.logger.info(f'Arquivo movido para a pasta: {self.final_dir}')
            moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                self.logger.info('Extraindo o zip...')
                zip_ref.extractall(self.final_dir)
                        
            self.logger.info('Deletando .zip')
            os.remove(moved_file_path)
        
            files = zip_ref.namelist()
            file_to_delete = next((file for file in files if delete_pattern and re.match(delete_pattern, os.path.basename(file))), None)
            file_to_rename = next((file for file in files if rename_pattern and re.match(rename_pattern, os.path.basename(file))), None)        

            self.logger.info(f"Arquivos encontrados - Para deletar: {file_to_delete}, Para renomear: {file_to_rename}")
        
            if file_to_delete:
                os.remove(os.path.join(self.final_dir, file_to_delete))
                self.logger.info(f'Arquivo "{file_to_delete}" deletado com sucesso!')
        
            if file_to_rename and rename_to:
                os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
                self.logger.info(f'Arquivo "{file_to_rename}" renomeado com sucesso para "{rename_to}"!')

        except Exception as e:
            error_message = f"Erro durante a extração e limpeza: {type(e).__name__}: {str(e)}"
            self.log_error(error_message)
            raise

    def check_directory_permissions(self, directory):
        if not os.access(directory, os.W_OK):
            error_message = f"Sem permissão de escrita no diretório: {directory}"
            self.log_error(error_message)
            raise PermissionError(error_message)
