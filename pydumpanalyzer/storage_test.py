''' home to tests for the Storage class '''
import io
import os
import unittest

import pytest
from werkzeug.exceptions import HTTPException

from flask_app_test import MockRequest
from storage import DATABASE_FILE, REQUIRED_TABLES, Storage


class TestStorage(unittest.TestCase):
    ''' all tests for storage are in here '''
    def setUp(self):
        ''' called at the start of all tests '''
        if os.path.isfile(DATABASE_FILE):
            os.remove(DATABASE_FILE)

    def test_storage_context_manager(self):
        ''' ensure we can use Storage as a contextmanager '''
        with Storage() as s:
            pass

        # hopefully we don't hang here
        with Storage() as s:
            pass

        # deleting this file at this point means we closed it up.
        os.remove(DATABASE_FILE)

    def test_storage_creates_needed_tables(self):
        ''' ensures required tables are auto created '''
        with Storage() as s:
            for tableName in REQUIRED_TABLES.keys():
                assert s.database.tableExists(tableName)

        # deleting this file at this point means we closed it up.
        os.remove(DATABASE_FILE)

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
