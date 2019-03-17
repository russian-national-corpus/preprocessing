from pathlib import Path
from src.Corpus.CorpusSource import CorpusSource
from src.FileSystem.FileSystem import FileSystem
from src.Pipeline.Pipeline import Pipeline
from src.Pipeline.Step.LegacyConvertRncXmlToTsakorpusJsonStep import LegacyConvertRncXmlToTsakorpusJsonStep
from src.Pipeline.Step.LegacyPreprocessingStep import LegacyPreprocessingStep
from src.PipelineConfigurator.IPipelineConfigurator import IPipelineConfigurator

# pylint: skip-file
# now MainSourcePipelineConfigurator.py is similar to MainStandardPipelineConfigurator.py,
# but it will differ from it when the legacy code is removed
# todo: remove pylint workaround when this file will be different from MainStandardPipelineConfigurator.py
class MainSourcePipelineConfigurator(IPipelineConfigurator):

    def __init__(self, path_to_mystem_binary: Path) -> None:
        self.path_to_mystem_binary = path_to_mystem_binary

    def get_pipeline(self, corpus_source: CorpusSource, destination_directory: Path) -> Pipeline:

        file_system = FileSystem()

        return Pipeline(
            corpus_source,
            [
                LegacyPreprocessingStep(file_system, self.path_to_mystem_binary),
                LegacyConvertRncXmlToTsakorpusJsonStep(
                    file_system.get_project_root() / 'src/Legacy/src_convertors/configuration/main',
                    destination_directory
                ),
            ]
        )
