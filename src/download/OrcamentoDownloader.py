import os
import time
import shutil
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

# OK FUNCIONOU.
class OrcamentoDownloader(BaseDownloader):
    
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = retry_delay
        self.logger.info(f"Inicializado com retry_delay: {retry_delay}")

    @BaseDownloader.retry(max_attempts=3, delay=5)
    def download(self, browser="firefox"):
        title = "Orçamento Geral da União"
        self.logger.info(f"Iniciando download do {title}")
        print(f"\n\n\033[37;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n")

        self.setup_directories()
        self.logger.info(f"Usando navegador: {browser}")
        driver = self.get_driver(browser)

        try:
            self.logger.info("Navegando para a página de downloads da Caixa")
            driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
            self.logger.info("Página carregada com sucesso")

            # Aceitar cookies se necessário
            try:
                self.logger.info("Tentando aceitar cookies...")
                accept_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="adopt-accept-all-button"]'))
                )
                accept_button.click()
                self.logger.info("Botão de aceitar cookies clicado com sucesso")
                print("Botão de aceitar cookies clicado com sucesso.")
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.warning(f"Botão de aceitar cookies não encontrado ou não necessário")
                self.logger.debug(f"Detalhes da exceção: {str(e)}")
                print("Botão de aceitar cookies não encontrado ou não necessário.")

            # Aguardar e clicar no botão de categoria
            self.logger.info("Tentando clicar no botão de categoria 944...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']"))
            ).click()
            self.logger.info("Botão de categoria clicado com sucesso")
            time.sleep(3)
            self.logger.info("Aguardando 3 segundos para carregamento da categoria")

            initial_files = set(os.listdir(self.download_dir))
            self.logger.info(f"Arquivos iniciais no diretório de download: {len(initial_files)}")

            # Tentar encontrar o link de download
            try:
                zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"
                self.logger.info(f"Tentando encontrar link para arquivo: {zip_file_name}")
                download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
                self.logger.info(f"Link para arquivo específico encontrado: {zip_file_name}")
            except NoSuchElementException:
                self.logger.info("Arquivo específico não encontrado, tentando o primeiro link da categoria")
                download_link = driver.find_element(By.XPATH, "//*[@id='categoria_944']/div/div/ul/li[1]/a")
                self.logger.info(f"Usando primeiro link disponível: {download_link.get_attribute('href')}")

            download_link.click()
            self.logger.info("Link de download clicado")
            print("Download iniciado...")

            # Aguardar download concluir
            self.logger.info("Aguardando conclusão do download...")
            downloaded_files = self._wait_for_download_to_complete(initial_files)
            if not downloaded_files:
                self.logger.error("Tempo limite excedido. Nenhum arquivo baixado.")
                raise TimeoutException("Nenhum novo arquivo detectado após o download.")

            downloaded_file = list(downloaded_files)[0]
            zip_path = os.path.join(self.download_dir, downloaded_file)
            self.logger.info(f"Download concluído. Arquivo baixado: {downloaded_file}")

        except Exception as e:
            self.logger.error(f"Erro durante o download: {type(e).__name__}: {str(e)}")
            raise
        finally:
            driver.quit()
            self.logger.info("Driver encerrado")
            print("Driver encerrado.")

        # Mover e extrair arquivos
        if os.path.exists(zip_path):
            self.logger.info(f"Arquivo ZIP encontrado: {zip_path}")
            self.clean_final_directory()
            
            self.logger.info(f"Movendo arquivo para diretório final: {self.final_dir}")
            shutil.move(zip_path, self.final_dir)
            final_zip_path = os.path.join(self.final_dir, downloaded_file)
            self.logger.info(f"Arquivo movido para: {final_zip_path}")
            
            self.logger.info("Iniciando extração do arquivo ZIP")
            self.extract_zip(final_zip_path)
        else:
            self.logger.error(f"Arquivo ZIP não encontrado: {zip_path}")

    def extract_zip(self, zip_path):
        """Extrai o conteúdo de um arquivo ZIP e o remove após a extração."""
        import zipfile
        
        self.logger.info(f"Extraindo arquivo ZIP: {zip_path}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.logger.info(f"Arquivos contidos no ZIP: {len(file_list)}")
                self.logger.debug(f"Lista de arquivos: {file_list}")
                zip_ref.extractall(self.final_dir)
                self.logger.info(f"Extração concluída no diretório: {self.final_dir}")
            
            os.remove(zip_path)
            self.logger.info(f"Arquivo ZIP removido após extração: {zip_path}")
            print("Arquivo de Orçamento Geral da União extraído e removido com sucesso!")
        except Exception as e:
            self.logger.error(f"Erro ao extrair arquivo ZIP: {type(e).__name__}: {str(e)}")
            raise

