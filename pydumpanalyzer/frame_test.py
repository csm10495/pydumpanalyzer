''' contains tests for the Frame class '''
import pytest

from frame import Frame
from variable import Variable

FRAMES_TO_TEST = [
    Frame('module', 1),
    Frame('module2', 10, 'thefunction'),
    Frame('module2', 10, sourceFile='source.cpp'),
    Frame('module2', 10, sourceFile='source.cpp', warningAboutCorrectness=True),
    Frame('module2', 10, sourceFile='source.cpp', variables=[Variable('Type', 'Name', "Value")]),
]

@pytest.mark.parametrize(
    'frame', FRAMES_TO_TEST
)
def test_frame_functions(frame):
    ''' ensures functions on Frame don't traceback '''
    assert str(frame)
    assert repr(frame)

@pytest.mark.parametrize(
    'frame', FRAMES_TO_TEST
)
def test_frame_properties(frame):
    ''' ensures we don't have attributes missing '''
    supportedAttributes = ['module', 'index', 'function', 'sourceFile', 'line', 'variables', 'warningAboutCorrectness']
    for name in supportedAttributes:
        assert hasattr(frame, name)
