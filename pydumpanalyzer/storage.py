''' file for the storage object for pda '''

import os
import threading

from abstract_database import AbstractDatabase, Column
from csmlog_setup import getLogger

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_STORAGE_LOCATION = os.path.join(THIS_DIR, 'storage')
DATABASE_FILE = os.path.join(ROOT_STORAGE_LOCATION, 'database.sqlite')

# the following is the format of tables needed to run
REQUIRED_TABLES = {
    'Applications': [
        Column('Name'           , "TEXT"),
    ],
}

# these columns are used in all application tables
APPLICATION_UPLOADS_COLUMNS = [
    Column('UID'                , "TEXT"), # Unique Id for this transaction
    Column('Timestamp'          , "TEXT"), # timestamp for adding this
    Column('UploaderIP'         , "TEXT"), # ip address of uploader
    Column('OperatingSystem'    , 'TEXT'), # OS for this artifact
    Column('Tag'                , 'TEXT'), # optional tag for this
    Column('Application'        , 'TEXT'), # optional version for the app this artifact came from
    Column('ApplicationVersion' , 'TEXT'), # optional version for the app this artifact came from
    Column('SymbolsPath'        , 'TEXT'), # path to associated symbols file
    Column('ExecutablePath'     , 'TEXT'), # path to associated executable file
    Column('CrashDumpPath'      , 'TEXT'), # path to associated crash dump file
]

logger = getLogger(__file__)

class Storage(object):
    ''' object that keeps track of the various storage needed by this object '''
    _LOCK = threading.Lock()
    def __enter__(self):
        ''' called when entering via a context manager '''
        Storage._LOCK.acquire()
        self.database = AbstractDatabase(DATABASE_FILE, commitOnClose=True)
        self.database.open()
        self._setupStorage()
        return self

    def __exit__(self, type, value, traceback):
        ''' called when exiting via a context manager '''
        self.database.close()
        Storage._LOCK.release()

    def _setupStorage(self):
        ''' called to ensure the environment is ready for storage, etc. '''
        # Ensure our storage folder exists
        try:
            os.makedirs(ROOT_STORAGE_LOCATION)
        except:
            pass

        # ensure we have required table(s)
        for requiredTablesName, requiredTableColumns in REQUIRED_TABLES.items():
            if not self.database.tableExists(requiredTablesName):
                assert self.database.createTable(requiredTablesName, [])
            if not self.database.ensureTableHasAtLeastTheseColumns(requiredTablesName, requiredTableColumns):
                raise RuntimeError("Unable to ensure we have needed table: %s" % requiredTablesName)

        for tableRow in self.database.execute("SELECT * FROM Applications").fetchall():
            assert self.database.ensureTableHasAtLeastTheseColumns(tableRow.Name, APPLICATION_UPLOADS_COLUMNS)

    def applicationExists(self, name):
        ''' called to check if an application exists in our tables '''
        return bool(self.database.execute('SELECT * FROM Applications WHERE Name="%s"' % name).fetchone())

    def applicationAdd(self, name):
        ''' called to add a table for this application '''
        if not self.database.addRow('Applications', {
            'Name' : name,
        }):
            logger.error("failed to add application row: %s" % name)
            return False

        if self.database.createTable(name, APPLICATION_UPLOADS_COLUMNS):
            self.database.database.commit()
            return True
        else:
            logger.error("failed to create a table for: %s" % name)
            return False

if __name__ == '__main__':
    s = Storage().__enter__()
