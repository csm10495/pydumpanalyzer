''' this contains tests for the Analysis class '''
from analysis import Analysis

def test_analysis_functions():
    ''' ensures that supported functions don't traceback '''
    a = Analysis('dump.dmp', ["The stack"], "This is the analysis")
    assert str(a)
    assert repr(a)

def test_analysis_properties():
    ''' ensures that supported properties return expected values '''
    a = Analysis('dump.dmp', ["The stack"], "This is the analysis")
    assert a.dumpFileName == 'dump.dmp'
    assert a.stacks == ["The stack"]
    assert a.rawAnalysisText == "This is the analysis"

def test_analysis_can_give_one_stack_instead_of_list():
    ''' ensures that if we don't give a list of stacks, it coerces it to a list of a single item (of 1 stack) '''
    a1 = Analysis('dump.dmp', ["The stack"], "This is the analysis")
    a2 = Analysis('dump.dmp', "The stack", "This is the analysis")
    assert a1.stacks == a2.stacks