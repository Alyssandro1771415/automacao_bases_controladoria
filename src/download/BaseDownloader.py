from abc import ABC, abstractmethod
import os
import time
import logging
from functools import wraps
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class BaseDownloader(ABC):
    def __init__(self, geckoDriver, download_dir, final_dir) -> None:
        self.download_dir = download_dir
        self.final_dir = final_dir
        self.geckoDriver = geckoDriver
        self.setup_logging()
        
        # Configurar diretórios após setup do logging
        self.setup_directories()
        self.logger.info(f"Inicializado com diretório de download: {self.download_dir} e diretório final: {self.final_dir}")
    
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

    def log_error(self, message, exception=None):
        if exception:
            self.logger.error(f"{message}: {type(exception).__name__}: {str(exception)}")
        else:
            self.logger.error(message)
    
    # Adicionando métodos auxiliares para compatibilidade com o código existente
    def log_info(self, message):
        self.logger.info(message)
    
    def log_warning(self, message):
        self.logger.warning(message)
    
    def log_debug(self, message):
        self.logger.debug(message)

    def setup_directories(self):
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        self.logger.info("Diretórios configurados com sucesso")

    def clean_final_directory(self):
        for file in os.listdir(self.final_dir):
            file_path = os.path.join(self.final_dir, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                self.logger.info(f"Arquivo '{file}' removido da pasta final.")

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

    @abstractmethod
    def download(self, browser="firefox"):
        pass

    def get_driver(self, browser):
        self.logger.info(f"Inicializando driver para navegador: {browser}")
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", self.download_dir)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.set_preference("pdfjs.disabled", True)
            options.add_argument("--headless")
            driver = webdriver.Firefox(service=self.geckoDriver, options=options)
            self.logger.info("Driver Firefox inicializado com sucesso")
            return driver
        elif browser == "edge":
            options = webdriver.EdgeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            options.add_argument("--headless")
            driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
            self.logger.info("Driver Edge inicializado com sucesso")
            return driver
        elif browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            options.add_argument("--headless")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            self.logger.info("Driver Chrome inicializado com sucesso")
            return driver
        else:
            self.logger.error(f"Navegador não suportado: {browser}")
            raise ValueError("Navegador não suportado")

    def _wait_for_download_to_complete(self, initial_files, timeout=120):
        self.logger.info(f"Aguardando download completar (timeout: {timeout}s)")
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            if new_files:
                self.logger.info(f"Download concluído. Novos arquivos: {new_files}")
                return new_files  
            time.sleep(1)
        self.logger.error("Tempo limite para download excedido")
        return set()

