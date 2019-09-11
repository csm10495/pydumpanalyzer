''' this file is home to the flask-based application that is the following:
    1. Receiver and storer of symbol files and executables
    2. Receiver and storer of crash dumps
    3. Analyzer of crash dumps
    4. Windows symbol server when accessible via an endpoint
'''
import datetime
import enum
import itertools
import os
import pickle

import flask
import flask_selfdoc
from werkzeug.exceptions import HTTPException

import __version__
import _html
import utility
from csmlog_setup import enableConsoleLogging, getLogger
from storage import Storage

CACHED_ANALYSIS_FILE_NAME = 'analysis.pickle'
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_STORAGE_LOCATION = os.path.join(THIS_DIR, 'storage')
WINDOWS_SYMBOLS_LOCATION = os.path.join(ROOT_STORAGE_LOCATION, "WindowsSymbols")

app = flask.Flask("PyDumpAnalyzerFlaskApp")
auto = flask_selfdoc.Autodoc(app)
logger = getLogger(__file__)

class WEBPAGES_NAVBAR(enum.Enum):
    ''' enum with all top level web pages for the navbar '''
    API_Docs = '/show/apidocs/'

class WEBPAGES_NOT_NAVBAR(enum.Enum):
    ''' enum with all outward web pages. Ones that are in here,
    but not in WEBPAGES_NAVBAR are not shown in the navbar '''
    Add_Item = '/add'
    Home = '/'
    View_Table = '/show/table/<tableName>'

WEBPAGES = enum.Enum('WEBPAGES', [(i.name, i.value) for i in itertools.chain(WEBPAGES_NAVBAR, WEBPAGES_NOT_NAVBAR)])

@app.context_processor
def injectTemplateContext():
    ''' everything returned in this function is added to the context for all
    templates that flask renders. Only global, template driven things should be here. '''
    return {
        # this is the version of PDA...
        'pda_version' : __version__.__version__,
        'navItems' : [(a.name.replace('_', ' '), a.value) for a in list(WEBPAGES_NAVBAR)]
    }

@app.route(WEBPAGES.API_Docs.value, methods=['GET'])
@auto.doc()
def apiDocumentation():
    ''' returns a lovely documentation page of all supported APIs. Generated by flask_selfdoc. '''
    return flask.render_template('base.html', html_content=auto.html())

@app.route(WEBPAGES.Home.value, methods=['GET'])
@auto.doc()
def home():
    ''' the home page for the app '''
    with Storage() as storage:
        cursor = storage.database.execute("SELECT Name FROM Applications")
        table = _html.HtmlTable.fromCursor(cursor, classes='content', name="Applications")

    if not table:
        table = '<p>No applications have reported back to PDA... yet!</p>'
    else:
        table.modifyAllRows(lambda row: [_html.getHtmlLinkString(flask.url_for('viewTable', tableName=row[0]), row[0])])

    return flask.render_template('home.html', html_content=table)

@app.route(WEBPAGES.View_Table.value, methods=['GET'])
@auto.doc()
def viewTable(tableName):
    ''' used to give back a view of the given database table '''
    with Storage() as storage:
        if storage.database.tableExists(tableName):
            cursor = storage.database.execute("SELECT * FROM %s" % tableName)
            table = _html.HtmlTable.fromCursor(cursor, classes='content', name=tableName)
        else:
            logger.warning("User requested table (%s) which does not exist" % tableName)
            table = None

    if table:
        return flask.render_template('table_view.html', table_content=table, title=tableName)
    else:
        flask.abort(404)

@app.errorhandler(Exception)
def error_handler(e):
    ''' this will handle all http errors we may encounter with a custom template '''
    logger.error("Giving back an error: %s\n... that error was encountered serving: %s" % (str(e), flask.request.path))
    return flask.render_template('error.html', code=e.code, errString=str(e)), e.code

@app.route(WEBPAGES.Add_Item.value, methods=['POST'])
def addHandler()
    ''' this handler is called when an item is being added via a POST request. A single call to this API shall not have unrelated Symbols/Executable/CrashDump files.
        In other words, do not give an Execuable that isn't related to the given Symbols file. Do seperate API calls for unrelated files.

    Required form-data Body Fields:
    OperatingSystem: String: (Should be "Windows")
    Application:     String: The name of the application this addition is related to

    At least one of the following is also required:
    SymbolsFile:     File: Symbols file for the application (On Windows a .pdb file can be given)
    ExecutableFile:  File: The executable to be debugged later (Can be a .exe, .dll, etc.)
    CrashDumpFile:   File: The dump file to be analyzed. (On Windows, the crash dump can be sent at a different time from the ExecutableFile and SymbolsFile)

    Optional form-data Body Fields:
    ApplicationVersion: String: Version for the application
    Tag:                String: Arbitrary tag for this upload. (Can be used for later filtering)
    '''
    with Storage() as storage:
        return storage.addFromAddRequest(flask.request)


if __name__ == '__main__':
    app.url_map.strict_slashes = False
    app.run()
    enableConsoleLogging()

