import os
import time
import hashlib
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

class PainelEmendas(BaseDownloader):

    def __init__(self, geckoDriver=None, retry_delay=5):
        super().__init__(geckoDriver=geckoDriver)
        self.retry_delay = retry_delay

    def _get_latest_file(self):
        files = os.listdir(self.download_dir)
        if not files:
            return None
        files_with_paths = [os.path.join(self.download_dir, f) for f in files]
        return max(files_with_paths, key=os.path.getctime)

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

    def _get_element_html(self, driver, xpath: str) -> str:
        try:
            element: WebElement = driver.find_element(By.XPATH, xpath)
            return element.get_attribute('outerHTML')
        except Exception as e:
            self.log_error(f"Erro ao obter o HTML do elemento: {e}")
            return ""

    def _compare_element_html(self, html1: str, html2: str) -> bool:
        hash1 = hashlib.md5(html1.encode('utf-8')).hexdigest()
        hash2 = hashlib.md5(html2.encode('utf-8')).hexdigest()
        return hash1 == hash2

    def download(self, browser="firefox"):
        retries = 0

        while True:
            driver = None
            try:
                title = "Painel Emendas - Pernambuco"
                self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

                self.setup_directories()

                driver = self.get_driver(browser)
                driver.get("https://dd-publico.serpro.gov.br/extensions/parlamentar/parlamentar.html")  

                # Aguarde o carregamento inicial do painel
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "fltr-uf-beneficiario"))
                )

                # UF Beneficiário
                self.log_info("UF Beneficiária...")
                seletor_uf_beneficiario = driver.find_element(By.ID, "fltr-uf-beneficiario")
                seletor_uf_beneficiario.click()
                opcao_pe = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'PE')]"))
                )
                opcao_pe.click()
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

                # Natureza Jurídica
                self.log_info("Natureza Jurídica...")
                seletor_natureza_juridica = driver.find_element(By.ID, "fltr-natureza-juridica-beneficiario")
                seletor_natureza_juridica.click()
                for valor in ["Administração Pública Estadual", "SEM/EPP"]:
                    opcao = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{valor}')]"))
                    )
                    opcao.click()
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

                # Modalidade: Todas (se necessário, senão pule)
                # modalidade = driver.find_element(By.ID, "fltr-modalidade")
                # modalidade.click()
                # driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

                # Filtros adicionais: Excluir situações
                self.log_info("Excluindo situações indesejadas...")
                btn_filtros_adicionais = driver.find_element(By.ID, "btn-filtros-adicionais")
                btn_filtros_adicionais.click()
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "modal-filtros-adicionais"))
                )
                situacao = driver.find_element(By.ID, "fltr-situacao-convenio")
                situacao.click()
                for valor in [
                    "Anulado",
                    "Rescindido",
                    "Prestação contas aprovada",
                    "Prestação contas aprovada com ressalva",
                    "prestação de contas concluída"
                ]:
                    opcao = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{valor}')]"))
                    )
                    opcao.click()
                btn_fechar = driver.find_element(By.XPATH, "//button[contains(text(), 'Fechar')]")
                btn_fechar.click()

                # Aguarde a tabela carregar e exporte os dados
                self.log_info("Exportando dados...")
                btn_exportar = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btn-export-tbl-ciente"))
                )
                initial_files = set(os.listdir(self.download_dir))
                btn_exportar.click()

                # Aguarda download
                downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
                self.log_info(f"Arquivo detectado: {downloaded_file}")

                file_path = os.path.join(self.download_dir, str(next(iter(downloaded_file))))
                new_filename = "Emendas.xlsx"
                final_path = os.path.join(self.final_dir, new_filename)

                self.clean_final_directory()
                os.rename(file_path, final_path)
                self.log_info(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")

                break

            except Exception as e:
                self.log_error(f"Erro durante a execução: {e}")
                retries += 1
                self.log_info(f"Tentativa {retries}. Tentando novamente em {self.retry_delay} segundos...")
                time.sleep(self.retry_delay)
            finally:
                if 'driver' in locals() and driver:
                    driver.quit()
                    self.log_info("Driver encerrado.")