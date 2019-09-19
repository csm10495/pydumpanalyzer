''' home for unit tests for the flask app'''

import io
import os
import sys
import unittest
import unittest.mock

import flask
import pytest
from werkzeug.exceptions import HTTPException

import __version__
from csmlog_setup import getLogger
from storage_test import MockRequest, Storage

logger = getLogger(__file__)

def url_for_ish(s, **kwargs):
    ''' sort of like url_for from flask, except you give a string and kwargs of replacements to make '''

    # handle if enum was given instead of str
    s = getattr(s, 'value', s)

    # modify things like <path:path> to just <path>
    s = s.replace(':path>', '>')

    for key, value in kwargs.items():
        s = s.replace("<" + key + ">", value)
    return s

class TestFlaskApp(unittest.TestCase):
    ''' test flask app test case '''

    def setUp(self):
        ''' called to setup each test case '''
        self.oldCwd = os.getcwd()

        # clear database to have a fresh run each time.
        if os.path.exists(Storage.DATABASE_FILE):
            os.remove(Storage.DATABASE_FILE)

        # our app must be imported while we're in the current directory for jinja templates to be found
        os.chdir(os.path.abspath(os.path.dirname(__file__)))
        import flask_app
        flask_app.Storage = Storage # monkeypatch
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

    def test_get_file(self):
        ''' ensures that getFile is working properly '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz')
        }, {
            'Application' : 'MyApp',
            'OperatingSystem' : 'Windows',
            'Tag' : 'MyTag17',
        })

        with Storage() as storage:
            uid = storage.addFromAddRequest(request).split('UID:')[-1].strip()

        result = self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid, column='OperatingSystem'))
        assert result.data.decode() == 'Windows'

        result = self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid, column='Tag'))
        assert result.data.decode() == 'MyTag17'

        result = self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid, column='SymbolsFile'))
        assert result.data.decode() == 'abcdefghijklmnopqrstuvwxyz'

        result = self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid, column='SymbolsFileName'))
        assert result.data.decode() == 'THEFILENAME' # set by MockRequest

        assert self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp2", rowUid=uid, column='SymbolsFileName')).status_code == 404

        self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid + '1', column='SymbolsFileName')).status_code == 404

        self.app.get(url_for_ish(self.WEBPAGES.Get_File, applicationName="MyApp", rowUid=uid, column='SymbolsFile2Name')).status_code == 404

    def test_get_analysis(self):
        ''' ensures that getAnalysis is working '''
        url = url_for_ish(self.WEBPAGES.Get_Analysis, applicationName='app', rowUid='rowUid')
        with unittest.mock.patch('storage.Storage.getAnalysis') as getAnalysis:
            getAnalysis.return_value = 'AnalysisReturn'
            result = self.app.get(url)
            assert 'AnalysisReturn' in result.data.decode()
            getAnalysis.assert_called_with('app', 'rowUid', True)

        with unittest.mock.patch('storage.Storage.getAnalysis') as getAnalysis:
            getAnalysis.return_value = 'AnalysisReturn'
            result = self.app.get(url + "?useCache=True")
            assert 'AnalysisReturn' in result.data.decode()
            getAnalysis.assert_called_with('app', 'rowUid', True)

        with unittest.mock.patch('storage.Storage.getAnalysis') as getAnalysis:
            getAnalysis.return_value = 'AnalysisReturn'
            result = self.app.get(url + "?useCache=False")
            assert 'AnalysisReturn' in result.data.decode()
            getAnalysis.assert_called_with('app', 'rowUid', False)

    def test_get_windows_symbols(self):
        ''' ensures that the windows symbol server endpoint is working '''
        url = url_for_ish(self.WEBPAGES.Get_Windows_Symbols, path='test_path')
        with unittest.mock.patch('flask.send_file') as send_file_mock:
            with unittest.mock.patch('storage.Storage.getWindowsSymbolFilePath', return_value=None) as mock:
                self.app.get(url)
                mock.assert_called_with('test_path')

            send_file_mock.assert_called_once()