import os
from dotenv import load_dotenv

from src.utils.paths import  (
    BASE_DIR,
    DOWNLOAD_DIR,
    FINAL_DIR,
    LOG_DIR,
    GECKO_DRIVER_PATH
)

from src.download import (
    PortalConvenioDownloader,
    OrcamentoDownloader,
    SiconvDownloader,
    PainelObras,
    PainelParlamentar,
)
from selenium.webdriver.firefox.service import Service

def main():
    # Carrega variáveis do .env
    load_dotenv()

    GECKO_DRIVER_PATH = os.getenv("GECKO_DRIVER_PATH")
    if GECKO_DRIVER_PATH:
        geckoDriver = Service(GECKO_DRIVER_PATH)
    else:
        geckoDriver = None  # webdriver_manager será usado automaticamente

    # Instancia os downloaders (sem passar diretórios)
    downloader_siconv = SiconvDownloader(geckoDriver=geckoDriver)
    downloader_portal = PortalConvenioDownloader(geckoDriver=geckoDriver)
    downloader_orcamento = OrcamentoDownloader(geckoDriver=geckoDriver)
    downloader_obras = PainelObras(geckoDriver=geckoDriver)
    downloader_parlamentar = PainelParlamentar(geckoDriver=geckoDriver)

    # Limpeza de arquivos residuais no diretório de download
    download_dir = downloader_siconv.download_dir  # Todos usam o mesmo download_dir
    initial_files = set(os.listdir(download_dir))

    try:
        downloader_siconv.download()
        downloader_portal.download()
        downloader_orcamento.download()
        downloader_parlamentar.download()
        downloader_obras.download()
        downloader_parlamentar.download(Emendas=True)
    finally:
        final_files = set(os.listdir(download_dir))
        files_difference = final_files - initial_files

        if files_difference:
            for file in files_difference:
                os.remove(os.path.join(download_dir, file))

if __name__ == "__main__":
    main()