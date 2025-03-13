import os
from selenium.webdriver.firefox.service import Service
from src.download import (
    PortalConvenioDownloader,
    OrcamentoDownloader,
    SiconvDownloader,
    PainelObras,
    PainelParlamentar
)

def main():
    download_dir = os.path.expanduser("~/Downloads")
    final_dir = os.path.expanduser("~/Desktop/Bases_Paineis")
    
    geckoDriver = Service("src/utils/geckodriver-v0.35.0-linux64/geckodriver")
    
    
    initial_files = set(os.listdir(download_dir))
    
    downloaders = [
        SiconvDownloader(geckoDriver, download_dir, os.path.join(final_dir, "SICONV")),
        #PortalConvenioDownloader(geckoDriver, download_dir, os.path.join(final_dir, "PORTAL")),
        #OrcamentoDownloader(geckoDriver, download_dir, os.path.join(final_dir, "ORCAMENTO")),
        #PainelObras(geckoDriver, download_dir, os.path.join(final_dir, "OBRAS")),
        #PainelParlamentar(geckoDriver, download_dir, os.path.join(final_dir, "EMENDAS")),
    ]

    try:
        for downloader in downloaders:
            downloader.download()
            
    finally:    
        final_files = set(os.listdir(download_dir)) 
        files_difference = final_files - initial_files
        
        if files_difference:
            for file in files_difference:
                os.remove(os.path.join(download_dir, file))

if __name__ == "__main__":
    main()
