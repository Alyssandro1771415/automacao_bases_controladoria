import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .BaseDownloader import BaseDownloader
import hashlib

# OK FUNCIONOU.
class PainelParlamentar(BaseDownloader):
    def __init__(self, geckoDriver, download_dir, final_dir):
        super().__init__(geckoDriver, download_dir, final_dir)
        self.retry_delay = 5
        self.logger.info(f"Inicializado com retry_delay: {self.retry_delay}")
    
    def _get_latest_file(self):
        """Obtém o arquivo mais recente no diretório de download."""
        files = os.listdir(self.download_dir)
        if not files:
            self.logger.warning("Nenhum arquivo encontrado no diretório de download")
            return None
        files_with_paths = [os.path.join(self.download_dir, f) for f in files]
        latest_file = max(files_with_paths, key=os.path.getctime)
        self.logger.info(f"Arquivo mais recente: {os.path.basename(latest_file)}")
        return latest_file

    # metodo especial de espera pelo download -> dada a complexidade.
    def _custom_wait_for_download(self, initial_files):
        
        self.logger.info("Aguardando conclusão do download com verificação de arquivos temporários")
        TEMPORARY_EXTENSIONS = ['.part', '.crdownload']
        previous_size = 0
        max_retries = 10
        retries = 0
        
        while True:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - initial_files
            
            self.logger.debug(f"Arquivos novos detectados: {new_files}")
                        
            temp_files = [
                file for file in new_files
                if any(file.endswith(ext) for ext in TEMPORARY_EXTENSIONS)
            ]

            if temp_files:
                temp_file_path = os.path.join(self.download_dir, temp_files[0])
                try:
                    current_size = os.path.getsize(temp_file_path)
                    self.logger.debug(f"Arquivo temporário: {temp_files[0]}, tamanho atual: {current_size}")
                    if current_size == previous_size:
                        retries += 1
                        self.logger.warning(f"Tamanho do arquivo não mudou. Tentativa {retries}/{max_retries}")
                        if retries >= max_retries:
                            self.logger.error("Download parece estar pausado ou com erro após várias tentativas")
                            raise TimeoutError("Download parece estar pausado ou com erro.")
                    else:
                        retries = 0
                        previous_size = current_size
                        self.logger.debug(f"Tamanho do arquivo atualizado: {current_size}")
                except FileNotFoundError:
                    self.logger.warning(f"Arquivo temporário não encontrado: {temp_files[0]}")
                    pass

            else:
                if new_files:
                    self.logger.info(f"Download concluído. Arquivos baixados: {new_files}")
                    break
                else:
                    self.logger.warning("Nenhum arquivo novo detectado ainda")

            time.sleep(5)

        return new_files
    
    def _get_element_html(self, driver, xpath: str) -> str:
        """Obtém o HTML de um elemento na página."""
        try:
            element: WebElement = driver.find_element(By.XPATH, xpath)
            html = element.get_attribute('outerHTML')
            self.logger.debug(f"HTML obtido para elemento {xpath} (primeiros 50 caracteres): {html[:50]}...")
            return html
        except Exception as e:
            self.logger.error(f"Erro ao obter o HTML do elemento {xpath}: {type(e).__name__}: {str(e)}")
            return ""

    def _compare_element_html(self, html1: str, html2: str) -> bool:
        """Compara dois elementos HTML usando hash MD5."""
        hash1 = hashlib.md5(html1.encode('utf-8')).hexdigest()
        hash2 = hashlib.md5(html2.encode('utf-8')).hexdigest()
        result = hash1 == hash2
        self.logger.debug(f"Comparação de HTML: {'iguais' if result else 'diferentes'}")
        return result
        
    @BaseDownloader.retry(max_attempts=3, delay=5)
    def download(self, browser="firefox"):
        """Método principal para download dos dados do Painel Parlamentar."""
        title = "Painel Parlamentar - Pernambuco"
        self.logger.info(f"Iniciando download do {title}")
        print(f"\n\n\n\033[32;40m{'-'*(60-(len(title)//2))} {title} {'-'*(60-(len(title)//2))}\033[0m\n\n\n")
        
        self.setup_directories()
        self.logger.info("Diretórios configurados")

        # Configuração do driver
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("intl.accept_languages", "pt-BR,pt,en-US,en")
        options.set_preference("browser.helperApps.alwaysAsk.force", False)
        options.set_preference("browser.download.encoding", "utf-8")
        options.add_argument("--headless")

        driver = webdriver.Firefox(service=self.geckoDriver, options=options)
        self.logger.info("Driver Firefox inicializado com configurações personalizadas")
        
        try:
            # Navegação para a página
            self.logger.info("Navegando para a página do Painel Parlamentar")
            driver.get("https://qlik-publico.paineis.gov.br/extensions/parlamentar/parlamentar.html")

            
            self.logger.info("Aguardando carregamento da página")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#sCBrmk_content > div > div > div > div > div > div > div > div > div.MuiGrid-root.MuiGrid-container.css-q0qbej > h6"))
            )
            self.logger.info("Página carregada com sucesso")
            
            # Definindo XPaths para elementos de gráfico
            xpath_first_graph_elemento = '//*[@id="HtUCmV_content"]'
            xpath_second_graph_elemento = '//*[@id="wWjwYjq_content"]'
            
            # Verificando bloqueador
            try:
                self.logger.info("Verificando se há bloqueador na página")
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, 'qv-ui-blocker'))
                )
                self.logger.info("Bloqueador removido.")
                print("Bloqueador removido.")
            except TimeoutException:
                self.logger.warning("Bloqueador não encontrado. Continuando...")
                print("Bloqueador não encontrado. Continuando...")
            except NoSuchElementException:
                self.logger.warning("Bloqueador não existe. Continuando...")
                print("Bloqueador não existe. Continuando...")
            
            
            self.logger.info("Iniciando seleção de UF Beneficiária")
            print("UF Beneficiária...")
            
            seletor_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#fltr-uf-beneficiario > div > article > div.qv-inner-object.no-titles > div')
            seletor_uf_beneficiario.click()
            self.logger.info("Seletor de UF Beneficiária clicado")
            
            # Capturando estado inicial dos gráficos
            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            
            
            self.logger.info("Selecionando UF 'PE'")
            uf_beneficiario = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
            uf_beneficiario.click()
            uf_beneficiario.send_keys("PE")
            uf_beneficiario.send_keys(Keys.RETURN)
            self.logger.info("UF 'PE' selecionada")
            
            
            self.logger.info("Aguardando atualização dos gráficos após seleção de UF")
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            wait_count = 0
            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                wait_count += 1
                self.logger.debug(f"Aguardando atualização dos gráficos (tentativa {wait_count})")
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            self.logger.info("Gráficos atualizados após seleção de UF")
            time.sleep(2)
            
            
            ok_button_uf_beneficiario = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_uf_beneficiario.click()
            self.logger.info("Seleção de UF confirmada")
            
            
            self.logger.info("Iniciando seleção de Natureza Jurídica")
            print("Natureza Jurídica...")
            
            seletor_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#pfmQYV_content > div > div')
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088'))
            )
            seletor_natureza_juridica.click()
            self.logger.info("Seletor de Natureza Jurídica clicado")
            
            
            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            
            
            self.logger.info("Selecionando 'ou do Distrito'")
            adm_publico_estadual = driver.find_element(By.CSS_SELECTOR, 'body > div.MuiPopover-root.listbox-popover.MuiModal-root.css-1nac088 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-1dmzujt > div > div > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-direction-xs-column.css-81e1gf > div.njs-e6be-Grid-root.njs-e6be-Grid-item.css-bb28t2 > div > input')
            adm_publico_estadual.click()
            adm_publico_estadual.send_keys("ou do Distrito")
            adm_publico_estadual.send_keys(Keys.RETURN)
            self.logger.info("'ou do Distrito' selecionado")
            
            
            self.logger.info("Aguardando atualização dos gráficos após primeira seleção de Natureza Jurídica")
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            wait_count = 0
            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                wait_count += 1
                self.logger.debug(f"Aguardando atualização dos gráficos (tentativa {wait_count})")
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            self.logger.info("Gráficos atualizados após primeira seleção de Natureza Jurídica")

            
            self.logger.info("Selecionando 'Empresa'")
            first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)
            adm_publico_estadual.send_keys("Empresa")
            adm_publico_estadual.send_keys(Keys.RETURN)
            self.logger.info("'Empresa' selecionado")
            
            
            self.logger.info("Aguardando atualização dos gráficos após segunda seleção de Natureza Jurídica")
            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)

            wait_count = 0
            while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                wait_count += 1
                self.logger.debug(f"Aguardando atualização dos gráficos (tentativa {wait_count})")
                time.sleep(5)
                first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
            
            self.logger.info("Gráficos atualizados após segunda seleção de Natureza Jurídica")

            
            ok_button_natureza_juridica = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_natureza_juridica.click()
            self.logger.info("Seleção de Natureza Jurídica confirmada")
            
            
            self.logger.info("Iniciando seleção de Modalidade")
            print("Modalidade...")
            
            seletor_modaliade = driver.find_element(By.CSS_SELECTOR, '#gPGwwUJ_content > div > div')
            seletor_modaliade.click()
            self.logger.info("Seletor de Modalidade clicado")
            time.sleep(10)
 
            # Elementos a selecionar
            elementos_a_selecionar = ["CONVENIO", "CONTRATO DE REPASSE", "CONVENIO OU CONTRATO DE REPASSE", "TERMO DE COMPROMISSO"]
            self.logger.info(f"Elementos a selecionar: {elementos_a_selecionar}")
            
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
            
            # Selecionando elementos de modalidade
            for elemento in all_elements:
                if len(elementos_a_selecionar) == 0:
                    self.logger.info("Todos os elementos necessários já foram selecionados")
                    break
                    
                time.sleep(5)
                first_html_before = self._get_element_html(driver, xpath_first_graph_elemento)
                second_html_before = self._get_element_html(driver, xpath_second_graph_elemento)

                try:
                    elemento_atual = driver.find_element(By.CSS_SELECTOR, elemento)
                    texto_elemento = elemento_atual.text
                    self.logger.info(f"Verificando elemento: {texto_elemento}")
                    
                    if texto_elemento in elementos_a_selecionar:
                        self.logger.info(f"Selecionando elemento: {texto_elemento}")
                        elemento_atual.click()
                        self.logger.info(f"Elemento {texto_elemento} clicado")
                        
                        # Aguardando atualização dos gráficos
                        self.logger.info(f"Aguardando atualização dos gráficos após seleção de {texto_elemento}")
                        first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                        second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
                        
                        wait_count = 0
                        while self._compare_element_html(first_html_before, first_html_after) == True and self._compare_element_html(second_html_before, second_html_after) == True:
                            wait_count += 1
                            self.logger.debug(f"Aguardando atualização dos gráficos (tentativa {wait_count})")
                            time.sleep(5)
                            first_html_after = self._get_element_html(driver, xpath_first_graph_elemento)
                            second_html_after = self._get_element_html(driver, xpath_second_graph_elemento)
                        
                        self.logger.info(f"Gráficos atualizados após seleção de {texto_elemento}")
                        elementos_a_selecionar.remove(texto_elemento)
                        self.logger.info(f"Elementos restantes a selecionar: {elementos_a_selecionar}")
                except Exception as e:
                    self.logger.error(f"Erro ao processar elemento {elemento}: {type(e).__name__}: {str(e)}")
     
            
            xpath_table_elemento = '//*[@id="myTabContent"]'
            self.logger.info("Capturando estado inicial da tabela")
            html_table_before = self._get_element_html(driver, xpath_table_elemento)
     
            
            ok_button_modalidade = driver.find_element(By.CSS_SELECTOR, '#actions-toolbar > div.njs-e6be-Grid-root.njs-e6be-Grid-container.njs-e6be-Grid-item.njs-e6be-Grid-wrap-xs-nowrap.actions-toolbar-default-actions.css-3cuy5k > div:nth-child(3) > button')
            ok_button_modalidade.click()
            self.logger.info("Seleção de Modalidade confirmada")
            
            
            initial_files = set(os.listdir(self.download_dir))
            self.logger.info(f"Arquivos iniciais no diretório de download: {len(initial_files)}")
            
            
            self.logger.info("Aguardando atualização da tabela")
            html_table_after = self._get_element_html(driver, xpath_table_elemento)
            
            wait_count = 0
            while self._compare_element_html(html_table_before, html_table_after) == True:
                wait_count += 1
                self.logger.info(f"Aguardando preparação do arquivo... (tentativa {wait_count})")
                print("Aguardando preparação do arquivo...")
                html_table_after = self._get_element_html(driver, xpath_table_elemento)    
                time.sleep(5)
            
            self.logger.info("Tabela atualizada, pronto para download")
            
            # Iniciando download
            download_database_button = driver.find_element(By.CSS_SELECTOR, '#btn-export-tbl-ciente > span')
            download_database_button.click()
            self.logger.info("Botão de download clicado")
            print("Download iniciado...")

            # Aguardando download
            time.sleep(5)
            self.logger.info("Aguardando conclusão do download")
            downloaded_files = self._custom_wait_for_download(initial_files=initial_files)
            
            if not downloaded_files:
                self.logger.error("Nenhum arquivo baixado")
                raise Exception("Nenhum arquivo baixado")
                
            downloaded_file = next(iter(downloaded_files))
            self.logger.info(f"Arquivo detectado: {downloaded_file}")
            print(f"Arquivo detectado: {downloaded_file}")
            
            # Processando arquivo baixado
            file_path = os.path.join(self.download_dir, downloaded_file)
            self.logger.info(f"Caminho do arquivo baixado: {file_path}")

            new_filename = "Emendas.xlsx"
            final_path = os.path.join(self.final_dir, new_filename)
            self.logger.info(f"Novo nome de arquivo: {new_filename}")

            # Limpando diretório final e movendo arquivo
            self.clean_final_directory()
            self.logger.info("Diretório final limpo")

            os.rename(file_path, final_path)
            self.logger.info(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")
            print(f"Arquivo renomeado para '{new_filename}' e movido para: {final_path}")

        except Exception as e:
            self.logger.error(f"Erro durante o download: {type(e).__name__}: {str(e)}")
            raise
        finally:
            driver.quit()
            self.logger.info("Driver encerrado")
            print("Driver encerrado.")

