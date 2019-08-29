''' this file contains tests for the Windows Symbol Store '''

import subprocess
import sys
import unittest

import pytest

from windows_symbol_store import WindowsSymbolStore

class _TestWindowsSymbolStore(WindowsSymbolStore):
    ''' special class with a mocked SYM_STORE '''
    SYM_STORE = __file__

class TestWindowsSymbolStore(unittest.TestCase):
    ''' test class for WindowsSymbolStore '''
    def setUp(self):
        ''' makes a symbol store in self.symbolStore '''
        self.symbolStore = _TestWindowsSymbolStore(__file__)

    def test_add(self):
        ''' tests the add() method '''

        # .add() should raise since SYM_STORE isn't an exe (and it won't give an exit code of 0)
        # OSError if we can't execute a py file (Windows)
        # Otherwise CalledProcessError for non-zero exit code
        with pytest.raises((subprocess.CalledProcessError, OSError)):
            self.symbolStore.add(__file__, compressed=True)

        with pytest.raises((subprocess.CalledProcessError, OSError)):
            self.symbolStore.add(__file__, compressed=False)
