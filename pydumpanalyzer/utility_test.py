''' this is where we have tests for utilities '''
import os

from utility import getUniqueId, getUniqueTableName, temporaryFilePath, zipDirectoryToBytesIo

def test_unique_id():
    ''' makes sure we get unique ids on each getUniqueId() call '''
    uids = set()
    for i in range(100):
        uids.add(getUniqueId())

    assert len(uids) == 100

def test_unique_table_name():
    ''' makes sure we get a unique table name '''
    names = set()
    for i in range(100):
        names.add(getUniqueTableName())

    assert len(names) == 100

    # make sure it doesn't have a - or . and does not start with a number
    for i in names:
        assert i[0] not in [0,1,2,3,4,5,6,7,8,9]
        assert '-' not in i
        assert '.' not in i

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