''' this contains tests for the _html.py file '''

import pytest

from _html import *
from abstract_database import AbstractDatabase, Column

def test_html_link_string():
    ''' ensures getHtmlLinkString works as expected '''
    URL = 'https://google.com'
    TXT = 'Google'
    assert getHtmlLinkString(URL, TXT) == r'<a href="%s">%s</a>' % (URL, TXT)

def test_invalid_html_table_row():
    ''' ensures that a row with the incorrect number of columns raises properly '''
    table = HtmlTable(['A', 'B', 'C'])
    assert table.__html__()

    with pytest.raises(ValueError):
        table.addRow(['OnlyOne'])

    table.addRow(['One', 'Two', 'Three'])

def test_search_can_be_added():
    ''' ensures we can addSearch '''
    table = HtmlTable(['A', 'B', 'C'], addSearch=False)
    assert table.__html__()

    assert 'This is code for search' not in table.__html__()

    table = HtmlTable(['A', 'B', 'C'], addSearch=True)
    assert table.__html__()

    assert 'This is code for search' in table.__html__()

def test_class_can_be_set():
    ''' ensures we can set the classes on a table '''
    table = HtmlTable(['A', 'B', 'C'])
    assert table.__html__()

    assert 'class=\"\"' in table.__html__()

    CLASSNAME = 'the class'
    table = HtmlTable(['A', 'B', 'C'], classes=CLASSNAME)
    assert ('class=\"%s\"' % CLASSNAME) in table.__html__()

def test_can_set_name():
    ''' ensures we can set the name on a table '''
    table = HtmlTable(['A', 'B', 'C'], name="TheName")
    assert table.__html__()

    assert 'TheName</h2>' in table.__html__()

def test_id_is_unique():
    ''' ensures that the id is unique '''
    ids = [HtmlTable([]).id for i in range(100)]
    assert len(ids) == len(set(ids))

def test_from_cursor():
    ''' ensures we can create a table from a cursor '''
    with AbstractDatabase() as db:
        assert db.createTable('OurTable', [
            Column("Column1", 'TEXT')
        ])
        assert db.addRow('OurTable', {
            'Column1' : 'MyValue'
        })

        cursor = db.execute("SELECT * FROM OurTable")
        assert cursor
        t = HtmlTable.fromCursor(cursor)
        html = t.__html__()
        assert html.count('MyValue') == 1
        assert html.count('Column1') == 1