''' this is the file for the Windows Symbol Store class '''

import os
import subprocess

from csmlog_setup import getLogger

logger = getLogger(__file__)

class WindowsSymbolStore(object):
    ''' implementation for the Windows symbol store. Contains an add() method to add an item to the symbol store '''
    SYM_STORE = r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\symstore.exe"
    def __init__(self, path):
        ''' Takes in the location to the symbol store. Uses SYM_STORE as the location to symstore.exe '''
        if not os.path.isfile(self.SYM_STORE):
            raise EnvironmentError("Can't find symstore: %s" % self.SYM_STORE)

        self.path = path

    def add(self, objPath, compressed=False):
        ''' adds the given object to the symbol store. Optionally can choose to compress the file.
        Warning: Do not use compression if this is the downstream-most store '''
        args = [
            self.SYM_STORE,
            'add',
            "/s",
            self.path,
            "/t",
            os.path.splitext(objPath)[0],
            "/f",
            objPath,
        ]

        if compressed:
            args.append('/compress')

        logger.debug("calling: %s" % args)
        output = subprocess.check_output(args)
        logger.debug("output: %s" % output)
