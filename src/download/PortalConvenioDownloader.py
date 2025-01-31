import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from .BaseDownloader import BaseDownloader

class PortalConvenioDownloader(BaseDownloader):
    
    def __init__(self, geckoDriver, download_dir, final_dir):
        super().__init__(geckoDriver, download_dir, final_dir)
        

    def download(self):
        
        title = "Portal da Transparência - Convênio"
        print(f"\n\n\n\033[31;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")
        
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)
        options.add_argument("--headless") #


        driver = webdriver.Firefox(service=self.geckoDriver, options=options)
        driver.get("https://portaldatransparencia.gov.br/download-de-dados/convenios")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='arquivo-unico']//a"))
        )
        
        try:
            click_accept_cookies = driver.find_element(By.CSS_SELECTOR, "#accept-all-btn")
            
            try:
                click_accept_cookies = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#accept-all-btn"))
                )
                click_accept_cookies.click()
                print("Botão de aceitar cookies clicado com sucesso.")
            except TimeoutException:
                print("Botão de aceitar cookies não encontrado. Continuando...")
            except NoSuchElementException:
                print("Botão de aceitar cookies não existe. Continuando...")
                    
            download_link = driver.find_element(By.XPATH, "//div[@id='arquivo-unico']//a")

            initial_files = set(os.listdir(self.download_dir))

            download_link.click()
            print("Download iniciado...")

            zip_file = self._wait_for_download_to_complete(initial_files=initial_files)
            
            zip_path = os.path.join(self.download_dir,  str(next(iter(zip_file))))

            if zip_path:
                self.extract_and_cleanup(zip_path, "Convenios.csv", r".*_Convenios_OrdensBancarias", r".*_Convenios.csv")

        finally:
            driver.quit()
        
        
    def _wait_for_download_to_complete(self, initial_files):
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        previous_size = 0
        max_retries = 10
        retries = 0
        
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files

            temp_files = [
                file for file in new_files
                if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
            ]

            if temp_files:
                temp_file_path = os.path.join(self.download_dir, temp_files[0])
                try:
                    current_size = os.path.getsize(temp_file_path)
                    if current_size == previous_size:
                        retries += 1
                        if retries >= max_retries:
                            raise TimeoutError("Download parece estar pausado ou com erro.")
                    else:
                        retries = 0
                        previous_size = current_size
                except FileNotFoundError:
                    pass

            else:
                break

            time.sleep(5)

        return new_files

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_patters):
        
        for file in os.listdir(self.final_dir):
            os.remove(os.path.join(self.final_dir, file))
            
        shutil.move(zip_path, self.final_dir)
        print("Arquivo movido para a pasta: ", self.final_dir)
        moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
        with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
            print("Dezipando")
            zip_ref.extractall(self.final_dir)
                        
        print("Deletando .zip")
        os.remove(moved_file_path)
        
        files = zip_ref.namelist()
        file_to_delete = next((file for file in files if re.match(delete_pattern, os.path.basename(file))), None)
        file_to_rename = next((file for file in files if re.match(rename_patters, os.path.basename(file))), None)        

        print(file_to_delete, file_to_rename)
        
        if file_to_delete:
            os.remove(os.path.join(self.final_dir, file_to_delete))
            print(f"Arquivo '{file_to_delete}' deletado com sucesso!")
        
        if file_to_rename:
                os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
                print(f"Arquivo '{file_to_rename}' renomeado com sucesso para '{rename_to}'!")