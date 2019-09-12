''' home to the abstract database class which is used for working with the a sqlite3 database '''
import collections
import os
import sqlite3
import threading

from csmlog_setup import getLogger

logger = getLogger(__file__)

Column = collections.namedtuple('Column', ['Name', 'Type'])

def _rowToNamedTuple(cursor, row):
    """ Returns sqlite rows as named tuples """
    fields = [col[0] for col in cursor.description]
    Row = collections.namedtuple("Row", fields)
    return Row(*row)

class SqlStatementUnsafeException(Exception):
    ''' exception to say the query did not look safe to execute '''
    pass

class AbstractDatabase(object):
    '''
    wrapper for working with the application database
    '''

    _LOCK = threading.Lock() # lock for async access

    def __init__(self, databaseFile=':memory:', commitOnClose=True):
        ''' initializer, takes in the location of the database. By default it is :memory:
        Optionally, the user can choose to commit on closing this or not at all. '''
        self.databaseFile = databaseFile
        self.database = None
        self.commitOnClose = commitOnClose

    def __enter__(self):
        ''' called when entering via a context manager '''
        AbstractDatabase._LOCK.acquire()
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        ''' called when exiting via a context manager '''
        self.close()
        AbstractDatabase._LOCK.release()

    def open(self):
        ''' opens the connection to the database '''
        self.database = sqlite3.connect(self.databaseFile, isolation_level=None)
        self.database.row_factory = _rowToNamedTuple

        # at this point we own the responsibility of commiting on our own since
        #  we are in our own transaction.
        self.execute('BEGIN')

    def close(self):
        ''' closes the connect to the database '''
        if self.database:
            if self.commitOnClose:
                self.database.commit()
            self.database.close()
            self.database = None

    @classmethod
    def _ensureSqlStatementSafe(cls, sqlStatement):
        ''' not great sql injection protection '''
        if ';' in sqlStatement:
            raise SqlStatementUnsafeException("%s is not safe due to having a semicolon" % sqlStatement)

    def execute(self, sqlStatement, *args):
        ''' executes the given sqlStatement, wants to return a cursor '''
        self._ensureSqlStatementSafe(sqlStatement)

        logger.info("Executing: %s" % sqlStatement)
        try:
            cursor = self.database.execute(sqlStatement, *args)
            return cursor
        except Exception as ex:
            logger.error("Got an exception executing: %s" % str(ex))
            raise

    def booleanExecute(self, sqlStatement, *args):
        ''' calls execute() but returns True if any cursor comes back, False otherwise '''
        try:
            self.execute(sqlStatement, *args)
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
            return self.execute('PRAGMA table_info(`%s`)' % tableName).fetchall()

        return False

    def tableExists(self, tableName):
        ''' returns true if the given table exists '''
        return bool(self.execute("PRAGMA table_info('%s')" % tableName).fetchall())

    def createTable(self, tableName, columns):
        ''' creates the given table with the given columns. The columns should be a list of Column tuples.'''
        sqlStatement = 'CREATE TABLE {tableName} (IdKey INTEGER PRIMARY KEY AUTOINCREMENT, '.format(tableName=tableName)
        for col in columns:
            sqlStatement += ('%s %s,' % (col.Name, col.Type))

        sqlStatement = sqlStatement.rstrip(', ') + ")"

        return self.booleanExecute(sqlStatement)

    def ensureTableHasAtLeastTheseColumns(self, tableName, columns):
        ''' goes to a given table and ensures that the given columns (list of Column) exist in the given table '''
        tableInfo = self.getTableInfo(tableName)
        if not tableInfo:
            logger.error("Could not get table info for table: %s" % tableName)
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
        sqlStatement = '''INSERT INTO `{tableName}` ({keys}) VALUES ({valuesAsQuestionMarks})'''.format(
            tableName=tableName,
            keys=','.join('`%s`' % a for a in list(rowAsDict.keys())),
            valuesAsQuestionMarks=','.join(['?'] * len(rowAsDict))
        )
        return self.booleanExecute(sqlStatement, list(rowAsDict.values()))
