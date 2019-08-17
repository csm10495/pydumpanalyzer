
class Debugger(object):
    def __init__(self, crashDump, symbols, executable):
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