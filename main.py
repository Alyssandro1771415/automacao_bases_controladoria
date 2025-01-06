import os

from src.download import PortalConvenioDownloader, OrcamentoDownloader, SiconvDownloader, PainelObras, PainelParlamentar
from src.utils import utils

def main():
    download_dir = utils.create_database_download_directory()
    final_dir = os.path.expanduser("~/Desktop/Bases_Paineis")

    utils.clean_database_download_directory(download_dir)

    downloader_siconv = SiconvDownloader(download_dir, os.path.join(final_dir, "SICONV"))
    downloader_portal = PortalConvenioDownloader(download_dir, os.path.join(final_dir, "PORTAL"))
    downloader_orcamento = OrcamentoDownloader(download_dir, os.path.join(final_dir, "OBRAS"))
    downloader_obras = PainelObras(download_dir, os.path.join(final_dir, "OBRAS"))
    download_parlamentar = PainelParlamentar(download_dir, os.path.join(final_dir, "EMENDAS"))

    for i in range(10):
        #downloader_siconv.download()
        downloader_portal.download()
        downloader_orcamento.download()
        downloader_obras.download()
        download_parlamentar.download()
        

if __name__ == "__main__":
    main()