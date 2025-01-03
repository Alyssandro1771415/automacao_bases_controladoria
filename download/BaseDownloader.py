from abc import ABC, abstractmethod
import os
import logging
from functools import wraps
import time

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
                        if attempts == max_attempts:
                            self.log_error(f'Todas as {max_attempts} tentativas falharam. Erro final: {str(e)}')
                            raise
                        self.logger.warning(f'Tentativa {attempts} falhou. Realizando outra tentativa em {delay} segundos..')
                        time.sleep(delay)
            return wrapper
        return decorator
    
    @abstractmethod
    def download(self):
        pass
        
    def setup_directories(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)