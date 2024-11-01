from sys import executable
from os.path import dirname, join, splitext, exists, isdir, isfile
from os import listdir

def get_standard_python_libraries():
    standard_lib_dir = join(dirname(executable), 'lib')
    standard_libraries = [splitext(f)[0] for f in listdir(standard_lib_dir) if f.endswith('.py') and f != '__init__.py' and isfile(join(standard_lib_dir, f))]
    standard_libraries += [f for f in listdir(standard_lib_dir) if isdir(join(standard_lib_dir, f)) and exists(join(standard_lib_dir, f, '__init__.py')) and not f.startswith('_')]
    return standard_libraries + ['sys']