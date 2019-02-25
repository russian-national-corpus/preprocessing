from abc import ABC, abstractmethod
from typing import TypeVar, List

from src.Pipeline.Step.IPipelineStep import IPipelineStep

TInitialValue = TypeVar('TInitialValue')

class IPipeline(ABC):

    @abstractmethod
    def get_initial_value(self) -> TInitialValue:
        pass

    @abstractmethod
    def get_steps(self) -> List[IPipelineStep]:
        pass
