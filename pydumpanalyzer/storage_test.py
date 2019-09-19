''' home to tests for the Storage class '''
import io
import os
import unittest
import unittest.mock

import pytest
from werkzeug.exceptions import HTTPException

from storage import REQUIRED_TABLES, ROOT_STORAGE_LOCATION, Storage as _Storage, WINDOWS_SYMBOL_STORE

class Storage(_Storage):
    ''' overloaded class to swap the DATABASE_FILE location '''
    DATABASE_FILE = os.path.join(ROOT_STORAGE_LOCATION, 'database_unit_tests.sqlite')

class MockRequest(object):
    ''' mocked out flask request object. '''
    def __init__(self, files, form):
        self.files = files # dict
        for v in self.files.values():
            v.filename = 'THEFILENAME'
        self.form = form # dict
        self.remote_addr = '127.0.0.1'

class TestStorage(unittest.TestCase):
    ''' all tests for storage are in here '''
    def setUp(self):
        ''' called at the start of all tests '''
        if os.path.isfile(Storage.DATABASE_FILE):
            os.remove(Storage.DATABASE_FILE)

    def test_storage_context_manager(self):
        ''' ensure we can use Storage as a contextmanager '''
        with Storage() as s:
            pass

        # hopefully we don't hang here
        with Storage() as s:
            pass

        # deleting this file at this point means we closed it up.
        os.remove(Storage.DATABASE_FILE)

    def test_storage_creates_needed_tables(self):
        ''' ensures required tables are auto created '''
        with Storage() as s:
            for tableName in REQUIRED_TABLES.keys():
                assert s.database.tableExists(tableName)

        # deleting this file at this point means we closed it up.
        os.remove(Storage.DATABASE_FILE)

    def test_storage_get_application_table_name_and_reverse(self):
        ''' ensures that we can get the an application table '''
        with Storage() as s:
            assert s.getApplicationTableName("MyApp") is False
            assert s.applicationAdd("MyApp")
            tableName = s.getApplicationTableName("MyApp")

            assert s.database.tableExists(tableName)
            assert not s.database.tableExists("MyApp")

            assert s.getApplicationNameFromTable(tableName) == 'MyApp'

    def test_storage_can_add_check_for_application_tables(self):
        ''' ensures we can add / check for application tables '''
        with Storage() as s:
            assert not s.applicationExists('mytable')
            assert s.applicationAdd('mytable')
            assert s.applicationExists('mytable')

        # persistence check (new storage instance)
        with Storage() as s:
            assert s.applicationExists('mytable')

    def test_storage_cant_have_duplicate_applications(self):
        ''' ensures that we'll fail if somehow we try to add a second application with the same name '''
        with Storage() as s:
            assert s.applicationAdd('mytable')
            assert not s.applicationAdd('mytable')

    def test_add_invalid_request_due_to_missing_operating_system(self):
        ''' ensure that adding with an invalid operating system fails '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz')
        }, {
            'Application' : 'MyApp',
            #'OperatingSystem' : 'Windows',
            'Tag' : 'MyTag17',
        })
        with Storage() as s:
            with pytest.raises(HTTPException):
                s.addFromAddRequest(request)

    def test_add_invalid_request_due_to_missing_application(self):
        ''' ensure that adding with an invalid operating system fails '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz')
        }, {
            #'Application' : 'MyApp',
            'OperatingSystem' : 'Windows',
            'Tag' : 'MyTag17',
        })
        with Storage() as s:
            with pytest.raises(HTTPException):
                s.addFromAddRequest(request)

    def test_add_invalid_request_due_to_missing_file(self):
        ''' ensure that adding with an invalid operating system fails '''
        request = MockRequest({
            #'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz')
        }, {
            'Application' : 'MyApp',
            'OperatingSystem' : 'Windows',
            'Tag' : 'MyTag17',
        })
        with Storage() as s:
            with pytest.raises(HTTPException):
                s.addFromAddRequest(request)

    def test_add_succeeds_with_multiple_files(self):
        ''' ensure that adding with an invalid operating system fails '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'ExecutableFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'CrashDumpFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
        }, {
            'Application' : 'MyApp',
            'OperatingSystem' : 'Windows',
        })
        with Storage() as s:
            assert 'Success' in s.addFromAddRequest(request)

    def test_get_set_application_cell(self):
        ''' ensures we can get a particular cell for an application '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'ExecutableFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'CrashDumpFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
        }, {
            'Application' : 'MyApp234',
            'OperatingSystem' : 'Windows',
            'Tag' : 'TestTag123',
        })
        with Storage() as s:
            msg = s.addFromAddRequest(request)
            uid = msg.split('UID:')[-1].strip()

            assert s.getApplicationCell('MyApp234', uid, 'Tag') == 'TestTag123'
            assert s.getApplicationCell('MyApp235', uid, 'Tag') is False
            assert s.getApplicationCell('MyApp235', uid + '1', 'Tag') is False
            assert s.getApplicationCell('MyApp234', uid, 'OperatingSystem') == 'Windows'
            assert s.getApplicationCell('MyApp234', uid, 'OperatingSystem2') is False

            assert s.setApplicationCell('MyApp234', uid, 'Tag', 'NewTag!')
            assert s.getApplicationCell('MyApp234', uid, 'Tag') == 'NewTag!'

            assert s.setApplicationCell('MyApp2345', uid, 'Tag', 'NewTag!') is False

    def test_get_analysis_with_and_without_cache(self):
        ''' ensures we can get analysis for an app name/rowUid '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'ExecutableFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'CrashDumpFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
        }, {
            'Application' : 'MyApp234',
            'OperatingSystem' : 'Windows',
            'Tag' : 'TestTag123',
        })
        with Storage() as s:
            msg = s.addFromAddRequest(request)
            uid = msg.split('UID:')[-1].strip()

            with unittest.mock.patch('windbg.WinDbg.getAnalysis') as getAnalysis:
                getAnalysis.return_value = "Hello"
                analysis = s.getAnalysis('MyApp234', uid, useCache=False)
                getAnalysis.assert_called_once()
                assert analysis ==  "Hello"

            # shouldn't need to mock since we're using the cache now
            assert s.getAnalysis('MyApp234', uid, useCache=True) == "Hello"

    def test_get_analysis_with_invalid_uid_and_name(self):
        ''' ensures we can fail properly when using invalid params to getAnalysis '''
        request = MockRequest({
            'SymbolsFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'ExecutableFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
            'CrashDumpFile' : io.BytesIO(b'abcdefghijklmnopqrstuvwxyz'),
        }, {
            'Application' : 'MyApp234',
            'OperatingSystem' : 'Windows',
            'Tag' : 'TestTag123',
        })
        with Storage() as s:
            msg = s.addFromAddRequest(request)
            uid = msg.split('UID:')[-1].strip()

            with pytest.raises(HTTPException):
                s.getAnalysis('NotARealApp', '0', True)
            with pytest.raises(HTTPException):
                s.getAnalysis('NotARealApp', '0', False)
            with pytest.raises(HTTPException):
                s.getAnalysis('NotARealApp', uid, True)
            with pytest.raises(HTTPException):
                s.getAnalysis('NotARealApp', uid, False)

    def test_get_windows_symbol_file(self):
        ''' ensures we can get a file from the windows symbol store '''
        testPath = os.path.join(WINDOWS_SYMBOL_STORE, 'test_file.txt')
        with open(testPath, 'w') as f:
            f.write("Hello")

        with Storage() as s:
            assert os.path.exists(s.getWindowsSymbolFilePath('test_file.txt'))

            with open(s.getWindowsSymbolFilePath('test_file.txt'), 'r') as f:
                assert f.read() == 'Hello'

            os.remove(testPath)

            with pytest.raises(HTTPException):
                s.getWindowsSymbolFilePath('test_file_not_real.txt')

            with pytest.raises(HTTPException):
                s.getWindowsSymbolFilePath('../../storage.py')
