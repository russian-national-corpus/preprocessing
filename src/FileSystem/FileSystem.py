from pathlib import Path
from src.FileSystem.IFileSystem import IFileSystem

class FileSystem(IFileSystem):

    def get_project_root(self) -> Path:
        return Path('.').resolve().absolute()
