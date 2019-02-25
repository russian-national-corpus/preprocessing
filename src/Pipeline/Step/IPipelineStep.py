from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TIn = TypeVar('TIn')
TOut = TypeVar('TOut')

class IPipelineStep(ABC, Generic[TIn, TOut]):

    @abstractmethod
    def run(self, step_input: TIn) -> TOut:
        pass
