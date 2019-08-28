import collections
import contextlib
import datetime
import enum
import os
import pickle
import shelve
import shutil
import subprocess
import tempfile
import threading
import uuid
from io import BytesIO

from flask import (Flask, Response, escape, jsonify, render_template, request,
                   send_file)

from csmlog_setup import getLogger
from windbg import WinDbg

CACHED_ANALYSIS_FILE_NAME = 'analysis.pickle'
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_STORAGE_LOCATION = os.path.join(THIS_DIR, 'storage')
DATABASE_LOCATION = os.path.join(ROOT_STORAGE_LOCATION, 'server.shelf')
SYM_STORE = r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\symstore.exe"
WINDOWS_SYMBOLS_LOCATION = os.path.join(ROOT_STORAGE_LOCATION, "WindowsSymbols")

class SupportedOperatingSystems(enum.Enum):
    WINDOWS = "Windows"
    LINUX = "Linux"

VERISON = "1.0" # todo.. get from package

Addition = collections.namedtuple("Addition", ("UploaderIp", "UUID", "Timestamp", "SymbolsPath", "ExePath", "DumpPath", "OS"))
Addition2 = collections.namedtuple("Addition", ("UploaderIp", "UUID", "Timestamp", "SymbolsPath", "ExePath", "DumpPath", "OS", 'Tag'))

app = Flask("PyDumpAnalyzerServer")
shelfLock = threading.Lock()

def _getHtmlLinkString(url, text):
    return r'<a href="%s">%s</a>' % (url, text)

def _getHtmlImage(url, style='display:block;', width='100%%', height='100%%', caption="A caption", onclick=""):
    return '<img style="%s" width="%s" height="%s" src="%s" title="%s" onclick="%s"/>' % (style, width, height, url, caption, onclick)

def _toHtmlSafe(s):
    return str(s).replace('#', '').replace(' ', '')

class HtmlTable(object):
    def __init__(self, headers):
        self.headers = [_toHtmlSafe(h) for h in headers]
        self.id = 'id_' + _toHtmlSafe(uuid.uuid4())
        self.rows = []
    def addRow(self, row):
        self.rows.append(row)
    def reverse(self):
        self.rows = self.rows[::-1]
    def __str__(self):
        HTML = '''
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
<script>
$(document).ready(function(){{
  $("#input_{id}").on("keyup", function() {{
    var value = $(this).val().toLowerCase();
    $("#table_{id} tr").filter(function() {{
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    }});
  }});
}});
</script>

<input id="input_{id}" type="text" placeholder="Search..." style="display: none">
{searchButton}

<table style="width:100%">
    <thead style="text-align: left">
        {headers}
    </thead>
    <tbody id="table_{id}">
        {rows}
    </tbody>
</table
'''

        headerText = '<tr>\n'
        for row in self.headers:
            headerText += '<th>%s</th>\n' % (row)
        headerText += '</tr>\n'

        rowText = ''
        for row in self.rows:
            rowText += '<tr>\n'
            for colIdx, value in enumerate(row):
                rowText += '<td>%s</td>\n' % (value)
            rowText += '</tr>\n'

        return HTML.format(id=self.id,
                           rows=rowText,
                           headers=headerText,
                           searchButton=_getHtmlImage("https://image.flaticon.com/icons/png/512/55/55369.png",
                                                      height="20", width="auto", caption="Search this table...",
                                                      onclick="document.getElementById('input_{id}').style.display='block';event.target.style.display='none'".format(id=self.id))
                          )

