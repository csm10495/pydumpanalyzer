'''
Script to clone down breakpad and others in a format that we'll be using for further development.
'''

import os
import requests
import shutil
import subprocess

try:
    # py2
    raw_input
    input = raw_input
except:
    # py3
    pass

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))
LOCAL_DIR = os.path.join(THIS_FOLDER, 'local')

if __name__ == '__main__':
    print('Step 1: create local directory (for clones, etc. This stuff is not commited upstream)')
    if os.path.isdir(LOCAL_DIR):
        i = input ("%s already exists. Delete it and rerun to continue." % LOCAL_DIR)
    else:
        os.makedirs(LOCAL_DIR)

        print('Step 2: Move to local dir')
        os.chdir(LOCAL_DIR)
        
        print("Step 3: Grab version 1.8 of CLI11")
        d = requests.get("https://github.com/CLIUtils/CLI11/releases/download/v1.8.0/CLI11.hpp").content.decode()
        with open(os.path.join(LOCAL_DIR, 'CLI11.hpp'), 'w') as f:
            f.write(d)

        print('Step 4: clone depot_tools')
        subprocess.check_call('git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git', shell=True)

        print('Step 5: put depot_tools in PATH')
        depotToolsPath = os.path.join(LOCAL_DIR, 'depot_tools')
        if os.name == 'nt':
            # on windows remove all path besides normal windows/powershell since we may have an incompatible python installed that would confuse depot_tools/fetch
            os.environ['PATH'] = r"C:/windows/system32;C:\Windows\System32\WindowsPowerShell\v1.0;" + depotToolsPath
        else:
            os.environ['PATH'] = depotToolsPath + os.pathsep + os.environ['PATH']

        print('Step 6: fetch breakpad')
        os.mkdir('breakpad')
        os.chdir('breakpad')
        subprocess.check_call(['fetch', 'breakpad'], shell=True)