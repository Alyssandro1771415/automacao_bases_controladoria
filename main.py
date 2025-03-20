import os

from src.download import PortalConvenioDownloader, OrcamentoDownloader, SiconvDownloader, PainelObras, PainelParlamentar
from src.utils import utils
from selenium.webdriver.firefox.service import Service

def main():
    download_dir = os.path.expanduser("~/Downloads")
    final_dir = os.path.expanduser("~/Desktop/Bases_Paineis")
    
    geckoDriver = Service("src/utils/geckodriver-v0.36.0-linux64/geckodriver")
    
    initial_files = set(os.listdir(download_dir))
    
    downloader_siconv = SiconvDownloader(geckoDriver, download_dir, os.path.join(final_dir, "SICONV"))
    downloader_portal = PortalConvenioDownloader(geckoDriver, download_dir, os.path.join(final_dir, "PORTAL"))
    downloader_orcamento = OrcamentoDownloader(geckoDriver, download_dir, os.path.join(final_dir, "OBRAS"))
    downloader_obras = PainelObras(geckoDriver, download_dir, os.path.join(final_dir, "OBRAS"))
    download_parlamentar = PainelParlamentar(geckoDriver, download_dir, os.path.join(final_dir, "EMENDAS"))

    try:
        downloader_siconv.download()
        downloader_portal.download()
        downloader_orcamento.download()
        downloader_obras.download()
        download_parlamentar.download()
            
    finally:    
        final_files = set(os.listdir(download_dir)) 
        files_diference = final_files - initial_files
        
        if len(files_diference) != 0:                
            for file in files_diference:
                os.remove(os.path.join(download_dir, file))
                

if __name__ == "__main__":
    main()
