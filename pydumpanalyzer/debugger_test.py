''' this contains test for the base Debugger class '''
from debugger import Debugger

def test_debugger_init():
    ''' simple test to ensure params are save on self '''
    d = Debugger('crashDump', 'symbols', 'executable')
    assert d.crashDump == 'crashDump'
    assert d.symbols == 'symbols'
    assert d.executable == 'executable'

def test_check_platform_setup_got_called():
    ''' ensure platformSetup() got called during __init__() '''
    class TestDebugger(Debugger):
        platformSetupCalled = False
        def _platformSetup(self):
            TestDebugger.platformSetupCalled = True

    d = TestDebugger('crashDump', 'symbols', 'executable')
    assert TestDebugger.platformSetupCalled