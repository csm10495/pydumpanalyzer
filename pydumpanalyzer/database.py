import collections
import csmlog
import os
import sqlite3
import threading
import unittest

from server import ROOT_STORAGE_LOCATION

DATABASE_FILE = os.path.join(ROOT_STORAGE_LOCATION, 'database.sqlite')
logger = csmlog.getLogger('database.py')

# Ensure our storage folder exists
try:
    os.makedirs(ROOT_STORAGE_LOCATION)
except:
    pass

Column = collections.namedtuple('Column', ['Name', 'Type'])

def _rowToNamedTuple(cursor, row):
    """ Returns sqlite rows as named tuples """
    fields = [col[0] for col in cursor.description]
    Row = collections.namedtuple("Row", fields)
    return Row(*row)

class Database(object):
    '''
    wrapper for working with the application database
    '''

    _LOCK = threading.Lock() # lock for async access

    def __init__(self, databaseFile=DATABASE_FILE):
        ''' initializer, takes in the location of the database '''
        self.databaseFile = databaseFile
        self.database = None

    def __enter__(self):
        ''' called when entering via a context manager '''
        Database._LOCK.acquire()
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        ''' called when exiting via a context manager '''
        self.close()
        Database._LOCK.acquire()

    def open(self):
        ''' opens the connection to the database '''
        self.database = sqlite3.connect(self.databaseFile)
        self.database.row_factory = _rowToNamedTuple

    def close(self):
        ''' closes the connect to the database '''
        if self.database:
            self.database.close()
            self.database = None

    def execute(self, sqlStatement):
        ''' executes the given sqlStatement, wants to return a cursor '''
        logger.info("Executing: %s" % sqlStatement)
        try:
            cursor = self.database.execute(sqlStatement)
            return cursor
        except Exception as ex:
            logger.error("Got an exception executing: %s" % str(ex))
            raise

    def booleanExecute(self, sqlStatement):
        ''' calls execute() but returns True if any cursor comes back, False otherwise '''
        try:
            self.execute(sqlStatement)
            logger.info("Successfully executed: %s" % sqlStatement)
            return True
        except Exception as ex:
            logger.warning("Failed when executing: %s...\n Failure: %s" % (sqlStatement, ex))
            return False

    def getTableInfo(self, tableName):
        '''
        returns the table info for a given table.
            Generally this is a list of Row tuples.
                Useful: .name/ .type within those tuples.
        '''
        if self.tableExists(tableName):
            return self.execute('PRAGMA table_info(%s)' % tableName).fetchall()

        return False

    def tableExists(self, tableName):
        ''' returns true if the given table exists '''
        return bool(self.execute("PRAGMA table_info('%s')" % tableName).fetchall())

    def createTable(self, tableName, columns):
        ''' creates the given table with the given columns. The columns should be a list of Column tuples.'''
        sqlStatement = 'CREATE TABLE {tableName} (Id INTEGER PRIMARY KEY AUTOINCREMENT, '.format(tableName=tableName)
        for col in columns:
            sqlStatement += ('%s %s,' % (col.Name, col.Type))

        sqlStatement = sqlStatement.rstrip(', ') + ")"

        return self.booleanExecute(sqlStatement)

    def ensureTableHasAtLeastTheseColumns(self, tableName, columns):
        ''' goes to a given table and ensures that the given columns (list of Column) exist in the given table '''
        tableInfo = self.getTableInfo(tableName)
        if not tableInfo:
            logger.error("Could not get table info for table: %s" % tableInfo)
            return False

        for col in columns:
            # if it already exists, don't alter the table
            if not [a for a in tableInfo if a.name == col.Name and a.type == col.Type]:
                sqlStatement = 'ALTER TABLE {tableName} ADD {name} {typ}'.format(tableName=tableName,
                                                                                name=col.Name,
                                                                                typ=col.Type)

                if not self.booleanExecute(sqlStatement):
                    logger.error("Failed to add column: %s!" % (col.Name))
                    return False

        return True

    def addRow(self, tableName, rowAsDict):
        ''' adds the given dict of column name -> value to the given table '''
        sqlStatement = 'INSERT INTO {tableName} ({keys}) VALUES ({values})'.format(tableName=tableName,
                                                                                   keys=','.join(list(rowAsDict.keys())),
                                                                                   values=','.join(map(lambda x: '"' + str(x) + '"', list(rowAsDict.values()))))
        return self.booleanExecute(sqlStatement)

class TestDatabase(unittest.TestCase):
    ''' quick unit tests for the database class '''

    def setUp(self):
        ''' called at the start of each test case '''
        logger.info("starting test case: %s" % self.id())
        self.database = Database(':memory:')
        self.database.open()

    def tearDown(self):
        ''' called at the end of each test case '''
        self.database.close()
        logger.info("ending test case: %s" % self.id())

    def test_create_table(self):
        ''' ensure we can create tables '''
        assert not self.database.tableExists('MyTable')

        assert self.database.createTable('MyTable', [
            Column("ColumnName", "TEXT")
        ])

        assert not self.database.createTable('MyTable', [
            Column("ColumnName", "TEXT")
        ])

        assert self.database.tableExists('MyTable')
        assert not self.database.tableExists('MyTable2')

    def test_add_row(self):
        ''' ensure we can add rows to a given table '''
        assert not self.database.addRow('MyTable', {
            "ColumnName" : "ColumnData"
        })

        assert self.database.createTable('MyTable', [
            Column("ColumnName", "TEXT")
        ])

        assert self.database.addRow('MyTable', {
            "ColumnName" : "ColumnData"
        })

        assert self.database.execute('SELECT * FROM MYTABLE').fetchall()[0].ColumnName == 'ColumnData'

    def test_ensure_has_columns(self):
        ''' ensure we can add columns if needed '''

        assert self.database.createTable('MyTable', [
            Column("TextColumn1", "TEXT")
        ])

        assert self.database.ensureTableHasAtLeastTheseColumns('MyTable', [
            Column('TextColumn1', "TEXT"),
            Column('TextColumn2', "INT"),
            Column('TextColumn3', "TEXT"),
        ])

        assert self.database.addRow('MyTable', {
            'TextColumn1' : 'Hello',
            'TextColumn2' : 123,
        })

        lastInsert = self.database.execute('SELECT * from MYTABLE').fetchall()[-1]
        assert lastInsert.TextColumn2 == 123
        assert lastInsert.TextColumn1 == 'Hello'

        assert not self.database.ensureTableHasAtLeastTheseColumns('MyTable', [
            Column('TextColumn1', "TEXT"),
            Column('TextColumn2', "INT"),
            Column('TextColumn3', "INT"), # wrong type!
        ])

