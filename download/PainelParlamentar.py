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
            seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
            seletor_uf_beneficiario.click()
            
            uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-8934-Grid-root.njs-8934-Grid-container.njs-8934-Grid-item.njs-8934-Grid-direction-xs-column.css-otmy2t > div.njs-8934-Grid-root.njs-8934-Grid-item.css-bb28t2 > div > input')
            uf_beneficiario.click()
            uf_beneficiario.send_keys("PE")
            uf_beneficiario.send_keys(Keys.RETURN)
            
        finally:
            time.sleep(5)
            driver.quit()
            print("Driver encerrado.")