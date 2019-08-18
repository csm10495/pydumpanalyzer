from analysis import Analysis
import os

class Debugger(object):
    def __init__(self, crashDump, symbols, executable=None):
        self.crashDump = crashDump
        self.symbols = symbols
        self.executable = executable

        # do last
        self._platformSetup()

    def _platformSetup(self):
        '''
        do platform specific things in here
        '''
        pass

    def getStackTrace(self):
        pass

    def getRawAnalysis(self):
        pass

    def getAnalysis(self):
        return Analysis(os.path.basename(self.crashDump),
        self.getStackTrace(), # hmm this is one stack... should we get others?... Analysis supports that if we want it
        self.getRawAnalysis())