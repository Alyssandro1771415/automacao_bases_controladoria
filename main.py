import os

from download import PortalConvenioDownloader, OrcamentoDownloader, SiconvDownloader

def main():
    download_dir = os.path.expanduser("~/Downloads")
    final_dir = os.path.expanduser("~/Desktop/Bases_Paineis")


    downloader_portal = PortalConvenioDownloader(download_dir, os.path.join(final_dir, "PORTAL"))
    downloader_siconv = SiconvDownloader(download_dir, os.path.join(final_dir, "SICONV"))
    downloader_orcamento = OrcamentoDownloader(download_dir, os.path.join(final_dir, "OBRAS"))

<<<<<<< HEAD
    downloader_siconv.download()
    # downloader_portal.download()
=======
    # downloader_siconv.download()
    downloader_portal.download()
>>>>>>> a17ff01bca45060ae3ff4aa56f0626dd16d3b962
    # downloader_orcamento.download()

if __name__ == "__main__":
    main()
