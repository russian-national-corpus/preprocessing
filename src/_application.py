from cleo import Application
from src.Command.ProcessCorpus.ProcessMainCorpusCommand import ProcessMainCorpusCommand

APPLICATION = Application()
APPLICATION.add(ProcessMainCorpusCommand())
