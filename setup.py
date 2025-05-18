from setuptools import find_packages,setup
from typing import List

HYPEN_E_DOT = '-e .'
def get_requirements(file_path:str)->List[str]:
    '''
    This function will return a list of requirements
    '''

    requirements = []
    try:

        with open(file_path,encoding='utf-8') as file_obj:

            requirements = file_obj.readlines()
            requirements = [req.replace("\n","") for req in requirements]

            if HYPEN_E_DOT in requirements:
                requirements.remove(HYPEN_E_DOT)

    except FileNotFoundError:
        print(f"Warning: {file_path} not found. No dependencies installed")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return requirements

setup(

    name = 'finance_web_app',
    version = '0.1',
    author = 'Nathan',
    author_email='menonnathanchristopher@gmail.com',
    packages = find_packages()
    install_requires = get_requirements('requirements.txt'),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',

    ],
    python_requires=">=3.12"
)