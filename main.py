import os
from dotenv import load_dotenv

from src.download import (
    PortalConvenioDownloader,
    OrcamentoDownloader,
    SiconvDownloader,
    PainelObras,
    PainelParlamentar
)
from selenium.webdriver.firefox.service import Service

def main():
    # Carrega variáveis do .env
    load_dotenv()

    # Lê caminhos do .env (ou usa padrão da classe BaseDownloader)
    # Se quiser forçar caminhos diferentes, pode sobrescrever aqui:
    # BASE_DIR = os.getenv("BASE_DIR", "/opt/automacao")
    # DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads"))
    # FINAL_DIR = os.getenv("FINAL_DIR", os.path.join(BASE_DIR, "outputs"))

    # Caminho do driver pode ser definido no .env ou deixado para o webdriver_manager
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
        downloader_obras.download()
        downloader_parlamentar.download()
    finally:
        final_files = set(os.listdir(download_dir))
        files_difference = final_files - initial_files

        if files_difference:
            for file in files_difference:
                os.remove(os.path.join(download_dir, file))

if __name__ == "__main__":
    main()