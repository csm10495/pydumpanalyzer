import collections
import contextlib
import datetime
import enum
import os
import shelve
import shutil
import subprocess
import tempfile
import threading
import uuid
from io import BytesIO

from flask import Flask, jsonify, request, send_file

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_STORAGE_LOCATION = os.path.join(THIS_DIR, 'storage')
DATABASE_LOCATION = os.path.join(ROOT_STORAGE_LOCATION, 'server.shelf')
SYM_STORE = r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\symstore.exe"
WINDOWS_SYMBOLS_LOCATION = os.path.join(ROOT_STORAGE_LOCATION, "WindowsSymbols")

VERISON = "1.0" # todo.. get from package

Addition = collections.namedtuple("Addition", ("UploaderIp", "UUID", "Timestamp", "SymbolsPath", "ExePath", "DumpPath"))

app = Flask("PyDumpAnalyzerServer")
shelfLock = threading.Lock()

class Database(object):
    '''
    the shelf/database has the following tables:
        additions:
            {uuid -> Addition}
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

    def getAdditionsList(self):
        if 'additions' not in self._rawShelf:
            self._rawShelf['additions'] = {}

        return self._rawShelf['additions']

    def getDestinationDirectory(self, uuid):
        uuidPath = os.path.join(ROOT_STORAGE_LOCATION, 'Additions', str(uuid))
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
        if not (symbolFile or executableFile or crashDump):
            return jsonify({
                "uuid" : str(uid),
                "status" : "Neither symbols/exe/dump file given",
            }), 400

        destDir = self.getDestinationDirectory(uid)
        os.makedirs(destDir)

        symbolFileName = None
        executableFileName = None
        crashDumpFileName = None

        if symbolFile:
            symbolFileName = os.path.join(destDir, symbolFile.filename)
            symbolFile.save(symbolFileName)
            if symbolFileName.endswith('.pdb'):
                self.addToWindowsSymbolStore(symbolFileName, str(uid))
            symbolFileName = os.path.relpath(symbolFileName, ROOT_STORAGE_LOCATION)

        if executableFile:
            executableFileName = os.path.join(destDir, executableFile.filename)
            executableFile.save(executableFileName)
            if executableFileName.endswith('.exe'):
                self.addToWindowsSymbolStore(executableFileName, str(uid))
            executableFileName = os.path.relpath(executableFileName, ROOT_STORAGE_LOCATION)

        if crashDump:
            crashDumpFileName = os.path.join(destDir, crashDump.filename)
            crashDump.save(crashDumpFileName)
            crashDumpFileName = os.path.relpath(crashDumpFileName, ROOT_STORAGE_LOCATION)

        self.getAdditionsList()[str(uid)] = Addition(ip, uid, datetime.datetime.utcnow(), symbolFileName, executableFileName, crashDumpFileName)

        return jsonify({
            "uuid" : str(uid),
            "status" : "successfully uploaded the given files",
        }), 200

@app.route('/')
def root():
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
        if uuid in db.getAdditionsList():
            fullDir = db.getDestinationDirectory(uuid)

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

if __name__ == '__main__':
    app.run()
