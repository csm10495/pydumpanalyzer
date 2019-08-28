''' this contains the Debugger class '''

import os

from analysis import Analysis

class Debugger(object):
    ''' The debugger class is the base class for all Debuggers.
    All public functions for all debuggers should be defined here '''
    def __init__(self, crashDump, symbols, executable=None):
        ''' initalizer takes in a crash dump file location, symbols file location, and
        optionally the executable that caused the crash.
        On certain platforms (Windows), symbols can refer to a symbol store as opposed to a single symbols file.
            Though if you give a single symbols file, it will be used by adding to the downstream symbol store.
         '''
        self.crashDump = crashDump
        self.symbols = symbols
        self.executable = executable

        # do last
        self._platformSetup()

    def _platformSetup(self):
        ''' Do platform specific things in here. This is called by __init__(..).
        Defined by children '''
        pass

    def getStackTrace(self):
        ''' Get a stack.Stack instance from the Debugger.
        Defined by children '''
        pass

    def getRawAnalysis(self):
        ''' Get a string of raw analysis data from the debugger.
        Defined by children '''
        pass

    def getAnalysis(self):
        ''' Uses getStackTrace() / getRawAnalysis() to get an Analysis object '''
        return Analysis(os.path.basename(self.crashDump),
        self.getStackTrace(), # hmm this is one stack... should we get others?... Analysis supports that if we want it
        self.getRawAnalysis())
