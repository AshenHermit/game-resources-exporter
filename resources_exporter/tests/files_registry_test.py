from os import stat_result
import mock
from resources_exporter.exporter import FileInfo
from pathlib import Path

from resources_exporter.exporter import FilesRegistry

def make_stat(mtime=1):
    stat = stat_result((0, 0, 0, 0, 0, 0, 0, 0, mtime, 0))
    return stat

def os_stat_mock(path):
    return make_stat(mtime=1)

def patch_pathlib(mocker):
    mocker.patch("pathlib.Path.stat", lambda x: make_stat(mtime=1))
    mocker.patch("pathlib.Path.exists", lambda s: True)
    mocker.patch("pathlib.Path.resolve", lambda s: s)

def patch_pathlib_stat(mocker, mtime):
    mocker.patch("pathlib.Path.stat", lambda x: make_stat(mtime=mtime))

def test_fileinfo(mocker):
    patch_pathlib(mocker)
    patch_pathlib_stat(mocker, 1)
    fileinfo = FileInfo.from_file("file")
    assert fileinfo.is_file_changed() == False
    patch_pathlib_stat(mocker, 2)
    assert fileinfo.is_file_changed() == True
    
def test_res(mocker):
    patch_pathlib(mocker)
    patch_pathlib_stat(mocker, 1)
    fileinfo = FileInfo.from_file("file")
    assert fileinfo.is_file_changed() == False
    patch_pathlib_stat(mocker, 2)
    assert fileinfo.is_file_changed() == True