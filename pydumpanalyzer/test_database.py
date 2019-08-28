''' this file contains tests for the database module '''

import csmlog
import unittest
from database import Database, Column

logger = csmlog.getLogger(__file__)

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

