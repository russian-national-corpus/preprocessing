from abc import ABC, abstractmethod
from typing import NoReturn

from src.Pipeline.Pipeline import Pipeline

class IPipelineProcessor(ABC):

    @abstractmethod
    def process(self, pipeline: Pipeline) -> NoReturn:
        pass
