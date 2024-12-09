import os
import time
import zipfile
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import datetime
from .BaseDownloader import BaseDownloader
from functools import wraps

# config logging:
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s ', 
                        handlers=[logging.FileHandler('download_ogu_log.txt'), logging.StreamHandler()])

# implementação do loop para tentativas.
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
                        logging.error(f'Todas as {max_attempts} falharam. Erro final: {str(e)}')
                        raise
                    logging.warning(f'Tentativa {attempts} falhou. Realizando outra tentativa em {delay} segundos..')
        return wrapper
    return decorator

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def find_most_recent_download_link(self, driver):
        wait = WebDriverWait(driver, 10)
        try:
            download_links = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'BD_Gestores_')]")))
        except FileNotFoundError:
            logging.info('Não foi possível encontrar links de download.')
            return None

        latest_date = datetime.date(1900, 1, 1)
        latest_link = None
        for link in download_links:
            href = link.get_attribute('href')
            date_str = href.split('BD_Gestores_')[1].split('.zip')[0]
            date = datetime.datetime.strptime(date_str, '%d_%m_%Y').date()
            if date > latest_date:
                latest_date = date
                latest_link = link

        return latest_link, latest_date

    @retry(max_attempts=3, delay=60)
    def download(self):
        self.setup_directories()
        logging.info(f'Iniciando o processo de download e busca - OGU..')

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
        logging.info(f'Página de download acessada..')
        time.sleep(5)

        try:
            download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
            download_button.click()
            logging.info(f'Botão de download clicado...')
            time.sleep(3)

            latest_link, latest_date = self.find_most_recent_download_link(driver)
            if latest_link:
                zip_file_name = f"BD_Gestores_{latest_date.strftime('%d_%m_%Y')}.zip"
                zip_path = os.path.join(self.download_dir, zip_file_name)
                latest_link.click()
                logging.info(f'Iniciando download de {zip_file_name}...')
            else:
                logging.error('Não foi possível encontrar um link de download válido.')
                return

            while True:
                if os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    logging.info(f'Download iniciado...')
                    break
                else:
                    logging.info('Aguardando o download do arquivo zip...')
                    time.sleep(15)
        
        except Exception as e:
            logging.exception('Erro durante o download...')
            raise

        
        finally:
            driver.quit()
            logging.info(f'Navegador fechado...')

        if os.path.exists(zip_path):
            shutil.move(zip_path, self.final_dir)
            moved_file_path = os.path.join(self.final_dir, zip_file_name)
            logging.info(f'Arquivo zip movido para {moved_file_path}')
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.final_dir)
                logging.info(f'arquivo zip extraído...')
                
            os.remove(moved_file_path)
            logging.info(f'Arquivo de Orçamento Geral da União extraído e removido com sucesso!')