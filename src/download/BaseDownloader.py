from abc import ABC, abstractmethod
import os

class BaseDownloader(ABC):
    
    def __init__(self, geckoDriver, download_dir, final_dir) -> None:
        self.download_dir = download_dir
        self.final_dir = final_dir
        self.geckoDriver = geckoDriver
    
    def download(self):
        pass
    
    def setup_directories(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)
    
    def clean_final_directory(self):
        for file in os.listdir(self.final_dir):
            file_path = os.path.join(self.final_dir, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                print(f"Arquivo '{file}' removido da pasta final.")