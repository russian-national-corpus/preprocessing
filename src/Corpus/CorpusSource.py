from pathlib import Path
from src.Corpus.ICorpusSource import ICorpusSource

class CorpusSource(ICorpusSource):

    def __init__(self, corpus_name: str, corpus_directory: Path):
        self.corpus_name = corpus_name
        self.corpus_directory = corpus_directory

        if not self.corpus_directory.exists():
            raise self.__create_exception(self.corpus_directory, 'directory does not exist')

    def get_corpus_name(self) -> str:
        return self.corpus_name

    def get_corpus_directory(self) -> Path:
        return self.corpus_directory

    def get_source_texts_directory(self) -> Path:

        source_texts_directory = Path(self.corpus_directory, 'texts')

        if not source_texts_directory.exists():
            raise self.__create_exception(self.corpus_directory, 'directory does not contain "texts" subdirectory')

        return source_texts_directory

    @staticmethod
    def __create_exception(corpus_directory: Path, reason: str) -> Exception:
        return Exception(
            'Cannot iterate "{corpus_directory}" directory because {reason}'.format(
                corpus_directory=str(corpus_directory),
                reason=reason,
            )
        )
