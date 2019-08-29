''' this file contains tests for the abstract_database module '''

import os
import unittest

from csmlog_setup import getLogger
from abstract_database import Column, AbstractDatabase

logger = getLogger(__file__)

class TestAbstractDatabase(unittest.TestCase):
    ''' quick unit tests for the abstract database class '''

    def setUp(self):
        ''' called at the start of each test case '''
        logger.info("starting test case: %s" % self.id())
        self.database = AbstractDatabase(':memory:')
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

    def test_ensure_commit_on_close_works(self):
        ''' ensure commitOnClose works '''
        TEST_DB_FILE = os.path.join(os.path.dirname(__file__), 'test_db.sqlite')
        if os.path.isfile(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)

        self.database = AbstractDatabase(TEST_DB_FILE, commitOnClose=False)
        self.database.open()

        assert self.database.createTable('MyTable', [
            Column("TextColumn1", "TEXT")
        ])
        assert self.database.tableExists('MyTable')

        self.database.close()

        # now the table shouldn't exist since we did not commit
        self.database = AbstractDatabase(TEST_DB_FILE, commitOnClose=True)
        self.database.open()

        assert not self.database.tableExists('MyTable')

        assert self.database.createTable('MyTable', [
            Column("TextColumn1", "TEXT")
        ])

        self.database.close()

        # now the table should exist since we did commit
        self.database = AbstractDatabase(TEST_DB_FILE)
        self.database.open()

        assert self.database.tableExists('MyTable')

        self.database.addRow('MyTable', {
            'TextColumn1': 'MyText'
        })

        assert len(self.database.execute("SELECT * FROM MyTable").fetchall()) == 1
        self.database.commitOnClose = False
        self.database.close()

        # Now make sure that row is gone
        self.database = AbstractDatabase(TEST_DB_FILE)
        self.database.open()

        assert self.database.tableExists('MyTable')

        assert len(self.database.execute("SELECT * FROM MyTable").fetchall()) == 0
        self.database.close()

        os.remove(TEST_DB_FILE)

    def test_database_as_contextmanager(self):
        ''' makes sure the context manager usage works '''
        with AbstractDatabase(':memory:') as m:
            assert m.createTable('Table2', [])
            assert m.tableExists('Table2')
