'''
Script to clone down breakpad in a format that we'll be using for further development.
'''

import os
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

        print('Step 3, clone depot_tools')
        subprocess.check_call('git clone https://chromium.googlesource.com/chromium/tools/depot_tools', shell=True)

        print('Step 4, put depot_tools in PATH before everything else')
        os.environ['PATH'] = os.path.join(LOCAL_DIR, 'depot_tools') + os.environ['PATH']

        print('Step 5, fetch breakpad')
        os.mkdir('breakpad')
        os.chdir('breakpad')
        subprocess.check_call('fetch breakpad', shell=True)