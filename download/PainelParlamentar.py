import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader
from selenium.webdriver.common.keys import Keys
import pandas as pd
import hashlib

class PainelParlamentar(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir) 
    
    def _get_latest_file(self):
        files = os.listdir(self.download_dir)
        if not files:
            return None
        files_with_paths = [os.path.join(self.download_dir, f) for f in files]
        return max(files_with_paths, key=os.path.getctime)

    def _wait_for_download_to_complete(self, initial_files):
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            if new_files:
                downloaded_file = new_files.pop()
                
                if not downloaded_file.endswith('.part'):
                    return downloaded_file
                else:
                    print(f"Aguardando conclusão do download: {downloaded_file}")
            
            time.sleep(5)
    
    def _get_element_html(self, driver, xpath: str) -> str:
        """
        Obtém o HTML ou conteúdo de um elemento específico com base no XPath.
        """
        try:
            element: WebElement = driver.find_element(By.XPATH, xpath)
            return element.get_attribute('outerHTML')
        except Exception as e:
            print(f"Erro ao obter o HTML do elemento: {e}")
            return ""

    def _compare_element_html(self, html1: str, html2: str) -> bool:
        """
        Compara o conteúdo de dois HTMLs de elementos específicos.
        Retorna True se forem idênticos, caso contrário, False.
        """
        hash1 = hashlib.md5(html1.encode('utf-8')).hexdigest()
        hash2 = hashlib.md5(html2.encode('utf-8')).hexdigest()
        return hash1 == hash2
        
    def download(self):
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("intl.accept_languages", "pt-BR,pt,en-US,en")
        options.set_preference("browser.helperApps.alwaysAsk.force", False)
        options.set_preference("browser.download.encoding", "utf-8")


        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://clusterqap2.economia.gov.br/extensions/painel-parlamentar/painel-parlamentar.html")
        time.sleep(10)
        
        xpath_first_graph_elemento = '//*[@id="HtUCmV_content"]'
        xpath_second_graph_elemento = '//*[@id="wWjwYjq_content"]'
        
        try:
            # UF Beneficiário
            seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
            seletor_uf_beneficiario.click()
            
            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            uf_beneficiario.click()
            uf_beneficiario.send_keys("PE")
            uf_beneficiario.send_keys(Keys.RETURN)
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            time.sleep(2)
            ok_button_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_uf_beneficiario.click()
            
            # Natureza Jurídica
            seletor_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#pfmQYV_content > div > div')
            seletor_natureza_juridica.click()
            
            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            adm_publico_estadual = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            adm_publico_estadual.click()
            adm_publico_estadual.send_keys("ou do Distrito")
            adm_publico_estadual.send_keys(Keys.RETURN)
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            adm_publico_estadual.send_keys("Empresa")
            adm_publico_estadual.send_keys(Keys.RETURN)
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

            ok_button_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_natureza_juridica.click()
            
            # Modalidade
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
                    while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                        time.sleep(5)
                        first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                        second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
                    elementos_a_selecionar.remove(elemento_atual.text)
                    
                    if len(elementos_a_selecionar) == 0:
                        break
     
            ok_button_modalidade = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_modalidade.click()
            
            xpath_table_elemento =  '//*[@id="myTabContent"]'
            html_table_before = self._get_element_html(driver, xpath_table_elemento)
            
            initial_files = set(os.listdir(self.download_dir))
            
            html_table_after = self._get_element_html(driver, xpath_table_elemento)
            
            while self._compare_element_html(html_table_before, html_table_after) == True:
                print("Aguardando preparação do arquivo...")
                html_table_after = self._get_element_html(driver, xpath_table_elemento)    
                time.sleep(5)
            
            download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
            download_database_button.click()
            print("Download iniciado...")

            time.sleep(5)
            downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
            print(f"Arquivo detectado: {downloaded_file}")

            file_path = os.path.join(self.download_dir, downloaded_file)

            new_filename = "Emendas.xlsx"
            final_path = os.path.join(self.final_dir, new_filename)

            self.clean_final_directory()

            os.rename(file_path, final_path)
            print(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")

        finally:
            driver.quit()
            print("Driver encerrado.")