from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .BaseDownloader import BaseDownloader

class PortalConvenioDownloader(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)
        
    @BaseDownloader.retry(max_attempts=3, delay=60)
    def download(self):
        self.setup_directories()
        self.logger.info('Iniciando processo de download Portal Convênio...')

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = None
        try:
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            wait = WebDriverWait(driver, 10)

            driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")
            self.logger.info('Página de download acessada...')

            try:
                botao_cookie = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "accept-all-btn"))
                )
                botao_cookie.click()
            except Exception as e:
                self.logger.warning(f'O banner de cookies não foi encontrado ou já estava fechado: {str(e)}')

            download_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='arquivo-unico']//a")))
            download_link.click()
            self.logger.info('Download Iniciado...')

            zip_file_name = r".*_Convenios.zip"
            zip_path = self.wait_for_download(zip_file_name)
            
            if zip_path:
                self.extract_and_cleanup(zip_path, "Convenios.csv", r".*_Convenios_OrdensBancarias", r".*_Convenios.csv")
            else:
                raise Exception("Falha no download do arquivo ZIP.")

        except Exception as e:
            error_message = f"Erro durante o download: {type(e).__name__}: {str(e)}"
            self.log_error(error_message)
            raise

        finally:
            if driver:
                driver.quit()
                self.logger.info('Navegador fechado.')