''' home to tests for the Storage class '''
import os

from storage import Storage, DATABASE_FILE, REQUIRED_TABLES

def test_storage_context_manager():
    ''' ensure we can use Storage as a contextmanager '''
    with Storage() as s:
        pass

    # hopefully we don't hang here
    with Storage() as s:
        pass

    # deleting this file at this point means we closed it up.
    os.remove(DATABASE_FILE)

def test_storage_creates_needed_tables():
    ''' ensures required tables are auto created '''
    with Storage() as s:
        for tableName in REQUIRED_TABLES.keys():
            assert s.database.tableExists(tableName)

    # deleting this file at this point means we closed it up.
    os.remove(DATABASE_FILE)

def test_storage_can_add_check_for_application_tables():
    ''' ensures we can add / check for application tables '''
    with Storage() as s:
        assert not s.applicationExists('mytable')
        assert s.applicationAdd('mytable')
        assert s.applicationExists('mytable')

    # persistence check (new storage instance)
    with Storage() as s:
        assert s.applicationExists('mytable')
