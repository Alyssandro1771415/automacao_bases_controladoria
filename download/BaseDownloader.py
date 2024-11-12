from abc import ABC, abstractmethod
import os

class BaseDownloader(ABC):
    
    def __init__(self, download_dir, final_dir) -> None:
        self.download_dir = download_dir
        self.final_dir = final_dir
    
    def download(self):
        pass
    
        
    def setup_directories(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)