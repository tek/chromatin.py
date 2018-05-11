from setuptools import setup, find_packages

version_parts = (0, 13, 0, 'a', 6)
version = '.'.join(map(str, version_parts))

setup(
    name='chromatin',
    description='neovim python plugin manager',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/chromatin',
    include_package_data=True,
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*', 'tests', 'tests.*']),
    install_requires=[
        'ribosome==13.0.0a50',
    ],
    tests_require=[
        'kallikrein',
    ],
    entry_points={
        'console_scripts': [
            'crm_run = chromatin.cli:run',
        ],
    },
)
