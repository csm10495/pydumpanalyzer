''' file for the storage object for pda '''

import datetime
import enum
import os
import pickle
import threading

import flask

import _html
from abstract_database import AbstractDatabase, Column
from csmlog_setup import getLogger
from utility import getUniqueId, getUniqueTableName, temporaryFilePath
from windbg import WinDbg
from windows_symbol_store import WindowsSymbolStore

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_STORAGE_LOCATION = os.path.join(THIS_DIR, 'storage')
if not os.path.isdir(ROOT_STORAGE_LOCATION): os.mkdir(ROOT_STORAGE_LOCATION)
WINDOWS_SYMBOL_STORE = os.path.join(ROOT_STORAGE_LOCATION, 'WindowsSymbols')

# the following is the format of tables needed to run
REQUIRED_TABLES = {
    'Applications': [
        Column('Name',                    "TEXT"),
        Column("ApplicationTable",        "TEXT")
    ],
}

# these columns are used in all application tables
APPLICATION_UPLOADS_COLUMNS = [
    Column('UID'                , "TEXT"), # Unique Id for this transaction
    Column('Timestamp'          , "TEXT"), # timestamp for adding this
    Column('UploaderIP'         , "TEXT"), # ip address of uploader
    Column('OperatingSystem'    , 'TEXT'), # OS for this artifact
    Column('Tag'                , 'TEXT'), # optional tag for this
    Column('ApplicationVersion' , 'TEXT'), # optional version for the app this artifact came from
    Column('SymbolsFile'        , 'BLOB'), # blob of associated symbols file
    Column('SymbolsFileName'    , 'TEXT'), # name of symbols file
    Column('ExecutableFile'     , 'BLOB'), # blob of associated executable file
    Column('ExecutableFileName' , 'TEXT'), # name of executable file
    Column('CrashDumpFile'      , 'BLOB'), # blob of associated crash dump file
    Column('CrashDumpFileName'  , 'TEXT'), # name of crash dump file
    Column('CrashDumpAnalysis'  , 'BLOB'), # blob of the crash dump analysis file (pickled)
]

logger = getLogger(__file__)

class SupportedOperatingSystems(enum.Enum):
    ''' enum for all operating systems supported '''
    WINDOWS = "Windows"

    @classmethod
    def isValidValue(cls, val):
        ''' returns True if the given string is a valid enum value '''
        return val in cls.getValues()

    @classmethod
    def getValues(cls):
        ''' gets a list of values for this enum '''
        return [v.value for v in cls.__members__.values()]

