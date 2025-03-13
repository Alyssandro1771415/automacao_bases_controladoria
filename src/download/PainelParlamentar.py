import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader
import hashlib

class PainelParlamentar(BaseDownloader):
    def __init__(self, geckoDriver, download_dir, final_dir):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = 5

    def _get_element_html(self, driver, xpath: str) -> str:
        try:
            element = driver.find_element(By.XPATH, xpath)
            return element.get_attribute('outerHTML')
        except Exception as e:
            self.logger.error(f"Erro ao obter o HTML do elemento: {e}")
            return ""

    def _compare_element_html(self, html1: str, html2: str) -> bool:
        hash1 = hashlib.md5(html1.encode('utf-8')).hexdigest()
        hash2 = hashlib.md5(html2.encode('utf-8')).hexdigest()
        return hash1 == hash2

    def _wait_for_element_update(self, driver, xpath, timeout=60):
        html_before = self._get_element_html(driver, xpath)
        start_time = time.time()
        while time.time() - start_time < timeout:
            html_after = self._get_element_html(driver, xpath)
            if not self._compare_element_html(html_before, html_after):
                return
            time.sleep(5)
        raise TimeoutException("Element did not update within the specified timeout")

    def download(self, driver):
        try:
            self.logger.info("Iniciando download do Painel Parlamentar - Pernambuco")
            
            driver.get("https://qlik-publico.paineis.gov.br/extensions/parlamentar/parlamentar.html")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#sCBrmk_content > div > div > div > div > div > div > div > div > div.MuiGrid-root.MuiGrid-container.css-q0qbej > h6"))
            )
            
            # UF Beneficiário
            self._select_uf_beneficiario(driver)
            
            # Natureza Jurídica
            self._select_natureza_juridica(driver)
            
            # Modalidade
            self._select_modalidade(driver)
            
            # Download do arquivo
            self._download_file(driver)
            
            return self._get_latest_file()

        except Exception as e:
            self.logger.error(f"Erro durante o download: {e}")
            raise

    def _select_uf_beneficiario(self, driver):
        self.logger.info("Selecionando UF Beneficiária...")
        seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
        seletor_uf_beneficiario.click()
        
        uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
        uf_beneficiario.click()
        uf_beneficiario.send_keys("PE")
        uf_beneficiario.send_keys(Keys.RETURN)
        
        self._wait_for_element_update(driver, '//*[@id="HtUCmV_content"]')
        
        ok_button = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
        ok_button.click()

    def _select_natureza_juridica(self, driver):
        self.logger.info("Selecionando Natureza Jurídica...")
        seletor_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#pfmQYV_content > div > div')
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088'))
        )
        seletor_natureza_juridica.click()
        
        adm_publico_estadual = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
        adm_publico_estadual.click()
        adm_publico_estadual.send_keys("ou do Distrito")
        adm_publico_estadual.send_keys(Keys.RETURN)
        
        self._wait_for_element_update(driver, '//*[@id="HtUCmV_content"]')
        
        adm_publico_estadual.send_keys("Empresa")
        adm_publico_estadual.send_keys(Keys.RETURN)
        
        self._wait_for_element_update(driver, '//*[@id="HtUCmV_content"]')
        
        ok_button = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
        ok_button.click()

    def _select_modalidade(self, driver):
        self.logger.info("Selecionando Modalidade...")
        seletor_modaliade = driver.find_element(By.CSS_SELECTOR, '#gPGwwUJ_content > div > div')
        seletor_modaliade.click()
        time.sleep(10)
 
        elementos_a_selecionar = ["CONVENIO", "CONTRATO DE REPASSE", "CONVENIO OU CONTRATO DE REPASSE", "TERMO DE COMPROMISSO"]
        all_elements = [f"div.RowColumn-barContainer:nth-child({i})" for i in range(1, 9)]
        
        for elemento in all_elements:
            elemento_atual = driver.find_element(By.CSS_SELECTOR, elemento)
            if elemento_atual.text in elementos_a_selecionar:
                elemento_atual.click()
                self._wait_for_element_update(driver, '//*[@id="HtUCmV_content"]')
                elementos_a_selecionar.remove(elemento_atual.text)
                
                if not elementos_a_selecionar:
                    break
     
        ok_button = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
        ok_button.click()

    def _download_file(self, driver):
        self.logger.info("Iniciando download do arquivo...")
        self._wait_for_element_update(driver, '//*[@id="myTabContent"]')
        
        download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
        download_database_button.click()
        
        downloaded_file = self._wait_for_download_to_complete(set(os.listdir(self.download_dir)))
        self.logger.info(f"Arquivo detectado: {downloaded_file}")
        
        file_path = os.path.join(self.download_dir, str(next(iter(downloaded_file))))
        new_filename = "Emendas.xlsx"
        final_path = os.path.join(self.final_dir, new_filename)
        
        self.clean_final_directory()
        os.rename(file_path, final_path)
        self.logger.info(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")

print("Processo finalizado.")