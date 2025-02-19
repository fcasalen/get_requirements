from get_requirements.run import get_requirements, get_modules_needed_to_install, PackagesInfo, Package, cli

from os.path import dirname, join, exists
from os import remove
from mocks_handler import MocksHandler
from unittest.mock import patch
import sys
import pytest

folder_path=dirname(__file__)
mh = MocksHandler()
mh.get_mocks_folder()

@pytest.fixture
def packages_in_files():
    return {
        'cli_pprinter': Package(
            files=[join(mh.mocks_folder, 'test2', 'main_test.py')],
            is_on_test_files=True
        ),
        'fake_module_2': Package(
            files=[join(mh.mocks_folder, 'test2', 'test2.py'), join(mh.mocks_folder, 'test2', 'test5.py')],
            is_on_standard_files=True
        ),
        'fake_module_3': Package(
            files=[join(mh.mocks_folder, 'test2', 'test3.py')],
            is_on_standard_files=True
        ),
        'custom_module': Package(files=[join(mh.mocks_folder, 'test2', 'test3.py')],
            is_on_standard_files=True
        ),
        'json': Package(
            files=[join(mh.mocks_folder, 'test2', 'test3.py')],
            is_on_standard_files=True,
            is_standard_module=True
        ),
        'file_handler': Package(
            files=[join(mh.mocks_folder, 'test2', 'test_main.py')],
            is_on_standard_files=False,
            is_on_test_files=True
        ),
    }

def test_get_modules_needed_to_install(packages_in_files):
    assert get_modules_needed_to_install(
        folder_path=mh.mocks_folder,
        requirements_file_path='mock_requirements_file_path',
        requirements_dev_file_path='mock_requirements_dev_file_path'
    ) == PackagesInfo(
        packages_in_files=packages_in_files,
        report=''
    )

def test_path_with_no_py_files():
    file_path = join(mh.mocks_folder, 'test1', 'test1.py')
    assert get_modules_needed_to_install(
        folder_path=file_path,
        requirements_file_path='mock_requirements_file_path',
        requirements_dev_file_path='mock_requirements_dev_file_path'
    ) == PackagesInfo()
    
def test_test1_folder():
    folder_path = join(mh.mocks_folder, 'test1')
    assert get_requirements(
        folder_path=folder_path,
        write_requirements_file=False,
        write_requirements_generated=False
    ) == PackagesInfo(
        report=mh.load_from_mocks_folder(join('test1', 'report_expected'), extension='txt').format(folder_path=join(mh.mocks_folder, 'test1'))
    )

def test_test2_folder(packages_in_files):
    folder_path = join(mh.mocks_folder, 'test2')
    inputs = iter(["y"] * 8)
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(
            folder_path=folder_path,
            write_requirements_file=False,
            write_requirements_generated=False
        )
    packages_in_files['custom_module'].is_on_requirements_file = True
    packages_in_files['oxe'] = Package(files=[], is_on_requirements_file=True)
    assert result.packages_in_files == PackagesInfo(
        requirements_packages={'oxe', 'custom_module'},
        requirements_dev_packages=set(),
        packages_in_files=packages_in_files,
        new_requirements_packages={'custom_module', 'fake_module_2', 'fake_module_3'},
        new_requirements_dev_packages={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'},
        report=mh.load_from_mocks_folder(join('test2', 'report_expected'), extension='txt').format(folder_path=join(mh.mocks_folder, 'test2'))
    ).packages_in_files
    
def test_mocks_folder(packages_in_files):
    inputs = iter(["y"] * 8)
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(
            folder_path=mh.mocks_folder,
            write_requirements_file=False,
            write_requirements_generated=False
        )
    assert result == PackagesInfo(
        requirements_packages=set(),
        requirements_dev_packages=set(),
        packages_in_files=packages_in_files,
        new_requirements_packages={'custom_module', 'fake_module_2', 'fake_module_3'},
        new_requirements_dev_packages={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'},
        report=mh.load_from_mocks_folder('report_expected', extension='txt').format(folder_path=mh.mocks_folder)
    )
    
    
def test_cli(packages_in_files):
    inputs = iter(["y"] * 16)
    requirements_file = join(mh.mocks_folder, 'requirements.txt')
    requirements_dev_file = join(mh.mocks_folder, 'requirements_dev.txt')
    if exists(requirements_file):
        remove(requirements_file)
    if exists(requirements_dev_file):
        remove(requirements_dev_file)
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder, '-dw']):
        with patch('builtins.input', lambda: next(inputs)):
            result = cli()
    assert result == PackagesInfo(
        requirements_packages=set(),
        requirements_dev_packages=set(),
        packages_in_files=packages_in_files,
        new_requirements_packages={'custom_module', 'fake_module_2', 'fake_module_3'},
        new_requirements_dev_packages={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'},
        report=mh.load_from_mocks_folder('report_expected', extension='txt').format(folder_path=mh.mocks_folder)
    )
    assert not exists(requirements_file)
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder]):
        with patch('builtins.input', lambda: next(inputs)):
            result = cli()
    assert result == PackagesInfo(
        requirements_packages=set(),
        requirements_dev_packages=set(),
        packages_in_files=packages_in_files,
        new_requirements_packages={'custom_module', 'fake_module_2', 'fake_module_3'},
        new_requirements_dev_packages={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'},
        report=mh.load_from_mocks_folder('report_expected', extension='txt').format(folder_path=mh.mocks_folder)
    )
    assert exists(requirements_file)
    remove(requirements_file)
    assert exists(requirements_dev_file)
    remove(requirements_dev_file)