from typing import Generic, List
from src.Pipeline.IPipeline import IPipeline, IPipelineStep, TInitialValue

# pylint: disable=unsubscriptable-object
class Pipeline(IPipeline, Generic[TInitialValue]):

    def __init__(self, initial_value: TInitialValue, steps: List[IPipelineStep]):
        self.initial_value = initial_value
        self.steps = steps
        # todo: check type-level integrity

    def get_initial_value(self) -> TInitialValue:
        return self.initial_value

    def get_steps(self) -> List[IPipelineStep]:
        return self.steps