class Database(object):
    '''
    the shelf/database has the following tables:
        additions:
            {uuid -> Addition}
        crashes:
            {idx -> uuid}
    '''
    def __enter__(self):
        try:
            os.makedirs(ROOT_STORAGE_LOCATION)
        except:
            pass

        shelfLock.acquire()
        self._rawShelf = shelve.open(DATABASE_LOCATION, writeback=True)
        return self

    def __exit__(self, type, value, traceback):
        self._rawShelf.close()
        shelfLock.release()

    def getAdditionsDict(self):
        if 'additions' not in self._rawShelf:
            self._rawShelf['additions'] = {}

        return self._rawShelf['additions']

    def getCrashesList(self):
        if 'crashes' not in self._rawShelf:
            self._rawShelf['crashes'] = []

        return self._rawShelf['crashes']

    def getAdditionsDirectory(self):
        return os.path.join(ROOT_STORAGE_LOCATION, 'Additions')

    def getAdditionDestinationDirectory(self, uuid):
        uuidPath = os.path.join(self.getAdditionsDirectory(), str(uuid))
        return uuidPath

    def addToWindowsSymbolStore(self, objPath, uid):
        assert os.path.isfile(SYM_STORE), "Could not find symstore.exe! Unable to store symbols in Windows symbol store"

        # set the comment as the uid
        subprocess.call([
            SYM_STORE,
            "add",
            "/compress",
            "/s",
            WINDOWS_SYMBOLS_LOCATION,
            "/t",
            os.path.splitext(objPath)[0],
            "/f",
            objPath,
            "/c",
            uid,
        ])

    def addAddition(self, request):
        uid = uuid.uuid4()
        ip = request.remote_addr

        symbolFile = request.files.get('symbols')
        executableFile = request.files.get('exe')
        crashDump = request.files.get('dump')
        operatingSystem = request.form.get('os')
        tag = request.form.get('tag')

        if operatingSystem not in [v.value for v in SupportedOperatingSystems.__members__.values()]:
            return jsonify({
                "uuid" : str(uid),
                "status" : "operating system is not supported. Should have been one of: %s" % [v.value for v in SupportedOperatingSystems.__members__.values()],
            }), 400
        operatingSystemEnumValue = SupportedOperatingSystems(operatingSystem).value

        if not (symbolFile or executableFile or crashDump):
            return jsonify({
                "uuid" : str(uid),
                "status" : "Neither symbols/exe/dump file given",
            }), 400

        destDir = self.getAdditionDestinationDirectory(uid)
        os.makedirs(destDir)

        symbolFileName = None
        executableFileName = None
        crashDumpFileName = None

        if symbolFile:
            symbolFileName = os.path.join(destDir, symbolFile.filename)
            symbolFile.save(symbolFileName)
            if operatingSystemEnumValue == SupportedOperatingSystems.WINDOWS.value:
                self.addToWindowsSymbolStore(symbolFileName, str(uid))
            symbolFileName = os.path.relpath(symbolFileName, ROOT_STORAGE_LOCATION)

        if executableFile:
            executableFileName = os.path.join(destDir, executableFile.filename)
            executableFile.save(executableFileName)
            if operatingSystemEnumValue == SupportedOperatingSystems.WINDOWS.value:
                self.addToWindowsSymbolStore(executableFileName, str(uid))
            executableFileName = os.path.relpath(executableFileName, ROOT_STORAGE_LOCATION)

        if crashDump:
            crashDumpFileName = os.path.join(destDir, crashDump.filename)
            crashDump.save(crashDumpFileName)
            crashDumpFileName = os.path.relpath(crashDumpFileName, ROOT_STORAGE_LOCATION)

            # add to crashes db
            self.getCrashesList().append(uid)

        self.getAdditionsDict()[str(uid)] = Addition(ip, uid, datetime.datetime.utcnow(), symbolFileName,
                                                     executableFileName, crashDumpFileName, operatingSystemEnumValue,
                                                     tag)

        return jsonify({
            "uuid" : str(uid),
            "status" : "successfully uploaded the given files",
        }), 200

@app.route('/get/version')
def version():
    return jsonify({
        'version' : VERISON
    })

@app.route('/add', methods=['POST'])
def add():
    with Database() as db:
        return db.addAddition(request)

@app.route('/get/all', methods=['GET'])
def getAll():
    with Database() as db:
        return jsonify(dict(db._rawShelf)), 200

@app.route('/get/zip/<uuid>', methods=['GET'])
def getZip(uuid):
    fullDir = None
    with Database() as db:
        if uuid in db.getAdditionsDict():
            fullDir = db.getAdditionDestinationDirectory(uuid)

    if not fullDir:
        return fullDir({
            "uuid" : str(uid),
            "status" : "failure due to non-existant uuid",
        }), 400

    # get temp location
    with tempfile.NamedTemporaryFile() as t:
        tempFilePath = t.name

    try:
        shutil.make_archive(tempFilePath, 'zip', fullDir)
        with open(tempFilePath + '.zip', 'rb') as f:
            fullBinaryBytesIo = BytesIO(f.read())
            fullBinaryBytesIo.seek(0)
    finally:
            os.remove(tempFilePath + '.zip')

    return send_file(fullBinaryBytesIo, attachment_filename=uuid + ".zip")

