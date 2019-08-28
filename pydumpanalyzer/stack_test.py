''' this contains tests for the Stack class '''
from stack import Stack

def test_stack_functions():
    ''' ensures that supported functions don't traceback '''
    s = Stack(['Frame1', 'Frame2'], 123)
    assert str(s)
    assert repr(s)

def test_stack_properties():
    ''' ensures that supported properties return expected values '''
    s = Stack(['Frame1', 'Frame2'], 123)
    assert s.frames == ['Frame1', 'Frame2']
    assert s.threadId == 123