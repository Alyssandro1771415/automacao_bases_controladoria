import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader
from selenium.webdriver.common.keys import Keys
import pandas as pd

class PainelParlamentar(BaseDownloader):
    
    def __init__(self, download_dir, final_dir):
        super().__init__(download_dir, final_dir) 
    
    def _get_latest_file(self):
        files = os.listdir(self.download_dir)
        if not files:
            return None
        files_with_paths = [os.path.join(self.download_dir, f) for f in files]
        return max(files_with_paths, key=os.path.getctime)

    def _wait_for_download_to_start(self, timeout=30):
        initial_files = set(os.listdir(self.download_dir))
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            if new_files:
                return new_files.pop()
            time.sleep(1)

        raise TimeoutError("Nenhum novo arquivo detectado no tempo limite.")
        
    def download(self):
        self.setup_directories()

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)

        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://clusterqap2.economia.gov.br/extensions/painel-parlamentar/painel-parlamentar.html")
        time.sleep(10)
        
        try:
            # UF Beneficiário
            seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
            seletor_uf_beneficiario.click()
            
            uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            uf_beneficiario.click()
            uf_beneficiario.send_keys("PE")
            uf_beneficiario.send_keys(Keys.RETURN)
            time.sleep(2)
            ok_button_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_uf_beneficiario.click()
            
            # Natureza Jurídica
            seletor_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#pfmQYV_content > div > div')
            seletor_natureza_juridica.click()
            
            adm_publico_estadual = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            adm_publico_estadual.click()
            adm_publico_estadual.send_keys("ou do Distrito")
            adm_publico_estadual.send_keys(Keys.RETURN)
            
            time.sleep(10)

            adm_publico_estadual.send_keys("Empresa")
            adm_publico_estadual.send_keys(Keys.RETURN)
            time.sleep(10)
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
                elemento_atual = driver.find_element(By.CSS_SELECTOR, elemento)
                if elemento_atual.text in elementos_a_selecionar:
                    elemento_atual.click()
                    time.sleep(5)
                    elementos_a_selecionar.remove(elemento_atual.text)
                    
                    if len(elementos_a_selecionar) == 0:
                        break

            
            ok_button_modalidade = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_modalidade.click()
            
            time.sleep(20)
            
            download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
            download_database_button.click()
            print("Download iniciado...")

            # Aguarda o download começar e concluir
            downloaded_file = self._wait_for_download_to_start()
            print(f"Arquivo detectado: {downloaded_file}")

            file_path = os.path.join(self.download_dir, downloaded_file)
            while True:
                if not downloaded_file.endswith(('.part', '.crdownload')) and os.path.exists(file_path):
                    print(f"Download concluído! Arquivo: {file_path}")
                    break
                else:
                    print("Aguardando conclusão do download...")
                    time.sleep(5)

            # Renomeia o arquivo ao movê-lo para a pasta final
            new_filename = "Emendas.xlsx"  # Novo nome desejado para o arquivo
            final_path = os.path.join(self.final_dir, new_filename)

            self.clean_final_directory()

            # Renomeia e move o arquivo
            os.rename(file_path, final_path)
            print(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")


        finally:
            driver.quit()
            print("Driver encerrado.")