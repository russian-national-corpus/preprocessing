from abc import ABC, abstractmethod
from pathlib import Path

class ICorpusSource(ABC):

    @abstractmethod
    def get_corpus_name(self) -> str:
        pass

    @abstractmethod
    def get_corpus_directory(self) -> Path:
        pass

    @abstractmethod
    def get_source_texts_directory(self) -> Path:
        pass
