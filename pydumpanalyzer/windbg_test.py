''' this contains tests for our windbg debugger '''
import unittest

from windbg import WinDbg
from variable import Variable

class _TestWindbg(WinDbg):
    ''' This is basically windbg while removing the requirement for CDB to be installed '''
    CDB_DBG_PATH = __file__

class TestWindbg(unittest.TestCase):
    ''' home to tests for WinDbg '''
    def setUp(self):
        ''' called when starting every test '''
        self.windbg = _TestWindbg(__file__, __file__)

    def test_get_thread_id(self):
        ''' ensures _getThreadId() works properly via parsing windbg output '''
        EXAMPLE_OUTPUT = r"""
        == Start Calling ~. ==

        .  0  Id: 97cc.e00 Suspend: 0 Teb: 00f81000 Unfrozen
            Priority: 0  Priority class: 32

        == End Calling ~. ==
        """
        self.windbg._callWinDbg = lambda *args, **kwargs: EXAMPLE_OUTPUT

        assert self.windbg._getThreadId() == 0xe00

    def test_get_variables_for_frame(self):
        ''' ensures _getVariablesForFrame() works properly via parsing windbg output '''
        EXAMPLE_OUTPUT = r"""
        == Start Calling .frame 0 ==

        00 010ffc14 00889ad9 TheCrasher!main+0x1b [c:\users\cmachalo\documents\visual studio 2015\projects\thecrasher\thecrasher\source.cpp @ 43]
        == End Calling .frame 0 ==
        == Start Calling dv /t * ==
        int argc = 0n1
        char ** argv = 0x032053f0
        char * p = 0x00000000 ""

        == End Calling dv /t * ==
        """
        self.windbg._callWinDbg = lambda *args, **kwargs: EXAMPLE_OUTPUT

        variables = self.windbg._getVariablesForFrame(0)
        assert [v for v in variables if v.type == 'int' and v.value == 1 and v.name == 'argc']
        assert [v for v in variables if v.type == 'char **' and v.value =="0x032053f0" and v.name == 'argv']
        assert [v for v in variables if v.type == 'char *' and v.value =='0x00000000 ""' and v.name == 'p']

    def test_get_stack_trace(self):
        ''' ensures getStackTrace() works properly via parsing windbg output '''
        EXAMPLE_KCN_OUTPUT = r"""
        == Start Calling kcn ==

        *** Stack trace for last set context - .thread/.cxr resets it
        #
        00 TheCrasher!main
        01 TheCrasher!invoke_main
        02 TheCrasher!__scrt_common_main_seh
        03 kernel32!BaseThreadInitThunk
        04 ntdll!__RtlUserThreadStart
        05 ntdll!_RtlUserThreadStart

        == End Calling kcn ==
        """

        EXAMPLE_KPN_OUTPUT = r"""
        == Start Calling kpn ==

        *** Stack trace for last set context - .thread/.cxr resets it
        # ChildEBP RetAddr
        00 010ffc14 00889ad9 TheCrasher!main(int argc = 0n1, char ** argv = 0x032053f0)+0x1b [c:\users\cmachalo\documents\visual studio 2015\projects\thecrasher\thecrasher\source.cpp @ 43]
        01 (Inline) -------- TheCrasher!invoke_main+0x1d [f:\dd\vctools\crt\vcstartup\src\startup\exe_common.inl @ 64]
        02 010ffc5c 754b8674 TheCrasher!__scrt_common_main_seh(void)+0xf9 [f:\dd\vctools\crt\vcstartup\src\startup\exe_common.inl @ 253]
        03 010ffc70 77225e17 kernel32!BaseThreadInitThunk+0x24
        04 010ffcb8 77225de7 ntdll!__RtlUserThreadStart+0x2f
        05 010ffcc8 00000000 ntdll!_RtlUserThreadStart+0x1b

        == End Calling kpn ==
        """

        def callWinDbg(cmd):
            ''' helper mock'd method for _callWinDbg '''
            if cmd == 'kcn':
                return EXAMPLE_KCN_OUTPUT
            return EXAMPLE_KPN_OUTPUT

        A_VARIABLE = Variable('int', 'theInt', 12)
        self.windbg._callWinDbg = callWinDbg
        self.windbg._getThreadId = lambda: 0xf2
        self.windbg._getVariablesForFrame = lambda *args, **kwargs: [A_VARIABLE]

        s = self.windbg.getStackTrace()

        assert len(s.frames) == 6
        assert s.threadId == 0xf2
        assert str(s)

        assert s.frames[0].module == 'TheCrasher'
        assert s.frames[0].function == 'main'
        assert s.frames[0].sourceFile == r'c:\users\cmachalo\documents\visual studio 2015\projects\thecrasher\thecrasher\source.cpp'
        assert s.frames[0].line == 43
        assert len(s.frames[0].variables) == 1
        assert s.frames[0].variables[0] == A_VARIABLE

        assert s.frames[2].module == 'TheCrasher'
        assert s.frames[2].function == '__scrt_common_main_seh'
        assert s.frames[2].sourceFile == r'f:\dd\vctools\crt\vcstartup\src\startup\exe_common.inl'
        assert s.frames[2].line == 253
        assert len(s.frames[2].variables) == 1
        assert s.frames[2].variables[0] == A_VARIABLE

        assert s.frames[4].module == 'ntdll'
        assert s.frames[4].function == '__RtlUserThreadStart'
        assert s.frames[4].sourceFile == None
        assert s.frames[4].line == None
        assert len(s.frames[4].variables) == 1
        assert s.frames[4].variables[0] == A_VARIABLE