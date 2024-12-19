import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from .BaseDownloader import BaseDownloader
from selenium.webdriver.common.keys import Keys

class PainelParlamentar(BaseDownloader):
    
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
            time.sleep(7)
            ok_button_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_natureza_juridica.click()
            
            # Modalidade
            seletor_modaliade = driver.find_element(By.CSS_SELECTOR, '#gPGwwUJ_content > div > div')
            seletor_modaliade.click()
            time.sleep(7)
            modalidade = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            modalidade_button = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div:nth-child(1) > div > button')
            modalidade_button.click()
            time.sleep(7)
            all_modalidades = driver.find_element(By.CSS_SELECTOR, '#moreMenuList > li:nth-child(1)')
            all_modalidades.click()
            time.sleep(7)
            modalidade.send_keys('especial')
            modalidade.send_keys(Keys.RETURN)
            time.sleep(7)
            ok_button_modalidade = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_modalidade.click()
            
            time.sleep(20)
            
            download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
            download_database_button.click()
            
        finally:
            time.sleep(10)
            #driver.quit()
            print("Driver encerrado.")