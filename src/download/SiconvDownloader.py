import os
import re
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from .BaseDownloader import BaseDownloader
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# tempo de espera curto
class SiconvDownloader(BaseDownloader):

    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = retry_delay
        self.logger.info(f"Inicializado com retry_delay: {self.retry_delay}")

    def _wait_for_download_to_complete(self, initial_files, timeout=600):
        self.logger.info(f"Aguardando download completar (timeout: {timeout}s)")
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        previous_size = 0
        max_retries = 10
        retries = 0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            self.logger.debug(f"Arquivos novos detectados: {new_files}")

            temp_files = [
                file for file in new_files
                if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
            ]

            if temp_files:
                temp_file_path = os.path.join(self.download_dir, temp_files[0])
                try:
                    current_size = os.path.getsize(temp_file_path)
                    self.logger.debug(f"Arquivo temporário: {temp_files[0]}, tamanho atual: {current_size}")
                    if current_size == previous_size:
                        retries += 1
                        self.logger.warning(f"Tamanho do arquivo não mudou. Tentativa {retries}/{max_retries}")
                        if retries >= max_retries:
                            self.logger.error("Download parece estar pausado ou com erro após várias tentativas")
                            raise TimeoutError("Download parece estar pausado ou com erro.")
                    else:
                        retries = 0
                        previous_size = current_size
                        self.logger.debug(f"Tamanho do arquivo atualizado: {current_size}")
                except FileNotFoundError:
                    self.logger.warning(f"Arquivo temporário não encontrado: {temp_files[0]}")
                    pass
            else:
                if new_files:
                    self.logger.info(f"Download concluído. Novos arquivos: {new_files}")
                    return new_files
            
            time.sleep(5)
        
        self.logger.error("Tempo limite para download excedido")
        return set()
    
    def extract_and_cleanup(self, zip_path):
        
        self.logger.info(f"Iniciando extração e limpeza do arquivo: {zip_path}")
        
        # Limpando diretório final
        self.clean_final_directory()
        self.logger.info("Diretório final limpo")
        
        # Movendo arquivo ZIP para diretório final
        shutil.move(zip_path, self.final_dir)
        self.logger.info(f"Arquivo movido para a pasta: {self.final_dir}")
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
        
        # Extraindo arquivo ZIP
        self.logger.info(f"Extraindo arquivo ZIP: {moved_file_path}")
        try:
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.logger.info(f"Arquivos contidos no ZIP: {len(file_list)}")
                self.logger.debug(f"Lista de arquivos: {file_list}")
                zip_ref.extractall(self.final_dir)
                self.logger.info(f"Extração concluída no diretório: {self.final_dir}")
                print("Dezipando")
        except Exception as e:
            self.logger.error(f"Erro ao extrair arquivo ZIP: {type(e).__name__}: {str(e)}")
            raise
        
        # Removendo arquivo ZIP após extração
        os.remove(moved_file_path)
        self.logger.info("Arquivo ZIP deletado após extração")
        print("Deletando .zip")
    
    def wait_for_element(self, driver, locator_value, timeout=100, poll_frequency=0.5):
       
        try:
            self.logger.info(f"Aguardando elemento: {locator_value} com timeout de {timeout}s...")
            print(f"Aguardando elemento: {locator_value} com timeout de {timeout}s...")
            element = WebDriverWait(driver, timeout, poll_frequency).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locator_value))
            )
            self.logger.info(f"Elemento encontrado: {locator_value}")
            print(f"Elemento encontrado: {locator_value}")
            return element
        except TimeoutException as e:
            self.logger.error(f"Elemento {locator_value} não encontrado após {timeout} segundos.")
            print(f"Elemento {locator_value} não encontrado após {timeout} segundos.")
            raise

    @BaseDownloader.retry(max_attempts=3, delay=5)
    def download(self, browser="firefox"):
        
        title = "Repositório de Dados GOV - SICONV"
        self.logger.info(f"Iniciando download do {title}")
        print(f"\n\n\n\033[35;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")

        self.setup_directories()
        self.logger.info("Diretórios configurados")

        # Configuração personalizada do Firefox para este downloader específico
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("browser.download.manager.showAlertOnComplete", False)
        options.set_preference("browser.download.manager.focusWhenStarting", False)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.tabs.warnOnClose", False)
        options.set_preference("browser.tabs.warnOnCloseOtherTabs", False)
        options.set_preference("browser.tabs.warnOnOpen", False)
        options.set_preference("browser.download.manager.quitBehavior", 2)
        options.set_preference("browser.download.folderList", 2)
        options.add_argument("--headless")

        driver = webdriver.Firefox(service=self.geckoDriver, options=options)
        self.logger.info("Driver Firefox inicializado com configurações personalizadas")
        
        try:
            # Navegação para a página
            self.logger.info("Navegando para o repositório de dados do SICONV")
            driver.get("https://repositorio.dados.gov.br/seges/detru/")
            
            
            self.logger.info("Aguardando carregamento da página")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "body > pre > a:nth-child(7)"))
            )
            self.logger.info("Página carregada com sucesso")

            
            initial_files = set(os.listdir(self.download_dir))
            self.logger.info(f"Arquivos iniciais no diretório de download: {len(initial_files)}")
            
            # Verificando diretório final
            if not os.path.exists(self.final_dir):
                os.mkdir(self.final_dir)
                self.logger.info(f"Diretório final criado: {self.final_dir}")

            # Iniciando download
            download_link = driver.find_element(By.XPATH, '/html/body/pre/a[7]')
            download_link.click()
            self.logger.info("Link de download clicado")
            print("Download iniciado...")

            # Aguardando download
            self.logger.info("Aguardando conclusão do download")
            downloaded_files = self._wait_for_download_to_complete(initial_files=initial_files)
            
            if not downloaded_files:
                self.logger.error("Nenhum arquivo baixado")
                raise TimeoutException("Nenhum novo arquivo detectado após o download.")
                
            self.logger.info(f"Arquivos detectados: {downloaded_files}")
            print(f"Arquivos detectados: {downloaded_files}")

            # Processando arquivo baixado
            zip_path = os.path.join(self.download_dir, next(iter(downloaded_files)))
            self.logger.info(f"Caminho do arquivo baixado: {zip_path}")

            if os.path.exists(zip_path):
                self.logger.info(f"Arquivo ZIP encontrado: {zip_path}")
                self.extract_and_cleanup(zip_path)
                self.logger.info("Processamento do arquivo concluído com sucesso")
            else:
                self.logger.error(f"Arquivo ZIP não encontrado: {zip_path}")
                raise FileNotFoundError(f"Arquivo ZIP não encontrado: {zip_path}")

        except Exception as e:
            self.logger.error(f"Erro durante o download: {type(e).__name__}: {str(e)}")
            raise
        finally:
            if 'driver' in locals() and driver:
                driver.quit()
                self.logger.info("Driver encerrado")

