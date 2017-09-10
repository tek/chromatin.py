from setuptools import setup, find_packages

version_parts = (0, 9, 3)
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
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*']),
    install_requires=[
        'ribosome~=11.0.0',
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
