from os.path import dirname, join
from mocks_handler import MocksHandler
from unittest.mock import patch
import sys
from .run import get_requirements, get_modules_needed_to_install, PackagesInfo, cli

folder_path=dirname(__file__)
mh = MocksHandler()
mh.get_mocks_folder()

def test_all(capfd):
    file_path = join(mh.mocks_folder, 'test1', 'test1.py')
    assert get_modules_needed_to_install(folder_path=file_path, skip_mock_paths=False) == set()
    out, err = capfd.readouterr()
    assert out.strip() == f'No py files found in {file_path}!'
    assert get_modules_needed_to_install(folder_path=mh.mocks_folder, skip_mock_paths=False) == {'custom_module', 'fake_module_2', 'fake_module_3'}
    folder_path = join(mh.mocks_folder, 'test1')
    assert get_requirements(folder_path=folder_path, write_requirements_file=False, skip_mock_paths=False) == PackagesInfo()
    out, err = capfd.readouterr()
    assert out.strip().splitlines()[-1] == f'No modules imported that are not standard python modules in py files in folder {folder_path}!'
    inputs = iter(["y", "y"])
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(folder_path=mh.mocks_folder, write_requirements_file=False, skip_mock_paths=False)
    assert result == PackagesInfo(
        needed_in_requirements_file={'custom_module', 'fake_module_2', 'fake_module_3'},
        already_in_requirements_file=set(),
        packages_not_needed_anymore=set(),
        new_packages_to_be_included={'custom_module', 'fake_module_2', 'fake_module_3'}
    )
    out, err = capfd.readouterr()
    assert '\n'.join(out.strip().splitlines()[-3:]) == f'''The following packages are being imported in the project in folder {mh.mocks_folder}, but are not in requirements.txt: custom_module, fake_module_2, fake_module_3.

Would you like to add them to requirements.txt? (y/n)'''
    folder_path = join(mh.mocks_folder, 'test2')
    inputs = iter(["y", "y"])
    with patch('builtins.input', lambda: next(inputs)):
        result = get_requirements(folder_path=folder_path, write_requirements_file=False, skip_mock_paths=False)
    assert result == PackagesInfo(
        needed_in_requirements_file={'custom_module', 'fake_module_2', 'fake_module_3'},
        already_in_requirements_file={'custom_module', 'oxe'},
        packages_not_needed_anymore={'oxe'},
        new_packages_to_be_included={'fake_module_2', 'fake_module_3'}
    )
    out, err = capfd.readouterr()
    assert '\n'.join(out.strip().splitlines()[-7:]) == f'''The following packages are in requirements.txt, but are not being imported in the project in folder {folder_path}: oxe.

Would you like to remove them from requirements.txt? (y/n)

The following packages are being imported in the project in folder {folder_path}, but are not in requirements.txt: fake_module_2, fake_module_3.

Would you like to add them to requirements.txt? (y/n)'''
    
def test_cli(capfd):
    inputs = iter(["y", "y"])
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder]):
        with patch('builtins.input', lambda: next(inputs)):
            cli()
    out, err = capfd.readouterr()
    assert "\n".join(out.strip().splitlines()[-5:]) == f'No py files found in {mh.mocks_folder}!\n\nNo modules imported that are not standard python modules in py files in folder {mh.mocks_folder}!\n\nrequirements.txt file was already updated!'
    with patch.object(sys, 'argv', ['run.py', '-f', mh.mocks_folder, '-dsm', '-dw']):
        with patch('builtins.input', lambda: next(inputs)):
            cli()
    out, err = capfd.readouterr()
    assert "\n".join(out.strip().splitlines()[-7:]) == 'needed_in_requirements_file: custom_module, fake_module_2, fake_module_3\n\nalready_in_requirements_file: None\n\npackages_not_needed_anymore: None\n\nnew_packages_to_be_included: custom_module, fake_module_2, fake_module_3'