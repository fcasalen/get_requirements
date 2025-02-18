from os.path import isfile, exists, join, basename
from os import getcwd
from glob import glob
from re import MULTILINE, finditer
from argparse import ArgumentParser
from pydantic import BaseModel
from cli_pprinter import CLIPPrinter
from file_handler import FileHandler
from datetime import datetime, UTC
from .get_standard_python_libraries import get_standard_python_libraries

class CToolStringArgs(BaseModel):
    folder_path:str|None

class PackagesInfo(BaseModel):
    needed_in_requirements_file_data:dict|None = None
    needed_in_requirements_file:set|None = None
    already_in_requirements_file:set|None = None
    packages_not_needed_anymore:set|None = None
    new_packages_to_be_included:set|None = None
  
def get_modules_needed_to_install(folder_path:str, is_dev_requirements:bool = False):
    "returns imported modules in py files in `folder_path`"
    CToolStringArgs(
        folder_path=folder_path
    )
    if folder_path is None:
        folder_path = getcwd()
    if not exists(folder_path):
        raise ValueError(f"folder_path {folder_path} doesn't exist!")
    if is_dev_requirements:
        file_paths = [f for f in glob(f'{folder_path}/**/*', recursive=True) if isfile(f) and f[-3:] == '.py']
    else:
        file_paths = [f for f in glob(f'{folder_path}/**/*', recursive=True) if isfile(f) and f[-3:] == '.py' and not f.endswith('_test.py') and not basename(f).startswith('test_')]
    if not file_paths:
        CLIPPrinter.red(f'No py files found in {folder_path}!')
        return set()
    pattern = r'^(?!\s*#)\s*(?:from\s+(\S+)\s+import\s+\S+|import\s+(\S+))'
    standard_modules = get_standard_python_libraries()
    modules = {}
    for file in file_paths:
        CLIPPrinter.white(f"Checking file {file}")
        data = FileHandler.load(file_paths=file, load_first_value=True, progress_bar=False)
        matches = finditer(pattern, data, MULTILINE)
        modules_found = [f.group(1).lower() if f.group(1) else f.group(2).lower() for f in matches]
        modules_found = [f.split('.')[0] for f in modules_found]
        modules_found = [f for f in modules_found if f != '']
        for mf in modules_found:
            if mf in standard_modules:
                continue
            if mf not in modules:
                modules[mf] = [file]
            else:
                modules[mf].append(file)
    return modules

def get_requirements(folder_path:str = None, write_requirements_file:bool = True, is_dev_requirements:bool = False):
    """assess packages being imported in py files inside a given folder and writes them to a requirements.txt file

    Args:
        folder_path (str, optional): folder_path to search in. Defaults to None (if None, will use current directory)
        write_requirements_file (bool, optional): will write the requirements.txt file if True. Defaults to True.
        is_dev_requirements (bool, optional): if True will write requirements_dev.txt instead of requirements.txt and look in all py files. If False, will look in py files that don't start with test_ or end with _test.py. Defaults to False.

    Returns:
        PacakagesInfo: class with the following attributes:
            needed_in_requirements_file_data (dict): dict with modules being imported in py files and the files they are being imported from
            needed_in_requirements_file (set): set with modules being imported in py files
            already_in_requirements_file (set): set with modules already in requirements.txt
            packages_not_needed_anymore (set): set with modules in requirements.txt that are not being imported in py files
            new_packages_to_be_included (set): set with modules being imported in py files that are not in requirements.txt
    """
    requirements_file_path = join(folder_path, 'requirements.txt')
    if is_dev_requirements:
        requirements_file_path = join(folder_path, 'requirements_dev.txt')
    needed_in_requirements_file_data = get_modules_needed_to_install(folder_path=folder_path, is_dev_requirements=is_dev_requirements)
    needed_in_requirements_file = []
    if needed_in_requirements_file_data:
        needed_in_requirements_file = set(needed_in_requirements_file_data)
    if not needed_in_requirements_file:
        CLIPPrinter.red(f'No modules imported that are not standard python modules in py files in folder {folder_path}!')
        return PackagesInfo()
    already_in_requirements_file = set()
    if exists(requirements_file_path):
        already_in_requirements_file = set(FileHandler.load(requirements_file_path, load_first_value=True).splitlines())
    new_packages_to_be_included = needed_in_requirements_file - already_in_requirements_file
    packages_not_needed_anymore = already_in_requirements_file - needed_in_requirements_file
    new_requirements_packages = already_in_requirements_file.copy()
    if packages_not_needed_anymore:
        CLIPPrinter.white(f'The following packages are in requirements.txt, but are not being imported in the project in folder {folder_path}: {", ".join(sorted(packages_not_needed_anymore))}.\n\nWould you like to remove them from requirements.txt? (y/n)')
        resposta = input()
        if resposta.lower() == 'y':
            new_requirements_packages -= packages_not_needed_anymore
    if new_packages_to_be_included:
        text = '\n'.join([f'{k} ({", ".join(v)})' for k,v in needed_in_requirements_file_data.items() if k in sorted(new_packages_to_be_included)])
        CLIPPrinter.white(f'The following packages are being imported in the project in folder {folder_path}, but are not in requirements.txt:\n{text}.\n\nWould you like to add them to requirements.txt? (y/n)')
        resposta = input()
        if resposta.lower() == 'y':
            new_requirements_packages |= new_packages_to_be_included
    if write_requirements_file:
        FileHandler.write({requirements_file_path: '\n'.join(sorted(new_requirements_packages))})
    FileHandler.write({join(folder_path, '.requirements_generated'): f'{datetime.now(UTC).isoformat()}'})
    return PackagesInfo(
        needed_in_requirements_file_data=needed_in_requirements_file_data,
        needed_in_requirements_file=sorted(needed_in_requirements_file),
        already_in_requirements_file=sorted(already_in_requirements_file),
        packages_not_needed_anymore=sorted(packages_not_needed_anymore),
        new_packages_to_be_included=sorted(new_packages_to_be_included)
    )

def cli():
    parser = ArgumentParser(description="A script that writes requirements.txt file for a project based on imports in py files in a project's folder")
    parser.add_argument("-f", help="Path to the folder to search in. Default to current directory if not passed")
    parser.add_argument("-dw", action='store_true', help="Don't write the requirements.txt file, only find the differences between the existing one and what is needed!")
    parser.add_argument("-is_dev", action='store_true', help="Will write requirements_dev.txt instead of requirements.txt and look in all py files. If False, will look in py files that don't start with test_ or end with _test.py.")
    args = parser.parse_args()
    if not args.f:
        folder_path = getcwd()
    else:
        folder_path = args.f
    print('oxe', folder_path)
    CLIPPrinter.white(f'making requirements.txt based on folder {folder_path}!')
    packages_info = get_requirements(folder_path=folder_path, write_requirements_file=not args.dw, is_dev_requirements=args.is_dev)
    if not packages_info.new_packages_to_be_included:
        CLIPPrinter.green('requirements.txt file was already updated!')
        return
    packages_info = packages_info.model_dump()
    for k,v in packages_info.items():
        if not v:
            CLIPPrinter.white(f'{k}: None')
        else:
            CLIPPrinter.yellow(f'{k}: {", ".join(sorted(v))}')

if __name__ == '__main__':
    cli()