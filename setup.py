from setuptools import setup, find_packages

setup(
    name='get_requirements',
    version='0.1.2',
    license="GNU General Public License",
    author="fcasalen",
    author_email="fcasalen@gmail.com",
    description="check for imports in py files in a directory and creates a requirements.txt file",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').readlines(),
    long_description=open("README.md").read(),
    classifiers=[
        "Development Status :: 5 - Prodution/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12"
    ],
    entry_points={ "console_scripts": [
        "get_requirements=get_requirements.run:cli"
    ]}
)
