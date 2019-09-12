''' home for unit tests for the flask app'''

import io
import os
import sys
import unittest

import flask

import __version__
from csmlog_setup import getLogger
from storage import DATABASE_FILE, Storage

logger = getLogger(__file__)

class MockRequest(object):
    ''' mocked out flask request object. '''
    def __init__(self, files, form):
        self.files = files # dict
        for v in self.files.values():
            v.filename = 'filename'
        self.form = form # dict
        self.remote_addr = '127.0.0.1'

def url_for_ish(s, **kwargs):
    ''' sort of like url_for from flask, except you give a string and kwargs of replacements to make '''

    # handle if enum was given instead of str
    s = getattr(s, 'value', s)

    for key, value in kwargs.items():
        s = s.replace("<" + key + ">", value)
    return s

class TestFlaskApp(unittest.TestCase):
    ''' test flask app test case '''

    def setUp(self):
        ''' called to setup each test case '''
        self.oldCwd = os.getcwd()

        # clear database to have a fresh run each time.
        if os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)

        # our app must be imported while we're in the current directory for jinja templates to be found
        os.chdir(os.path.abspath(os.path.dirname(__file__)))
        import flask_app
        self.WEBPAGES = flask_app.WEBPAGES
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def tearDown(self):
        ''' called to tear down every test case '''
        os.chdir(self.oldCwd)

    def test_error_page(self):
        ''' ensures that the error page seems to be working '''
        result = self.app.get('/jdalsjdads')
        assert result.status_code == 404
        assert 'PDA' in result.data.decode()
        assert 'Error' in result.data.decode()

    def test_home_page(self):
        ''' ensures the home page loads '''
        result = self.app.get(self.WEBPAGES.Home.value)
        assert result.status_code == 200
        assert 'PDA' in result.data.decode()
        assert 'Welcome' in result.data.decode()
        assert __version__.__version__ in result.data.decode()

    def test_apidoc_page(self):
        ''' ensures we can show the apidocs page '''
        result = self.app.get(self.WEBPAGES.API_Docs.value)

    def test_show_nonexistant_table(self):
        ''' ensures a nonexistant table can be failed with a 404 '''
        result = self.app.get(url_for_ish(self.WEBPAGES.View_Application_Table, applicationName="notrealtable"))
        assert result.status_code == 404

    def test_show_empty_table(self):
        ''' ensures an empty table can be shown '''
        with Storage() as storage:
            storage.applicationAdd('MyApp')

        result = self.app.get(url_for_ish(self.WEBPAGES.View_Application_Table, applicationName="MyApp"))
        assert result.status_code == 200
        assert 'Table is empty' in result.data.decode()

    def test_show_table(self):
        ''' ensures a nonempty table can be shown '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz')
        }, {
            'Application' : 'MyApp',
            'OperatingSystem' : 'Windows',
            'Tag' : 'MyTag17',
        })

        with Storage() as storage:
            storage.applicationAdd('MyApp')
            storage.addFromAddRequest(request)

        result = self.app.get(url_for_ish(self.WEBPAGES.View_Application_Table, applicationName="MyApp"))
        assert result.data.decode().count('MyTag17') == 1
        assert result.status_code == 200
