from os.path import dirname, join, exists
from os import remove
from mocks_handler import MocksHandler
from unittest.mock import patch
import sys
from get_requirements.run import get_requirements, get_modules_needed_to_install, PackagesInfo, cli

folder_path=dirname(__file__)
mh = MocksHandler()
mh.get_mocks_folder()

def test_get_modules_needed_to_install():
    assert get_modules_needed_to_install(folder_path=mh.mocks_folder) == {
        'custom_module': [join(mh.mocks_folder, 'test2', 'test3.py')],
        'fake_module_2': [join(mh.mocks_folder, 'test2', 'test2.py')],
        'fake_module_3': [join(mh.mocks_folder, 'test2', 'test3.py')]
    }

def test_path_with_no_py_files(capfd):
    file_path = join(mh.mocks_folder, 'test1', 'test1.py')
    assert get_modules_needed_to_install(folder_path=file_path) == set()
    out, err = capfd.readouterr()
    assert out.strip() == f'No py files found in {file_path}!'

def test_test1_folder(capfd):
    folder_path = join(mh.mocks_folder, 'test1')
    assert get_requirements(folder_path=folder_path, write_requirements_file=False) == PackagesInfo()
    out, err = capfd.readouterr()
    assert out.strip().splitlines()[-1] == f'No modules imported that are not standard python modules in py files in folder {folder_path}!'

def test_test2_folder(capfd):
    folder_path = join(mh.mocks_folder, 'test2')
    inputs = iter(["y", "y"])
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(folder_path=folder_path, write_requirements_file=False)
    assert result == PackagesInfo(
        needed_in_requirements_file_data={
            'custom_module': [join(mh.mocks_folder, 'test2', 'test3.py')],
            'fake_module_2': [join(mh.mocks_folder, 'test2', 'test2.py')],
            'fake_module_3': [join(mh.mocks_folder, 'test2', 'test3.py')]
        },
        needed_in_requirements_file={'custom_module', 'fake_module_2', 'fake_module_3'},
        already_in_requirements_file={'custom_module', 'oxe'},
        packages_not_needed_anymore={'oxe'},
        new_packages_to_be_included={'fake_module_2', 'fake_module_3'}
    )
    out, err = capfd.readouterr()
    assert '\n'.join(out.strip().splitlines()[-5:]) == f'''The following packages are being imported in the project in folder {join(mh.mocks_folder, 'test2')}, but are not in requirements.txt:
fake_module_2 ({join(mh.mocks_folder, 'test2', 'test2.py')})
fake_module_3 ({join(mh.mocks_folder, 'test2', 'test3.py')}).

Would you like to add them to requirements.txt? (y/n)'''
    
def test_mocks_folder(capfd):
    inputs = iter(["y", "y"])
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(folder_path=mh.mocks_folder, write_requirements_file=False)
    assert result == PackagesInfo(
        needed_in_requirements_file_data={
            'fake_module_2': [join(mh.mocks_folder, 'test2', 'test2.py')],
            'fake_module_3': [join(mh.mocks_folder, 'test2', 'test3.py')],
            'custom_module': [join(mh.mocks_folder, 'test2', 'test3.py')]
        },
        needed_in_requirements_file={'custom_module', 'fake_module_2', 'fake_module_3'},
        already_in_requirements_file=set(),
        packages_not_needed_anymore=set(),
        new_packages_to_be_included={'custom_module', 'fake_module_2', 'fake_module_3'}
    )
    out, err = capfd.readouterr()
    assert '\n'.join(out.strip().splitlines()[-6:]) == f'''The following packages are being imported in the project in folder {mh.mocks_folder}, but are not in requirements.txt:
fake_module_2 ({join(mh.mocks_folder, 'test2', 'test2.py')})
fake_module_3 ({join(mh.mocks_folder, 'test2', 'test3.py')})
custom_module ({join(mh.mocks_folder, 'test2', 'test3.py')}).

Would you like to add them to requirements.txt? (y/n)'''
    
def test_mocks_folder_is_dev(capfd):
    inputs = iter(["y", "y"])
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(folder_path=mh.mocks_folder, write_requirements_file=False, is_dev_requirements=True)
    assert result == PackagesInfo(
        needed_in_requirements_file_data={
            'cli_pprinter': [join(mh.mocks_folder, 'test2', 'main_test.py')],
            'fake_module_2': [join(mh.mocks_folder, 'test2', 'test2.py')],
            'fake_module_3': [join(mh.mocks_folder, 'test2', 'test3.py')],
            'custom_module': [join(mh.mocks_folder, 'test2', 'test3.py')],
            'file_handler': [join(mh.mocks_folder, 'test2', 'test_main.py')]
        },
        needed_in_requirements_file={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'},
        already_in_requirements_file=set(),
        packages_not_needed_anymore=set(),
        new_packages_to_be_included={'custom_module', 'fake_module_2', 'fake_module_3', 'cli_pprinter', 'file_handler'}
    )
    out, err = capfd.readouterr()
    assert '\n'.join(out.strip().splitlines()[-8:]) == f'''The following packages are being imported in the project in folder {mh.mocks_folder}, but are not in requirements.txt:
cli_pprinter ({join(mh.mocks_folder, 'test2', 'main_test.py')})
fake_module_2 ({join(mh.mocks_folder, 'test2', 'test2.py')})
fake_module_3 ({join(mh.mocks_folder, 'test2', 'test3.py')})
custom_module ({join(mh.mocks_folder, 'test2', 'test3.py')})
file_handler ({join(mh.mocks_folder, 'test2', 'test_main.py')}).

Would you like to add them to requirements.txt? (y/n)'''

def test_cli(capfd):
    inputs = iter(["y", "y"])
    requirements_file = join(mh.mocks_folder, 'requirements.txt')
    if exists(requirements_file):
        remove(requirements_file)
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder, '-dw']):
        with patch('builtins.input', lambda: next(inputs)):
            cli()
    out, err = capfd.readouterr()
    assert "\n".join(out.strip().splitlines()[-7:]) == 'needed_in_requirements_file: custom_module, fake_module_2, fake_module_3\n\nalready_in_requirements_file: None\n\npackages_not_needed_anymore: None\n\nnew_packages_to_be_included: custom_module, fake_module_2, fake_module_3'
    assert not exists(requirements_file)
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder]):
        with patch('builtins.input', lambda: next(inputs)):
            cli()
    out, err = capfd.readouterr()
    assert "\n".join(out.strip().splitlines()[-1:]) == 'new_packages_to_be_included: custom_module, fake_module_2, fake_module_3'
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder]):
        with patch('builtins.input', lambda: next(inputs)):
            cli()
    out, err = capfd.readouterr()
    assert "\n".join(out.strip().splitlines()[-1:]) == 'requirements.txt file was already updated!'
    if exists(requirements_file):
        remove(requirements_file)
    