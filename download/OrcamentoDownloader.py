# import os
# import time
# import zipfile
# # implementação de logging
# import logging 
# import shutil
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.firefox import GeckoDriverManager
# import datetime
# from .BaseDownloader import BaseDownloader
# # para implementar a retry
# from functools import wraps

# #configurando logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s ', 
#                     handlers=[logging.FileHandler("download_OGU_log.txt"), logging.StreamHandler()]) 

# def retry(max_attempts=3, delay=60):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             attempts = 0
#             while attempts < max_attempts:
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as error:
#                     attempts+= 1
#                     if attempts == max_attempts:
#                         logging.error(f"Todas as {max_attempts} falharam. Erro final: {str(error)}")
#                         raise
#                     logging.warning(f"Tentativa {attempts} falhou. Realizando outra tentaiva em {delay} segundos...")
#                     time.sleep(delay)
#         return wrapper
#     return decorator


# class OrcamentoDownloader(BaseDownloader):

#     def __init__(self, download_dir, final_dir):
#         super().__init__(download_dir, final_dir)

#     @retry(max_attempts=5, delay=60)
#     def download(self):
#         logging.info("Iniciando o processo de download do OGU - Caixa...")
#         self.setup_directories()

#         options = webdriver.FirefoxOptions()
#         options.set_preference("browser.download.folderList", 2)
#         options.set_preference("browser.download.dir", self.download_dir)
#         options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
#         options.set_preference("pdfjs.disabled", True)

#         driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
#         driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
#         logging.info("Página de downloads acessada...")

#         try:
#             botao_coockie = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.ID, "accept-all-btn"))
#             )
#             botao_coockie.click()
#             logging.info("Banner de cookies fechado com sucesso...")
#         except:
#             logging.info("O banner de cookies não foi encontrado ou já estava fechado..")

#         time.sleep(5)

#         zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"
#         zip_path = os.path.join(self.download_dir, zip_file_name)

#         try:
#             download_button = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']"))
#             )
#             download_button.click()
#             logging.info("Botão de download clicado...")
#             time.sleep(3)

#             download_link = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{zip_file_name}')]"))
#             )
#             download_link.click()
#             logging.info("Download iniciado...")
            
#             timeout = time.time() + 60 #1 minuto a partir deste momento
#             while True:
#                 if os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
#                     logging.info("Download concluído...")
#                     break
#                 else:
                    
#                     logging.info("Aguardando o download do arquivo ZIP...")
#                     time.sleep(15)
        
#         except Exception as error:
#             logging.exception("Erro durante o download...")
#             raise
        
#         finally:
#             driver.quit()
#             logging.info("Navegador fechado...")

#         if os.path.exists(zip_path):
#             shutil.move(zip_path, self.final_dir)
#             moved_file_path = os.path.join(self.final_dir, zip_file_name)
#             logging.inofo(f"Arquivo zip movido para {moved_file_path}")
            
#             with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
#                 zip_ref.extractall(self.final_dir)
#                 logging.info("Arquivo ZIP extraído...")
                
#             os.remove(moved_file_path)
#             logging.info("Arquivo ZIP removido após extração...")
#             logging.info("Arquivo de Orçamento Geral da União extraido e removido com sucesso!")
        
#         else:
#             logging.error(f"Arquivo {zip_path} não encontrado após o download..")

import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import datetime
from .BaseDownloader import BaseDownloader

class OrcamentoDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

    def download(self):
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://www.caixa.gov.br/site/paginas/downloads.aspx")
        time.sleep(5)

        zip_file_name = f"BD_Gestores_{datetime.date.today().strftime('%d_%m_%Y')}.zip"
        zip_path = os.path.join(self.download_dir, zip_file_name)

        try:
            download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'botao-categoria') and @data-categoria='944']")
            download_button.click()
            time.sleep(3)

            download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{zip_file_name}')]")
            download_link.click()
            print("Download iniciado...")
            
            while True:
                if os.path.exists(zip_path) and not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    print("Download concluído!")
                    break
                else:
                    
                    print("Aguardando o download do arquivo zip...")
                    time.sleep(15)
        
        finally:
            driver.quit()

        if os.path.exists(zip_path):
            shutil.move(zip_path, self.final_dir)
            moved_file_path = os.path.join(self.final_dir, zip_file_name)
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.final_dir)
                
            os.remove(moved_file_path)
            print("Arquivo de Orçamento Geral da União extraido e removido com sucesso!")