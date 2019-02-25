from abc import ABC, abstractmethod
from pathlib import Path

class IFileSystem(ABC):

    @abstractmethod
    def get_project_root(self) -> Path:
        pass