class Storage(object):
    ''' object that keeps track of the various storage needed by this object '''
    DATABASE_FILE = os.path.join(ROOT_STORAGE_LOCATION, 'database.sqlite')
    _LOCK = threading.Lock()
    def __enter__(self):
        ''' called when entering via a context manager '''
        Storage._LOCK.acquire()
        self.database = AbstractDatabase(self.DATABASE_FILE, commitOnClose=True)
        self.database.open()
        self.windowsSymbolStore = WindowsSymbolStore(WINDOWS_SYMBOL_STORE)
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
            if not self.database.tableExists(tableRow.ApplicationTable):
                assert self.database.createTable(tableRow.ApplicationTable, [])
            assert self.database.ensureTableHasAtLeastTheseColumns(tableRow.ApplicationTable, APPLICATION_UPLOADS_COLUMNS)

    def applicationExists(self, name):
        ''' called to check if an application exists in our tables '''
        return bool(self.database.execute('SELECT * FROM Applications WHERE Name="%s"' % name).fetchone())

    def applicationAdd(self, name):
        ''' called to add a table for this application '''
        applicationTableName = getUniqueTableName()

        if not self.applicationExists(name) and self.database.createTable(applicationTableName, APPLICATION_UPLOADS_COLUMNS):
            if not self.database.addRow('Applications', {
                'Name' : name,
                'ApplicationTable' : applicationTableName
            }):
                logger.error("failed to add application row: %s" % name)
                return False

            return True
        else:
            logger.error("failed to create a table for: %s with a table name of %s" % (name, applicationTableName))
            return False

    def getApplicationTableName(self, applicationName):
        ''' gets an application's table name '''
        result = self.database.execute("SELECT * FROM Applications WHERE Name=\"%s\"" % applicationName).fetchone()
        if result:
            return result.ApplicationTable
        return False

    def getApplicationNameFromTable(self, tableName):
        ''' gets the name of an app from the table name '''
        result = self.database.execute("SELECT * FROM Applications WHERE ApplicationTable=\"%s\"" % tableName).fetchone()
        if result:
            return result.Name
        return False

    def getApplicationCell(self, applicationName, rowUid, column):
        ''' finds the application database, then goes to a specific row and returns the given column '''
        tableName = self.getApplicationTableName(applicationName)
        if not tableName:
            logger.warning("Application doesn't exist")
            return False

        result = self.database.execute("SELECT * FROM `%s` WHERE UID=\"%s\"" % (tableName, rowUid)).fetchone()
        if not result:
            logger.warning("UID didn't exist: %s" % rowUid)
            return False

        if not hasattr(result, column):
            logger.warning("Column %s doesn't exist" % column)
            return False

        return getattr(result, column)

    def setApplicationCell(self, applicationName, rowUid, column, value):
        ''' finds the application database, then goes to a specific row and modifies the given column to the given value '''
        tableName = self.getApplicationTableName(applicationName)
        if not tableName:
            logger.warning("Application doesn't exist")
            return False

        result = self.database.execute("UPDATE `%s` SET `%s` = ? WHERE UID = ?" % (tableName, column), [value, rowUid])
        if not result:
            logger.warning("Unable to update cell with row UID: %s" % rowUid)
            return False

        return True

    def getApplicationTable(self, applicationName):
        ''' used to get back a view of the given application's table '''
        tableName = self.getApplicationTableName(applicationName)
        if not tableName:
            logger.warning("User requested application (%s) which doesn't have a matching table" % applicationName)
            flask.abort(404)

        cursor = self.database.execute("SELECT * FROM %s" % tableName)
        table = _html.HtmlTable.fromCursor(cursor, classes='content', name=applicationName)
        table.addColumn('Actions')

        def getLinks(row):
            ''' helper to get links to files in the current table '''
            rowUid = table.getCellFromRow(row, 'UID')
            for columnName in 'SymbolsFile', 'ExecutableFile', 'CrashDumpFile':
                url = flask.url_for("getFile", applicationName=applicationName, rowUid=rowUid, column=columnName)
                index = table.tableHeaders.index(columnName)
                cellValue = self.getApplicationCell(applicationName, rowUid, columnName + "Name")
                if cellValue:
                    row[index] = _html.getHtmlLinkString(url, cellValue)

            actionRowIdx = table.tableHeaders.index('Actions')
            row[actionRowIdx] = _html.getDropLeft('...', [
                ('Show Analysis', flask.url_for('getAnalysis', applicationName=applicationName, rowUid=rowUid, useCache=True)),
                ('Show Analysis (No Cache)', flask.url_for('getAnalysis', applicationName=applicationName, rowUid=rowUid, useCache=False))
            ])

            return row

        table.modifyAllRows(getLinks)
        table.removeColumns(['SymbolsFileName', 'ExecutableFileName', 'CrashDumpFileName', 'CrashDumpAnalysis'])

        return table

    def getAnalysis(self, applicationName, rowUid, useCache=True):
        ''' internal function called to get the Analysis object for the given rowUid '''
        if useCache:
            dataBlob = self.getApplicationCell(applicationName, rowUid, 'CrashDumpAnalysis')
            if dataBlob:
                logger.debug("Returning from cache, analysis: %s / %s" % (applicationName, rowUid))
                try:
                    return pickle.loads(dataBlob)
                except Exception as ex:
                    logger.error("Failed to de-serialize pickle data: %s" % str(ex))

        logger.info("Attempting to generate Analysis for: %s / %s" % (applicationName, rowUid))

        crashDumpBinary = self.getApplicationCell(applicationName, rowUid, 'CrashDumpFile')
        if not crashDumpBinary:
            logger.error("Crash dump file was not available with the given uid")
            flask.abort(404)

        operatingSystem = self.getApplicationCell(applicationName, rowUid, 'OperatingSystem')
        if not operatingSystem:
            logger.error("Operating system was not available with the given uid... this should not be possible!")
            flask.abort(404)

        with temporaryFilePath() as crashDumpBinaryFilePath:
            with open(crashDumpBinaryFilePath, 'wb') as f:
                f.write(crashDumpBinary)

            if operatingSystem == SupportedOperatingSystems.WINDOWS.value:
                debugger = WinDbg(crashDumpBinaryFilePath, WINDOWS_SYMBOL_STORE)
            else:
                logger.error("Unsupported OS is somehow in the database")
                logger.abort(500)

            analysis = debugger.getAnalysis()
        analysisAsPickledData = pickle.dumps(analysis)
        if not self.setApplicationCell(applicationName, rowUid, 'CrashDumpAnalysis', analysisAsPickledData):
            logger.warning("Failed to save off crash dump analysis pickle data.. uid=%s" % rowUid)
            flask.abort(500)

        return analysis

    def getWindowsSymbolFilePath(self, path):
        ''' internal function used to serve back a Windows Symbol Store path '''
        fullPath = os.path.abspath(os.path.join(WINDOWS_SYMBOL_STORE, path))

        # the right side of the and is to make sure that somehow we aren't out of the symbols directory
        if os.path.isfile(fullPath) and os.path.normpath(WINDOWS_SYMBOL_STORE) in os.path.normpath(fullPath):
            return fullPath

        flask.abort(404)

    def addFromAddRequest(self, request):
        ''' called by the flask app to add something for the given request to addHandler
        Note that this will return the status that will be returned by addHandler() '''

        def failAnd401(msg):
            ''' helper to at this moment and log to the logger with the given message '''
            logger.error(msg)
            flask.abort(flask.Response(msg, 401))

        # verify valid request 1st.

        # need to have the operating system set
        operatingSystem = request.form.get("OperatingSystem")
        if not operatingSystem:
            failAnd401("request was missing required field: OperatingSystem")

        if not SupportedOperatingSystems.isValidValue(operatingSystem):
            failAnd401("request's OperatingSystem is not supported: %s. Valid options: %s" % (operatingSystem, str(SupportedOperatingSystems.getValues())))

        # need to have the application set
        application = request.form.get("Application")
        if not application:
            failAnd401("request was missing required field: Application")

        # need at least one of: SymbolsFile, ExecutableFile, CrashDumpFile
        symbolsFile = request.files.get("SymbolsFile")
        executableFile = request.files.get("ExecutableFile")
        crashDumpFile = request.files.get("CrashDumpFile")

        if not (symbolsFile or executableFile or crashDumpFile):
            failAnd401("request needed to include at least one of the following: SymbolsFile, ExecutableFile, CrashDumpFile")

        # if we made it here, the request is valid

        # ensure we have a table for this application
        if not self.applicationExists(application):
            if not self.applicationAdd(application):
                failAnd401("unable to add application with name: %s" % application)

        applicationTableName = self.getApplicationTableName(application)

        # get binary data
        symbolsFileBinary = symbolsFile.read() if symbolsFile else None
        executableFileBinary = executableFile.read() if executableFile else None
        crashDumpFileBinary = crashDumpFile.read() if crashDumpFile else None

        # get binary file names
        symbolsFileName = symbolsFile.filename if symbolsFile else None
        executableFileName = executableFile.filename if executableFile else None
        crashDumpFileName = crashDumpFile.filename if crashDumpFile else None

        # add objects to symbol store
        if operatingSystem == SupportedOperatingSystems.WINDOWS.value:
            if symbolsFileBinary:
                # additions must have original name (to work in symbol store)
                with temporaryFilePath(fileName=symbolsFileName) as temp:
                    with open(temp, 'wb') as f:
                        f.write(symbolsFileBinary)

                    try:
                        self.windowsSymbolStore.add(temp, compressed=True)
                    except Exception as ex:
                        failAnd401("Failed to add symbols file to store: %s" % str(ex))

            if executableFileBinary:
                 # additions must have original name (to work in symbol store)
                with temporaryFilePath(fileName=executableFileName) as temp:
                    with open(temp, 'wb') as f:
                        f.write(executableFileBinary)

                    try:
                        self.windowsSymbolStore.add(temp, compressed=True)
                    except Exception as ex:
                        failAnd401("Failed to add executable file to store: %s" % str(ex))

        # add to database
        uid = getUniqueId()
        if not self.database.addRow(applicationTableName, {
            'UID' : uid,
            'Timestamp' : str(datetime.datetime.now()),
            'UploaderIP' : request.remote_addr,
            'OperatingSystem' : operatingSystem,
            'Tag' : request.form.get('Tag'),
            'ApplicationVersion' : request.form.get('ApplicationVersion'),
            'SymbolsFile' : symbolsFileBinary,
            'SymbolsFileName' : symbolsFileName,
            'ExecutableFile' : executableFileBinary,
            'ExecutableFileName' : executableFileName,
            'CrashDumpFile' : crashDumpFileBinary,
            'CrashDumpFileName' : crashDumpFileName,
            # CrashDumpAnalysis is not given here, it can be generated later.
        }):
            failAnd401("Unable to add to database")

        # success!
        return "Successfully added! UID: %s" % uid


if __name__ == '__main__':
    s = Storage().__enter__()
