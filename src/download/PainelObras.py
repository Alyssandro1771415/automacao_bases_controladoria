import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, SessionNotCreatedException
import pandas as pd
from .BaseDownloader import BaseDownloader

# OK FUNCIONOU 
class PainelObras(BaseDownloader):
    
    def __init__(self, geckoDriver, download_dir, final_dir, retry_delay=5):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = retry_delay
        self.logger.info(f"Inicializado com retry_delay: {retry_delay}")
    

    @BaseDownloader.retry(max_attempts=3, delay=5)  
    def download(self, browser="firefox"):  
        title = "Painel de Obras - Pernambuco"
        self.logger.info(f"Iniciando download do {title}")
        print(f"\n\n\n\033[36;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")
        
        self.setup_directories()
        self.logger.info("Diretórios configurados")
        
    
        driver = self.get_driver(browser)
        
        try:
            self.logger.info("Navegando para a página do Painel de Obras")
            driver.get("https://qlik-publico.paineis.gov.br/extensions/obras/obras.html")
            
            self.logger.info("Aguardando carregamento da página")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'text[data-label="PE"]'))
            )
            self.logger.info("Página carregada com sucesso")
            
            # Clicando no elemento PE
            self.logger.info("Tentando clicar no elemento PE")
            uf_element = driver.find_element(By.CSS_SELECTOR, 'text[data-label="PE"]')
            uf_element.click()
            self.logger.info("Elemento PE clicado com sucesso")
            
            # Iniciando download
            self.logger.info("Localizando botão de download")
            download_button = driver.find_element(By.XPATH, '//*[@id="btn-export-tbl-detalhes-obras"]')
            initial_files = set(os.listdir(self.download_dir))
            self.logger.info(f"Arquivos iniciais no diretório de download: {len(initial_files)}")
            
            download_button.click()
            self.logger.info("Botão de download clicado")
            print("Download iniciado...")
            
        
            downloaded_files = self._wait_for_download_to_complete(initial_files)
            if not downloaded_files:
                self.logger.error("Tempo limite excedido. Nenhum arquivo baixado.")
                raise TimeoutException("Nenhum novo arquivo detectado após o download.")
            
            downloaded_file = list(downloaded_files)[0]
            self.logger.info(f"Arquivo detectado: {downloaded_file}")
            
            file_path = os.path.join(self.download_dir, downloaded_file)
            self.logger.info(f"Lendo arquivo Excel: {file_path}")
            
            try:
                file_downloaded = pd.read_excel(file_path, dtype=str, engine="openpyxl")
                self.logger.info(f"Arquivo lido com sucesso. Linhas: {len(file_downloaded)}")
                
                # Processando os dados
                self.logger.info("Processando campos de porcentagem")
                campos_porcentagem = ["Execução Física", "Execução Financeira"]
                
                for campo in campos_porcentagem:
                    for index, row in file_downloaded.iterrows():
                        if str(row[campo]) != "-":
                            row[campo] = str(round(float(row[campo])*100, 2))+"%"
                
                self.logger.info("Campos de porcentagem processados")
                
                # Salvando o arquivo processado
                self.clean_final_directory()
                self.logger.info("Diretório final limpo")
                
                csv_path = os.path.join(self.final_dir, "Obras.csv")
                self.logger.info(f"Salvando arquivo CSV em: {csv_path}")
                file_downloaded.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
                self.logger.info("Arquivo CSV salvo com sucesso")
                print(f"Novo arquivo salvo em: {csv_path}")
                
                # Removendo o arquivo original
                os.remove(file_path)
                self.logger.info(f"Arquivo original removido: {file_path}")
            except Exception as e:
                self.logger.error(f"Erro ao processar o arquivo Excel: {type(e).__name__}: {str(e)}")
                raise
                
        except Exception as e:
            self.logger.error(f"Erro durante o download: {type(e).__name__}: {str(e)}")
            raise
        finally:
            driver.quit()
            self.logger.info("Driver encerrado")
            print("Driver encerrado.")

