from pathlib import Path
from cleo import Command
from src.Corpus.CorpusSource import CorpusSource
from src.PipelineConfigurator.MainSourcePipelineConfigurator import MainSourcePipelineConfigurator
from src.PipelineConfigurator.MainStandardPipelineConfigurator import MainStandardPipelineConfigurator
from src.PipelineProcessor.PipelineProcessor import PipelineProcessor

class ProcessMainCorpusCommand(Command):
    """
    Process main corpus

    process-corpus:main
        {source-directory : Directory where source files are placed (including `standard` and `source` subdirectories)}
        {destination-directory : Directory where to place processed files}
        {mystem-binary : Path to mystem binary file}
    """

    def handle(self):

        source_directory = Path(self.argument('source-directory'))
        destination_directory = Path(self.argument('destination-directory'))
        mystem_binary = Path(self.argument('mystem-binary'))

        source_source_directory = (source_directory / 'source').resolve()
        standard_source_directory = (source_directory / 'standard').resolve()

        pipeline_processor = PipelineProcessor()

        source_source = CorpusSource('source', source_source_directory)
        source_pipeline = MainSourcePipelineConfigurator(mystem_binary).get_pipeline(
            source_source,
            destination_directory / source_source.get_corpus_name()
        )

        standard_source = CorpusSource('standard', standard_source_directory)
        standard_pipeline = MainStandardPipelineConfigurator(mystem_binary).get_pipeline(
            standard_source,
            destination_directory / standard_source.get_corpus_name()
        )

        pipeline_processor.process(source_pipeline)
        pipeline_processor.process(standard_pipeline)
