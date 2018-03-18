from setuptools import setup, find_packages

version_parts = (0, 13, 0, 'a', 4)
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
        'ribosome==13.0.0a22',
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
