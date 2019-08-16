import os
import subprocess
import sys
import time
import tempfile

from debugger import Debugger

class WinDbg(Debugger):
    def _platformSetup(self):
        self._winDbgPath = r'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\windbg.exe'
        if not os.path.isfile(self._winDbgPath):
            raise EnvironmentError("Could not find windbg: %s" % self._winDbgPath)

    def _callWinDbg(self, debugCommandsList, gotoExceptionContext=True):
        if isinstance(debugCommandsList, str):
            debugCommandsList = [debugCommandsList]
        debugCommandsList.append('q')

        if gotoExceptionContext:
            debugCommandsList = ['.ecxr'] + debugCommandsList

        # cheap... this will get deleted immediately but we'll have the path
        with tempfile.NamedTemporaryFile() as tempFile:
            tempFileName = tempFile.name

        retCode = subprocess.check_call([
            self._winDbgPath,
            "-z",
            self.crashDump,
            "-y",
            self.symbols,
            "-i",
            self.executable,
            "-logo",
            tempFileName,
            "-c",
            ';'.join(debugCommandsList),
        ], shell=True)

        # above will raise on failure!
        with open(tempFile.name, 'r') as f:
            return f.read()

    def _callCommandOnEveryStackFrame(self, cmd):
        return self._callWinDbg(['!for_each_frame %s' % cmd])

    def _getRawStackTraceForEachFrame(self, formatCode='P'):
        return self._callCommandOnEveryStackFrame('k' + formatCode)

    def getStackTrace(self):
        pass

if __name__ == '__main__':
    w = WinDbg(r"C:\Users\cmachalo\Documents\Visual Studio 2015\Projects\TheCrasher\TestAll\6e71a81b-9d54-4966-be65-bbe7ef2b390a.dmp", r"C:\Users\cmachalo\Documents\Visual Studio 2015\Projects\TheCrasher\TestAll\TheCrasher.pdb", r"C:\Users\cmachalo\Documents\Visual Studio 2015\Projects\TheCrasher\TestAll\TheCrasher.exe")