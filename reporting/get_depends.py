'''
Script to clone down breakpad and others in a format that we'll be using for further development.
'''

import hashlib
import io
import multiprocessing.pool
import os
import shutil
import subprocess
import zipfile

import requests

try:
    # py2
    raw_input
    input = raw_input
except:
    # py3
    pass

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))
LOCAL_DIR = os.path.join(THIS_FOLDER, 'local')
BOOST_TEMP_FOLDER = os.path.join(LOCAL_DIR, 'boost_tmp')
BOOST_FINAL_FOLDER = os.path.join(LOCAL_DIR, 'boost')

def getGoogleToolchain():
    ''' gets depot_tools / breakpad '''
    print('Step 4: clone depot_tools')
    subprocess.check_call(['git', 'clone', 'https://chromium.googlesource.com/chromium/tools/depot_tools.git'], shell=True)

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

def getBoost():
    ''' gets boost ready to use '''
    print('Step 7: fetch Boost 1.71')
    data = requests.get('https://dl.bintray.com/boostorg/release/1.71.0/source/boost_1_71_0.zip').content

    print('Step 8: verifying sha256 hash')
    if hashlib.sha256(data).hexdigest().lower() != '85a94ac71c28e59cf97a96714e4c58a18550c227ac8b0388c260d6c717e47a69':
        print ("HASH DID NOT MATCH!")
        input('Press enter to continue... (though you should try to see why the hash doesn\'t match... something bad may be happening!)')

    print('Step 9: extracting Boost')
    # workaround long paths with \\?\
    zipfile.ZipFile(io.BytesIO(data)).extractall('\\\\?\\' + BOOST_TEMP_FOLDER)

    print('Step 10: coerce boost folder to not have version')
    # get one folder name in here (should be boost_version)
    actualBoostFolder = os.path.join(BOOST_TEMP_FOLDER, os.listdir(BOOST_TEMP_FOLDER)[0])

    os.mkdir(BOOST_FINAL_FOLDER)

    for thing in os.listdir(actualBoostFolder):
        fullOldPath = os.path.join(actualBoostFolder, thing)
        fullNewPath = os.path.join(BOOST_FINAL_FOLDER, thing)
        shutil.move(fullOldPath, fullNewPath)

    shutil.rmtree(BOOST_TEMP_FOLDER, ignore_errors=True)

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

        print ("... Remaining steps will be done asynchronously!")
        # now slower things (do in multiple processes)
        pool = multiprocessing.pool.ThreadPool(processes=8)
        results = []
        results.append(pool.apply_async(func=getGoogleToolchain))
        results.append(pool.apply_async(func=getBoost))

        for i in results:
            i.get()
