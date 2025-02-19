from os.path import isfile, exists, join, basename, dirname
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

class Package(BaseModel):
    files:list[str] = []
    is_on_standard_files:bool = False
    is_standard_module:bool = False
    is_on_requirements_file:bool = False
    is_on_requirements_dev_file:bool = False

class PackagesInfo(BaseModel):
    requirements_packages:set = set()
    requirements_dev_packages:set = set()
    packages_in_files:dict[str, Package] = {}
    new_requirements_packages:set = set()
    new_requirements_dev_packages:set = set()
    report:str = ''
  
def get_modules_needed_to_install(folder_path:str, requirements_file_path:str, requirements_dev_file_path:str) -> PackagesInfo:
    "returns imported modules in py files in `folder_path`"
    CToolStringArgs(
        folder_path=folder_path
    )
    if folder_path is None:
        folder_path = getcwd()
    if not exists(folder_path):
        raise ValueError(f"folder_path {folder_path} doesn't exist!")
    already_in_requirements_file = set()
    if exists(requirements_file_path):
        already_in_requirements_file = set(FileHandler.load(requirements_file_path, load_first_value=True).splitlines())
    already_in_requirements_dev_file = set()
    if exists(requirements_dev_file_path):
        already_in_requirements_dev_file = set(FileHandler.load(requirements_file_path, load_first_value=True).splitlines())
    file_paths = [f for f in glob(f'{folder_path}/**/*', recursive=True) if isfile(f) and f[-3:] == '.py']
    pi = PackagesInfo(
        requirements_packages=already_in_requirements_file,
        requirements_dev_packages=already_in_requirements_dev_file,
        new_requirements_packages=already_in_requirements_file,
        new_requirements_dev_packages=already_in_requirements_dev_file
    )
    if not file_paths:
        CLIPPrinter.red(f'No py files found in {folder_path}!')
        return pi
    standard_modules = get_standard_python_libraries()
    pattern = r'^(?!\s*#)\s*(?:from\s+(\S+)\s+import\s+\S+|import\s+(\S+))'
    for file in file_paths:
        CLIPPrinter.white(f"Checking file {file}")
        data = FileHandler.load(file_paths=file, load_first_value=True, progress_bar=False)
        matches = finditer(pattern, data, MULTILINE)
        modules_found = [f.group(1).lower() if f.group(1) else f.group(2).lower() for f in matches]
        modules_found = [f.split('.')[0] for f in modules_found]
        modules_found = [f for f in modules_found if f != '']
        for mf in modules_found:
            if mf not in pi.packages_in_files:
                pi.packages_in_files[mf] = Package()
            if not file.endswith('_test.py') and not basename(file).startswith('test_') and not basename(file) == 'conftest.py':
                pi.packages_in_files[mf].is_on_standard_files = True
            if mf in standard_modules:
                pi.packages_in_files[mf].is_standard_module = True
            pi.packages_in_files[mf].files.append(file)
            if mf in pi.requirements_packages:
                pi.packages_in_files[mf].is_on_requirements_file = True
            if mf in pi.requirements_dev_packages:
                pi.packages_in_files[mf].is_on_requirements_dev_file = True
    for mod_in_req in pi.requirements_packages:
        if mod_in_req not in pi.packages_in_files:
            pi.packages_in_files[mod_in_req] = Package()
        pi.packages_in_files[mod_in_req].is_on_requirements_file = True
        if mod_in_req in standard_modules:
            pi.packages_in_files[mod_in_req].is_standard_module = True
    for mod_in_req_dev in pi.requirements_dev_packages:
        if mod_in_req_dev not in pi.packages_in_files:
            pi.packages_in_files[mod_in_req_dev] = Package()
        pi.packages_in_files[mod_in_req_dev].is_on_requirements_dev_file = True
        if mod_in_req_dev in standard_modules:
            pi.packages_in_files[mod_in_req_dev].is_standard_module = True
    return pi

