from abc import ABC, abstractmethod
import os
import logging
from functools import wraps
import time
import glob
import re
import zipfile
import shutil

class BaseDownloader(ABC):
    
    def __init__(self, download_dir, final_dir) -> None:
        self.download_dir = download_dir
        self.final_dir = final_dir
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('downloader_log.txt'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger()

    def log_error(self, message):
        self.logger.error(message)

    @staticmethod
    def retry(max_attempts=3, delay=60):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                attempts = 0
                while attempts < max_attempts:
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        error_message = f'Tentativa {attempts} falhou. Erro: {type(e).__name__}: {str(e)}'
                        self.log_error(error_message)
                        if attempts == max_attempts:
                            final_error = f'Todas as {max_attempts} tentativas falharam. Erro final: {type(e).__name__}: {str(e)}'
                            self.log_error(final_error)
                            raise
                        self.logger.info(f'Tentando novamente em {delay} segundos...')
                        time.sleep(delay)
            return wrapper
        return decorator
    
    @abstractmethod
    def download(self):
        pass
        
    def setup_directories(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)

    def wait_for_download(self, zip_file_name, max_wait_time=900):
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            zip_files = glob.glob(os.path.join(self.download_dir, "*.zip"))
            matching_files = [file for file in zip_files if re.match(zip_file_name, os.path.basename(file))]
            
            if matching_files:
                zip_path = matching_files[0]
                if not any(file.endswith('.part') or file.endswith('.crdownload') for file in os.listdir(self.download_dir)):
                    self.logger.info('Download concluído...')
                    return zip_path
            
            self.logger.info('Aguardando o download do arquivo zip...')
            time.sleep(15)

        error_message = "Timeout: O download não foi concluído no tempo esperado."
        self.log_error(error_message)
        raise TimeoutError(error_message)

    def extract_and_cleanup(self, zip_path, rename_to, delete_pattern, rename_pattern):
        try:
            shutil.move(zip_path, self.final_dir)
            self.logger.info(f'Arquivo movido para a pasta: {self.final_dir}')
            moved_file_path = os.path.join(self.final_dir, os.path.basename(zip_path))
            
            with zipfile.ZipFile(moved_file_path, 'r') as zip_ref:
                self.logger.info('Extraindo o zip...')
                zip_ref.extractall(self.final_dir)
                        
            self.logger.info('Deletando .zip')
            os.remove(moved_file_path)
        
            files = zip_ref.namelist()
            file_to_delete = next((file for file in files if delete_pattern and re.match(delete_pattern, os.path.basename(file))), None)
            file_to_rename = next((file for file in files if rename_pattern and re.match(rename_pattern, os.path.basename(file))), None)        

            self.logger.info(f"Arquivos encontrados - Para deletar: {file_to_delete}, Para renomear: {file_to_rename}")
        
            if file_to_delete:
                os.remove(os.path.join(self.final_dir, file_to_delete))
                self.logger.info(f'Arquivo "{file_to_delete}" deletado com sucesso!')
        
            if file_to_rename and rename_to:
                os.rename(os.path.join(self.final_dir, file_to_rename), os.path.join(self.final_dir, rename_to))
                self.logger.info(f'Arquivo "{file_to_rename}" renomeado com sucesso para "{rename_to}"!')

        except Exception as e:
            error_message = f"Erro durante a extração e limpeza: {type(e).__name__}: {str(e)}"
            self.log_error(error_message)
            raise