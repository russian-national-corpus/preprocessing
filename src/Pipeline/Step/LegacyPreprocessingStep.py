from pathlib import Path
from subprocess import run
from src.Corpus.ICorpusSource import ICorpusSource
from src.FileSystem.IFileSystem import IFileSystem
from src.Pipeline.Exception.PipelineBreakException import PipelineBreakException
from src.Pipeline.Step.IPipelineStep import IPipelineStep

class LegacyPreprocessingStep(IPipelineStep):

    def __init__(self, file_system: IFileSystem, path_to_mystem_binary: Path):
        self.file_system = file_system
        self.path_to_mystem_binary = path_to_mystem_binary

    def run(self, corpus_source: ICorpusSource) -> Path:

        project_root = self.file_system.get_project_root()

        corpus_name = corpus_source.get_corpus_name()
        corpus_directory = corpus_source.get_corpus_directory()
        corpus_root = (corpus_directory / '..' / '..').resolve()

        # todo semantic.csv has wrong encoding in svn
        # todo mystem_ruscorpora binary is not present in the repository, you need to download it manually
        # and put to var/bin directory
        # todo now svn logs are needed for some legacy stuff, and are present in the repository
        # so all of the svn logs are needed to be updated with the commands
        # cd corpora/{corpus name}
        # svn log -v -q -r 1:HEAD --xml >> src/Legacy/svn-log/{corpus name}-svnlog.log
        # where {corpus name} need to be replaced with the corpus name

        completed_process = run(
            [
                str((project_root / 'src/Legacy/begin_processing.sh').resolve()),
                corpus_name,
                str(corpus_root),
                str((project_root / 'var/output/texts').resolve()),
                './ruscorpora_tagging',
                str(corpus_root / 'tables' / 'semantic.csv'),
                str(corpus_root / 'tables' / 'add.cfg'),
                str(corpus_root / 'tables' / 'del.cfg'),
                str((project_root / 'var/log/legacy').resolve()),
                './svn-log',
                str(self.path_to_mystem_binary.resolve()),
                '1',
            ]
        )

        if completed_process.returncode != 0:
            raise PipelineBreakException("Legacy preprocessing subprocess returned %s" % completed_process.returncode)

        return (self.file_system.get_project_root() / 'var/output/texts/finalized' / corpus_name).resolve()