def get_requirements(folder_path:str = None, write_requirements_file:bool = True, requirements_file_path:str = None, requirements_dev_file_path:str = None, write_requirements_generated:bool = True) -> PackagesInfo:
    """
    Assess packages being imported in py files inside a given folder in relation to the requirements.txt and requirements_dev.txt files.
    
    User can choose to remove (if package is not being imported anymore but it's in requirements) or add (if package is being imported but not in requirements) packages to the requirements.txt and requirements_dev.txt files.
    
    Creates a report with the differences between the current requirements.txt and requirements_dev.txt and the new ones after considering the user's choices.

    Args:
        folder_path (str, optional): folder_path to search in. Defaults to None (if None, will use current directory)
        write_requirements_file (bool, optional): will write the requirements.txt file if True. Defaults to True.
        requirements_file_path (str, optional): path to the requirements.txt file. Defaults to None (will use folder_path/requirements.txt)
        requirements_dev_file_path (str, optional): path to the requirements_dev.txt file. Defaults to None (will use folder_path/requirements_dev.txt
        write_requirements_generated (bool, optional): will write a file with the date and time the requirements were generated. Defaults to True.
        
    Returns:
        PacakagesInfo: class with the following attributes:
            requirements_packages (set): set with modules in requirements.txt
            requirements_dev_packages (set): set with modules in requirements_dev.txt
            new_requirements_packages (set): set with modules after considering the user's choices
            new_requirements_dev_packages (set): set with modules for dev after considering the user's choices
            report (str): text with the differences between the current requirements.txt and requirements_dev.txt and the new ones after considering the user's choices
            packages_in_files (dict): dict with modules being imported in py files and the files they are being imported from with the following attributes:
                files (list): list of files the module is being imported from
                is_on_standard_files (bool): True if the module is being imported from a standard file
                is_standard_module (bool): True if the module is a standard python module
                is_on_requirements_file (bool): True if the module is in requirements.txt
                is_on_requirements_dev_file (bool): True if the module is in requirements_dev.txt
    """
    if requirements_file_path is None:
        requirements_file_path = join(folder_path, 'requirements.txt')
    if requirements_dev_file_path is None:
        requirements_dev_file_path = join(folder_path, 'requirements_dev.txt')
    pi = get_modules_needed_to_install(
        folder_path=folder_path,
        requirements_file_path=requirements_file_path,
        requirements_dev_file_path=requirements_dev_file_path
    )
    standard_packages_not_needed_anymore_text = "\nNo packages found in this situation!"
    new_standard_packages_to_be_included_text = "\nNo packages found in this situation!"
    dev_packages_not_needed_anymore_text = "\nNo packages found in this situation!"
    new_dev_packages_to_be_included_text = "\nNo packages found in this situation!"
    standard_packages_not_needed_anymore = [k for k,v in pi.packages_in_files.items() if (not v.is_on_standard_files or v.is_standard_module) and v.is_on_requirements_file]
    if standard_packages_not_needed_anymore:
        standard_packages_not_needed_anymore_text = ''
        for p in sorted(standard_packages_not_needed_anymore):
            standard_packages_not_needed_anymore_text += f'\n--{p}: '
            CLIPPrinter.yellow(f'{p}: Would you like to remove it from requirements.txt? (y/n)')
            if input().lower() == 'y':
                pi.new_requirements_packages.remove(p)
                standard_packages_not_needed_anymore_text += 'removed'
            else:
                standard_packages_not_needed_anymore_text += 'maintained'
    new_standard_packages_to_be_included = [k for k,v in pi.packages_in_files.items() if v.is_on_standard_files and not v.is_on_requirements_file and not v.is_standard_module]
    if new_standard_packages_to_be_included:
        new_standard_packages_to_be_included_text = ''
        for p in sorted(new_standard_packages_to_be_included):
            new_standard_packages_to_be_included_text += f'\n--{p}: '
            CLIPPrinter.yellow(f'{p}: Would you like to add it to requirements.txt? (y/n)')
            if input().lower() == 'y':
                pi.new_requirements_packages.add(p)
                new_standard_packages_to_be_included_text += 'added'
            else:
                new_standard_packages_to_be_included_text += 'not added'
    if write_requirements_file:
        FileHandler.write({requirements_file_path: '\n'.join(sorted(pi.new_requirements_packages))})

    dev_packages_not_needed_anymore = [k for k,v in pi.packages_in_files.items() if (not v.files or v.is_standard_module) and v.is_on_requirements_dev_file]
    if dev_packages_not_needed_anymore:
        dev_packages_not_needed_anymore_text = ""
        for p in sorted(dev_packages_not_needed_anymore):
            dev_packages_not_needed_anymore_text = f'\n--{p}: '
            CLIPPrinter.cyan(f'{p}: Would you like to remove it from requirements_dev.txt? (y/n)')
            if input().lower() == 'y':
                pi.new_requirements_dev_packages.remove(p)
                dev_packages_not_needed_anymore_text += 'removed'
            else:
                dev_packages_not_needed_anymore_text += 'maintained'
    new_dev_packages_to_be_included = [k for k,v in pi.packages_in_files.items() if v.files and not v.is_standard_module and not v.is_on_requirements_dev_file ]
    if new_dev_packages_to_be_included:
        new_dev_packages_to_be_included_text = ''
        for p in sorted(new_dev_packages_to_be_included):
            new_dev_packages_to_be_included_text += f'\n--{p}: '
            CLIPPrinter.cyan(f'{p}: Would you like to add it to requirements_dev.txt? (y/n)')
            if input().lower() == 'y':
                pi.new_requirements_dev_packages.add(p)
                new_dev_packages_to_be_included_text += 'added'
            else:
                new_dev_packages_to_be_included_text += 'not added'
    if write_requirements_file:
        FileHandler.write({requirements_dev_file_path: '\n'.join(sorted(pi.new_requirements_dev_packages))})
    if write_requirements_generated:
        FileHandler.write({join(folder_path, '.requirements_generated'): f'{datetime.now(UTC).isoformat()}'})
    report = FileHandler.load(join(dirname(__file__), 'report_template.txt'), load_first_value=True)
    pi.report = report.format(
        folder_path=folder_path,
        standard_packages_not_needed_anymore_text=standard_packages_not_needed_anymore_text,
        new_standard_packages_to_be_included_text=new_standard_packages_to_be_included_text,
        dev_packages_not_needed_anymore_text=dev_packages_not_needed_anymore_text,
        new_dev_packages_to_be_included_text=new_dev_packages_to_be_included_text
    )
    CLIPPrinter.green(pi.report)
    return pi

