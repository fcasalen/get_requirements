from get_requirements.get_standard_python_libraries import get_standard_python_libraries

def test_all():
    standard_libraries = get_standard_python_libraries()
    assert not {'re', 'os', 'asyncio', 'subprocess'} - set(standard_libraries)