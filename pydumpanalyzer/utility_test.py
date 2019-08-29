''' this is where we have tests for utilities '''
import os

from utility import getUniqueId, temporaryFilePath, zipDirectoryToBytesIo

def test_unique_id():
    ''' makes sure we get unique ids on each getUniqueId() call '''
    uids = set()
    for i in range(100):
        uids.add(getUniqueId())

    assert len(uids) == 100

def test_temp_file_path_with_a_file():
    ''' ensures temporaryFilePaths() can be created and delete appropriately with a file '''
    testPath = None
    with temporaryFilePath() as t:
        testPath = str(t)
        assert not os.path.exists(t)
        with open(t, 'w') as f:
            f.write('bleh')
        assert os.path.isfile(t)

    assert not os.path.exists(testPath)

def test_temp_file_path_with_a_directory():
    ''' ensures temporaryFilePaths() can be created and delete appropriately with a folder '''
    testPath = None
    with temporaryFilePath() as t:
        testPath = str(t)
        assert not os.path.exists(t)
        os.mkdir(t)
        with open(os.path.join(t, 'myfile'), 'w') as f:
            f.write('bleh')
        assert os.path.isdir(t)

    assert not os.path.exists(testPath)

def test_zip_directory_to_bytes_io():
    ''' ensures we can zip a directory to io.BytesIO '''
    with temporaryFilePath() as tempFile:
        # make a directory
        os.mkdir(tempFile)

        # make a file in there
        with open(os.path.join(tempFile, 'tmp'), 'w') as f:
            f.write('bleh')

        binaryData = zipDirectoryToBytesIo(tempFile).read()
        assert len(binaryData) > 10
        assert binaryData[0] == 0x50 # all zip files start with 0x50