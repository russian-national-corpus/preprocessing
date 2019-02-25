from pathlib import Path
from subprocess import run
from src.Corpus.ICorpusSource import ICorpusSource
from src.FileSystem.IFileSystem import IFileSystem
from src.Pipeline.Exception.PipelineBreakException import PipelineBreakException
from src.Pipeline.Step.IPipelineStep import IPipelineStep

class LegacyPreprocessingStep(IPipelineStep):

    def __init__(self, file_system: IFileSystem):
        self.file_system = file_system

    def run(self, corpus_source: ICorpusSource) -> Path:

        project_root = self.file_system.get_project_root()

        corpus_name = corpus_source.get_corpus_name()
        corpus_directory = corpus_source.get_corpus_directory()
        corpus_root = (corpus_directory / '..' / '..').resolve()

        # todo add.cfg and del.cfg are not present in svn, you need to download it manually and put to the defined place
        # todo semantic.csv has wrong encoding in svn
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
                str((project_root / 'var/bin/mystem_ruscorpora').resolve()),
                '1',
            ]
        )

        if completed_process.returncode != 0:
            raise PipelineBreakException("Legacy preprocessing subprocess returned %s" % completed_process.returncode)

        return (self.file_system.get_project_root() / 'var/output/texts/finalized' / corpus_name).resolve()