@app.route('/get/windows/symbolstore/<path:path>', methods=['GET'])
def getWindowsSymbolStore(path):
    fullPath = os.path.abspath(os.path.join(WINDOWS_SYMBOLS_LOCATION, path))

    # the right side of the and is to make sure that somehow we aren't out of the symbols directory
    if os.path.isfile(fullPath) and os.path.normpath(WINDOWS_SYMBOLS_LOCATION) in os.path.normpath(fullPath):
        return send_file(fullPath)

    return jsonify({
        'status' : 'file does not exist'
    }), 404

@app.route('/show/crashes', methods=['GET'])
def showCrashList():
    retStr = ''
    table = HtmlTable(["Crash #", "Submission UUID", "Dump File", "Tag", "UTC Timestamp", "OS", "Actions"])
    with Database() as db:
        crashes = db.getCrashesList()
        for idx, itm in enumerate(crashes):
            addition = db.getAdditionsDict()[str(itm)]
            table.addRow([_getHtmlLinkString('/show/crashes/%s' % str(itm),
                                            str(idx)),
                           _getHtmlLinkString('/get/zip/%s' % str(itm),
                                              str(itm)),
                                              os.path.basename(addition.DumpPath),
                           getattr(addition, 'Tag', None),
                           addition.Timestamp,
                           addition.OS,
                           _getHtmlLinkString('/do/delete/cache/%s' % str(itm),
                                              _getHtmlImage("https://www.recycling.com/wp-content/uploads/recycling%20symbols/black/Black%20Recycling%20Symbol%20%28U%2B267B%29.jpg",
                                              width="20",
                                              height="",
                                              caption="Delete cached analysis file"))
                         ])
        table.reverse()

    return render_template('base.html', html_content=str(table))

@app.route('/show/crashes/<uuid>', methods=['GET'])
def showCrashAnalysis(uuid):
    with Database() as db:
        theAddition = db.getAdditionsDict().get(uuid, None)
        additionsDirectory = db.getAdditionsDirectory()
        thisUuidAdditonPath = db.getAdditionDestinationDirectory(uuid)

    if not theAddition:
        return jsonify({
            'status' : 'uuid was not found',
        }), 404

    if not theAddition.DumpPath:
        return jsonify({
            'status' : 'dump was not found for given uuid',
        }), 404

    fullDumpPath = os.path.join(ROOT_STORAGE_LOCATION, theAddition.DumpPath)

    # exe is hopefully in symbol store, so if we don't have it here, it should be ok
    fullExePath = None
    if theAddition.ExePath:
        fullExePath = os.path.join(ROOT_STORAGE_LOCATION, theAddition.ExePath)

    # we may already have the analysis saved off. If we do use it. Don't regen
    cachedAnalysisFile = os.path.join(thisUuidAdditonPath, CACHED_ANALYSIS_FILE_NAME)
    if os.path.isfile(cachedAnalysisFile):
        with open(cachedAnalysisFile, 'rb') as f:
            analysis = pickle.loads(f.read())
    elif theAddition.OS == SupportedOperatingSystems.WINDOWS.value:
        analysis = WinDbg(fullDumpPath, WINDOWS_SYMBOLS_LOCATION, fullExePath).getAnalysis()
        with open(cachedAnalysisFile, 'wb') as f:
            f.write(pickle.dumps(analysis))
    else:
        return jsonify({
            "status" : "unable to debug the given uuid",
        }), 400

    return render_template('analysis.html', uuid=uuid, analysis=escape(str(analysis)).splitlines())

@app.route('/', methods=['GET'])
def showHome():
    return render_template('home.html')


@app.route('/do/delete/cache/<uuid>', methods=['GET'])
def deleteAnalysisCache(uuid):
    with Database() as db:
        thisUuidAdditonPath = db.getAdditionDestinationDirectory(uuid)

    cachedAnalysisFile = os.path.join(thisUuidAdditonPath, CACHED_ANALYSIS_FILE_NAME)
    if os.path.isfile(cachedAnalysisFile):
        os.remove(cachedAnalysisFile)
        return jsonify({
            "status" : "cached analysis file removed"
        }), 200

    return jsonify({
            "status" : "cached analysis file did not exist, so nothing happened"
    }), 200

if __name__ == '__main__':
    app.url_map.strict_slashes = False
    app.run()
