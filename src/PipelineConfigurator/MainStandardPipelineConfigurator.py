from pathlib import Path
from src.Corpus.CorpusSource import CorpusSource
from src.FileSystem.FileSystem import FileSystem
from src.Pipeline.Pipeline import Pipeline
from src.Pipeline.Step.LegacyConvertRncXmlToTsakorpusJsonStep import LegacyConvertRncXmlToTsakorpusJsonStep
from src.Pipeline.Step.LegacyPreprocessingStep import LegacyPreprocessingStep
from src.PipelineConfigurator.IPipelineConfigurator import IPipelineConfigurator

class MainStandardPipelineConfigurator(IPipelineConfigurator):

    def get_pipeline(self, corpus_source: CorpusSource, destination_directory: Path) -> Pipeline:

        file_system = FileSystem()

        return Pipeline(
            corpus_source,
            [
                LegacyPreprocessingStep(file_system),
                LegacyConvertRncXmlToTsakorpusJsonStep(
                    file_system.get_project_root() / 'src/Legacy/src_convertors/configuration/main',
                    destination_directory
                ),
            ]
        )
