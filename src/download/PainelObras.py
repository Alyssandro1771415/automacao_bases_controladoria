import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader

class PainelObras(BaseDownloader):
    def download(self, driver):
        try:
            title = "Painel de Obras - Pernambuco"
            self.logger.info(f"\n\n\n{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\n\n\n")
            
            driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")
            
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
            )
            
            uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
            uf_element.click()
            
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]'))
            )
            initial_files = set(os.listdir(self.download_dir))
            download_button.click()
            self.logger.info("Download iniciado...")
            
            self.logger.info("Aguardando a conclusão do download...")
            downloaded_files = self._wait_for_download_to_complete(initial_files)

            if not downloaded_files:
                raise Exception("Nenhum arquivo foi baixado")
            
            downloaded_file = downloaded_files.pop()
            file_path = os.path.join(self.download_dir, downloaded_file)
            self.logger.info(f"Arquivo detectado: {file_path}")

            # verifica os primeiros 100bytes do arquivo
            with open(file_path, 'rb') as f:
                self.logger.info(f"Primeiros 100 bytes do arquivo: {f.read(100)}")
            
            self.logger.info(f"Iniciando leitura do arquivo Excel: {file_path}")
            # mecanismo está explicito no openpyxl - tentar com xlrd em caso de erro
            file_downloaded = pd.read_excel(file_path, engine='openpyxl')
            self.logger.info("Leitura do arquivo Excel concluída com sucesso")
            
            csv_path = os.path.join(self.final_dir, "Obras.csv")
            file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
            self.logger.info(f"Novo arquivo salvo em: {csv_path}")
            
            os.remove(file_path)
            self.logger.info(f"Arquivo original removido: {file_path}")
            
            return csv_path
            
        except TimeoutException as e:
            self.logger.error(f"Timeout ao esperar pelo elemento: {e}")
            raise
        except NoSuchElementException as e:
            self.logger.error(f"Elemento não encontrado: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro inesperado durante o download: {e}")
            raise