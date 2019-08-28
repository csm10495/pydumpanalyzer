''' this contains tests for the variable class '''
from variable import Variable

def test_variable_functions():
    ''' ensures that supported functions don't traceback '''
    v = Variable("MyType", "MyName", "MyValue")
    assert str(v)
    assert repr(v)

    assert Variable("MyType", "MyName", "MyValue") == Variable("MyType", "MyName", "MyValue")

def test_variable_properties():
    ''' ensures that supported properties return expected values '''
    v = Variable("MyType", "MyName", "MyValue")
    assert v.type == "MyType"
    assert v.name == "MyName"
    assert v.value == "MyValue"