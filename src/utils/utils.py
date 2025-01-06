import os


def create_database_download_directory():
    path_downloads_directory = os.path.expanduser("~/Downloads")
    databases_download_path = os.path.join(path_downloads_directory, "databases_download")

    if not os.path.exists(databases_download_path):
        os.makedirs(databases_download_path)
    
    return databases_download_path


def clean_database_download_directory(path: str):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    print("Pasta final pronta para iniciar processo!")