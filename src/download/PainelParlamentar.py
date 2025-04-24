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

class PainelParlamentar(BaseDownloader):

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
                title = "Painel Parlamentar - Pernambuco"
                self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

                self.setup_directories()

                driver = self.get_driver(browser)
                driver.get("https://qlik-publico.paineis.gov.br/extensions/parlamentar/parlamentar.html")

                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#sCBrmk_content > div > div > div > div > div > div > div > div > div.MuiGrid-root.MuiGrid-container.css-q0qbej > h6"))
                )

                xpath_first_graph_elemento = '//*[@id="HtUCmV_content"]'
                xpath_second_graph_elemento = '//*[@id="wWjwYjq_content"]'

                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, 'qv-ui-blocker'))
                    )
                    self.log_info("Bloqueador removido.")
                except TimeoutException:
                    self.log_info("Bloqueador não encontrado. Continuando...")
                except NoSuchElementException:
                    self.log_info("Bloqueador não existe. Continuando...")

                # UF Beneficiário
                self.log_info("UF Beneficiária...")

                seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
                seletor_uf_beneficiario.click()

                first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
                uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
                uf_beneficiario.click()
                uf_beneficiario.send_keys("PE")
                uf_beneficiario.send_keys(Keys.RETURN)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                while self._compare_element_html(first_html_before, first_html_after) and self._compare_element_html(second_html_before, second_html_after):
                    time.sleep(5)
                    first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                    second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                time.sleep(2)
                ok_button_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
                ok_button_uf_beneficiario.click()

                # Natureza Jurídica
                self.log_info("Natureza Jurídica...")

                seletor_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#pfmQYV_content > div > div')
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088'))
                )
                seletor_natureza_juridica.click()

                first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
                adm_publico_estadual = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
                adm_publico_estadual.click()
                adm_publico_estadual.send_keys("ou do Distrito")
                adm_publico_estadual.send_keys(Keys.RETURN)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                while self._compare_element_html(first_html_before, first_html_after) and self._compare_element_html(second_html_before, second_html_after):
                    time.sleep(5)
                    first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                    second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
                adm_publico_estadual.send_keys("Empresa")
                adm_publico_estadual.send_keys(Keys.RETURN)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                while self._compare_element_html(first_html_before, first_html_after) and self._compare_element_html(second_html_before, second_html_after):
                    time.sleep(5)
                    first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                    second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

                ok_button_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
                ok_button_natureza_juridica.click()

                # Modalidade
                self.log_info("Modalidade...")

                seletor_modaliade = driver.find_element(By.CSS_SELECTOR, '#gPGwwUJ_content > div > div')
                seletor_modaliade.click()
                time.sleep(10)

                elementos_a_selecionar = ["CONVENIO", "CONTRATO DE REPASSE", "CONVENIO OU CONTRATO DE REPASSE", "TERMO DE COMPROMISSO"]
                all_elements = [
                    "div.RowColumn-barContainer:nth-child(1)",
                    "div.RowColumn-barContainer:nth-child(2)",
                    "div.RowColumn-barContainer:nth-child(3)",
                    "div.RowColumn-barContainer:nth-child(4)",
                    "div.RowColumn-barContainer:nth-child(5)",
                    "div.RowColumn-barContainer:nth-child(6)",
                    "div.RowColumn-barContainer:nth-child(7)",
                    "div.RowColumn-barContainer:nth-child(8)"
                ]

                for elemento in all_elements:
                    time.sleep(5)
                    first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
                    second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)

                    elemento_atual = driver.find_element(By.CSS_SELECTOR, elemento)
                    if elemento_atual.text in elementos_a_selecionar:
                        elemento_atual.click()
                        first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                        second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
                        while self._compare_element_html(first_html_before, first_html_after) and self._compare_element_html(second_html_before, second_html_after):
                            time.sleep(5)
                            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
                        elementos_a_selecionar.remove(elemento_atual.text)

                        if len(elementos_a_selecionar) == 0:
                            break

                xpath_table_elemento = '//*[@id="myTabContent"]'
                html_table_before = self._get_element_html(driver, xpath_table_elemento)

                ok_button_modalidade = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
                ok_button_modalidade.click()

                initial_files = set(os.listdir(self.download_dir))

                html_table_after = self._get_element_html(driver, xpath_table_elemento)

                while self._compare_element_html(html_table_before, html_table_after):
                    self.log_info("Aguardando preparação do arquivo...")
                    html_table_after = self._get_element_html(driver, xpath_table_elemento)
                    time.sleep(5)

                download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
                download_database_button.click()
                self.log_info("Download iniciado...")

                time.sleep(5)
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