def cli():
    parser = ArgumentParser(
        description="Assess packages being imported in py files inside a given folder in relation to the requirements.txt and requirements_dev.txt files."\
        "\nUser can choose to remove (if package is not being imported anymore but it's in requirements) or add (if package is being imported but not in requirements) packages to the requirements.txt and requirements_dev.txt files."\
        "\nCreates a report with the differences between the current requirements.txt and requirements_dev.txt and the new ones after considering the user's choices."
    )
    parser.add_argument("-f", help="Path to the folder to search in. Default to current directory if not passed")
    parser.add_argument("-dw", action='store_true', help="Don't write the requirements.txt file, only find the differences between the existing one and what is needed!")
    parser.add_argument("-dwg", action='store_true', help="Don't write the requirements_generated file!")
    parser.add_argument("-rf", help="Relative path to the requirements.txt file. Default to folder_path/requirements.txt")
    parser.add_argument("-rdf", help="Relative path to the requirements_dev.txt file. Default to folder_path/requirements_dev.txt")
    args = parser.parse_args()
    if not args.f:
        folder_path = getcwd()
    else:
        folder_path = args.f
    CLIPPrinter.white(f'making requirements.txt based on folder {folder_path}!')
    return get_requirements(
        folder_path=folder_path,
        write_requirements_file=not args.dw,
        requirements_file_path=args.rf,
        requirements_dev_file_path=args.rdf,
        write_requirements_generated=args.dwg
    )

if __name__ == '__main__':
    cli()