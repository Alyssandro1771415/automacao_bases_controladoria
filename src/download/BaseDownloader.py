# BaseDownloader.py
from abc import ABC, abstractmethod
import os
import time
import zipfile
import shutil
import logging
import re
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from src.utils import utils

class BaseDownloader(ABC):
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5, max_retries=5):
        self.download_dir = download_dir
        self.final_dir = final_dir
        self.geckoDriver = geckoDriver
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_directories(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)
        utils.clean_database_download_directory(self.download_dir)

    def clean_final_directory(self):
        utils.clean_database_download_directory(self.final_dir)
        self.logger.info("Pasta final limpa e pronta para iniciar o processo.")

    def get_driver(self, browser="firefox"):
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", self.download_dir)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.set_preference("pdfjs.disabled", True)
            options.add_argument("--headless")
            return webdriver.Firefox(service=self.geckoDriver, options=options)
        elif browser == "edge":
            options = webdriver.EdgeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            options.add_argument("--headless")
            return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
        elif browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            options.add_argument("--headless")
            return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        else:
            raise ValueError("Navegador não suportado")
        

    def _wait_for_download_to_complete(self, initial_files, timeout=300):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            completed_files = [f for f in new_files if not any(f.endswith(ext) for ext in TEMPORARY_EXTENSIONS)]
            
            if completed_files:
                return completed_files
            
            time.sleep(1)
        
        return None

    def _check_file_size(self, file_path, min_size=1):
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size >= min_size:
                self.logger.info(f"Arquivo baixado com sucesso: {file_path} (Tamanho: {file_size} bytes)")
                return True
            else:
                self.logger.warning(f"Arquivo baixado está vazio ou muito pequeno: {file_path} (Tamanho: {file_size} bytes)")
                return False
        else:
            self.logger.error(f"Arquivo não encontrado: {file_path}")
            return False

    def extract_and_cleanup(self, zip_path, rename_to=None, delete_pattern=None, rename_pattern=None):
        self.clean_final_directory()
        
        shutil.move(zip_path, self.final_dir)
        self.logger.info(f"Arquivo movido para a pasta: {self.final_dir}")
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
        
        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.final_dir)
        
        os.remove(moved_file_path)
        self.logger.info("Arquivo zip deletado após extração.")
        
        if delete_pattern:
            for file in os.listdir(self.final_dir):
                if re.match(delete_pattern, file):
                    os.remove(os.path.join(self.final_dir, file))
                    self.logger.info(f"Arquivo '{file}' deletado com sucesso!")
        
        if rename_pattern and rename_to:
            for file in os.listdir(self.final_dir):
                if re.match(rename_pattern, file):
                    os.rename(os.path.join(self.final_dir, file), os.path.join(self.final_dir, rename_to))
                    self.logger.info(f"Arquivo '{file}' renomeado para '{rename_to}'!")

    @abstractmethod
    def download(self, driver):
        pass

    def run(self):
        browsers = ["firefox", "edge", "chrome"]
        for browser in browsers:
            retries = 0
            while retries < self.max_retries:
                driver = None
                try:
                    self.setup_directories()
                    self.clean_final_directory()
                    driver = self.get_driver(browser)
                    driver.set_page_load_timeout(300)
                    self.logger.info(f"Tentando download com o navegador: {browser}")
                    downloaded_file = self.download(driver)
                    
                    if downloaded_file and self._check_file_size(downloaded_file):
                        self.logger.info(f"Download concluído com sucesso usando {browser}.")
                        return
                    else:
                        raise Exception("Arquivo baixado inválido ou vazio.")
                    
                except (TimeoutException, NoSuchElementException) as e:
                    retries += 1
                    self.logger.error(f"Erro de timeout ou elemento não encontrado: {e}. Tentativa {retries} de {self.max_retries} com {browser}...")
                except WebDriverException as e:
                    retries += 1
                    self.logger.error(f"Erro do WebDriver: {e}. Tentativa {retries} de {self.max_retries} com {browser}...")
                except Exception as e:
                    retries += 1
                    self.logger.error(f"Erro inesperado: {e}. Tentativa {retries} de {self.max_retries} com {browser}...")
                finally:
                    if driver:
                        driver.quit()
                
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Número máximo de tentativas atingido com {browser}. Tentando próximo navegador...")
                    break
        
        self.logger.error("Falha ao baixar o arquivo após tentar com todos os navegadores.")
        raise Exception("Falha ao baixar o arquivo após várias tentativas com todos os navegadores")