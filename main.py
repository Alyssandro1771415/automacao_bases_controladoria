import os

from download import PortalConvenioDownloader, OrcamentoDownloader, SiconvDownloader

def main():
    download_dir = os.path.expanduser("~/Downloads")
    final_dir = os.path.expanduser("~/Desktop/Bases_Paineis")


    downloader_portal = PortalConvenioDownloader(download_dir, os.path.join(final_dir, "PORTAL"))
    downloader_siconv = SiconvDownloader(download_dir, os.path.join(final_dir, "SICONV"))
    downloader_orcamento = OrcamentoDownloader(download_dir, os.path.join(final_dir, "OBRAS"))


    #downloader_portal.download()
    downloader_siconv.download()
    #downloader_orcamento.download()

if __name__ == "__main__":
    main()
