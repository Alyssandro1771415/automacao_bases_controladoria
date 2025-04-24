import os
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, SessionNotCreatedException
from .BaseDownloader import BaseDownloader

class PainelObras(BaseDownloader):

    def __init__(self, geckoDriver=None, retry_delay=5):
        super().__init__(geckoDriver=geckoDriver)
        self.retry_delay = retry_delay

    def _wait_for_download_to_complete(self, initial_files):
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files

            if new_files:
                downloaded_file = new_files.pop()
                if not downloaded_file.endswith('.part'):
                    return downloaded_file
                else:
                    self.log_info(f"Aguardando conclusão do download: {downloaded_file}")
            time.sleep(5)

    def download(self, browser="firefox"):
        retries = 0

        while True:
            driver = None
            try:
                title = "Painel de Obras - Pernambuco"
                self.log_info(f"{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}")

                self.setup_directories()
                initial_files = set(os.listdir(self.download_dir))

                driver = self.get_driver(browser)
                driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")

                # ATENÇÃO: Seletor do painel pode ter mudado!
                # Antes: 'text[data-label="PE"]'
                # Se o painel mudou de posição, talvez precise ajustar o seletor.
                # Exemplo: Se agora é o 5º painel, pode ser necessário usar um índice diferente ou outro atributo.
                # Sugestão: Use um seletor mais robusto, se possível.
                try:
                    # Aguarda o elemento de Pernambuco aparecer
                    uf_element = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
                    )
                    uf_element.click()

                    download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
                    download_button.click()
                    self.log_info("Download iniciado...")

                    downloaded_file = self._wait_for_download_to_complete(initial_files=initial_files)
                    self.log_info(f"Arquivo detectado: {downloaded_file}")

                    file_path = os.path.join(self.download_dir, downloaded_file)
                    file_downloaded = pd.read_excel(file_path, dtype=str, engine="openpyxl")

                    campos_porcentagem = ["Execução Física", "Execução Financeira"]

                    for campo in campos_porcentagem:
                        for index, row in file_downloaded.iterrows():
                            if str(row[campo]) != "-":
                                row[campo] = str(round(float(row[campo])*100, 2))+"%"

                    self.clean_final_directory()
                    csv_path = os.path.join(self.final_dir, "Obras.csv")
                    file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
                    self.log_info(f"Novo arquivo salvo em: {csv_path}")

                    os.remove(file_path)
                    break

                finally:
                    if driver:
                        driver.quit()
                    self.log_info("Driver encerrado.")

            except Exception as e:
                self.log_error(f"Erro durante a execução. Tentativa {retries + 1}...", e)
                if driver:
                    driver.quit()
                retries += 1
                time.sleep(self.retry_delay)