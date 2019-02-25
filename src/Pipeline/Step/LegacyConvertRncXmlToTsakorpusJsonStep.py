from pathlib import Path
from src.Legacy.src_convertors.xml_rnc2json import Xml_Rnc2JSON
from src.Pipeline.Step.IPipelineStep import IPipelineStep

class LegacyConvertRncXmlToTsakorpusJsonStep(IPipelineStep):

    def __init__(self, path_to_configuration: Path, destination_directory: Path) -> None:
        self.path_to_configuration = path_to_configuration.resolve()
        self.destination_directory = destination_directory.resolve()

    def run(self, source_directory: Path) -> None:
        x2j = Xml_Rnc2JSON(str(self.path_to_configuration))
        x2j.process_corpus(source_directory, self.destination_directory)
