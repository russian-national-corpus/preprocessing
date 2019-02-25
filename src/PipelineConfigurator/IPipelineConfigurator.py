from abc import ABC, abstractmethod
from pathlib import Path
from src.Corpus.CorpusSource import CorpusSource
from src.Pipeline.Pipeline import Pipeline

class IPipelineConfigurator(ABC):

    @abstractmethod
    def get_pipeline(self, corpus_source: CorpusSource, destination_directory: Path) -> Pipeline:
        pass
