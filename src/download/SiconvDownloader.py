import os
import time
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader

class SiconvDownloader(BaseDownloader):

    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir)

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

    def download(self):
        print(f"\n\n\n\033[35;40m{'-'*10} Repositório de Dados GOV - SICONV {'-'*10}\033[0m\n\n\n")

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://repositorio.dados.gov.br/seges/detru/")
        time.sleep(10)

        initial_files = set(os.listdir(self.download_dir))

        try:
            download_link = driver.find_element(By.XPATH, '/html/body/pre/a[7]')
            download_link.click()
            print("Download iniciado...")

            downloaded_files = self._wait_for_download_to_complete(initial_files=initial_files)
            print(f"Arquivos detectados: {downloaded_files}")

        except TimeoutError as e:
            print(f"Erro: {e}. Reiniciando o download...")
            driver.quit()  # Fecha o navegador para liberar recursos
            self.download()  # Reinicia o processo de download
            return

        except Exception as e:
            print(f"Erro durante o download: {e}")
            driver.quit()
            return

        finally:
            if driver:
                driver.quit()

        print("Chegou na dezipagem")

        zip_path = os.path.join(self.download_dir, "siconv.zip")

        if os.path.exists(zip_path):
            file_path = os.path.join(self.download_dir, "siconv.zip")

            self.clean_final_directory()

            shutil.move(file_path, self.final_dir)
            print("Arquivo movido para a pasta: ", self.final_dir)

            moved_file_path = os.path.join(self.final_dir, "siconv.zip")

            try:
                with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                    print("Dezipando")
                    zip_ref.extractall(self.final_dir)
            except zipfile.BadZipFile as e:
                print(f"Erro ao descompactar o arquivo ZIP: {e}")
                return

            print("Deletando siconv.zip")
            os.remove(moved_file_path)
            print("Programa finalizado!")
        else:
            print("Arquivo ZIP não encontrado após o download.")
