# BaseDownloader.py

from abc import ABC, abstractmethod
import os
import time
import zipfile
import shutil
import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BaseDownloader(ABC):
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5, max_retries=3):
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

    def clean_final_directory(self):
        for file in os.listdir(self.final_dir):
            file_path = os.path.join(self.final_dir, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                self.logger.info(f"Arquivo '{file}' removido da pasta final.")

    
    def get_driver(self, browser="firefox"):
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", self.download_dir)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.set_preference("pdfjs.disabled", True)
            options.add_argument("--headless")
            return webdriver.Firefox(service=self.geckoDriver, options = options)
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

    # def _setup_webdriver(self):
    #     options = webdriver.FirefoxOptions()
    #     options.set_preference("browser.download.folderList", 2)
    #     options.set_preference("browser.download.dir", self.download_dir)
    #     options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    #     options.set_preference("pdfjs.disabled", True)
    #     options.add_argument("--headless")
    #     return webdriver.Firefox(service=self.geckoDriver, options=options)

    def _wait_for_download_to_complete(self, initial_files):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        previous_size = 0
        retries = 0
        
        while retries < self.max_retries:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            temp_files = [file for file in new_files if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)]
            
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

    def _get_element_html(self, driver, xpath: str) -> str:
        try:
            element = driver.find_element(By.XPATH, xpath)
            return element.get_attribute('outerHTML')
        except Exception as e:
            self.logger.error(f"Erro ao obter o HTML do elemento: {e}")
            return ""

    def _compare_element_html(self, html1: str, html2: str) -> bool:
        import hashlib
        hash1 = hashlib.md5(html1.encode('utf-8')).hexdigest()
        hash2 = hashlib.md5(html2.encode('utf-8')).hexdigest()
        return hash1 == hash2

    @abstractmethod
    def download(self, browser="firefox"):
        pass
def run(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.setup_directories()
                self.clean_final_directory()
                self.download()
                break
            except (TimeoutException, NoSuchElementException) as e:
                retries += 1
                self.logger.error(f"Erro de timeout ou elemento não encontrado: {e}. Tentativa {retries} de {self.max_retries}...")
            except WebDriverException as e:
                retries += 1
                self.logger.error(f"Erro do WebDriver: {e}. Tentativa {retries} de {self.max_retries}...")
            except Exception as e:
                retries += 1
                self.logger.error(f"Erro inesperado: {e}. Tentativa {retries} de {self.max_retries}...")
            
            if retries < self.max_retries:
                time.sleep(self.retry_delay)
            else:
                self.logger.error("Número máximo de tentativas atingido. Abortando.")