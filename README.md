check for imports in py files in a directory and creates a requirements.txt file

## Shell Commands

```bash
#checking a given folder
get_requirements -f folder

#checking current directory
get_requirements

#checking current directory, but not writing the requirements.txt file, only finding the differences
get_requirements -dw

#checking current directory and looking in all py files, including the test ones
get_requirements -is_dev

```

# Python

```python
from get_requirements import get_requirements

#checking a given folder
get_requirements(folder_path="folder_path")

#checking current directory
get_requirements()

#checking current directory, but not writing the requirements.txt file, only finding the differences
get_requirements(write_requirements_file=False)

#checking current directory and looking in all py files, including the test ones
get_requirements(is_dev_requirements=True)
```
