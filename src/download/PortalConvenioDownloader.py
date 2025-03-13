import os
import time
import zipfile
import shutil
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

# OK FUNCIONOU.
class PortalConvenioDownloader(BaseDownloader):
    
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = retry_delay
        self.logger.info(f"Inicializado com retry_delay: {self.retry_delay}")
    
    @BaseDownloader.retry(max_attempts=3, delay=5)
    def download(self, browser="firefox"):
       
        title = "Portal da Transparência - Convênio"
        self.logger.info(f"Iniciando download do {title}")
        print(f"\n\n\n\033[31;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")
        
        self.setup_directories()
        self.logger.info("Diretórios configurados")
        
        
        driver = self.get_driver(browser)
        self.logger.info(f"Driver {browser} inicializado")
        
        try:
            
            self.logger.info("Navegando para a página do Portal da Transparência - Convênios")
            driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")
            
            
            self.logger.info("Aguardando carregamento da página")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='arquivo-unico']//a"))
            )
            self.logger.info("Página carregada com sucesso")
            
            
            try:
                self.logger.info("Tentando aceitar cookies...")
                accept_cookies = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#accept-all-btn"))
                )
                accept_cookies.click()
                self.logger.info("Botão de aceitar cookies clicado com sucesso")
                print("Botão de aceitar cookies clicado com sucesso.")
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.warning(f"Botão de aceitar cookies não encontrado: {str(e)}")
                print("Botão de aceitar cookies não encontrado. Continuando...")
            
            # Iniciando download
            download_link = driver.find_element(By.XPATH, "//div[@id='arquivo-unico']//a")
            initial_files = set(os.listdir(self.download_dir))
            self.logger.info(f"Arquivos iniciais no diretório de download: {len(initial_files)}")
            
            download_link.click()
            self.logger.info("Link de download clicado")
            print("Download iniciado...")
            
            # Aguardando download completar
            self.logger.info("Aguardando conclusão do download")
            downloaded_files = self._wait_for_download_to_complete(initial_files)
            
            if not downloaded_files:
                self.logger.error("Tempo limite excedido. Nenhum arquivo baixado.")
                raise TimeoutException("Nenhum novo arquivo detectado após o download.")
            
            # Processando arquivo baixado
            downloaded_file = next(iter(downloaded_files))
            zip_path = os.path.join(self.download_dir, downloaded_file)
            self.logger.info(f"Download concluído. Arquivo baixado: {downloaded_file}")
            
            # Extraindo e limpando
            self.logger.info("Iniciando extração e limpeza do arquivo")
            self.extract_and_cleanup(zip_path, "Convenios.csv", r".*_Convenios_OrdensBancarias", r".*_Convenios.csv")
            self.logger.info("Extração e limpeza concluídas com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante o download: {type(e).__name__}: {str(e)}")
            raise
        finally:
            driver.quit()
            self.logger.info("Driver encerrado")
            print("Driver encerrado.")
    
    def _wait_for_download_to_complete(self, initial_files, timeout=120):
        
        self.logger.info(f"Aguardando download completar (timeout: {timeout}s)")
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        retries = 0
        max_retries = 10
        previous_size = 0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            self.logger.debug(f"Arquivos novos detectados: {new_files}")
            
            temp_files = [
                file for file in new_files if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
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
    
    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_pattern):
      
        self.logger.info(f"Iniciando extração e limpeza do arquivo: {zip_path}")
        
        
        self.clean_final_directory()
        self.logger.info("Diretório final limpo")
        
        
        shutil.move(zip_path, self.final_dir)
        self.logger.info(f"Arquivo movido para a pasta: {self.final_dir}")
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
        
        
        self.logger.info(f"Extraindo arquivo ZIP: {moved_file_path}")
        try:
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.logger.info(f"Arquivos contidos no ZIP: {len(file_list)}")
                self.logger.debug(f"Lista de arquivos: {file_list}")
                zip_ref.extractall(self.final_dir)
                self.logger.info(f"Extração concluída no diretório: {self.final_dir}")
        except Exception as e:
            self.logger.error(f"Erro ao extrair arquivo ZIP: {type(e).__name__}: {str(e)}")
            raise
        
        
        os.remove(moved_file_path)
        self.logger.info("Arquivo ZIP deletado após extração")
        print("Arquivo zip deletado após extração.")
        
        # Processando arquivos extraídos
        files = os.listdir(self.final_dir)
        self.logger.info(f"Arquivos extraídos: {files}")
        
        # Identificando e excluindo arquivo desnecessário
        file_to_delete = next((file for file in files if re.match(delete_pattern, file)), None)
        if file_to_delete:
            os.remove(os.path.join(self.final_dir, file_to_delete))
            self.logger.info(f"Arquivo '{file_to_delete}' deletado com sucesso")
            print(f"Arquivo '{file_to_delete}' deletado com sucesso!")
        else:
            self.logger.warning(f"Nenhum arquivo encontrado para o padrão de exclusão: {delete_pattern}")
        
        # Identificando e renomeando arquivo principal
        file_to_rename = next((file for file in files if re.match(rename_pattern, file)), None)
        if file_to_rename:
            os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
            self.logger.info(f"Arquivo '{file_to_rename}' renomeado para '{rename_to}'")
            print(f"Arquivo '{file_to_rename}' renomeado para '{rename_to}'!")
        else:
            self.logger.warning(f"Nenhum arquivo encontrado para o padrão de renomeação: {rename_pattern}")

