from typing import NoReturn

from src.Pipeline.Pipeline import Pipeline
from src.PipelineProcessor.IPipelineProcessor import IPipelineProcessor

class PipelineProcessor(IPipelineProcessor):

    # todo: explore the mechanism of arguments in Python and use the arrays of input and output values
    def process(self, pipeline: Pipeline) -> NoReturn:

        steps = pipeline.get_steps()

        output_value = pipeline.get_initial_value()

        for step in steps:
            output_value = step.run(output_value)
