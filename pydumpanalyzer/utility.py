''' home to cross-functional utilities '''

import contextlib
import io
import os
import shutil
import tempfile
import uuid

from csmlog_setup import getLogger

logger = getLogger(__file__)

def getUniqueId():
    ''' gets a unique id string '''
    return str(uuid.uuid4())

def getUniqueTableName():
    ''' gets a psuedo random name for a table '''
    uid = getUniqueId()
    return 'table_' + uid.replace('-', '')

@contextlib.contextmanager
def temporaryFilePath(delete=True, fileName=None):
    ''' yields a path we can use for temp files... will attempt to delete it after use.
    This function will create a directory in the tempdir to ensure we can use names as we please (and not conflict
    with other threads, etc.) '''
    folderPath = None
    while True:
        folderPath = os.path.join(tempfile.gettempdir(), 'pda_' + getUniqueId())
        if not os.path.exists(folderPath):
            break

    os.mkdir(folderPath)
    if fileName is None:
        fileName = 'pda_' + getUniqueId()
    path = os.path.join(folderPath, fileName)
    try:
        yield path
    finally:
        if delete:
            shutil.rmtree(folderPath, ignore_errors=True)

def textToSafeHtmlText(s):
    ''' coerces a string into html-safe text '''
    return s.replace(' ', '&nbsp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

def zipDirectoryToBytesIo(directory):
    ''' zips a directory and returns a io.BytesIO object '''
    with temporaryFilePath() as tempPath:
        shutil.make_archive(tempPath, 'zip', directory)
        with open(tempPath + '.zip', 'rb') as f:
            fullBinaryBytesIo = io.BytesIO(f.read())
            fullBinaryBytesIo.seek(0)

        return fullBinaryBytesIo
